import json
import os
import re
from typing import TypedDict

import httpx

from app.prompts import build_trail_prompt

OLLAMA_URL = os.getenv("TRAILBUDDY_OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
MODEL = os.getenv("TRAILBUDDY_MODEL", "qwen2.5:3b")


class Activity(TypedDict):
    title: str
    description: str
    duration: str
    bring: str


_IDEAS: list[tuple[Activity, set[str], int]] = [
    (
        {
            "title": "Take the slower path",
            "description": "Walk a familiar block or path and look for one thing you have never noticed.",
            "duration": "25 min",
            "bring": "Comfortable shoes",
        },
        {"walk", "nature", "easy", "explore"},
        25,
    ),
    (
        {
            "title": "A tiny birdwatch",
            "description": "Find a quiet spot, listen for a minute, then notice the colors and movement around you.",
            "duration": "20 min",
            "bring": "Curiosity; binoculars are optional",
        },
        {"bird", "birds", "wildlife", "nature", "photography"},
        20,
    ),
    (
        {
            "title": "Try a sit-spot",
            "description": "Sit outside and name five things you can see, four you can hear, and three you can feel.",
            "duration": "15 min",
            "bring": "A layer to sit on",
        },
        {"calm", "mindfulness", "quiet", "nature", "rest"},
        15,
    ),
    (
        {
            "title": "Sketch one small thing",
            "description": "Take a short walk, pick a leaf or cloud, and draw it without worrying about getting it right.",
            "duration": "30 min",
            "bring": "Paper and a pencil",
        },
        {"art", "sketch", "drawing", "creative", "walk"},
        30,
    ),
    (
        {
            "title": "Give a green space a hand",
            "description": "Water a plant, tidy a garden bed, or check what is growing near your home.",
            "duration": "20 min",
            "bring": "Water and gardening gloves if needed",
        },
        {"garden", "gardening", "plants", "nature"},
        20,
    ),
    (
        {
            "title": "Move outside, gently",
            "description": "Take an easy walk with a few comfortable stretches or short jogs along the way.",
            "duration": "30 min",
            "bring": "Water and shoes that feel good",
        },
        {"run", "running", "fitness", "movement", "exercise"},
        30,
    ),
    (
        {
            "title": "Notice the sky",
            "description": "Step outside and watch the clouds or changing light for a few minutes, away from notifications.",
            "duration": "15 min",
            "bring": "A light layer if it is cool",
        },
        {"sky", "sunset", "calm", "mindfulness", "rest"},
        15,
    ),
    (
        {
            "title": "Leave a place a little better",
            "description": "Take a short walk and pick up a few pieces of litter where it is safe to do so.",
            "duration": "20 min",
            "bring": "A small bag and gloves",
        },
        {"community", "walk", "cleanup", "nature"},
        20,
    ),
]

_ALIASES = {
    "birding": "bird",
    "birds": "bird",
    "gardening": "garden",
    "plants": "garden",
    "running": "run",
    "jogging": "run",
    "drawing": "sketch",
    "sketching": "sketch",
    "hiking": "walk",
    "walking": "walk",
    "exercise": "fitness",
    "workout": "fitness",
}
_AVAILABLE_MINUTES = {
    "20 minutes": 20,
    "45 minutes": 45,
    "1 hour": 60,
    "2 hours": 120,
    "Half a day": 240,
}


def _offline_suggestions(location: str, interests: str, duration: str) -> list[Activity]:
    interest_words = set(re.findall(r"[a-z]+", interests.lower()))
    interest_words = {_ALIASES.get(word, word) for word in interest_words}
    available_minutes = _AVAILABLE_MINUTES.get(duration, 60)
    location_hint = f"near {location}: " if location.lower() != "nearby" else ""

    ranked_ideas = sorted(
        _IDEAS,
        key=lambda idea: len(interest_words.intersection(idea[1])),
        reverse=True,
    )
    suggestions = []
    for idea, _, minutes in ranked_ideas[:3]:
        activity = idea.copy()
        description = activity["description"]
        if location_hint:
            description = description[0].lower() + description[1:]
        activity["description"] = location_hint + description
        activity["duration"] = f"{min(minutes, available_minutes)} min"
        suggestions.append(activity)
    return suggestions


def _parse_activities(response: str) -> list[Activity]:
    payload = json.loads(response)
    activities = payload.get("activities") if isinstance(payload, dict) else None
    if not isinstance(activities, list) or len(activities) < 3:
        raise ValueError("The local model did not return three activities.")

    parsed: list[Activity] = []
    for item in activities[:3]:
        if not isinstance(item, dict):
            raise ValueError("The local model returned an invalid activity.")
        fields = ("title", "description", "duration", "bring")
        if any(not isinstance(item.get(field), str) or not item[field].strip() for field in fields):
            raise ValueError("The local model returned an incomplete activity.")
        parsed.append({field: item[field].strip() for field in fields})
    return parsed


def generate_suggestions(location: str, interests: str, duration: str) -> dict[str, object]:
    prompt = build_trail_prompt(location, interests, duration)
    try:
        with httpx.Client(timeout=90) as client:
            response = client.post(
                OLLAMA_URL,
                json={
                    "model": MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
            )
        response.raise_for_status()
        activities = _parse_activities(response.json()["response"])
        return {"activities": activities, "mode": "local-ai", "notice": ""}
    except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
        return {
            "activities": _offline_suggestions(location, interests, duration),
            "mode": "offline",
            "notice": (
                f"Local AI is unavailable ({error}). These built-in ideas work offline; "
                f"start Ollama and download {MODEL} to use Qwen."
            ),
        }
