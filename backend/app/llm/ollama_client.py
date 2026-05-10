"""Ollama LLM client for local/free model inference."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Async client for the Ollama REST API.

    Supports text generation and chat completions using local models
    like Llama 3.1, Qwen 2.5-Coder, etc.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self._base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self._model = model or settings.ollama_model
        self._timeout = timeout or settings.ollama_timeout
        self._client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(self._timeout),
        )
        logger.info("Ollama client started (model=%s, url=%s)", self._model, self._base_url)

    async def stop(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        if not self._client:
            raise RuntimeError("Ollama client not started")

        payload: dict[str, Any] = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system:
            payload["system"] = system

        try:
            response = await self._client.post("/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except httpx.HTTPStatusError as e:
            logger.error("Ollama API error: %s %s", e.response.status_code, e.response.text)
            raise
        except httpx.ConnectError:
            logger.error("Cannot connect to Ollama at %s", self._base_url)
            raise ConnectionError(
                f"Cannot connect to Ollama at {self._base_url}. "
                "Ensure Ollama is running: 'ollama serve'"
            )

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        if not self._client:
            raise RuntimeError("Ollama client not started")

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            response = await self._client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")
        except httpx.HTTPStatusError as e:
            logger.error("Ollama chat error: %s", e.response.text)
            raise

    async def list_models(self) -> list[dict[str, Any]]:
        if not self._client:
            raise RuntimeError("Ollama client not started")
        response = await self._client.get("/api/tags")
        response.raise_for_status()
        data = response.json()
        return data.get("models", [])

    async def pull_model(self, model_name: str) -> None:
        if not self._client:
            raise RuntimeError("Ollama client not started")
        logger.info("Pulling model %s...", model_name)
        response = await self._client.post(
            "/api/pull",
            json={"name": model_name, "stream": False},
            timeout=httpx.Timeout(600),
        )
        response.raise_for_status()
        logger.info("Model %s pulled successfully", model_name)

    async def health_check(self) -> bool:
        try:
            if not self._client:
                return False
            response = await self._client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False
