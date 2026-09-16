"""Resolve OpenAI-compatible ``api_base`` for the Alias gateway and custom endpoints."""

from __future__ import annotations

import os
import urllib.parse

DEFAULT_ALIAS_LLM_API_BASE = "https://api.aliasrobotics.com:666/"

# Model ids for which ``CSI_CUSTOM_ENDPOINT`` / ``ALIAS_API_URL`` may apply (prefix match, case-insensitive).
_ALIAS_API_URL_MODEL_PREFIXES: tuple[str, ...] = ("cai", "alias", "csi")

# Venice.ai (https://docs.venice.ai): OpenAI-compatible ``/chat/completions`` behind an
# API key. Model ids carry a ``venice/`` prefix so routing is explicit (LiteLLM 1.80.x has
# no Venice provider and cannot infer one from a bare id such as ``openai-gpt-6-astra``).
VENICE_MODEL_PREFIX = "venice/"
DEFAULT_VENICE_API_BASE = "https://api.venice.ai/api/v1"


def is_venice_model(model: str | None) -> bool:
    """True for ``venice/<model>`` ids (case-insensitive)."""
    return (model or "").strip().lower().startswith(VENICE_MODEL_PREFIX)


def strip_venice_prefix(model: str | None) -> str:
    """``venice/openai-gpt-6-astra`` -> ``openai-gpt-6-astra`` (unchanged if no prefix)."""
    m = (model or "").strip()
    if m.lower().startswith(VENICE_MODEL_PREFIX):
        return m[len(VENICE_MODEL_PREFIX):]
    return m


def resolve_venice_api_base() -> str:
    """``VENICE_API_BASE`` if non-empty, else the public Venice endpoint (ends with ``/``)."""
    return _normalize_api_base_url(
        (os.getenv("VENICE_API_BASE") or "").strip() or DEFAULT_VENICE_API_BASE
    )


def _venice_parameters() -> dict:
    """Venice-only request fields.

    Venice merges its own system prompt into every request unless told not to; CAI agents
    ship their own instructions, so that is disabled by default. Set
    ``VENICE_INCLUDE_SYSTEM_PROMPT=true`` to opt back in.
    """
    include = (os.getenv("VENICE_INCLUDE_SYSTEM_PROMPT") or "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    return {"include_venice_system_prompt": include}


def venice_request_config(model: str | None) -> dict:
    """Request overrides for the direct httpx client (fields land in the JSON body as-is).

    ``custom_llm_provider`` is included so the same dict also satisfies LiteLLM if a caller
    hands it there; the httpx client drops it before sending.
    """
    return {
        "model": strip_venice_prefix(model),
        "api_base": resolve_venice_api_base().rstrip("/"),
        "api_key": (os.getenv("VENICE_API_KEY") or "").strip(),
        "custom_llm_provider": "openai",
        "venice_parameters": _venice_parameters(),
    }


def venice_litellm_kwargs(model: str | None) -> dict:
    """Same as :func:`venice_request_config` but shaped for ``litellm.acompletion``.

    LiteLLM's OpenAI provider forwards unknown top-level kwargs as *optional params* and
    rejects them, so the Venice-only fields travel under ``extra_body``.
    """
    cfg = venice_request_config(model)
    cfg["extra_body"] = {"venice_parameters": cfg.pop("venice_parameters")}
    return cfg


def cai_model_uses_alias_mini_url_pattern(model: str | None) -> bool:
    """Legacy helper: true when ``model`` looks like ``alias…`` + ``-mini`` (case-insensitive).

    Kept for callers/tests; gateway resolution uses `model_qualifies_for_alias_api_url` instead.
    """
    m = (model or "").strip()
    if not m:
        return False
    ml = m.lower()
    return ml.startswith("alias") and ml.endswith("-mini")


def model_qualifies_for_alias_api_url(model: str | None) -> bool:
    """True when ``CSI_CUSTOM_ENDPOINT`` / ``ALIAS_API_URL`` may apply (cai, alias, or csi prefix).

    For ``provider/model`` ids, only the provider segment (before the first ``/``) is checked.
    """
    raw = (model or "").strip().lower()
    if not raw:
        return False
    base = raw.split("/", 1)[0]
    return any(base.startswith(p) for p in _ALIAS_API_URL_MODEL_PREFIXES)


def _normalize_api_base_url(url: str) -> str:
    u = (url or "").strip()
    if not u:
        return DEFAULT_ALIAS_LLM_API_BASE
    parsed = urllib.parse.urlparse(u if "://" in u else f"https://{u}")
    if not parsed.scheme:
        u = "https://" + u.lstrip("/")
        parsed = urllib.parse.urlparse(u)
    path = parsed.path or "/"
    if not path.endswith("/"):
        path = path + "/"
    netloc = parsed.netloc or ""
    if not netloc:
        return DEFAULT_ALIAS_LLM_API_BASE
    return urllib.parse.urlunparse((parsed.scheme or "https", netloc, path, "", "", ""))


def explicit_custom_llm_api_base_configured(model: str | None = None) -> bool:
    """True if a custom OpenAI-compatible base is in effect for this model."""
    effective = (model if model is not None else os.getenv("CAI_MODEL")) or ""
    if is_venice_model(effective):
        return True
    if model_qualifies_for_alias_api_url(effective):
        if (os.getenv("CSI_CUSTOM_ENDPOINT") or "").strip():
            return True
        if (os.getenv("ALIAS_API_URL") or "").strip():
            return True
    if (os.getenv("OPENAI_API_BASE") or "").strip():
        return True
    return False


def resolve_llm_openai_compatible_base(model: str | None = None) -> str:
    """Effective API base URL for ``/chat/completions`` (always ends with ``/``).

    When ``model_qualifies_for_alias_api_url``:

    1. ``CSI_CUSTOM_ENDPOINT`` if non-empty (e.g. CSI + CAI backend).
    2. ``ALIAS_API_URL`` if non-empty.
    3. ``OPENAI_API_BASE`` if non-empty.
    4. Built-in Alias gateway default.

    If the model does not qualify, only steps 3–4 apply.

    ``venice/<model>`` ids always resolve to the Venice base (``VENICE_API_BASE`` or the
    public endpoint); ``OPENAI_API_BASE`` never applies to them.

    ``model`` defaults to ``CAI_MODEL`` from the environment when omitted.
    """
    effective = (model if model is not None else os.getenv("CAI_MODEL")) or ""
    if is_venice_model(effective):
        return resolve_venice_api_base()
    if model_qualifies_for_alias_api_url(effective):
        csi_url = (os.getenv("CSI_CUSTOM_ENDPOINT") or "").strip()
        if csi_url:
            return _normalize_api_base_url(csi_url)
        alias_url = (os.getenv("ALIAS_API_URL") or "").strip()
        if alias_url:
            return _normalize_api_base_url(alias_url)
    legacy = (os.getenv("OPENAI_API_BASE") or "").strip()
    if legacy:
        return _normalize_api_base_url(legacy)
    return DEFAULT_ALIAS_LLM_API_BASE


def resolve_llm_openai_compatible_api_key(model: str | None = None) -> str:
    """Resolve API key for OpenAI-compatible clients.

    Rules:
    - Alias-family models (``cai*``, ``alias*``, ``csi*``) MUST use ``ALIAS_API_KEY``.
      They must never fall back to ``OPENAI_API_KEY`` (prevents accidental 401s when
      OPENAI_API_KEY is a placeholder and the model is routed via the Alias gateway).
    - Venice models (``venice/*``) use ``VENICE_API_KEY`` and never ``OPENAI_API_KEY``.
    - Non-alias models fall back to ``OPENAI_API_KEY``.
    """
    effective = (model if model is not None else os.getenv("CAI_MODEL")) or ""
    if model_qualifies_for_alias_api_url(effective):
        return (os.getenv("ALIAS_API_KEY") or "").strip()
    if is_venice_model(effective):
        return (os.getenv("VENICE_API_KEY") or "").strip()
    return (os.getenv("OPENAI_API_KEY") or "").strip()
