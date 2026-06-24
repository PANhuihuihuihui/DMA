import tempfile
import unittest
from pathlib import Path

from backend.app import store, tiktok_publisher
from backend.app.contracts import json_dumps, json_loads


def _video_ref(mime="video/mp4", media_id="media_x", storage_ref="localpilot-media/demo/clip.mp4"):
    return {"kind": "video", "mimeType": mime, "mediaAssetId": media_id, "storageRef": storage_ref}


class TiktokMediaValidationTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "workflow.sqlite")
        store.ensure_database(self.db_path)
        self.conn = store.connect(self.db_path)

    def tearDown(self):
        self.conn.close()
        self.temp_dir.cleanup()

    def approve_tiktok(self):
        workflow = store.get_workflow(self.conn)
        draft = next(item for item in workflow["platformDrafts"] if item["platform"] == "tiktok")
        info = store.get_tiktok_creator_info(self.conn, draft["connectedChannelId"])
        return store.approve_draft(
            self.conn,
            draft["id"],
            {
                "draftVersionId": draft["currentVersion"]["id"],
                "confirmation": "APPROVE_EXACT_VERSION",
                "approver": {"name": "Karen Li", "email": "karen@example.com"},
                "tiktokConfirmations": {
                    "creatorInfoVersion": info["version"],
                    "privacyLevel": "PUBLIC_TO_EVERYONE",
                    "disclosureReviewed": True,
                    "interactionReviewed": True,
                    "allowComment": True,
                },
            },
        )["approval"]

    def test_seeded_demo_video_passes_validation(self):
        approval = self.approve_tiktok()
        payload = tiktok_publisher.queue_tiktok_publish(self.conn, approval["id"], {})
        self.assertEqual("published", payload["job"]["status"])

    def test_missing_video_is_classified_media_validation(self):
        snapshot = {"mediaRefs": [{"kind": "image", "mimeType": "image/jpeg"}]}
        with self.assertRaises(tiktok_publisher.TiktokMediaError) as raised:
            tiktok_publisher.validate_tiktok_media(snapshot)
        self.assertEqual("media_validation", raised.exception.diagnostics["errorClass"])

    def test_validation_reasons_are_stable(self):
        cases = {
            "file_type": {"mediaRefs": [_video_ref(mime="video/x-bad", storage_ref="clip")]},
            "format_incompatible": {"mediaRefs": [_video_ref(mime="", storage_ref="clip.avi")]},
            "duration": {
                "mediaRefs": [_video_ref()],
                "providerPayloadSummary": {"durationSeconds": 99999},
                "creatorInfoSnapshot": {"maxVideoPostDurationSec": 600},
            },
            "url_unreachable": {"mediaRefs": [_video_ref(storage_ref="http://127.0.0.1/private.mp4")]},
        }
        for expected_reason, snapshot in cases.items():
            with self.assertRaises(tiktok_publisher.TiktokMediaError) as raised:
                tiktok_publisher.validate_tiktok_media(snapshot)
            diagnostics = raised.exception.diagnostics
            self.assertEqual("media_validation", diagnostics["errorClass"])
            self.assertEqual(expected_reason, diagnostics["reason"])

    def test_invalid_media_rejected_before_publish_job_created(self):
        approval = self.approve_tiktok()
        stored = self.conn.execute(
            "select snapshot_json from approvals where id = ?", (approval["id"],)
        ).fetchone()
        snapshot = json_loads(stored["snapshot_json"], {})
        snapshot.setdefault("providerPayloadSummary", {})["durationSeconds"] = 99999
        self.conn.execute(
            "update approvals set snapshot_json = ? where id = ?",
            (json_dumps(snapshot), approval["id"]),
        )
        self.conn.commit()

        with self.assertRaises(store.StoreError) as raised:
            tiktok_publisher.queue_tiktok_publish(self.conn, approval["id"], {})
        self.assertEqual(400, raised.exception.status)
        self.assertIn("media_validation", raised.exception.message)

        job_count = self.conn.execute("select count(*) from publish_jobs").fetchone()[0]
        self.assertEqual(0, job_count)


if __name__ == "__main__":
    unittest.main()
