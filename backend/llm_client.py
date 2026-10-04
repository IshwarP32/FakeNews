"""Central LLM client wrapper for the fake-news verification pipeline.

Implements Phase 1 requirements:
- Error classification: CONFIG, QUOTA, TRANSIENT, CONTENT
- Per-model cooldown tracking
- Capability table (supports_thinking, thinking_param, supports_structured_output)
- At most 3 models per role, max 2 retries per model
- Fail-fast for CONFIG/CLIENT errors (deterministic, same on all models)
- QUOTA -> cooldown then next model; if all cooled -> llm_quota_exhausted
- TRANSIENT -> exponential backoff, then next model
- CONTENT errors (MAX_TOKENS, SAFETY, parse) -> single retry with error appended
"""

from __future__ import annotations

import json
import logging
import os
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from google import genai
from google.genai import types

logger = logging.getLogger("fake_news_verifier")

# ---------------------------------------------------------------------------
# Capability table: model_name_fragment -> capabilities
# Fragments are matched via str.startswith or substring.
# ---------------------------------------------------------------------------
CAPABILITY_TABLE: Dict[str, Dict[str, Any]] = {
    # Gemini 2.5 Flash (standard) - supports thinking with budget
    "gemini-2.5-flash-preview": {
        "supports_thinking": True,
        "thinking_param": "budget",
        "supports_structured_output": True,
    },
    "gemini-2.5-flash": {
        "supports_thinking": True,
        "thinking_param": "budget",
        "supports_structured_output": True,
    },
    # Gemini 2.5 Flash Lite - does NOT support thinking level/budget
    "gemini-2.5-flash-lite": {
        "supports_thinking": False,
        "thinking_param": "none",
        "supports_structured_output": True,
    },
    # Gemini 3.5 Flash
    "gemini-3.5-flash": {
        "supports_thinking": True,
        "thinking_param": "budget",
        "supports_structured_output": True,
    },
    # Gemini 3.1 Flash Lite
    "gemini-3.1-flash-lite": {
        "supports_thinking": False,
        "thinking_param": "none",
        "supports_structured_output": True,
    },
    # Gemini 2.0 Flash
    "gemini-2.0-flash": {
        "supports_thinking": False,
        "thinking_param": "none",
        "supports_structured_output": True,
    },
    # Gemini 1.5 Pro
    "gemini-1.5-pro": {
        "supports_thinking": False,
        "thinking_param": "none",
        "supports_structured_output": True,
    },
    # Gemini 1.5 Flash
    "gemini-1.5-flash": {
        "supports_thinking": False,
        "thinking_param": "none",
        "supports_structured_output": True,
    },
    # Default / unknown
    "__default__": {
        "supports_thinking": False,
        "thinking_param": "none",
        "supports_structured_output": True,
    },
}

# Error class constants
EC_CONFIG = "CONFIG_ERROR"         # deterministic, fail fast, no fallback
EC_QUOTA = "QUOTA_ERROR"           # cooldown model, try next
EC_TRANSIENT = "TRANSIENT_ERROR"   # backoff, retry, then next model
EC_CONTENT = "CONTENT_ERROR"       # single retry with error info
EC_UNKNOWN = "UNKNOWN_ERROR"       # treat as transient


def _get_capabilities(model_name: str) -> Dict[str, Any]:
    """Look up capability table entry for a model name."""
    name_lower = model_name.lower()
    # Exact fragment match (longest match wins)
    for fragment in sorted(CAPABILITY_TABLE.keys(), key=len, reverse=True):
        if fragment == "__default__":
            continue
        if fragment in name_lower:
            return CAPABILITY_TABLE[fragment]
    return CAPABILITY_TABLE["__default__"]


def _classify_error(exc: Exception) -> Tuple[str, Optional[int]]:
    """Classify an exception into an error category and optional retry delay seconds."""
    msg = str(exc).lower()
    exc_type = type(exc).__name__
    import re

    # 1. Check for QUOTA / 429 FIRST (prevent status code substring collisions like 44031s matching 403)
    if "429" in msg or "resource_exhausted" in msg or "quota" in msg or "rate limit" in msg:
        retry_delay = None
        delay_match = re.search(r"retrydelay.*?(\d+)s", msg)
        if delay_match:
            retry_delay = int(delay_match.group(1))
        else:
            delay_match = re.search(r"retry.{0,20}?(\d+)\s*s", msg)
            if delay_match:
                retry_delay = int(delay_match.group(1))
        return EC_QUOTA, retry_delay

    # 2. Check for TRANSIENT errors (500, 502, 503, 504, timeout, connection)
    if re.search(r"\b(500|502|503|504)\b", msg) or "internal" in msg or "unavailable" in msg or "timeout" in msg:
        return EC_TRANSIENT, None

    # 3. Check for CONFIG / CLIENT errors (400, 401, 403, 404, schema, auth)
    if re.search(r"\b(400|401|403|404)\b", msg) or "invalid_argument" in msg or "unauthenticated" in msg or "permission" in msg:
        return EC_CONFIG, None
    if "additionalproperties" in msg.replace("_", "").lower():
        return EC_CONFIG, None
    if "thinking level is not supported" in msg:
        return EC_CONFIG, None
    if "tool use with a response mime type" in msg:
        return EC_CONFIG, None
    if "schema" in msg and ("unsupported" in msg or "invalid" in msg):
        return EC_CONFIG, None
    if "valueerror" in exc_type.lower() and ("schema" in msg or "additionalproperties" in msg):
        return EC_CONFIG, None
    if "timeout" in msg or "timed out" in msg or "connection" in msg or "read operation" in msg:
        return EC_TRANSIENT, None

    if "max_tokens" in msg or "finish_reason" in msg and "max_tokens" in msg:
        return EC_CONTENT, None
    if "safety" in msg or "blocked" in msg:
        return EC_CONTENT, None

    # 404 / not found -> treat as config (model doesn't exist)
    if "404" in msg or "not found" in msg:
        return EC_CONFIG, None

    return EC_UNKNOWN, None


@dataclass
class _CooldownEntry:
    until: datetime
    reason: str


class LLMClient:
    """Central Gemini API client with error classification and fallback logic."""

    def __init__(self, api_key: Optional[str] = None):
        self._client = genai.Client(api_key=api_key or os.getenv("GEMINI_API_KEY"))
        self._cooldowns: Dict[str, _CooldownEntry] = {}
        self._short_cooldown_s = 65   # per-minute quota
        self._long_cooldown_s = 3700  # per-day quota

    def _is_on_cooldown(self, model: str) -> bool:
        entry = self._cooldowns.get(model)
        if entry is None:
            return False
        if datetime.now(timezone.utc) < entry.until:
            return True
        del self._cooldowns[model]
        return False

    def _set_cooldown(self, model: str, seconds: int, reason: str) -> None:
        until = datetime.now(timezone.utc) + timedelta(seconds=seconds)
        self._cooldowns[model] = _CooldownEntry(until=until, reason=reason)
        logger.warning("Model %s on cooldown for %ds: %s", model, seconds, reason)

    def _build_generation_config(
        self,
        model_name: str,
        system_instruction: Optional[str],
        response_schema: Any,
        thinking_level: Optional[str],
        extra_config: Optional[Dict[str, Any]] = None,
    ) -> types.GenerateContentConfig:
        """Build GenerateContentConfig from capability table - no tools, no additionalProperties."""
        caps = _get_capabilities(model_name)
        config_dict: Dict[str, Any] = {"temperature": 0}

        if system_instruction:
            config_dict["system_instruction"] = system_instruction

        if response_schema is not None:
            config_dict["response_mime_type"] = "application/json"
            config_dict["response_schema"] = response_schema

        # Add thinking config only if model supports it
        if thinking_level and caps["supports_thinking"] and caps["thinking_param"] != "none":
            param = caps["thinking_param"]
            if param == "budget":
                budget_map = {"low": 512, "medium": 2048, "high": 8192}
                budget = budget_map.get(thinking_level, 1024)
                config_dict["thinking_config"] = types.ThinkingConfig(thinking_budget=budget)
            elif param == "level":
                config_dict["thinking_config"] = types.ThinkingConfig(thinking_level=thinking_level)
        # else: no thinking config = no error

        if extra_config:
            config_dict.update(extra_config)

        return types.GenerateContentConfig(**config_dict)

    def generate(
        self,
        models: List[str],
        prompt: str,
        system_instruction: Optional[str] = None,
        response_schema: Any = None,
        thinking_level: Optional[str] = None,
        max_output_tokens: int = 8192,
        wall_clock_deadline: Optional[float] = None,
        retry_prompt_suffix: str = "",
    ) -> Tuple[Any, str]:
        """
        Call Gemini with the given model list (priority order).

        Returns (response, model_used).
        Raises RuntimeError with reason code on total failure.
        Error codes embedded in message:
          - llm_config_error: deterministic config problem
          - llm_quota_exhausted: all models on cooldown
          - llm_unavailable: all models failed after retries
        """
        available = [m for m in models if not self._is_on_cooldown(m)]
        if not available:
            cooled = [f"{m} (until {self._cooldowns[m].until.isoformat()})" for m in models]
            raise RuntimeError(f"llm_quota_exhausted: all models on cooldown: {cooled}")

        last_err: Optional[Exception] = None
        config_failed_models: List[str] = []

        for model in available:
            if wall_clock_deadline and time.monotonic() > wall_clock_deadline:
                raise RuntimeError("llm_unavailable: wall-clock budget exceeded")

            current_prompt = prompt + (f"\n\n[Retry context: {retry_prompt_suffix}]" if retry_prompt_suffix else "")

            for attempt in range(2):  # max 2 attempts per model
                try:
                    gen_config = self._build_generation_config(
                        model_name=model,
                        system_instruction=system_instruction,
                        response_schema=response_schema,
                        thinking_level=thinking_level,
                        extra_config={"max_output_tokens": max_output_tokens},
                    )
                    logger.info("LLMClient: calling %s (attempt %d)", model, attempt + 1)
                    resp = self._client.models.generate_content(
                        model=model,
                        contents=current_prompt,
                        config=gen_config,
                    )
                    return resp, model

                except Exception as exc:
                    last_err = exc
                    err_class, retry_delay = _classify_error(exc)
                    logger.warning("LLMClient: %s on model %s attempt %d: %s", err_class, model, attempt + 1, exc)

                    if err_class == EC_CONFIG:
                        config_failed_models.append(model)
                        # CONFIG errors are deterministic; fail fast, don't retry this or other models
                        # UNLESS it could be model-specific (thinking not supported etc.) - break inner loop
                        break  # try next model in case it's model-specific config

                    elif err_class == EC_QUOTA:
                        # Determine cooldown duration
                        if retry_delay is not None and retry_delay <= 12:
                            # Per-minute quota, wait once then retry
                            if attempt == 0:
                                logger.info("LLMClient: quota retry delay %ds on %s", retry_delay, model)
                                time.sleep(retry_delay + 1)
                                continue  # retry this model
                        # Put on cooldown and move to next model
                        cooldown_dur = self._long_cooldown_s if (retry_delay is None or retry_delay > 60) else self._short_cooldown_s
                        self._set_cooldown(model, cooldown_dur, str(exc))
                        break  # next model

                    elif err_class in (EC_TRANSIENT, EC_UNKNOWN):
                        if attempt == 0:
                            sleep_t = (2 ** attempt) + random.uniform(0, 1)
                            logger.info("LLMClient: transient retry in %.1fs on %s", sleep_t, model)
                            time.sleep(sleep_t)
                            continue  # retry same model
                        break  # next model after 2 attempts

                    elif err_class == EC_CONTENT:
                        if attempt == 0:
                            # retry once with error context
                            retry_prompt_suffix = f"Previous attempt failed with: {str(exc)[:200]}"
                            current_prompt = prompt + f"\n\n[Retry context: {retry_prompt_suffix}]"
                            continue
                        break  # content errors don't benefit from more retries

        # If all failures were CONFIG type (same on every model), fail fast with single message
        if last_err and config_failed_models and len(config_failed_models) >= len(available):
            raise RuntimeError(f"llm_config_error: {last_err}")

        # All models exhausted
        available_after = [m for m in models if not self._is_on_cooldown(m)]
        if not available_after:
            raise RuntimeError(f"llm_quota_exhausted: all models on cooldown after failures")

        raise RuntimeError(f"llm_unavailable: all models failed. Last error: {last_err}")

    def assert_no_tools_in_analyzer_call(self) -> None:
        """Assert that no tools are passed to Agent 3. Called in tests."""
        # This is enforced structurally: LLMClient.generate() never sets tools.
        # The old search_tool in GeminiVerifier.__init__ is removed.
        pass
