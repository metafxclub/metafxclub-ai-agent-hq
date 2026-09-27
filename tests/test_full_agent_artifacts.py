from __future__ import annotations

import base64
import importlib.util
import io
import json
import tempfile
import struct
import unittest
import zipfile
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    PROJECT_ROOT / "backend" / "local-runner" / "full_agent_artifacts.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("metafx_full_agent_artifacts_tests", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FullAgentArtifactStoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.store = self.module.FullAgentArtifactStore(self.root / "media")
        self.thread_id = "thread_media_test_0001"
        self.turn_id = "turn_media_test_0001"

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def png_bytes() -> bytes:
        return base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )

    @staticmethod
    def presentation_bytes() -> bytes:
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", "<Types />")
            archive.writestr("ppt/presentation.xml", "<p:presentation />")
        return output.getvalue()

    @staticmethod
    def jpeg_bytes(width: int = 2, height: int = 2) -> bytes:
        sof_payload = b"\x08" + struct.pack(">HH", height, width) + b"\x01\x01\x11\x00"
        sos_payload = b"\x01\x01\x00\x00\x3f\x00"
        return (
            b"\xff\xd8\xff\xc0"
            + struct.pack(">H", len(sof_payload) + 2)
            + sof_payload
            + b"\xff\xda"
            + struct.pack(">H", len(sos_payload) + 2)
            + sos_payload
            + b"\x00\xff\xd9"
        )

    @staticmethod
    def webp_bytes(width: int = 2, height: int = 2) -> bytes:
        extended = b"\x00\x00\x00\x00" + (width - 1).to_bytes(3, "little") + (
            height - 1
        ).to_bytes(3, "little")
        body = b"WEBP" + b"VP8X" + struct.pack("<I", len(extended)) + extended
        return b"RIFF" + struct.pack("<I", len(body)) + body

    @staticmethod
    def office_bytes(marker: str) -> bytes:
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", "<Types />")
            archive.writestr(marker, "<root />")
        return output.getvalue()

    @staticmethod
    def unsafe_presentation_bytes(entry_name: str, payload: bytes) -> bytes:
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", "<Types />")
            archive.writestr("ppt/presentation.xml", "<p:presentation />")
            archive.writestr(entry_name, payload)
        return output.getvalue()

    @staticmethod
    def zip_bytes(entries: dict[str, bytes]) -> bytes:
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, payload in entries.items():
                archive.writestr(name, payload)
        return output.getvalue()

    def upload(self, name: str, payload: bytes, media_type: str) -> dict:
        return self.store.save_upload(
            self.thread_id,
            self.turn_id,
            file_name=name,
            media_type=media_type,
            data_base64=base64.b64encode(payload).decode("ascii"),
        )

    def test_image_upload_is_thread_bound_path_opaque_and_integrity_checked(self) -> None:
        result = self.upload("chart.png", self.png_bytes(), "image/png")
        self.assertEqual(result["kind"], "image")
        self.assertTrue(result["modelInputReady"])
        self.assertEqual(result["name"], "chart.png")
        self.assertNotIn(str(self.root), json.dumps(result))

        path, metadata = self.store.resolve(self.thread_id, self.turn_id, result["id"])
        self.assertEqual(path.read_bytes(), self.png_bytes())
        self.assertEqual(metadata["sha256"], result["sha256"])
        with self.assertRaises(self.module.FullAgentArtifactError) as caught:
            self.store.resolve("thread_media_test_0002", self.turn_id, result["id"])
        self.assertEqual(caught.exception.status, 404)

        path.write_bytes(path.read_bytes() + b"tampered")
        with self.assertRaises(self.module.FullAgentArtifactError) as integrity:
            self.store.resolve(self.thread_id, self.turn_id, result["id"])
        self.assertEqual(integrity.exception.code, "artifact_integrity_failed")

    def test_rejects_traversal_mime_mismatch_bad_base64_and_fake_image(self) -> None:
        cases = (
            {
                "file_name": "../chart.png",
                "media_type": "image/png",
                "data_base64": base64.b64encode(self.png_bytes()).decode("ascii"),
            },
            {
                "file_name": "chart.png",
                "media_type": "application/pdf",
                "data_base64": base64.b64encode(self.png_bytes()).decode("ascii"),
            },
            {
                "file_name": "chart.png",
                "media_type": "image/png",
                "data_base64": "not-base64!!",
            },
            {
                "file_name": "chart.png",
                "media_type": "image/png",
                "data_base64": base64.b64encode(b"not a png").decode("ascii"),
            },
        )
        for payload in cases:
            with self.subTest(payload=payload["file_name"]):
                with self.assertRaises(self.module.FullAgentArtifactError):
                    self.store.save_upload(self.thread_id, self.turn_id, **payload)

    def test_presentation_upload_validates_ooxml_and_is_not_chat_image_input(self) -> None:
        result = self.upload(
            "lesson.pptx",
            self.presentation_bytes(),
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
        self.assertEqual(result["kind"], "presentation")
        self.assertFalse(result["modelInputReady"])
        path, _metadata = self.store.resolve(self.thread_id, self.turn_id, result["id"])
        self.assertEqual(path.suffix, ".pptx")

        with self.assertRaises(self.module.FullAgentArtifactError) as invalid:
            self.upload(
                "fake.pptx",
                b"PK\x03\x04not-an-office-file",
                "application/octet-stream",
            )
        self.assertEqual(invalid.exception.code, "invalid_file_content")

        unsafe_documents = (
            self.unsafe_presentation_bytes("ppt/vbaProject.bin", b"macro"),
            self.unsafe_presentation_bytes(
                "ppt/_rels/presentation.xml.rels",
                b'<Relationship TargetMode = "External" Target="https://example.invalid"/>',
            ),
        )
        for index, payload in enumerate(unsafe_documents):
            with self.subTest(index=index):
                with self.assertRaises(self.module.FullAgentArtifactError) as unsafe:
                    self.upload(
                        f"unsafe-{index}.pptx",
                        payload,
                        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    )
                self.assertEqual(unsafe.exception.code, "invalid_file_content")

    def test_publish_output_copies_an_immutable_path_opaque_artifact(self) -> None:
        output_root = self.root / "generated"
        output_root.mkdir()
        source = output_root / "generated-slide.pptx"
        source.write_bytes(self.presentation_bytes())
        result = self.store.publish_output(
            self.thread_id,
            self.turn_id,
            source,
            allowed_roots=(output_root,),
        )
        self.assertEqual(result["direction"], "output")
        self.assertEqual(result["kind"], "presentation")
        self.assertNotIn(str(source), json.dumps(result))
        published, metadata = self.store.resolve(
            self.thread_id, self.turn_id, result["id"]
        )
        self.assertNotEqual(published, source)
        self.assertEqual(published.read_bytes(), source.read_bytes())
        self.assertEqual(metadata["name"], "generated-slide.pptx")

        outside = self.root / "outside.txt"
        outside.write_text("private", encoding="utf-8")
        with self.assertRaises(self.module.FullAgentArtifactError) as blocked:
            self.store.publish_output(
                self.thread_id,
                self.turn_id,
                outside,
                allowed_roots=(output_root,),
            )
        self.assertEqual(blocked.exception.code, "unsafe_output_source")

        with self.assertRaises(self.module.FullAgentArtifactError) as unconfigured:
            self.store.publish_output(
                self.thread_id,
                self.turn_id,
                source,
                allowed_roots=(),
            )
        self.assertEqual(unconfigured.exception.code, "unsafe_output_source")

    def test_manual_output_stage_is_owner_bound_and_finalized_atomically(self) -> None:
        stage = self.store.begin_output(
            self.thread_id,
            self.turn_id,
            file_name="lesson.md",
            media_type="text/markdown",
        )
        self.assertNotIn(str(self.root), json.dumps(stage))
        with self.assertRaises(self.module.FullAgentArtifactError) as wrong_owner:
            self.store.staging_path(
                self.thread_id, "turn_media_test_9999", stage["stageId"]
            )
        self.assertEqual(wrong_owner.exception.status, 404)

        staged_path = self.store.staging_path(
            self.thread_id, self.turn_id, stage["stageId"]
        )
        staged_path.write_text("# Safe lesson", encoding="utf-8")
        result = self.store.finalize_output(
            self.thread_id, self.turn_id, stage["stageId"]
        )

        self.assertFalse(staged_path.exists())
        self.assertEqual(result["direction"], "output")
        self.assertEqual(result["kind"], "text")
        path, metadata = self.store.resolve(
            self.thread_id, self.turn_id, result["id"]
        )
        self.assertEqual(path.read_text(encoding="utf-8"), "# Safe lesson")
        self.assertEqual(metadata["turnId"], self.turn_id)

    def test_invalid_staged_output_is_quarantined_and_never_resolvable(self) -> None:
        stage = self.store.begin_output(
            self.thread_id,
            self.turn_id,
            file_name="broken.pdf",
            media_type="application/pdf",
        )
        staged_path = self.store.staging_path(
            self.thread_id, self.turn_id, stage["stageId"]
        )
        staged_path.write_bytes(b"not-a-pdf")

        with self.assertRaises(self.module.FullAgentArtifactError) as invalid:
            self.store.finalize_output(
                self.thread_id, self.turn_id, stage["stageId"]
            )

        self.assertEqual(invalid.exception.code, "invalid_file_content")
        self.assertFalse(staged_path.exists())
        self.assertEqual(self.store.quarantine_summary(), {"count": 1})
        with self.assertRaises(self.module.FullAgentArtifactError) as missing:
            self.store.staging_path(
                self.thread_id, self.turn_id, stage["stageId"]
            )
        self.assertEqual(missing.exception.status, 404)

    def test_finalize_metadata_failure_quarantines_unpublished_file(self) -> None:
        stage = self.store.begin_output(
            self.thread_id,
            self.turn_id,
            file_name="report.txt",
        )
        self.store.staging_path(
            self.thread_id, self.turn_id, stage["stageId"]
        ).write_text("safe report", encoding="utf-8")

        with mock.patch.object(
            self.store,
            "_write_metadata",
            side_effect=OSError("simulated metadata failure"),
        ):
            with self.assertRaises(self.module.FullAgentArtifactError) as failed:
                self.store.finalize_output(
                    self.thread_id, self.turn_id, stage["stageId"]
                )

        self.assertEqual(failed.exception.code, "atomic_finalize_failed")
        self.assertEqual(self.store.quarantine_summary(), {"count": 1})
        self.assertEqual(list(self.store.root.glob("art_*.json")), [])
        self.assertEqual(list(self.store.root.glob("art_*.txt")), [])

    def test_zip_output_validates_entries_and_rejects_traversal_or_executables(self) -> None:
        valid = self.upload(
            "source.zip",
            self.zip_bytes({"src/strategy.py": b"print('safe')\n", "README.md": b"safe"}),
            "application/zip",
        )
        self.assertEqual(valid["kind"], "archive")
        self.assertFalse(valid["modelInputReady"])

        unsafe_archives = (
            self.zip_bytes({"../escape.txt": b"bad"}),
            self.zip_bytes({"run/evil.exe": b"MZ"}),
        )
        for index, payload in enumerate(unsafe_archives):
            with self.subTest(index=index):
                with self.assertRaises(self.module.FullAgentArtifactError) as unsafe:
                    self.upload(f"unsafe-{index}.zip", payload, "application/zip")
                self.assertEqual(unsafe.exception.code, "invalid_file_content")

    def test_pdf_requires_eof_and_rejects_active_content(self) -> None:
        safe_pdf = b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n"
        result = self.upload("guide.pdf", safe_pdf, "application/pdf")
        self.assertEqual(result["kind"], "document")

        unsafe_values = (
            b"%PDF-1.7\nmissing eof",
            b"%PDF-1.7\n/JavaScript (alert)\n%%EOF",
        )
        for index, payload in enumerate(unsafe_values):
            with self.subTest(index=index):
                with self.assertRaises(self.module.FullAgentArtifactError) as unsafe:
                    self.upload(f"unsafe-{index}.pdf", payload, "application/pdf")
                self.assertEqual(unsafe.exception.code, "invalid_file_content")

    def test_text_and_source_reject_binary_secrets_and_malformed_json(self) -> None:
        invalid_values = (
            ("binary.txt", b"hello\x00world", "text/plain"),
            ("secret.py", b"api_key=abcdefghijklmnop\n", "text/x-python"),
            ("broken.json", b"{not json}", "application/json"),
        )
        for name, payload, media_type in invalid_values:
            with self.subTest(name=name):
                with self.assertRaises(self.module.FullAgentArtifactError):
                    self.upload(name, payload, media_type)

        result = self.upload(
            "strategy.mq5",
            "// UTF-8 source\ninput double Risk = 1.0;\n".encode("utf-8"),
            "text/plain",
        )
        self.assertEqual(result["kind"], "source")

    def test_attachment_count_is_enforced_per_thread_and_turn(self) -> None:
        for index in range(self.module.MAX_ATTACHMENTS_PER_TURN):
            self.upload(f"chart-{index}.png", self.png_bytes(), "image/png")
        with self.assertRaises(self.module.FullAgentArtifactError) as limited:
            self.upload("chart-over.png", self.png_bytes(), "image/png")
        self.assertEqual(limited.exception.code, "too_many_attachments")

        other_turn = self.store.save_upload(
            self.thread_id,
            "turn_media_test_0002",
            file_name="allowed.png",
            media_type="image/png",
            data_base64=base64.b64encode(self.png_bytes()).decode("ascii"),
        )
        self.assertTrue(other_turn["modelInputReady"])

    def test_turn_ownership_applies_to_resolve_download_and_model_input(self) -> None:
        result = self.upload("chart.png", self.png_bytes(), "image/png")
        wrong_turn = "turn_media_test_9999"
        for action in (
            lambda: self.store.resolve(self.thread_id, wrong_turn, result["id"]),
            lambda: self.store.download_metadata(
                self.thread_id, wrong_turn, result["id"]
            ),
            lambda: self.store.model_input_path(
                self.thread_id, wrong_turn, result["id"]
            ),
        ):
            with self.assertRaises(self.module.FullAgentArtifactError) as denied:
                action()
            self.assertEqual(denied.exception.status, 404)

        path = self.store.model_input_path(
            self.thread_id, self.turn_id, result["id"]
        )
        self.assertEqual(path.read_bytes(), self.png_bytes())

    def test_consumed_input_is_a_durable_one_shot_tombstone_until_ttl_cleanup(self) -> None:
        now = [1_800_000_000.0]
        store = self.module.FullAgentArtifactStore(
            self.root / "consumed",
            default_ttl_seconds=self.module.MIN_TTL_SECONDS,
            clock=lambda: now[0],
        )
        result = store.save_upload(
            self.thread_id,
            self.turn_id,
            file_name="chart.png",
            media_type="image/png",
            data_base64=base64.b64encode(self.png_bytes()).decode("ascii"),
        )
        payload_path, _metadata = store.resolve(
            self.thread_id, self.turn_id, result["id"]
        )
        metadata_path = store._metadata_path(result["id"])

        consumed = store.consume_input(
            self.thread_id, self.turn_id, result["id"]
        )

        self.assertEqual(consumed["state"], "consumed")
        self.assertFalse(payload_path.exists())
        tombstone = json.loads(metadata_path.read_text(encoding="utf-8"))
        self.assertEqual(tombstone["state"], "consumed")
        self.assertFalse(tombstone["modelInputReady"])
        self.assertTrue(tombstone["consumedAt"])
        for action in (
            lambda: store.resolve(self.thread_id, self.turn_id, result["id"]),
            lambda: store.download_metadata(
                self.thread_id, self.turn_id, result["id"]
            ),
            lambda: store.consume_input(self.thread_id, self.turn_id, result["id"]),
        ):
            with self.assertRaises(self.module.FullAgentArtifactError) as unavailable:
                action()
            self.assertEqual(unavailable.exception.status, 404)

        now[0] += self.module.MIN_TTL_SECONDS + 1
        cleanup = store.cleanup_expired()
        self.assertEqual(cleanup["artifacts"], 1)
        self.assertFalse(metadata_path.exists())

    def test_capacity_reclaims_expired_and_does_not_charge_consumed_tombstones(self) -> None:
        now = [1_800_000_000.0]
        store = self.module.FullAgentArtifactStore(
            self.root / "capacity",
            default_ttl_seconds=self.module.MIN_TTL_SECONDS,
            clock=lambda: now[0],
        )
        with mock.patch.object(self.module, "MAX_STORE_ITEMS", 1):
            expired = store.save_upload(
                self.thread_id,
                self.turn_id,
                file_name="expired.png",
                media_type="image/png",
                data_base64=base64.b64encode(self.png_bytes()).decode("ascii"),
            )
            expired_meta = store._metadata_path(expired["id"])
            now[0] += self.module.MIN_TTL_SECONDS + 1
            current = store.save_upload(
                self.thread_id,
                "turn_media_capacity_0002",
                file_name="current.png",
                media_type="image/png",
                data_base64=base64.b64encode(self.png_bytes()).decode("ascii"),
            )
            self.assertFalse(expired_meta.exists())
            store.consume_input(
                self.thread_id, "turn_media_capacity_0002", current["id"]
            )
            replacement = store.save_upload(
                self.thread_id,
                "turn_media_capacity_0003",
                file_name="replacement.png",
                media_type="image/png",
                data_base64=base64.b64encode(self.png_bytes()).decode("ascii"),
            )
        self.assertTrue(replacement["modelInputReady"])

    def test_output_batch_rolls_back_ready_prefix_when_later_file_is_invalid(self) -> None:
        output_root = self.root / "batch-output"
        output_root.mkdir()
        valid = output_root / "first.txt"
        invalid = output_root / "second.pdf"
        valid.write_text("safe\n", encoding="utf-8")
        invalid.write_bytes(b"not a pdf")

        with self.assertRaises(self.module.FullAgentArtifactError) as failed:
            self.store.publish_outputs(
                self.thread_id,
                self.turn_id,
                (valid, invalid),
                allowed_roots=(output_root,),
            )

        self.assertIn(
            failed.exception.code, {"invalid_file_content", "artifact_changed"}
        )
        self.assertEqual(list(self.store.root.glob("art_*.meta.json")), [])
        self.assertEqual(list(self.store.root.glob("art_*.txt")), [])

    def test_download_metadata_is_path_opaque_and_attachment_only(self) -> None:
        result = self.upload("กราฟ.png", self.png_bytes(), "image/png")
        download = self.store.download_metadata(
            self.thread_id, self.turn_id, result["id"]
        )

        self.assertEqual(download["cacheControl"], "private, no-store")
        self.assertEqual(download["contentTypeOptions"], "nosniff")
        self.assertTrue(download["contentDisposition"].startswith("attachment;"))
        self.assertIn("filename*=UTF-8''", download["contentDisposition"])
        self.assertNotIn(str(self.root), json.dumps(download, ensure_ascii=False))
        self.assertNotIn("threadId", json.dumps(download))
        self.assertNotIn("turnId", json.dumps(download))

    def test_expired_artifact_is_deleted_and_returns_gone(self) -> None:
        now = [1_800_000_000.0]
        store = self.module.FullAgentArtifactStore(
            self.root / "expiring",
            default_ttl_seconds=self.module.MIN_TTL_SECONDS,
            clock=lambda: now[0],
        )
        result = store.save_upload(
            self.thread_id,
            self.turn_id,
            file_name="chart.png",
            media_type="image/png",
            data_base64=base64.b64encode(self.png_bytes()).decode("ascii"),
        )
        path, _metadata = store.resolve(self.thread_id, self.turn_id, result["id"])
        now[0] += self.module.MIN_TTL_SECONDS + 1

        with self.assertRaises(self.module.FullAgentArtifactError) as expired:
            store.resolve(self.thread_id, self.turn_id, result["id"])

        self.assertEqual(expired.exception.code, "artifact_expired")
        self.assertEqual(expired.exception.status, 410)
        self.assertFalse(path.exists())

    def test_cleanup_expires_stages_then_quarantine_records(self) -> None:
        now = [1_800_000_000.0]
        store = self.module.FullAgentArtifactStore(
            self.root / "cleanup",
            default_ttl_seconds=self.module.MIN_TTL_SECONDS,
            clock=lambda: now[0],
        )
        stage = store.begin_output(
            self.thread_id,
            self.turn_id,
            file_name="pending.txt",
        )
        store.staging_path(
            self.thread_id, self.turn_id, stage["stageId"]
        ).write_text("pending", encoding="utf-8")
        now[0] += self.module.MIN_TTL_SECONDS + 1

        first = store.cleanup_expired()
        self.assertEqual(first["stages"], 1)
        self.assertEqual(store.quarantine_summary(), {"count": 1})
        now[0] += self.module.MIN_TTL_SECONDS + 1
        second = store.cleanup_expired()
        self.assertEqual(second["quarantine"], 1)
        self.assertEqual(store.quarantine_summary(), {"count": 0})

    def test_output_source_link_is_rejected_before_publication(self) -> None:
        output_root = self.root / "generated-link-test"
        output_root.mkdir()
        source = output_root / "result.txt"
        source.write_text("safe", encoding="utf-8")

        with mock.patch.object(
            self.module,
            "_is_link",
            side_effect=lambda path: Path(path) == source,
        ):
            with self.assertRaises(self.module.FullAgentArtifactError) as blocked:
                self.store.publish_output(
                    self.thread_id,
                    self.turn_id,
                    source,
                    allowed_roots=(output_root,),
                )

        self.assertIn(blocked.exception.code, {"artifact_unavailable", "unsafe_output_source"})

    def test_supported_extension_contract_includes_documents_archives_and_source(self) -> None:
        extensions = set(self.store.accepted_extensions())
        self.assertTrue(
            {
                ".png",
                ".jpg",
                ".jpeg",
                ".webp",
                ".pdf",
                ".pptx",
                ".docx",
                ".xlsx",
                ".txt",
                ".md",
                ".json",
                ".zip",
                ".py",
                ".mq4",
                ".mq5",
            }.issubset(extensions)
        )

    def test_jpeg_webp_docx_xlsx_and_json_are_content_validated(self) -> None:
        fixtures = (
            ("photo.jpg", self.jpeg_bytes(), "image/jpeg", "image"),
            ("preview.webp", self.webp_bytes(), "image/webp", "image"),
            (
                "guide.docx",
                self.office_bytes("word/document.xml"),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "document",
            ),
            (
                "metrics.xlsx",
                self.office_bytes("xl/workbook.xml"),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "spreadsheet",
            ),
            ("summary.json", b'{"ok":true}', "application/json", "text"),
        )
        for index, (name, payload, media_type, kind) in enumerate(fixtures):
            with self.subTest(name=name):
                result = self.store.save_upload(
                    self.thread_id,
                    f"turn_media_format_{index:04d}",
                    file_name=name,
                    media_type=media_type,
                    data_base64=base64.b64encode(payload).decode("ascii"),
                )
                self.assertEqual(result["kind"], kind)
                self.assertEqual(result["mediaType"], media_type)

    def test_invalid_ttl_and_bidi_filename_fail_closed(self) -> None:
        encoded = base64.b64encode(self.png_bytes()).decode("ascii")
        with self.assertRaises(self.module.FullAgentArtifactError) as ttl:
            self.store.save_upload(
                self.thread_id,
                self.turn_id,
                file_name="chart.png",
                media_type="image/png",
                data_base64=encoded,
                ttl_seconds=1,
            )
        self.assertEqual(ttl.exception.code, "invalid_ttl")

        # Bidi controls are removed rather than persisted or reflected.
        result = self.store.save_upload(
            self.thread_id,
            self.turn_id,
            file_name="safe\u202egnp.png",
            media_type="image/png",
            data_base64=encoded,
        )
        self.assertNotIn("\u202e", result["name"])

    def test_tampered_metadata_is_rejected_before_download(self) -> None:
        result = self.upload("chart.png", self.png_bytes(), "image/png")
        metadata_path = self.store._metadata_path(result["id"])
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["mediaType"] = "text/html"
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

        with self.assertRaises(self.module.FullAgentArtifactError) as tampered:
            self.store.download_metadata(
                self.thread_id, self.turn_id, result["id"]
            )

        self.assertEqual(tampered.exception.code, "artifact_integrity_failed")

    def test_cleanup_of_corrupt_metadata_cannot_escape_store_root(self) -> None:
        now = [1_800_000_000.0]
        store = self.module.FullAgentArtifactStore(
            self.root / "corrupt-cleanup",
            default_ttl_seconds=self.module.MIN_TTL_SECONDS,
            clock=lambda: now[0],
        )
        victim = self.root / "victim.txt"
        victim.write_text("keep", encoding="utf-8")
        expired = "2000-01-01T00:00:00.000Z"
        malicious_artifact_record = {
            "id": "../../victim",
            "suffix": ".txt",
            "expiresAt": expired,
        }
        (store.root / "malicious.meta.json").write_text(
            json.dumps(malicious_artifact_record), encoding="utf-8"
        )
        malicious_stage_record = {
            "stageId": "../../victim",
            "suffix": ".txt",
            "expiresAt": expired,
        }
        (store.staging_root / "malicious.meta.json").write_text(
            json.dumps(malicious_stage_record), encoding="utf-8"
        )

        store.cleanup_expired()

        self.assertEqual(victim.read_text(encoding="utf-8"), "keep")
        self.assertFalse((store.root / "malicious.meta.json").exists())
        self.assertFalse((store.staging_root / "malicious.meta.json").exists())


if __name__ == "__main__":
    unittest.main()
