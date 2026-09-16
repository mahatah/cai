"""Venice.ai routing through OpenAIChatCompletionsModel and the direct httpx client.

Verifies the transport decision for ``venice/<model>`` ids: they must reach CAI's direct
httpx client with the Venice endpoint, ``VENICE_API_KEY`` and ``venice_parameters`` even
when ``CAI_FORCE_HTTPX`` / ``OPENAI_API_BASE`` / ``ALIAS_API_KEY`` describe another
endpoint, they must never reach LiteLLM (which cannot infer a Venice provider from the
bare id) and they must never fall into the Anthropic cache-control paths. The direct
LiteLLM side callers (exception recovery, continuation) must get the LiteLLM-shaped
config for the same ids.
"""

from __future__ import annotations

import json
import pathlib

import httpx
import pytest
from openai import NOT_GIVEN, AsyncOpenAI
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.completion_usage import CompletionUsage

from cai.config import reset_config
from cai.repl import exception_recovery
from cai.sdk.agents import ModelSettings, ModelTracing, OpenAIChatCompletionsModel, generation_span
from cai.sdk.agents.models import openai_chatcompletions as occ
from cai.sdk.agents.models.chatcompletions import httpx_client
from cai.util import llm_api_base as lab

VENICE_BASE = "https://api.venice.ai/api/v1"
MODEL_ID = "venice/openai-gpt-6-astra"
BARE_ID = "openai-gpt-6-astra"
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _venice_env(monkeypatch):
    """A Venice key plus the user's LM Studio / Alias env (which must be ignored)."""
    monkeypatch.setenv("VENICE_API_KEY", "venice-secret")
    monkeypatch.delenv("VENICE_API_BASE", raising=False)
    monkeypatch.delenv("VENICE_INCLUDE_SYSTEM_PROMPT", raising=False)
    monkeypatch.setenv("CAI_FORCE_HTTPX", "true")
    monkeypatch.setenv("OPENAI_API_BASE", "http://localhost:8000/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "lmstudio-dummy")
    monkeypatch.setenv("ALIAS_API_KEY", "sk-alias-placeholder")
    monkeypatch.delenv("OLLAMA", raising=False)
    monkeypatch.delenv("CAI_MODEL_LIST", raising=False)
    reset_config()
    yield
    reset_config()


def _fake_completion(model: str = BARE_ID) -> ChatCompletion:
    return ChatCompletion(
        id="resp-id",
        created=0,
        model=model,
        object="chat.completion",
        choices=[Choice(index=0, finish_reason="stop",
                        message=ChatCompletionMessage(role="assistant", content="Hello"))],
        usage=CompletionUsage(completion_tokens=5, prompt_tokens=7, total_tokens=12),
    )


async def _run_fetch(model_id: str, monkeypatch, *, ollama: bool = False):
    captured = {}

    async def fake_direct(**kwargs):
        captured.update(kwargs)
        return _fake_completion()

    async def fail_litellm(*args, **kwargs):  # pragma: no cover - regression guard
        raise AssertionError("venice models must not reach LiteLLM")

    monkeypatch.setattr(occ, "_direct_httpx_completion_impl", fake_direct)
    monkeypatch.setattr(OpenAIChatCompletionsModel, "_fetch_response_litellm_openai", fail_litellm)
    monkeypatch.setattr(OpenAIChatCompletionsModel, "_fetch_response_litellm_ollama", fail_litellm)

    model = OpenAIChatCompletionsModel(
        model=model_id,
        openai_client=AsyncOpenAI(api_key="unused", base_url="http://localhost:1"),
    )
    if ollama:
        model.is_ollama = True
    span = generation_span(disabled=True)
    result = await model._fetch_response(
        system_instructions="You are CAI.",
        input="scan 10.0.0.1",
        model_settings=ModelSettings(),
        tools=[],
        output_schema=None,
        handoffs=[],
        span=span,
        tracing=ModelTracing.DISABLED,
        stream=False,
    )
    return result, captured


# ---------------------------------------------------------------------------
# OpenAIChatCompletionsModel._fetch_response: transport decision
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_venice_model_uses_direct_client_with_venice_auth(monkeypatch):
    result, captured = await _run_fetch(MODEL_ID, monkeypatch)
    assert isinstance(result, ChatCompletion)
    kwargs = captured["kwargs"]
    assert kwargs["model"] == BARE_ID
    assert kwargs["api_base"] == VENICE_BASE
    assert kwargs["api_key"] == "venice-secret"
    assert kwargs["custom_llm_provider"] == "openai"
    assert kwargs["venice_parameters"] == {"include_venice_system_prompt": False}
    assert "extra_body" not in kwargs
    assert "tool_choice" not in kwargs  # no tools -> no tool_choice
    assert kwargs["messages"][0]["role"] == "system"
    assert kwargs["messages"][0]["content"].startswith("You are CAI.")
    assert captured["model_name"] == MODEL_ID


@pytest.mark.asyncio
@pytest.mark.parametrize("force_httpx", ["true", "false"])
async def test_venice_ignores_force_httpx_and_openai_env(monkeypatch, force_httpx):
    monkeypatch.setenv("CAI_FORCE_HTTPX", force_httpx)
    reset_config()
    _, captured = await _run_fetch(MODEL_ID, monkeypatch)
    assert captured["kwargs"]["api_base"] == VENICE_BASE
    assert captured["kwargs"]["api_key"] == "venice-secret"


@pytest.mark.asyncio
async def test_venice_wins_over_ollama_mode(monkeypatch):
    _, captured = await _run_fetch(MODEL_ID, monkeypatch, ollama=True)
    assert captured["kwargs"]["api_base"] == VENICE_BASE
    assert captured["kwargs"]["model"] == BARE_ID


@pytest.mark.asyncio
async def test_venice_api_base_override(monkeypatch):
    monkeypatch.setenv("VENICE_API_BASE", "https://venice-proxy.example/api/v1/")
    _, captured = await _run_fetch(MODEL_ID, monkeypatch)
    assert captured["kwargs"]["api_base"] == "https://venice-proxy.example/api/v1"


@pytest.mark.asyncio
async def test_venice_system_prompt_opt_in(monkeypatch):
    monkeypatch.setenv("VENICE_INCLUDE_SYSTEM_PROMPT", "true")
    _, captured = await _run_fetch(MODEL_ID, monkeypatch)
    assert captured["kwargs"]["venice_parameters"] == {"include_venice_system_prompt": True}


@pytest.mark.asyncio
async def test_venice_claude_skips_cache_control_normalisation(monkeypatch):
    _, captured = await _run_fetch("venice/claude-sonnet-4.5", monkeypatch)
    kwargs = captured["kwargs"]
    assert kwargs["model"] == "claude-sonnet-4.5"
    for message in kwargs["messages"]:
        assert isinstance(message["content"], str), "no Anthropic cache_control blocks for Venice"
        assert "cache_control" not in message
    assert kwargs["api_base"] == VENICE_BASE


@pytest.mark.asyncio
async def test_non_venice_model_still_uses_openai_env(monkeypatch):
    """Regression guard: the venice branch must not change routing for other ids."""
    _, captured = await _run_fetch("local-model", monkeypatch)
    kwargs = captured["kwargs"]
    assert kwargs["model"] == "local-model"
    assert "api_base" not in kwargs
    assert "venice_parameters" not in kwargs
    assert captured["model_name"] == "local-model"


# ---------------------------------------------------------------------------
# Direct httpx client: wire format
# ---------------------------------------------------------------------------
def _install_async_transport(monkeypatch, handler):
    class _Client(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handler)
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(httpx_client.httpx, "AsyncClient", _Client)


def _venice_kwargs(stream: bool) -> dict:
    kwargs = {
        "model": MODEL_ID,
        "messages": [{"role": "system", "content": "You are CAI."},
                     {"role": "user", "content": "hi"}],
        "stream": stream,
        "tools": NOT_GIVEN,
        "extra_headers": {"User-Agent": "Agents/Python test"},
    }
    kwargs.update(lab.venice_request_config(kwargs["model"]))
    return kwargs


@pytest.mark.asyncio
async def test_direct_client_sends_bearer_key_bare_model_and_venice_parameters(monkeypatch):
    seen = {}

    def handler(request):
        seen["headers"] = dict(request.headers)
        seen["body"] = json.loads(request.content)
        seen["url"] = str(request.url)
        return httpx.Response(200, json=_fake_completion().model_dump())

    _install_async_transport(monkeypatch, handler)
    resp = await httpx_client.direct_httpx_completion(
        kwargs=_venice_kwargs(stream=False), model_settings=ModelSettings(), tool_choice=NOT_GIVEN,
        stream=False, parallel_tool_calls=False, model_name=MODEL_ID, user_agent="Agents/Python test",
    )
    assert resp.choices[0].message.content == "Hello"
    assert seen["url"] == f"{VENICE_BASE}/chat/completions"
    assert seen["headers"]["authorization"] == "Bearer venice-secret"
    assert seen["headers"]["user-agent"] == "Agents/Python test"
    body = seen["body"]
    assert body["model"] == BARE_ID
    assert body["venice_parameters"] == {"include_venice_system_prompt": False}
    assert body["messages"][0] == {"role": "system", "content": "You are CAI."}
    for key in ("api_base", "api_key", "custom_llm_provider", "extra_headers", "extra_body"):
        assert key not in body, key


@pytest.mark.asyncio
async def test_direct_client_streaming_uses_same_wire_format(monkeypatch):
    seen = {}
    chunk1 = {
        "id": "c1", "object": "chat.completion.chunk", "created": 0, "model": BARE_ID,
        "choices": [{"index": 0, "delta": {"role": "assistant", "content": "pong"},
                     "finish_reason": None}],
    }
    chunk2 = {
        "id": "c1", "object": "chat.completion.chunk", "created": 0, "model": BARE_ID,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }
    # OpenAI-style ``stream_options.include_usage``: a final usage-only chunk with no choices.
    chunk3 = {
        "id": "c1", "object": "chat.completion.chunk", "created": 0, "model": BARE_ID,
        "choices": [],
        "usage": {"prompt_tokens": 3, "completion_tokens": 1, "total_tokens": 4},
    }
    sse = "".join(f"data: {json.dumps(c)}\n\n" for c in (chunk1, chunk2, chunk3)) + "data: [DONE]\n\n"

    def handler(request):
        seen["headers"] = dict(request.headers)
        seen["body"] = json.loads(request.content)
        seen["url"] = str(request.url)
        return httpx.Response(
            200, content=sse.encode(), headers={"content-type": "text/event-stream"}
        )

    _install_async_transport(monkeypatch, handler)
    _, gen = await httpx_client.direct_httpx_completion(
        kwargs=_venice_kwargs(stream=True), model_settings=ModelSettings(), tool_choice=NOT_GIVEN,
        stream=True, parallel_tool_calls=False, model_name=MODEL_ID, user_agent="Agents/Python test",
    )
    chunks = [c async for c in gen]
    assert [c.choices[0].delta.content for c in chunks] == ["pong", None, None]
    assert [c.choices[0].finish_reason for c in chunks] == [None, "stop", None]
    assert chunks[-1].usage.prompt_tokens == 3 and chunks[-1].usage.completion_tokens == 1
    assert seen["url"] == f"{VENICE_BASE}/chat/completions"
    assert seen["headers"]["authorization"] == "Bearer venice-secret"
    assert seen["body"]["stream"] is True
    assert seen["body"]["model"] == BARE_ID
    assert seen["body"]["venice_parameters"] == {"include_venice_system_prompt": False}


# ---------------------------------------------------------------------------
# Regression guards from review
# ---------------------------------------------------------------------------
async def _run_real_fetch(model, monkeypatch, *, stream=False):
    """Drive _fetch_response with LiteLLM fenced off (direct client left as the caller set it)."""

    async def fail_litellm(*args, **kwargs):  # pragma: no cover - regression guard
        raise AssertionError("venice models must not reach LiteLLM")

    monkeypatch.setattr(OpenAIChatCompletionsModel, "_fetch_response_litellm_openai", fail_litellm)
    monkeypatch.setattr(OpenAIChatCompletionsModel, "_fetch_response_litellm_ollama", fail_litellm)
    return await model._fetch_response(
        system_instructions="You are CAI.",
        input="scan 10.0.0.1",
        model_settings=ModelSettings(),
        tools=[],
        output_schema=None,
        handoffs=[],
        span=generation_span(disabled=True),
        tracing=ModelTracing.DISABLED,
        stream=stream,
    )


@pytest.mark.asyncio
async def test_outer_rate_limit_retry_stays_on_venice(monkeypatch):
    """The client's pops must not leak into the caller's dict: after Venice 429s enough times
    to exhaust the client's own retries, the outer retry in _fetch_response re-dispatches the
    same kwargs and must still hit Venice with the Venice key (not OPENAI_API_BASE / Alias)."""
    seen = []
    client_attempts = httpx_client._MAX_RETRIES + 1

    def handler(request):
        seen.append((str(request.url), request.headers.get("authorization"),
                     json.loads(request.content)["model"]))
        if len(seen) <= client_attempts:
            return httpx.Response(429, json={"error": "rate limited"})
        return httpx.Response(200, json=_fake_completion().model_dump())

    async def no_sleep(*args, **kwargs):
        return None

    _install_async_transport(monkeypatch, handler)
    monkeypatch.setattr(httpx_client, "sleep_with_retry_backoff_hint", no_sleep)
    monkeypatch.setattr(occ, "sleep_with_retry_backoff_hint", no_sleep)

    model = OpenAIChatCompletionsModel(
        model=MODEL_ID, openai_client=AsyncOpenAI(api_key="unused", base_url="http://localhost:1"),
    )
    result = await _run_real_fetch(model, monkeypatch)
    assert result.choices[0].message.content == "Hello"
    assert len(seen) == client_attempts + 1, "outer retry must have re-dispatched once"
    assert {url for url, _, _ in seen} == {f"{VENICE_BASE}/chat/completions"}
    assert {auth for _, auth, _ in seen} == {"Bearer venice-secret"}
    assert {m for _, _, m in seen} == {BARE_ID}


@pytest.mark.asyncio
async def test_alias_to_venice_hot_swap_sends_no_extra_body(monkeypatch):
    """A model built for alias1 keeps a stale _is_alias_model flag after the REPL swaps
    self.model in place; the alias steering extra_body must not reach Venice (strict schema)."""
    captured = {}

    async def fake_direct(**kwargs):
        captured.update(kwargs)
        return _fake_completion()

    monkeypatch.setattr(occ, "_direct_httpx_completion_impl", fake_direct)
    model = OpenAIChatCompletionsModel(
        model="alias1", openai_client=AsyncOpenAI(api_key="unused", base_url="http://localhost:1"),
    )
    assert model._is_alias_model is True
    model.model = MODEL_ID  # what cli_headless.update_agent_models_recursively does
    model._client = None
    await _run_real_fetch(model, monkeypatch)
    kwargs = captured["kwargs"]
    assert "extra_body" not in kwargs
    assert kwargs["model"] == BARE_ID
    assert kwargs["api_base"] == VENICE_BASE
    assert kwargs["api_key"] == "venice-secret"


# ---------------------------------------------------------------------------
# Direct LiteLLM side callers
# ---------------------------------------------------------------------------
def test_exception_recovery_kwargs_for_venice():
    kwargs = exception_recovery._litellm_kwargs_for_model(MODEL_ID, cfg=None)
    assert kwargs["model"] == BARE_ID
    assert kwargs["api_base"] == VENICE_BASE
    assert kwargs["api_key"] == "venice-secret"
    assert kwargs["custom_llm_provider"] == "openai"
    assert kwargs["extra_body"] == {"venice_parameters": {"include_venice_system_prompt": False}}
    assert "venice_parameters" not in kwargs


def test_exception_recovery_kwargs_unchanged_for_other_models():
    assert exception_recovery._litellm_kwargs_for_model("gpt-4o", cfg=None) == {}
    alias = exception_recovery._litellm_kwargs_for_model("alias1", cfg=None)
    assert alias["custom_llm_provider"] == "openai"
    assert "extra_body" not in alias


@pytest.mark.asyncio
async def test_exception_recovery_completion_reaches_litellm_with_provider(monkeypatch):
    import litellm

    seen = {}

    async def fake_acompletion(**kwargs):
        seen.update(kwargs)
        return _fake_completion()

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)
    out = await exception_recovery._acompletion_once(MODEL_ID, "Traceback: boom", cfg=None)
    assert out == "Hello"
    assert seen["model"] == BARE_ID
    assert seen["custom_llm_provider"] == "openai"
    assert seen["api_base"] == VENICE_BASE
    assert seen["api_key"] == "venice-secret"
    assert seen["extra_body"]["venice_parameters"]["include_venice_system_prompt"] is False


@pytest.mark.asyncio
async def test_continuation_advice_reaches_litellm_with_provider(monkeypatch):
    import litellm
    from cai import continuation

    monkeypatch.setenv("CAI_MODEL", MODEL_ID)
    reset_config()
    seen = {}

    async def fake_acompletion(**kwargs):
        seen.update(kwargs)
        return _fake_completion()

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)
    history = [
        {"role": "user", "content": "enumerate the target"},
        {"role": "assistant", "content": "Running nmap against 10.0.0.1"},
    ]
    prompt = await continuation.generate_continuation_advice("Agent", history)
    assert isinstance(prompt, str) and prompt
    assert seen["model"] == BARE_ID
    assert seen["custom_llm_provider"] == "openai"
    assert seen["api_base"] == VENICE_BASE
    assert seen["api_key"] == "venice-secret"
    assert seen["extra_body"] == {"venice_parameters": {"include_venice_system_prompt": False}}


# ---------------------------------------------------------------------------
# Pricing / context window
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "rel_path",
    ["pricings/pricing.json", "src/cai/pricings/pricing.json"],
    ids=["context-window-file", "cost-tracker-package-file"],
)
def test_venice_astra_pricing_entry(rel_path):
    data = json.loads((REPO_ROOT / rel_path).read_text(encoding="utf-8"))
    entry = data[MODEL_ID]
    assert entry["max_input_tokens"] == 922_000
    assert entry["input_cost_per_token"] == pytest.approx(1e-5)
    assert entry["output_cost_per_token"] == pytest.approx(5e-5)


def test_venice_astra_context_window_and_cost_resolve(monkeypatch):
    monkeypatch.chdir(REPO_ROOT)
    monkeypatch.delenv("CAI_PRICINGS_DIR", raising=False)
    monkeypatch.delenv("CAI_PRICING_FILE", raising=False)
    from cai.util.pricing import COST_TRACKER, calculate_model_cost
    from cai.util.tokens import get_model_input_tokens

    assert get_model_input_tokens(MODEL_ID) == 922_000
    COST_TRACKER.model_pricing_cache.pop(MODEL_ID, None)
    assert COST_TRACKER.get_model_pricing(MODEL_ID) == (pytest.approx(1e-5), pytest.approx(5e-5))
    # 42 prompt + 5 completion tokens at $10 / $50 per 1M tokens
    assert calculate_model_cost(MODEL_ID, 42, 5) == pytest.approx(42e-5 + 25e-5)
