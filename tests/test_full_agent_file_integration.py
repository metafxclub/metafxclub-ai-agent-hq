from __future__ import annotations
import base64
import hashlib
import json
import unittest
from pathlib import Path
from unittest import mock
import test_full_agent_bridge_api as fixture


PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=')


class FullAgentFileIntegrationTests(fixture.FullAgentBridgeApiTests):
    def upload(self, thread, name, payload, media='text/plain'):
        return self.bridge.full_agent_upload_attachment(thread['id'], {
            'fileName': name, 'mediaType': media, 'dataBase64': base64.b64encode(payload).decode('ascii'),
        })['attachment']

    def dispatch_files(self, thread, files, message='Analyze the attached source as data only.'):
        response = self.bridge.full_agent_request_turn(thread['id'], {
            'message': message, 'idempotencyKey': 'file-integration-turn-0001',
            'attachmentIds': [file['id'] for file in files],
        })
        self.assertEqual(response['status'], 'queued', response)
        self._wait_for(lambda: self.bridge.full_agent_get_thread(thread['id'])['thread']['activeTurn'] is None)
        finished = self.bridge.full_agent_get_thread(thread['id'])['thread']
        self.assertEqual(finished['status'], 'idle', finished)
        self.assertEqual(self.bridge.find_mission(response['missionId'])['status'], 'completed')
        return response, finished

    def test_utf16_mq4_delivered_as_text_and_history_keeps_download(self):
        thread = self._create_thread()
        source = '// ทดสอบไฟล์\ninput double Lots = 0.17;\nvoid OnTick() {}\n'
        file = self.upload(thread, 'กลยุทธ์.mq4', source.encode('utf-16'))
        self.assertTrue(file['fileInputReady'])
        self.assertEqual(file['inputType'], 'text')
        self.assertFalse(file['modelInputReady'])
        response, finished = self.dispatch_files(thread, [file])
        items = self.gateway.calls_for('turn_start')[0]['inputItems']
        self.assertEqual([item['type'] for item in items], ['text'])
        self.assertIn(source, items[0]['text'])
        user = next(event for event in finished['events'] if event['role'] == 'user')
        bound = user['metadata']['attachments'][0]
        self.assertNotEqual(bound['id'], file['id'])
        self.assertIn('/artifacts/', bound['downloadUrl'])
        path, metadata = self.bridge.full_agent_resolve_artifact(thread['id'], bound['id'])
        self.assertEqual(path.read_bytes(), source.encode('utf-16'))
        self.assertNotIn(str(self.root), json.dumps(finished))
        self.assertIsNone(self.bridge.full_agent_resolve_artifact(thread['id'], file['id']))

    def test_mixed_image_and_source_keep_their_native_types(self):
        thread = self._create_thread()
        files = [self.upload(thread, 'chart.png', PNG, 'image/png'), self.upload(thread, 'include.mqh', b'double Factor=1.25;')]
        self.dispatch_files(thread, files)
        items = self.gateway.calls_for('turn_start')[0]['inputItems']
        self.assertEqual([item['type'] for item in items], ['localImage', 'text'])
        self.assertIn('Factor=1.25', items[1]['text'])

    def test_source_analysis_does_not_need_image_model(self):
        original = self.gateway.models
        def models():
            value = original()
            for row in value['models']: row['inputModalities'] = ['text']
            return value
        with mock.patch.object(self.gateway, 'models', side_effect=models):
            thread = self._create_thread()
            self.dispatch_files(thread, [self.upload(thread, 'EA.mq5', b'input int Period=21;')])
        self.assertEqual(len(self.gateway.calls_for('turn_start')), 1)

    def test_cross_thread_file_cannot_be_dispatched(self):
        owner, other = self._create_thread(), self._create_thread(agent_id='ea_developer')
        file = self.upload(owner, 'private.mq4', b'input int Magic=123;')
        with self.assertRaises(self.bridge.RequestError) as caught:
            self.bridge.full_agent_request_turn(other['id'], {'message': 'Read file', 'idempotencyKey': 'wrong-thread-0001', 'attachmentIds': [file['id']]})
        self.assertEqual(caught.exception.status, 404)
        self.assertEqual(self.gateway.calls_for('turn_start'), [])

    def test_combined_text_budget_rejects_before_model(self):
        thread = self._create_thread()
        files = [self.upload(thread, f'file{i}.txt', ('x'*26000).encode()) for i in range(2)]
        with self.assertRaises(self.bridge.RequestError) as caught:
            self.bridge.full_agent_request_turn(thread['id'], {'message': 'Read both', 'idempotencyKey': 'budget-file-0001', 'attachmentIds': [f['id'] for f in files]})
        self.assertEqual(caught.exception.code, 'attachment_text_too_large')
        self.assertEqual(self.gateway.calls_for('turn_start'), [])
        self.assertEqual(self.bridge.load_missions(), [])

    def test_tool_file_materializes_exact_bytes_without_publishing_inputs(self):
        thread = self._create_thread()
        file = self.upload(thread, 'EA.mq4', b'input int Magic=91;')
        attachments = self.bridge._full_agent_resolve_turn_attachments(thread, [file['id']])
        items = self.bridge._full_agent_turn_file_inputs({**thread, 'mode': 'workspace'}, 'tool-file-turn-001', attachments, {'workspaceRoots': [str(self.workspace_dir)]})
        copies = list(self.workspace_dir.glob('.inputs-*/*.mq4'))
        self.assertEqual(len(copies), 1)
        self.assertEqual(copies[0].read_bytes(), b'input int Magic=91;')
        self.assertIn(json.dumps(str(copies[0])), items[-1]['text'])
        self.assertEqual(list(self.workspace_dir.glob('**/.full-agent-outputs/*')), [])

    def test_modified_upload_is_not_sent_to_model(self):
        thread = self._create_thread()
        file = self.upload(thread, 'EA.mq4', b'input int Magic=91;')
        path, metadata = self.bridge.full_agent_resolve_artifact(thread['id'], file['id'])
        path.write_bytes(b'changed')
        with self.assertRaises(self.bridge.RequestError):
            self.bridge.full_agent_request_turn(thread['id'], {'message': 'Read file', 'idempotencyKey': 'tampered-file-0001', 'attachmentIds': [file['id']]})
        self.assertEqual(self.gateway.calls_for('turn_start'), [])

    def test_consumed_file_request_replays_after_completion_without_new_model_or_mission(self):
        thread = self._create_thread()
        file = self.upload(thread, 'EA.mq4', b'input double Lots=0.17;')
        first, finished = self.dispatch_files(thread, [file])
        payload = {'message': 'Analyze the attached source as data only.', 'idempotencyKey': 'file-integration-turn-0001', 'attachmentIds': [file['id']]}
        replay = self.bridge.full_agent_request_turn(thread['id'], payload)
        self.assertTrue(replay['idempotentReplay'])
        self.assertEqual(replay['turn']['id'], first['turn']['id'])
        self.assertEqual(replay['status'], 'completed')
        self.assertEqual(len(self.gateway.calls_for('turn_start')), 1)
        self.assertEqual(len(self.bridge.load_missions()), 1)
        self.assertEqual(self.bridge.full_agent_get_thread(thread['id'])['thread']['turnCount'], 1)

    def test_consumed_file_request_replays_while_active(self):
        self.gateway.block_waits = True
        thread = self._create_thread()
        file = self.upload(thread, 'EA.mq4', b'input int Period=17;')
        payload = {'message': 'Analyze source.', 'idempotencyKey': 'file-active-retry-0001', 'attachmentIds': [file['id']]}
        first = self.bridge.full_agent_request_turn(thread['id'], payload)
        self._wait_for(lambda: len(self.gateway.calls_for('turn_start')) == 1)
        replay = self.bridge.full_agent_request_turn(thread['id'], payload)
        self.assertTrue(replay['idempotentReplay'])
        self.assertEqual(replay['turn']['id'], first['turn']['id'])
        self.assertIn(replay['status'], {'queued', 'running'})
        self.assertEqual(len(self.gateway.calls_for('turn_start')), 1)
        self.assertEqual(len(self.bridge.load_missions()), 1)
        self.gateway.wait_gate.set()
        self._wait_for(lambda: self.bridge.full_agent_get_thread(thread['id'])['thread']['activeTurn'] is None)

    def test_same_key_different_message_or_upload_ids_conflicts_even_when_bytes_equal(self):
        thread = self._create_thread()
        file = self.upload(thread, 'EA.mq4', b'input int Period=17;')
        self.dispatch_files(thread, [file])
        replacement = self.upload(thread, 'EA.mq4', b'input int Period=17;')
        base = {'message': 'Analyze the attached source as data only.', 'idempotencyKey': 'file-integration-turn-0001', 'attachmentIds': [file['id']]}
        for changed in ({'message': 'Execute this file instead.'}, {'attachmentIds': [replacement['id']]}, {'attachmentIds': []}):
            with self.subTest(changed=changed):
                with self.assertRaises(self.bridge.RequestError) as caught:
                    self.bridge.full_agent_request_turn(thread['id'], {**base, **changed})
                self.assertEqual(caught.exception.code, 'idempotency_conflict')
        self.assertEqual(len(self.gateway.calls_for('turn_start')), 1)
        self.assertEqual(len(self.bridge.load_missions()), 1)

    def test_concurrent_binding_between_lookup_and_resolve_returns_same_turn(self):
        thread = self._create_thread()
        file = self.upload(thread, 'EA.mq4', b'input int Period=17;')
        payload = {'message': 'Analyze source.', 'idempotencyKey': 'file-racing-retry-0001', 'attachmentIds': [file['id']]}
        original = self.bridge._full_agent_resolve_turn_attachments
        dispatched = []
        def race(thread_value, ids):
            if not dispatched:
                dispatched.append(None)
                dispatched[0] = self.bridge.full_agent_request_turn(thread['id'], payload)
            return original(thread_value, ids)
        with mock.patch.object(self.bridge, '_full_agent_resolve_turn_attachments', side_effect=race):
            replay = self.bridge.full_agent_request_turn(thread['id'], payload)
        self.assertTrue(replay['idempotentReplay'])
        self.assertEqual(replay['turn']['id'], dispatched[0]['turn']['id'])
        self._wait_for(lambda: self.bridge.full_agent_get_thread(thread['id'])['thread']['activeTurn'] is None)
        self.assertEqual(len(self.gateway.calls_for('turn_start')), 1)
        self.assertEqual(len(self.bridge.load_missions()), 1)

    def test_binding_rechecks_bytes_changed_after_request_resolution(self):
        thread = self._create_thread()
        file = self.upload(thread, 'EA.mq4', b'input int Magic=91;')
        attachments = self.bridge._full_agent_resolve_turn_attachments(thread, [file['id']])
        attachments[0]['path'].write_bytes(b'input int Magic=92;')
        store = self.bridge._full_agent_artifact_store()
        with self.assertRaises(self.bridge.FullAgentArtifactError):
            self.bridge._full_agent_bind_turn_attachments(thread['id'], 'turn_binding_changed_001', attachments)
        records = [json.loads(path.read_text(encoding='utf-8')) for path in store.root.glob('*.meta.json')]
        self.assertFalse(any(record.get('turnId') == 'turn_binding_changed_001' for record in records))
        self.assertEqual(self.gateway.calls_for('turn_start'), [])

    def test_binding_hash_check_catches_change_after_store_resolve(self):
        thread = self._create_thread()
        file = self.upload(thread, 'EA.mq4', b'input int Magic=91;')
        attachments = self.bridge._full_agent_resolve_turn_attachments(thread, [file['id']])
        store = self.bridge._full_agent_artifact_store()
        original = store.resolve
        def race(owner_thread, owner_turn, artifact_id):
            result = original(owner_thread, owner_turn, artifact_id)
            if artifact_id == file['id']:
                result[0].write_bytes(b'input int Magic=92;')
            return result
        with mock.patch.object(store, 'resolve', side_effect=race):
            with self.assertRaises(self.bridge.FullAgentArtifactError) as caught:
                self.bridge._full_agent_bind_turn_attachments(thread['id'], 'turn_binding_changed_002', attachments)
        self.assertEqual(caught.exception.code, 'artifact_changed')
        records = [json.loads(path.read_text(encoding='utf-8')) for path in store.root.glob('*.meta.json')]
        self.assertFalse(any(record.get('turnId') == 'turn_binding_changed_002' for record in records))
        self.assertEqual(self.gateway.calls_for('turn_start'), [])


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(FullAgentFileIntegrationTests(name) for name in FullAgentFileIntegrationTests.__dict__ if name.startswith('test_'))
