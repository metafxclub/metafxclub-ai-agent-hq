"""Portable MT4 source contracts; no native terminal or order calls."""
import hashlib
import re
import unittest
from tests import test_mt4_unified_ea as legacy
source = legacy.UNIFIED_EA_PATH.read_text(encoding="utf-8")
code = legacy.strip_mql_comments(source)
# Reviewed 2.19 function bodies. InitializeGateway includes only the audited
# owned-cleanup insertion and relocation of READY until the runtime latch opens.
REVIEWED_FUNCTION_DIGESTS = {'ResolvePositionSize': 'ef69841527b7aa6f6f92992293408426ccf4f4e161bc19e751cdd02c10acefe7', 'ValidateRiskEnvelopeAtEntry': '9f962c852e24da5ce8a28083088feeb985afba8faad1be18b52adae1ba42b319', 'ValidateClosedBarBinding': '5d851aabeece2306ff6b257ef6d7bd5c29ee0bd3050581cc0cbb54f59e80f174', 'ValidateMarginPreflight': '09689f6f7558f246574f7f0b3fb3039b3ed64a9413d317823165a9d243071bef', 'ValidateStops': 'b7346067697c859425b8f64837c4a6ff4e1d5cb388bde7865889358bb12ee99c', 'ReconcileExecutingCommand': '4504a51d706e67b5fe8c074fc1e328869f80519c10ad034ee2bfedbef1e8ef89', 'WriteExecutionMarkers': '72705bbf9138a663e24924952f043d74caeba3b2eb10b4b0c1167a35ab3f841f', 'WriteLastOrderBar': '71b901742feb7f12425c624beefb189d4f021fe3d116aa73717b97081ccbc9cc', 'ValidateConfiguredModes': 'c393b3ee2fc3d6072953cc8f4cd503d8367048efea8f27c279bc29bbd6a12ed8', 'InitializeGateway': 'a1ede17cf029d480f8369833ee6b19143b528586bc1c54b229e85c7372c3a303'}

def body(name,text=code):
    value=legacy.named_block(text,r'\b(?:void|int|bool|string)\s+'+name+r'\s*\([^)]*\)')
    if not value: raise AssertionError(name)
    return value

class Mt4ResidentInitializationTests(unittest.TestCase):
    def test_duplicate_failure_cannot_delete_another_instances_snapshot(self):
        invalidator=body('InvalidatePublishedRuntimeState')
        self.assertRegex(invalidator,r'^\s*if\(g_channel_lock_handle == INVALID_HANDLE\)\s*return;')
        self.assertEqual(invalidator.count('FileDelete('),3)

    def test_failed_instance_diagnostic_requires_own_lock_and_releases_only_temporary_lock(self):
        diagnostic=body('RecordInitDiagnostic')
        self.assertLess(diagnostic.index('temporary_ownership && !AcquireChannelLock()'),diagnostic.index('WriteCommonTextAtomic('))
        self.assertRegex(diagnostic,r'if\(temporary_ownership && !AcquireChannelLock\(\)\)\s*return false;')
        self.assertRegex(diagnostic,r'if\(temporary_ownership\)\s*ReleaseChannelLock\(\);')
        self.assertLess(diagnostic.index('AppendAudit('),diagnostic.index('ReleaseChannelLock()'))

    def test_deinit_keeps_failed_init_reason_and_requires_owner_for_shared_writes(self):
        deinit=body('OnDeinit')
        owned=legacy.named_block(deinit,r'if\(g_channel_lock_handle != INVALID_HANDLE\)')
        ready=legacy.named_block(owned,r'if\(g_runtime_initialized\)')
        for call in ('AppendAudit(', 'RecordInitDiagnostic('):
            self.assertIn(call,ready)
        self.assertIn('InvalidatePublishedRuntimeState()',owned)
        tail=deinit.replace(owned,'').replace(ready,'')
        self.assertNotIn('AppendAudit(',tail)
        self.assertNotIn('RecordInitDiagnostic(',tail)

    def test_any_init_failure_remains_attached_but_cannot_open_runtime_latch(self):
        self.assertIn('AttemptGatewayInitialization();',body('OnInit'))
        self.assertNotIn('return INIT_FAILED',body('OnInit'))
        self.assertIn('return INIT_SUCCEEDED;',body('OnInit'))
        attempt=body('AttemptGatewayInitialization')
        complete=legacy.named_block(attempt,r'if\(result == INIT_SUCCEEDED\)')
        self.assertIn('g_runtime_initialized = true;',complete)
        self.assertNotIn('g_runtime_initialized = true;',attempt.replace(complete,''))
        for call in ('EventKillTimer()', 'ReleaseAccountExecutionLock()', 'ReleasePortfolioPolicyLease()', 'ReleaseChannelLock()'):
            self.assertIn(call,attempt)
        self.assertIn('return false;',attempt)

    def test_timer_and_direct_entry_points_are_closed_before_command_reads_or_order_calls(self):
        timer=body('OnTimer')
        blocked=legacy.named_block(timer,r'if\(!GatewayInitializationReady\(\)\)')
        self.assertIn('ServiceBlockedInitialization()',blocked)
        self.assertIn('return;',blocked)
        self.assertLess(timer.index('if(!GatewayInitializationReady())'),timer.index('ApplyOptionalPositionLifecycle()'))
        for name in ('ProcessCommandFile','ExecuteCommand'):
            self.assertRegex(body(name),r'^\s*if\(!GatewayInitializationReady\(\)\)\s*return;')
        for name in ('EvaluateExecutionGuard','ValidateRuntime','LifecycleCloseGuard'):
            gate=legacy.named_block(body(name),r'if\(!GatewayInitializationReady\(\)\)')
            self.assertIn('return false;',gate)

    def test_initial_publication_is_non_authorizing_and_unowned_writers_are_rejected(self):
        self.assertIn('GatewayInitializationReady() && RefreshSigningReadiness',body('BuildCapabilitiesJson'))
        self.assertIn('GatewayInitializationReady() && SignedCommandVerificationAvailable',body('BuildStatusJson'))
        for name in ('WriteSnapshot','WriteCapabilitiesSnapshot','WriteStatusSnapshot'):
            self.assertRegex(body(name),r'^\s*if\(g_init_blocked \|\| g_channel_lock_handle == INVALID_HANDLE\)\s*return false;')

    def test_only_transient_readiness_retries_at_bounded_interval_not_invalid_config_or_duplicate(self):
        transient=body('InitializationFailureIsTransient')
        for forbidden in ('GATEWAY_INPUT_CONFIGURATION_INVALID','SNAPSHOT_CHANNEL_ALREADY_OWNED','CRYPTO_SELF_TEST_FAILED','LIVE_SIGNING_KEY_PIN_MISMATCH','PORTFOLIO_POLICY_MISMATCH','LIVE_COMMISSION_POLICY_UNCONFIRMED'):
            self.assertNotIn(forbidden,transient)
        retry=body('ServiceBlockedInitialization')
        self.assertIn('elapsed < 10000',retry)
        self.assertIn('!InitializationFailureIsTransient()',retry)
        self.assertNotIn('OrderSend',retry)
        self.assertNotIn('ProcessCommandFile',retry)

    def test_disconnect_requires_new_tick_and_trade_guards_are_not_removed(self):
        self.assertRegex(body('OnTimer'),r'if\(!IsConnected\(\)\)\s*g_last_tick_millis = 0;')
        self.assertEqual(code.count('OrderSend('),1)
        self.assertEqual(code.count('OrderClose('),1)
        self.assertNotIn('ExpertRemove(',code)
        self.assertNotIn('WebRequest(',code)
        for token in ('"LIVE_NOT_ARMED"','"COMMAND_EXPIRED"','"ONE_ORDER_PER_BAR_LIMIT"','"KILL_SWITCH_ACTIVE"','ReverifyCommandEnvelope','ValidateHeartbeat','ValidateRiskEnvelopeAtEntry','WriteExecutionMarkers'):
            self.assertIn(token, code)

    def test_sizing_order_recovery_and_risk_functions_keep_reviewed_body(self):
        for name in ('ResolvePositionSize','ValidateRiskEnvelopeAtEntry','ValidateClosedBarBinding','ValidateMarginPreflight','ValidateStops','ReconcileExecutingCommand','WriteExecutionMarkers','WriteLastOrderBar','ValidateConfiguredModes'):
            self.assertEqual(hashlib.sha256(body(name).strip().encode()).hexdigest(), REVIEWED_FUNCTION_DIGESTS[name], name)

    def test_candidate_version_and_failure_telemetry_are_explicit(self):
        self.assertIn('#property version   "2.20"',code)
        self.assertIn('string EA_VERSION = "2.20";',code)
        self.assertIn('g_init_failure_reason = reason_code;',body('InitFailure'))
        self.assertIn('g_init_failure_return_code = return_code;',body('InitFailure'))
        self.assertIn('ATTACHED / BLOCKED',body('UpdateBlockedChartStatus'))

    def test_original_initialization_guards_remain_intact_before_runtime_latch(self):
        self.assertEqual(hashlib.sha256(body('InitializeGateway').strip().encode()).hexdigest(), REVIEWED_FUNCTION_DIGESTS['InitializeGateway'])
        diagnostic=body('RecordInitDiagnostic')
        self.assertIn('JsonBoolean(stage != "deinit")',diagnostic)

    def test_late_write_failure_cleanup_happens_while_channel_is_owned(self):
        initialize=body('InitializeGateway')
        releases=list(re.finditer(r'ReleaseChannelLock\(\);',initialize))
        self.assertGreaterEqual(len(releases),7)
        for release in releases:
            before=initialize[:release.start()].rstrip()
            self.assertTrue(before.endswith('InvalidatePublishedRuntimeState();'))
        for signature in (r'if\(!g_last_snapshot_write_ok\)',r'if\(!WriteCapabilitiesSnapshot\(\)\)',r'if\(!WriteStatusSnapshot\(\)\)'):
            failure=legacy.named_block(initialize,signature)
            self.assertLess(failure.index('InvalidatePublishedRuntimeState()'),failure.index('ReleaseChannelLock()'))
        duplicate=legacy.named_block(initialize,r'if\(!AcquireChannelLock\(\)\)')
        self.assertNotIn('InvalidatePublishedRuntimeState()',duplicate)
        self.assertNotIn('ReleaseChannelLock()',duplicate)

    def test_successful_latch_precedes_ready_diagnostic_and_next_timer_publication(self):
        success=legacy.named_block(body('AttemptGatewayInitialization'),r'if\(result == INIT_SUCCEEDED\)')
        self.assertLess(success.index('g_runtime_initialized = true;'),success.index('RecordInitDiagnostic('))
        timer=body('OnTimer')
        self.assertLess(timer.index('if(!GatewayInitializationReady())'),timer.index('WriteCapabilitiesSnapshot()'))
        self.assertLess(timer.index('if(!GatewayInitializationReady())'),timer.index('WriteStatusSnapshot()'))

if __name__=='__main__':
    unittest.main()
