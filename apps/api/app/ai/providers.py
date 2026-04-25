from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

import httpx
from pydantic import BaseModel

from app.ai.schemas import StructuredAIResponse, validate_structured_output
from app.core.config import Settings


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: type[BaseModel],
        purpose: str,
    ) -> BaseModel:
        raise NotImplementedError


class DisabledLLMProvider(LLMProvider):
    name = "disabled"

    async def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: type[BaseModel],
        purpose: str,
    ) -> BaseModel:
        raise RuntimeError(
            f"LLM provider is disabled for '{purpose}'. DashForge will use deterministic fallback."
        )


class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, *, name: str, base_url: str, api_key: str, model: str) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    async def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: type[BaseModel],
        purpose: str,
    ) -> BaseModel:
        schema_payload = schema.model_json_schema()
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "schema": schema_payload,
                    "strict": True,
                },
            },
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(f"{self.base_url}/chat/completions", json=body, headers=headers)
            response.raise_for_status()
            payload = response.json()
        raw_text = payload["choices"][0]["message"]["content"]
        data = json.loads(raw_text)
        structured = StructuredAIResponse(
            raw_text=raw_text,
            data=data,
            provider=self.name,
            model=self.model,
        )
        return validate_structured_output(schema, structured.data, structured.raw_text)


def build_provider(settings: Settings, purpose: str = "default") -> LLMProvider:
    if settings.llm_provider == "openai-compatible" and settings.llm_api_key:
        return OpenAICompatibleProvider(
            name="openai-compatible",
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )
    if settings.llm_provider == "router" and settings.router_api_key:
        return OpenAICompatibleProvider(
            name="fast-router",
            base_url=settings.router_base_url,
            api_key=settings.router_api_key,
            model=settings.router_model,
        )
    return DisabledLLMProvider()

