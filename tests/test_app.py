import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class AppTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_homepage_loads_local_assets_and_form(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Find my outside hour", response.text)
        self.assertIn("/static/app.js", response.text)

    def test_health_endpoint(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    @patch("app.main.generate_suggestions")
    def test_suggestions_endpoint_returns_activity_cards(self, generate):
        generate.return_value = {
            "activities": [
                {
                    "title": "A quiet birdwatch",
                    "description": "Listen for birds in a nearby green space.",
                    "duration": "20 min",
                    "bring": "Curiosity",
                }
            ],
            "mode": "offline",
            "notice": "",
        }

        response = self.client.post(
            "/api/suggest",
            json={"location": "Nearby", "interests": "Birds", "duration": "20 minutes"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mode"], "offline")
        generate.assert_called_once_with(
            location="Nearby",
            interests="Birds",
            duration="20 minutes",
        )

    def test_rejects_oversized_interest_input(self):
        response = self.client.post(
            "/api/suggest",
            json={"interests": "outside " * 30},
        )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
