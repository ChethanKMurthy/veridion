"""Replaceable LLM providers.

Veridion talks to any OpenAI-compatible chat completions endpoint: Groq (hosted),
a local Ollama or vLLM server, or another vendor. The model never takes actions;
it returns JSON that is validated against a schema and then against the database.

Responses are cached by a hash of (model, prompt version, inputs) so repeated
assessments are reproducible and identical calls are paid for once.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Protocol

import httpx

from veridion.config import get_settings
from veridion.db import session_scope
from veridion.ids import sha256_text
from veridion.models import LLMCacheEntry

log = logging.getLogger("veridion.llm")


class LLMError(Exception):
    pass


@dataclass
class LLMResponse:
    data: dict
    raw: str
    model: str
    usage: dict = field(default_factory=dict)
    latency_ms: float = 0.0
    cached: bool = False


class LLMProvider(Protocol):
    name: str
    model: str

    def complete_json(self, system: str, user: str, schema: dict, *, schema_name: str = "result",
                      max_tokens: int = 1500, cache_namespace: str = "") -> LLMResponse: ...


class _RateGate:
    """Pace requests using the provider's rate-limit headers (tokens per minute)."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.remaining_tokens: float | None = None
        self.reset_at: float = 0.0

    def wait(self, estimated_tokens: int) -> None:
        with self.lock:
            if self.remaining_tokens is not None and self.remaining_tokens < estimated_tokens:
                delay = self.reset_at - time.monotonic()
                if delay > 0:
                    log.info("Rate limit: waiting %.1fs for token budget", delay)
                    time.sleep(min(delay, 65))
                self.remaining_tokens = None

    def update(self, headers: httpx.Headers) -> None:
        remaining = headers.get("x-ratelimit-remaining-tokens")
        reset = headers.get("x-ratelimit-reset-tokens")
        with self.lock:
            if remaining is not None:
                try:
                    self.remaining_tokens = float(remaining)
                except ValueError:
                    self.remaining_tokens = None
            if reset:
                self.reset_at = time.monotonic() + _parse_duration(reset)


def _parse_duration(text: str) -> float:
    """'4.297s', '1m26.4s', '250ms' → seconds."""
    total = 0.0
    for value, unit in re.findall(r"([\d.]+)(ms|s|m|h)", text):
        v = float(value)
        total += {"ms": v / 1000, "s": v, "m": v * 60, "h": v * 3600}[unit]
    return total


class OpenAICompatibleProvider:
    def __init__(self, *, name: str, base_url: str, api_key: str, model: str, timeout: float = 60.0,
                 max_retries: int = 4, use_cache: bool = True) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.use_cache = use_cache
        self.gate = _RateGate()
        self.client = httpx.Client(timeout=timeout)

    def _cache_key(self, namespace: str, system: str, user: str, schema: dict) -> str:
        return sha256_text(json.dumps([self.model, namespace, system, user, schema], sort_keys=True))

    def complete_json(self, system: str, user: str, schema: dict, *, schema_name: str = "result",
                      max_tokens: int = 1500, cache_namespace: str = "") -> LLMResponse:
        key = self._cache_key(cache_namespace, system, user, schema)
        if self.use_cache:
            with session_scope() as session:
                hit = session.get(LLMCacheEntry, key)
                if hit is not None:
                    return LLMResponse(data=hit.response, raw=json.dumps(hit.response), model=hit.model,
                                       usage=hit.usage, cached=True)

        body: dict = {
            "model": self.model,
            "temperature": 0,
            "max_completion_tokens": max_tokens,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "response_format": {"type": "json_schema",
                                "json_schema": {"name": schema_name, "strict": True, "schema": schema}},
        }
        if "gpt-oss" in self.model:
            body["reasoning_effort"] = "low"
        estimated = (len(system) + len(user)) // 3 + max_tokens
        response = self._post(body, estimated)
        if response.status_code == 400 and "response_format" in response.text:
            # Provider without strict schema support: fall back to JSON mode.
            body["response_format"] = {"type": "json_object"}
            body["messages"][0]["content"] += "\nRespond with a single JSON object matching this schema:\n" + \
                json.dumps(schema)
            response = self._post(body, estimated)
        if response.status_code >= 400:
            raise LLMError(f"{self.name} returned {response.status_code}: {response.text[:300]}")

        payload = response.json()
        content = payload["choices"][0]["message"].get("content") or ""
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if not match:
                raise LLMError(f"Model returned non-JSON content: {content[:200]}") from exc
            data = json.loads(match.group(0))
        usage = payload.get("usage", {}) or {}
        usage_slim = {k: usage.get(k) for k in ("prompt_tokens", "completion_tokens", "total_tokens")}
        latency = float(usage.get("total_time", 0) or 0) * 1000
        if self.use_cache:
            try:
                with session_scope() as session:
                    if session.get(LLMCacheEntry, key) is None:
                        session.add(LLMCacheEntry(key=key, model=self.model, prompt_version=cache_namespace,
                                                  response=data, usage=usage_slim))
            except Exception as exc:
                log.warning("Could not cache model response: %s", exc)
        return LLMResponse(data=data, raw=content, model=payload.get("model", self.model), usage=usage_slim,
                           latency_ms=latency, cached=False)

    def _post(self, body: dict, estimated_tokens: int) -> httpx.Response:
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            self.gate.wait(estimated_tokens)
            try:
                response = self.client.post(url, json=body, headers=headers)
            except httpx.HTTPError as exc:
                last_error = exc
                time.sleep(min(2 ** attempt, 20))
                continue
            self.gate.update(response.headers)
            if response.status_code == 429 or response.status_code >= 500:
                retry_after = response.headers.get("retry-after")
                delay = float(retry_after) if retry_after and retry_after.replace(".", "").isdigit() \
                    else min(2 ** (attempt + 1), 30)
                log.warning("%s returned %s; retrying in %.1fs", self.name, response.status_code, delay)
                time.sleep(min(delay, 65))
                last_error = LLMError(f"HTTP {response.status_code}")
                continue
            return response
        raise LLMError(f"{self.name} request failed after retries: {last_error}")


_provider: LLMProvider | None = None
_explicit = False
_provider_lock = threading.Lock()


def get_provider() -> LLMProvider | None:
    """The configured provider, or None when the deployment runs rules-only."""
    global _provider
    if _explicit:
        return _provider
    settings = get_settings()
    if not settings.llm_enabled:
        return None
    with _provider_lock:
        if _provider is None:
            _provider = OpenAICompatibleProvider(
                name=settings.llm_provider_label, base_url=settings.effective_llm_base_url,
                api_key=settings.effective_llm_api_key, model=settings.llm_model,
                timeout=settings.llm_timeout_seconds, max_retries=settings.llm_max_retries,
            )
        return _provider


def set_provider(provider: LLMProvider | None, *, explicit: bool = True) -> None:
    """Install a provider explicitly (tests use a deterministic fake). `explicit=False` restores config."""
    global _provider, _explicit
    _provider = provider
    _explicit = explicit and provider is not None
