import json
import os
from dataclasses import dataclass
from typing import Any, Literal

import httpx
from pydantic import BaseModel, Field, ValidationError


class ConciergeIntent(BaseModel):
    task: Literal["find_spot", "plan_group"]
    subject: str | None = Field(default=None, max_length=120)
    location_hint: str | None = Field(default=None, max_length=160)
    time_hint: str | None = Field(default=None, max_length=160)
    duration_minutes: int | None = Field(default=None, ge=15, le=480)
    constraints: list[str] = Field(default_factory=list, max_length=12)


@dataclass(frozen=True)
class OpenRouterSettings:
    api_key: str | None
    model: str
    base_url: str
    timeout_seconds: float

    @classmethod
    def from_environment(cls) -> "OpenRouterSettings":
        return cls(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b:free"),
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            timeout_seconds=float(os.getenv("OPENROUTER_TIMEOUT_SECONDS", "20")),
        )


def fallback_intent(message: str, mode: str) -> ConciergeIntent:
    task = "plan_group" if mode == "group_match" else "find_spot"
    return ConciergeIntent(task=task, constraints=[message[:160]])


class OpenRouterClient:
    def __init__(self, settings: OpenRouterSettings | None = None) -> None:
        self.settings = settings or OpenRouterSettings.from_environment()

    @property
    def configured(self) -> bool:
        return bool(self.settings.api_key)

    async def extract_intent(self, message: str, mode: str) -> ConciergeIntent:
        if not self.configured:
            return fallback_intent(message, mode)

        payload = {
            "model": self.settings.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You extract structured intent for a university study concierge. "
                        "Return only JSON with task, subject, location_hint, time_hint, "
                        "duration_minutes, and constraints. task must be find_spot or plan_group. "
                        "Use null when a value is absent."
                    ),
                },
                {"role": "user", "content": f"Requested mode: {mode}\nMessage: {message}"},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.settings.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://studyuic.local",
            "X-Title": "StudyUIC Autonomous Campus Concierge",
        }
        async with httpx.AsyncClient(timeout=self.settings.timeout_seconds) as client:
            response = await client.post(
                f"{self.settings.base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
            )
        response.raise_for_status()
        body: dict[str, Any] = response.json()
        content = body["choices"][0]["message"]["content"]
        try:
            return ConciergeIntent.model_validate(json.loads(content))
        except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValidationError) as exc:
            raise ValueError("OpenRouter returned an invalid concierge intent") from exc