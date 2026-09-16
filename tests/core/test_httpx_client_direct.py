"""Direct httpx client contract: it must not mutate the caller's kwargs, and its SSE parser
must accept an OpenAI-style usage-only chunk (``"choices": []``, sent with
``stream_options.include_usage``).
"""

from __future__ import annotations

import json

import httpx
import pytest
from openai import NOT_GIVEN
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.completion_usage import CompletionUsage

from cai.sdk.agents import ModelSettings
from cai.sdk.agents.models.chatcompletions import httpx_client

BASE = "https://gateway.example/v1"


def _completion() -> dict:
    return ChatCompletion(
        id="resp-id", created=0, model="m", object="chat.completion",
        choices=[Choice(index=0, finish_reason="stop",
                        message=ChatCompletionMessage(role="assistant", content="Hello"))],
        usage=CompletionUsage(completion_tokens=5, prompt_tokens=7, total_tokens=12),
    ).model_dump()


def _install(monkeypatch, handler):
    class _Client(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handler)
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(httpx_client.httpx, "AsyncClient", _Client)


async def _call(kwargs, *, stream=False):
    return await httpx_client.direct_httpx_completion(
        kwargs=kwargs, model_settings=ModelSettings(), tool_choice=NOT_GIVEN, stream=stream,
        parallel_tool_calls=False, model_name=kwargs["model"], user_agent="Agents/Python test",
    )


@pytest.mark.asyncio
async def test_caller_kwargs_are_not_mutated_and_redispatch_keeps_routing(monkeypatch):
    """Callers retry with the same dict; api_base/api_key/extra_headers must survive a call."""
    monkeypatch.setenv("OPENAI_API_BASE", "http://localhost:8000/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "other-key")
    monkeypatch.delenv("ALIAS_API_KEY", raising=False)
    seen = []

    def handler(request):
        seen.append((str(request.url), request.headers.get("authorization"),
                     json.loads(request.content)))
        return httpx.Response(200, json=_completion())

    _install(monkeypatch, handler)
    kwargs = {
        "model": "m",
        "messages": [{"role": "user", "content": "hi"}],
        "stream": False,
        "api_base": BASE,
        "api_key": "gateway-key",
        "custom_llm_provider": "openai",
        "extra_headers": {"X-Extra": "1"},
    }
    snapshot = dict(kwargs)
    await _call(kwargs)
    assert kwargs == snapshot, "direct_httpx_completion must not pop keys from the caller's dict"
    await _call(kwargs)  # what an outer retry loop does
    assert [(u, a) for u, a, _ in seen] == [(f"{BASE}/chat/completions", "Bearer gateway-key")] * 2
    for _, _, body in seen:
        assert set(body) == {"model", "messages", "stream"}, "routing keys must never reach the body"


@pytest.mark.asyncio
async def test_stream_parser_accepts_usage_only_chunk(monkeypatch):
    monkeypatch.setenv("OPENAI_API_BASE", BASE)
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    monkeypatch.delenv("ALIAS_API_KEY", raising=False)
    chunks_in = [
        {"id": "c", "object": "chat.completion.chunk", "created": 0, "model": "m",
         "choices": [{"index": 0, "delta": {"role": "assistant", "content": "pong"}, "finish_reason": None}]},
        {"id": "c", "object": "chat.completion.chunk", "created": 0, "model": "m",
         "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]},
        {"id": "c", "object": "chat.completion.chunk", "created": 0, "model": "m",
         "choices": [], "usage": {"prompt_tokens": 3, "completion_tokens": 1, "total_tokens": 4}},
    ]
    sse = "".join(f"data: {json.dumps(c)}\n\n" for c in chunks_in) + "data: [DONE]\n\n"

    def handler(request):
        return httpx.Response(200, content=sse.encode(), headers={"content-type": "text/event-stream"})

    _install(monkeypatch, handler)
    _, gen = await _call({"model": "m", "messages": [{"role": "user", "content": "hi"}], "stream": True},
                         stream=True)
    out = [c async for c in gen]
    assert [c.choices[0].delta.content for c in out] == ["pong", None, None]
    assert [c.choices[0].finish_reason for c in out] == [None, "stop", None]
    assert out[-1].usage.prompt_tokens == 3 and out[-1].usage.completion_tokens == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "provider_cost,expected",
    [
        ({"usd": 0.00067, "diem": 0.0}, 0.00067),   # Venice.ai breakdown object
        ({"diem": 0.1}, None),                       # no USD figure -> dropped
        (0.0004, 0.0004),                            # plain number passes through
    ],
    ids=["venice-object", "object-without-usd", "plain-number"],
)
async def test_non_stream_response_normalises_provider_cost(monkeypatch, provider_cost, expected):
    monkeypatch.setenv("OPENAI_API_BASE", BASE)
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    monkeypatch.delenv("ALIAS_API_KEY", raising=False)
    payload = _completion()
    payload["cost"] = provider_cost
    payload["venice_parameters"] = {"include_venice_system_prompt": False}
    _install(monkeypatch, lambda request: httpx.Response(200, json=payload))

    resp = await _call({"model": "m", "messages": [{"role": "user", "content": "hi"}], "stream": False})
    assert resp.choices[0].message.content == "Hello"
    cost = getattr(resp, "cost", None)
    if expected is None:
        assert cost is None
    else:
        assert isinstance(cost, float) and cost == pytest.approx(expected)
        float(cost)  # what run_to_jsonl does with it
