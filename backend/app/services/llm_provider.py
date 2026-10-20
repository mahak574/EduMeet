import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger(__name__)


class LLMPlanOutput(BaseModel):
    objectives: List[str] = Field(default_factory=list)
    discussion_prompts: List[str] = Field(default_factory=list)
    checklist: List[str] = Field(default_factory=list)


class LLMExplanationOutput(BaseModel):
    title: str
    analogy: str
    explanation: str
    key_takeaway: str


class LLMProvider(ABC):
    @abstractmethod
    async def generate_completion(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Generates a text completion for given system and user prompts."""
        pass


class MockLLMProvider(LLMProvider):
    def __init__(self, response: Optional[str] = None):
        self.response = response

    async def generate_completion(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        return self.response


class GeminiLLMProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash"):
        self.api_key = api_key or getattr(settings, "GEMINI_API_KEY", None)
        self.model = model

    async def generate_completion(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        if not self.api_key:
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}],
                }
            ],
            "generationConfig": {
                "temperature": 0.4,
                "responseMimeType": "application/json",
            },
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text")
        except Exception as exc:
            logger.warning("Gemini LLM call failed: %s", exc)

        return None


class LiteLLMProvider(LLMProvider):
    """LiteLLM / OpenAI compatible provider."""
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or getattr(settings, "OPENAI_API_KEY", None)
        self.model = model or getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")

    async def generate_completion(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        if not self.api_key:
            return None

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.4,
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content")
        except Exception as exc:
            logger.warning("LiteLLM / OpenAI call failed: %s", exc)

        return None


def get_default_llm_provider() -> LLMProvider:
    gemini_key = getattr(settings, "GEMINI_API_KEY", None)
    openai_key = getattr(settings, "OPENAI_API_KEY", None)
    if gemini_key:
        return GeminiLLMProvider(api_key=gemini_key)
    elif openai_key:
        return LiteLLMProvider(api_key=openai_key)
    return MockLLMProvider()
