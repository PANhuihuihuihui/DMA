import unittest

from backend.app.generation_providers import minimax_adapter


class MiniMaxImageAdapterTest(unittest.TestCase):
    def test_submit_accepts_string_data_items(self):
        adapter = minimax_adapter.MiniMaxImageAdapter()
        original_post = minimax_adapter._post

        def fake_post(path, payload):
            self.assertEqual("/v1/image_generation", path)
            self.assertEqual("3:4", payload["aspect_ratio"])
            return {
                "id": "minimax-job-1",
                "data": [
                    "https://example.com/slide-1.jpg",
                    "https://example.com/slide-2.jpg",
                ],
            }

        minimax_adapter._post = fake_post
        try:
            provider_job_id = adapter.submit(
                model_key="image-01",
                prompt="Turn one timely local offer into a five-slide owner-ready carousel.",
                request={"workflowType": "carousel"},
                settings={"aspectRatio": "3:4", "slideCount": 2},
            )
        finally:
            minimax_adapter._post = original_post

        result = adapter.poll(provider_job_id)
        self.assertEqual("succeeded", result["status"])
        self.assertEqual(2, len(result["outputs"]))
        self.assertEqual("https://example.com/slide-1.jpg", result["outputs"][0]["storageRef"])
        self.assertEqual(1, result["outputs"][0]["metadata"]["index"])
        self.assertEqual("https://example.com/slide-2.jpg", result["outputs"][1]["previewRef"])
        self.assertEqual(2, result["outputs"][1]["metadata"]["index"])

    def test_submit_unwraps_image_urls_payload(self):
        adapter = minimax_adapter.MiniMaxImageAdapter()
        original_post = minimax_adapter._post

        def fake_post(path, payload):
            self.assertEqual("/v1/image_generation", path)
            return {
                "id": "minimax-job-2",
                "data": {
                    "image_urls": [
                        "https://example.com/wrapped-1.jpg",
                        "https://example.com/wrapped-2.jpg",
                    ]
                },
            }

        minimax_adapter._post = fake_post
        try:
            provider_job_id = adapter.submit(
                model_key="image-01",
                prompt="Turn one timely local offer into a five-slide owner-ready carousel.",
                request={"workflowType": "carousel"},
                settings={"aspectRatio": "3:4", "slideCount": 2},
            )
        finally:
            minimax_adapter._post = original_post

        result = adapter.poll(provider_job_id)
        self.assertEqual("https://example.com/wrapped-1.jpg", result["outputs"][0]["storageRef"])
        self.assertEqual("https://example.com/wrapped-2.jpg", result["outputs"][1]["previewRef"])


if __name__ == "__main__":
    unittest.main()
