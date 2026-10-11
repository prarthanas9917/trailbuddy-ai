import json
import unittest
from unittest.mock import Mock, patch

import httpx

from app.ai import MODEL, generate_suggestions


class GenerateSuggestionsTests(unittest.TestCase):
    def test_uses_local_qwen_response(self):
        activities = [
            {
                "title": f"Idea {index}",
                "description": "A short outdoor activity.",
                "duration": "20 min",
                "bring": "Water",
            }
            for index in range(3)
        ]
        response = Mock()
        response.json.return_value = {
            "response": json.dumps({"activities": activities})
        }
        client = Mock()
        client.__enter__ = Mock(return_value=client)
        client.__exit__ = Mock(return_value=False)
        client.post.return_value = response

        with patch("app.ai.httpx.Client", return_value=client):
            result = generate_suggestions("Nearby", "Birds", "20 minutes")

        self.assertEqual(result["mode"], "local-ai")
        self.assertEqual(result["activities"], activities)
        self.assertEqual(client.post.call_args.kwargs["json"]["model"], MODEL)
        response.raise_for_status.assert_called_once_with()

    def test_uses_personalized_offline_ideas_when_ollama_is_unavailable(self):
        with patch("app.ai.httpx.Client", side_effect=httpx.ConnectError("connection refused")):
            result = generate_suggestions("Nearby", "Birds", "20 minutes")

        self.assertEqual(result["mode"], "offline")
        titles = " ".join(item["title"] for item in result["activities"]).lower()
        self.assertIn("birdwatch", titles)
        self.assertTrue(result["notice"])

    def test_uses_offline_ideas_for_invalid_model_json(self):
        response = Mock()
        response.json.return_value = {"response": "not json"}
        client = Mock()
        client.__enter__ = Mock(return_value=client)
        client.__exit__ = Mock(return_value=False)
        client.post.return_value = response

        with patch("app.ai.httpx.Client", return_value=client):
            result = generate_suggestions("Nearby", "Garden", "1 hour")

        self.assertEqual(result["mode"], "offline")
        self.assertIn("green space", " ".join(item["title"] for item in result["activities"]).lower())


if __name__ == "__main__":
    unittest.main()
