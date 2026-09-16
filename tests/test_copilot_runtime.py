"""Runtime contract tests using SDK values, without starting a CLI or model."""

from __future__ import annotations

import asyncio
import dataclasses
import json
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

pytest.importorskip("copilot")

from copilot import (  # noqa: E402
    ModelBilling,
    ModelCapabilities,
    ModelInfo,
    ModelLimits,
    ModelPolicy,
    ModelSupports,
)
from copilot.rpc import PermissionDecisionApproveOnce, PermissionDecisionReject  # noqa: E402
from copilot.session_events import (  # noqa: E402
    AssistantMessageData,
    AssistantMessageDeltaData,
    PermissionRequestCustomTool,
    PermissionRequestMcp,
    PermissionRequestRead,
    PermissionRequestShell,
    SessionErrorData,
    SessionEvent,
    SessionEventType,
    SessionIdleData,
)
from copilot.tools import Tool, ToolInvocation, ToolResult  # noqa: E402
from jsonschema.exceptions import SchemaError  # noqa: E402

from cai.copilot import CopilotError  # noqa: E402
from cai.copilot.runtime import CopilotRuntime, serialize_model  # noqa: E402
from cai.sdk.agents import (  # noqa: E402
    Agent,
    AgentHooks,
    FileSearchTool,
    FunctionTool,
    InputGuardrail,
    OutputGuardrail,
    RunContextWrapper,
    WebSearchTool,
)
from cai.sdk.agents.exceptions import AgentsException, UserCancelledCommand  # noqa: E402
from cai.sdk.agents.mcp import MCPServerStdio  # noqa: E402

SCHEMA = {
    "type": "object",
    "properties": {"value": {"type": "integer"}},
    "required": ["value"],
    "additionalProperties": False,
}
EVENT_TYPES = {
    AssistantMessageData: SessionEventType.ASSISTANT_MESSAGE,
    AssistantMessageDeltaData: SessionEventType.ASSISTANT_MESSAGE_DELTA,
    SessionErrorData: SessionEventType.SESSION_ERROR,
    SessionIdleData: SessionEventType.SESSION_IDLE,
}
RESTRICTIONS = {
    "excluded_tools": ["builtin:*", "mcp:*"],
    "streaming": True,
    "enable_config_discovery": False,
    "skip_custom_instructions": True,
    "organization_custom_instructions": "",
    "enable_on_demand_instruction_discovery": False,
    "enable_file_hooks": False,
    "enable_host_git_operations": False,
    "enable_skills": False,
    "included_builtin_skills": [],
    "skill_directories": [],
    "instruction_directories": [],
    "plugin_directories": [],
    "custom_agents": [],
    "mcp_servers": {},
    "request_extensions": False,
    "enable_session_store": False,
    "memory": {"enabled": False},
    "enable_session_telemetry": False,
    "enable_experimental_mode": False,
}


class FakeSession:
    """Dispatch genuine SDK events to synchronous, removable subscriptions."""

    def __init__(self, session_id="session-1"):
        self.session_id = session_id
        self.callbacks = []
        self.unsubscribers = []
        self.prompts = []
        self.history = []
        self.script = None
        self.send = AsyncMock(side_effect=self._send)
        self.abort = AsyncMock()
        self.disconnect = AsyncMock()
        self.set_model = AsyncMock()

    def on(self, callback):
        self.callbacks.append(callback)
        unsubscribe = Mock(side_effect=lambda: self.callbacks.remove(callback))
        self.unsubscribers.append(unsubscribe)
        return unsubscribe

    def emit(self, data):
        event = SessionEvent(
            data=data,
            id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            type=EVENT_TYPES[type(data)],
        )
        self.history.append(event)
        for callback in tuple(self.callbacks):
            assert callback(event) is None, "SDK event callbacks are synchronous"

    def finish(self, content="answer", message_id="message-1"):
        self.emit(AssistantMessageData(content=content, message_id=message_id))
        self.emit(SessionIdleData())

    async def _send(self, prompt):
        self.prompts.append(prompt)
        if self.script is None:
            self.finish()
        else:
            await self.script(self, prompt)
        return f"user-message-{len(self.prompts)}"


def make_tool(name="inspect_item", schema=None):
    async def original(context, encoded):
        assert isinstance(context, RunContextWrapper)
        return {"tool": name, "arguments": json.loads(encoded), "label": "café"}

    return FunctionTool(
        name=name,
        description=f"Inspect with {name}",
        params_json_schema=SCHEMA if schema is None else schema,
        on_invoke_tool=AsyncMock(wraps=original),
    )


@pytest.fixture
def make_runtime():
    def factory(*, tools=None, **agent_options):
        agent_options.setdefault("instructions", "Use only explicitly approved CAI tools.")
        agent = Agent(
            name="test-agent",
            tools=[make_tool()] if tools is None else tools,
            **agent_options,
        )
        session = FakeSession()
        client = SimpleNamespace(create_session=AsyncMock(return_value=session))
        approve = AsyncMock(return_value=True)
        output = []
        runtime = CopilotRuntime(
            client, agent, "catalog-model", approve=approve, emit=output.append
        )
        return SimpleNamespace(
            runtime=runtime,
            agent=agent,
            session=session,
            client=client,
            approve=approve,
            output=output,
        )

    return factory


def registered_tools(harness):
    return harness.client.create_session.await_args.kwargs["tools"]


def invocation(harness, *, index=0, arguments=None, **overrides):
    values = {
        "session_id": harness.session.session_id,
        "tool_call_id": str(uuid4()),
        "tool_name": registered_tools(harness)[index].name,
        "arguments": {"value": 1} if arguments is None else arguments,
    }
    values.update(overrides)
    return ToolInvocation(**values)


async def call_during_turn(harness, call, *, index=0):
    results = []

    async def script(session, prompt):
        results.append(await registered_tools(harness)[index].handler(call))
        session.finish()

    harness.session.script = script
    assert await harness.runtime.send("inspect") == "answer"
    assert len(results) == 1
    assert isinstance(results[0], ToolResult)
    return results[0]


def assert_unsubscribed(session):
    assert session.callbacks == []
    assert len(session.unsubscribers) == len(session.prompts)
    for unsubscribe in session.unsubscribers:
        unsubscribe.assert_called_once_with()


@pytest.mark.parametrize("names", [[], ["inspect_item", "second_tool"]])
async def test_session_creation_is_exactly_hardened(make_runtime, names):
    h = make_runtime(tools=[make_tool(name) for name in names])
    async with h.runtime as entered:
        assert entered is h.runtime
        assert h.runtime.session is h.session
        h.client.create_session.assert_awaited_once()
        bridged = registered_tools(h)
        assert h.client.create_session.await_args.args == ()
        assert h.client.create_session.await_args.kwargs == {
            **RESTRICTIONS,
            "model": "catalog-model",
            "tools": bridged,
            "available_tools": [f"custom:{name}" for name in names],
            "system_message": {"mode": "replace", "content": h.agent.instructions},
            "on_permission_request": h.runtime._permission_gate,
        }
        assert len(bridged) == len(names)
        for source, tool in zip(h.agent.tools, bridged):
            assert isinstance(tool, Tool)
            assert dataclasses.is_dataclass(tool)
            assert tool.name == source.name
            assert tool.description == source.description
            assert tool.parameters == source.params_json_schema
            assert callable(tool.handler)
            assert tool.skip_permission is False
            assert tool.overrides_built_in_tool is False
            assert tool.defer == "never"
        h.approve.assert_not_awaited()
    h.session.disconnect.assert_awaited_once_with()
    assert h.runtime.session is None


async def test_dynamic_system_prompt_receives_real_agent_and_context(make_runtime):
    instructions = AsyncMock(return_value="Dynamic CAI instructions")
    h = make_runtime(instructions=instructions)
    async with h.runtime:
        context, agent = instructions.await_args.args
        assert isinstance(context, RunContextWrapper)
        assert context.context is None
        assert agent is h.agent
        assert h.client.create_session.await_args.kwargs["system_message"] == {
            "mode": "replace",
            "content": "Dynamic CAI instructions",
        }


@pytest.mark.parametrize(
    ("options", "message"),
    [
        ({"handoffs": [Agent(name="other")]}, "handoffs"),
        ({"input_guardrails": [InputGuardrail(AsyncMock())]}, "input_guardrails"),
        ({"output_guardrails": [OutputGuardrail(AsyncMock())]}, "output_guardrails"),
        ({"hooks": AgentHooks()}, "hooks"),
        ({"output_type": dict}, "output_type"),
        (
            {"mcp_servers": [MCPServerStdio(params={"command": "must-not-be-started"})]},
            "mcp_servers",
        ),
        ({"tools": [WebSearchTool()]}, "FunctionTools only"),
        ({"tools": [FileSearchTool(vector_store_ids=["unused"])]}, "FunctionTools only"),
        ({"tools": [make_tool("same"), make_tool("same")]}, "duplicate"),
        ({"tools": [make_tool("builtin:inspect_item")]}, "Invalid"),
        ({"tools": [make_tool("*")]}, "Invalid"),
        ({"tools": [make_tool("1invalid")]}, "Invalid"),
        ({"tool_use_behavior": "stop_on_first_tool"}, "tool_use_behavior"),
        ({"instructions": ""}, "nonempty system prompt"),
        ({"instructions": None}, "nonempty system prompt"),
    ],
)
async def test_unsupported_agent_fails_before_session_creation(make_runtime, options, message):
    h = make_runtime(**options)
    with pytest.raises(CopilotError, match=message):
        async with h.runtime:
            pytest.fail("Unsupported agent entered the runtime")
    h.client.create_session.assert_not_awaited()
    h.approve.assert_not_awaited()
    assert h.runtime.session is None


async def test_invalid_function_schema_is_rejected_before_registration(make_runtime):
    h = make_runtime(tools=[make_tool(schema={"type": "not-a-json-schema-type"})])
    with pytest.raises(SchemaError):
        async with h.runtime:
            pytest.fail("Invalid schema was registered")
    h.client.create_session.assert_not_awaited()
    h.approve.assert_not_awaited()


@pytest.mark.parametrize(
    "arguments",
    [{}, {"value": "1"}, {"value": True}, {"value": 1, "extra": 2}, [], "{}", 7, None],
)
async def test_schema_validation_precedes_approval(make_runtime, arguments):
    h = make_runtime()
    async with h.runtime:
        call = invocation(h)
        call.arguments = arguments
        result = await call_during_turn(h, call)
        assert result.result_type == "failure"
        assert "Invalid arguments" in result.text_result_for_llm
        h.approve.assert_not_awaited()
        h.agent.tools[0].on_invoke_tool.assert_not_awaited()


@pytest.mark.parametrize("value", [float("nan"), float("inf"), {1, 2}])
async def test_non_json_arguments_fail_without_approval(make_runtime, value):
    h = make_runtime(tools=[make_tool(schema={"type": "object"})])
    async with h.runtime:
        result = await call_during_turn(h, invocation(h, arguments={"value": value}))
        assert result.result_type == "failure"
        h.approve.assert_not_awaited()
        h.agent.tools[0].on_invoke_tool.assert_not_awaited()


@pytest.mark.parametrize("decision", [True, False, None, 0, 1, "yes", {"approved": True}])
async def test_only_explicit_true_approval_invokes_original_tool(make_runtime, decision):
    h = make_runtime()
    original = h.agent.tools[0].on_invoke_tool

    async def approve(name, encoded):
        original.assert_not_awaited()
        assert name == "inspect_item"
        assert json.loads(encoded) == {"value": 1}
        return decision

    h.approve.side_effect = approve
    async with h.runtime:
        result = await call_during_turn(h, invocation(h))
        h.approve.assert_awaited_once_with("inspect_item", '{"value": 1}')
        if decision is True:
            assert result.result_type == "success"
            assert json.loads(result.text_result_for_llm) == {
                "tool": "inspect_item",
                "arguments": {"value": 1},
                "label": "café",
            }
            original.assert_awaited_once()
            context, encoded = original.await_args.args
            assert isinstance(context, RunContextWrapper)
            assert context.context is None
            assert encoded == h.approve.await_args.args[1]
        else:
            assert result.result_type == "denied"
            original.assert_not_awaited()


@pytest.mark.parametrize(
    "overrides", [{"session_id": "another-session"}, {"tool_name": "another-tool"}]
)
async def test_tool_identity_must_match_active_session_and_registered_tool(make_runtime, overrides):
    h = make_runtime()
    async with h.runtime:
        result = await call_during_turn(h, invocation(h, **overrides))
        assert result.result_type == "denied"
        h.approve.assert_not_awaited()
        h.agent.tools[0].on_invoke_tool.assert_not_awaited()


async def test_tool_callbacks_are_denied_before_after_and_outside_session(make_runtime):
    h = make_runtime()
    async with h.runtime:
        tool = registered_tools(h)[0]
        call = invocation(h)
        before = await tool.handler(call)
        assert isinstance(before, ToolResult)
        assert before.result_type == "denied"
        h.approve.assert_not_awaited()
        assert (await call_during_turn(h, call)).result_type == "success"
        after = await tool.handler(call)
        assert isinstance(after, ToolResult)
        assert after.result_type == "denied"
    disconnected = await tool.handler(call)
    assert isinstance(disconnected, ToolResult)
    assert disconnected.result_type == "denied"
    h.approve.assert_awaited_once()
    h.agent.tools[0].on_invoke_tool.assert_awaited_once()


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (UserCancelledCommand("test-operation"), "denied"),
        (AgentsException("agent failed"), "failure"),
        (OSError("operation failed"), "failure"),
        (ValueError("bad value"), "failure"),
        (TypeError("bad type"), "failure"),
        (RuntimeError("runtime failed"), "failure"),
        (KeyError("missing result"), "failure"),
    ],
)
async def test_function_cancellation_and_errors_return_typed_results(make_runtime, error, expected):
    h = make_runtime()
    h.agent.tools[0].on_invoke_tool.side_effect = error
    async with h.runtime:
        result = await call_during_turn(h, invocation(h))
        assert result.result_type == expected
        assert result.text_result_for_llm
        h.approve.assert_awaited_once()
        h.agent.tools[0].on_invoke_tool.assert_awaited_once()


@pytest.mark.parametrize(
    ("error", "expected"),
    [(UserCancelledCommand("approval"), "denied"), (RuntimeError("approval failed"), "failure")],
)
async def test_approval_cancellation_and_errors_never_invoke_tool(make_runtime, error, expected):
    h = make_runtime()
    h.approve.side_effect = error
    async with h.runtime:
        result = await call_during_turn(h, invocation(h))
        assert result.result_type == expected
        h.agent.tools[0].on_invoke_tool.assert_not_awaited()


async def test_two_bridges_bind_their_own_name_schema_and_callback(make_runtime):
    string_schema = {
        **SCHEMA,
        "properties": {"value": {"type": "string"}},
    }
    first, second = make_tool("first"), make_tool("second", string_schema)
    h = make_runtime(tools=[first, second])
    async with h.runtime:
        second_result = await call_during_turn(
            h, invocation(h, index=1, arguments={"value": "second"}), index=1
        )
        first.on_invoke_tool.assert_not_awaited()
        first_result = await call_during_turn(h, invocation(h))
        assert json.loads(first_result.text_result_for_llm)["tool"] == "first"
        assert json.loads(second_result.text_result_for_llm)["tool"] == "second"
        assert first.on_invoke_tool.await_args.args[1] == '{"value": 1}'
        assert second.on_invoke_tool.await_args.args[1] == '{"value": "second"}'
        assert first.on_invoke_tool.await_args.args[0] is second.on_invoke_tool.await_args.args[0]
        assert [args.args[0] for args in h.approve.await_args_list] == ["second", "first"]


@pytest.mark.parametrize("second_index", [0, 1], ids=["same-tool", "different-tools"])
async def test_approval_and_execution_are_serialized(make_runtime, second_index):
    h = make_runtime(tools=[make_tool("first"), make_tool("second")])
    entered = asyncio.Event()
    release = asyncio.Event()
    second_attempted = asyncio.Event()
    timeline = []

    async def approve(name, encoded):
        timeline.append(("approve", json.loads(encoded)["value"]))
        return True

    async def original(context, encoded):
        value = json.loads(encoded)["value"]
        timeline.append(("invoke", value))
        if value == 1:
            entered.set()
            await release.wait()
        timeline.append(("finish", value))
        return {"value": value}

    h.approve.side_effect = approve
    for tool in h.agent.tools:
        tool.on_invoke_tool.side_effect = original

    async def script(session, prompt):
        first = asyncio.create_task(registered_tools(h)[0].handler(invocation(h)))
        second = None
        try:
            await asyncio.wait_for(entered.wait(), 1)

            async def invoke_second():
                second_attempted.set()
                return await registered_tools(h)[second_index].handler(
                    invocation(h, index=second_index, arguments={"value": 2})
                )

            second = asyncio.create_task(invoke_second())
            await asyncio.wait_for(second_attempted.wait(), 1)
            assert timeline == [("approve", 1), ("invoke", 1)]
            assert not second.done()
            release.set()
            results = await asyncio.wait_for(asyncio.gather(first, second), 1)
            assert all(isinstance(result, ToolResult) for result in results)
            assert [result.result_type for result in results] == ["success", "success"]
        finally:
            release.set()
            tasks = [task for task in (first, second) if task is not None]
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        session.finish()

    h.session.script = script
    async with h.runtime:
        await h.runtime.send("two calls")
    assert timeline == [
        ("approve", 1),
        ("invoke", 1),
        ("finish", 1),
        ("approve", 2),
        ("invoke", 2),
        ("finish", 2),
    ]


@pytest.mark.parametrize(
    ("permission", "allowed"),
    [
        (PermissionRequestCustomTool("known", "inspect_item"), True),
        (
            PermissionRequestCustomTool("known", "inspect_item", managed_approval_required=False),
            True,
        ),
        (PermissionRequestCustomTool("unknown", "unknown"), False),
        (PermissionRequestCustomTool("builtin", "builtin:inspect_item"), False),
        (PermissionRequestCustomTool("mcp", "mcp:inspect_item"), False),
        (
            PermissionRequestCustomTool("managed", "inspect_item", managed_approval_required=True),
            False,
        ),
        (PermissionRequestRead(intention="read", path="unused"), False),
        (
            PermissionRequestShell(
                can_offer_session_approval=False,
                commands=[],
                full_command_text="must-not-run",
                has_write_file_redirection=False,
                intention="unused",
                possible_paths=[],
                possible_urls=[],
            ),
            False,
        ),
        (PermissionRequestMcp(True, "server", "inspect_item", "same tool name"), False),
    ],
)
async def test_permission_gate_only_admits_known_unmanaged_custom_tools_in_turn(
    make_runtime, permission, allowed
):
    h = make_runtime()
    async with h.runtime:
        gate = h.client.create_session.await_args.kwargs["on_permission_request"]
        context = {"session_id": h.session.session_id}
        assert isinstance(gate(permission, context), PermissionDecisionReject)

        async def script(session, prompt):
            decision = gate(permission, context)
            expected = PermissionDecisionApproveOnce if allowed else PermissionDecisionReject
            assert isinstance(decision, expected)
            h.approve.assert_not_awaited()
            h.agent.tools[0].on_invoke_tool.assert_not_awaited()
            session.finish()

        h.session.script = script
        await h.runtime.send("permission")
        assert isinstance(gate(permission, context), PermissionDecisionReject)
    assert isinstance(gate(permission, context), PermissionDecisionReject)


async def test_no_tools_mode_rejects_custom_permission_during_turn(make_runtime):
    h = make_runtime(tools=[])

    async def script(session, prompt):
        gate = h.client.create_session.await_args.kwargs["on_permission_request"]
        request = PermissionRequestCustomTool("not registered", "inspect_item")
        assert isinstance(
            gate(request, {"session_id": session.session_id}), PermissionDecisionReject
        )
        session.finish()

    h.session.script = script
    async with h.runtime:
        await h.runtime.send("no tools")
    h.approve.assert_not_awaited()


@pytest.mark.parametrize(
    ("events", "output", "answer"),
    [
        (
            [
                AssistantMessageDeltaData("hello ", "one"),
                AssistantMessageDeltaData("world", "one"),
                AssistantMessageData("hello world", "one"),
            ],
            "hello world\n",
            "hello world",
        ),
        ([AssistantMessageData("final only", "one")], "final only\n", "final only"),
        (
            [
                AssistantMessageDeltaData("first", "one"),
                AssistantMessageData("first", "one"),
                AssistantMessageData("second", "two"),
            ],
            "first\nsecond\n",
            "second",
        ),
    ],
)
async def test_streaming_deduplicates_final_by_message_id(make_runtime, events, output, answer):
    h = make_runtime()

    async def script(session, prompt):
        for data in events:
            session.emit(data)
        session.emit(SessionIdleData())
        session.emit(AssistantMessageData("late event after idle", "late"))

    h.session.script = script
    async with h.runtime:
        assert await h.runtime.send("question") == answer
        assert "".join(h.output) == output
        assert_unsubscribed(h.session)
        h.session.emit(AssistantMessageDeltaData("unsubscribed", "late"))
        assert "".join(h.output) == output
        h.session.abort.assert_not_awaited()


async def test_multiple_turns_reuse_session_and_reset_stream_tracking(make_runtime):
    h = make_runtime()

    async def script(session, prompt):
        if prompt == "first":
            session.emit(AssistantMessageDeltaData("first response", "reused-id"))
        session.finish(f"{prompt} response", "reused-id")

    h.session.script = script
    async with h.runtime:
        assert await h.runtime.send("first") == "first response"
        assert await h.runtime.send("second") == "second response"
        assert h.runtime.session is h.session
        assert h.session.prompts == ["first", "second"]
        assert "".join(h.output) == "first response\nsecond response\n"
        h.client.create_session.assert_awaited_once()
        assert_unsubscribed(h.session)


@pytest.mark.parametrize(
    ("events", "error"),
    [
        ([SessionErrorData("provider_error", "not available")], "provider_error: not available"),
        ([SessionIdleData(aborted=True)], "aborted"),
        ([AssistantMessageData("partial", "one"), SessionIdleData(aborted=True)], "aborted"),
        ([SessionIdleData()], "without an assistant response"),
        ([AssistantMessageData("", "one"), SessionIdleData()], "without an assistant response"),
    ],
)
async def test_session_failures_abort_unsubscribe_and_allow_next_turn(make_runtime, events, error):
    h = make_runtime()

    async def script(session, prompt):
        for data in events:
            session.emit(data)

    h.session.script = script
    async with h.runtime:
        with pytest.raises(CopilotError, match=error):
            await h.runtime.send("failure")
        h.session.abort.assert_awaited_once_with()
        assert_unsubscribed(h.session)
        h.session.script = None
        assert await h.runtime.send("recovery") == "answer"
        assert_unsubscribed(h.session)


@pytest.mark.parametrize("emit_error_first", [False, True])
async def test_send_exception_propagates_and_unsubscribes(make_runtime, emit_error_first):
    h = make_runtime()

    async def script(session, prompt):
        if emit_error_first:
            session.emit(SessionErrorData("session_error", "secondary error"))
        raise OSError("send failed")

    h.session.script = script
    async with h.runtime:
        with pytest.raises(OSError, match="send failed"):
            await h.runtime.send("failure")
        h.session.abort.assert_awaited_once_with()
        assert_unsubscribed(h.session)


@pytest.mark.parametrize("mode", ["timeout", "cancel"])
@pytest.mark.parametrize("stage", ["send", "approval", "handler"])
async def test_interrupted_turn_aborts_sdk_and_cancels_inflight_work(make_runtime, mode, stage):
    h = make_runtime()
    started = asyncio.Event()
    stopped = asyncio.Event()
    blocked = asyncio.Event()
    tool_tasks = []

    async def wait_until_cancelled(*args):
        started.set()
        try:
            await blocked.wait()
        finally:
            stopped.set()

    if stage == "approval":
        h.approve.side_effect = wait_until_cancelled
    elif stage == "handler":
        h.agent.tools[0].on_invoke_tool.side_effect = wait_until_cancelled

    async def script(session, prompt):
        if stage == "send":
            await wait_until_cancelled()
        else:
            # A second queued callback must be cancelled without reaching approval.
            for _ in range(2):
                tool_tasks.append(
                    asyncio.create_task(registered_tools(h)[0].handler(invocation(h)))
                )

    h.session.script = script
    async with h.runtime:
        turn = asyncio.create_task(
            h.runtime.send("interrupt", timeout=0.1 if mode == "timeout" else 5)
        )
        try:
            await asyncio.wait_for(started.wait(), 1)
            if mode == "cancel":
                turn.cancel()
            error = CopilotError if mode == "timeout" else asyncio.CancelledError
            with pytest.raises(error, match="timed out" if mode == "timeout" else None):
                await asyncio.wait_for(turn, 1)
            assert stopped.is_set()
            assert all(task.done() and task.cancelled() for task in tool_tasks)
            h.session.abort.assert_awaited_once_with()
            assert_unsubscribed(h.session)
            assert h.approve.await_count == (stage != "send")
            assert h.agent.tools[0].on_invoke_tool.await_count == (stage == "handler")
            assert h.runtime._tool_tasks == set()
        finally:
            turn.cancel()
            for task in tool_tasks:
                task.cancel()
            await asyncio.gather(turn, *tool_tasks, return_exceptions=True)
        h.session.script = None
        assert await h.runtime.send("next turn") == "answer"


@pytest.mark.parametrize("late_approval", [False, True])
async def test_idle_cancels_pending_approval_without_invoking_tool(make_runtime, late_approval):
    h = make_runtime()
    started = asyncio.Event()
    stopped = asyncio.Event()
    tasks = []

    async def approve(name, encoded):
        started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            if late_approval:
                return True
            raise
        finally:
            stopped.set()

    async def script(session, prompt):
        tasks.append(asyncio.create_task(registered_tools(h)[0].handler(invocation(h))))
        await started.wait()
        session.finish()

    h.approve.side_effect = approve
    h.session.script = script
    async with h.runtime:
        assert await h.runtime.send("finish early", timeout=1) == "answer"
        assert stopped.is_set()
        assert len(tasks) == 1
        if late_approval:
            result = tasks[0].result()
            assert isinstance(result, ToolResult)
            assert result.result_type == "denied"
        else:
            assert tasks[0].cancelled()
        h.agent.tools[0].on_invoke_tool.assert_not_awaited()
        h.session.abort.assert_not_awaited()
        assert_unsubscribed(h.session)


@pytest.mark.parametrize(
    ("prompt", "timeout", "message"),
    [
        ("", 1, "empty prompt"),
        (" \t\n", 1, "empty prompt"),
        ("valid", 0, "positive and finite"),
        ("valid", -1, "positive and finite"),
        ("valid", float("inf"), "positive and finite"),
        ("valid", float("nan"), "positive and finite"),
    ],
)
async def test_invalid_turn_is_rejected_without_sdk_send(make_runtime, prompt, timeout, message):
    h = make_runtime()
    async with h.runtime:
        with pytest.raises(CopilotError, match=message):
            await h.runtime.send(prompt, timeout=timeout)
        h.session.send.assert_not_awaited()
        h.session.abort.assert_not_awaited()
        assert h.session.unsubscribers == []


async def test_operations_require_an_active_session(make_runtime):
    h = make_runtime()
    with pytest.raises(CopilotError, match="No active Copilot session"):
        await h.runtime.send("question")
    with pytest.raises(CopilotError, match="No active Copilot session"):
        await h.runtime.set_model("other-model")
    h.client.create_session.assert_not_awaited()


@pytest.mark.parametrize("fails", [False, True], ids=["success", "failure"])
async def test_model_switch_preserves_session_and_history(make_runtime, fails):
    h = make_runtime()
    async with h.runtime:
        await h.runtime.send("first turn")
        history = h.session.history.copy()
        if fails:
            h.session.set_model.side_effect = RuntimeError("model unavailable")
            with pytest.raises(RuntimeError, match="model unavailable"):
                await h.runtime.set_model("other-model")
            assert h.runtime.model == "catalog-model"
        else:
            await h.runtime.set_model("other-model")
            assert h.runtime.model == "other-model"
        h.session.set_model.assert_awaited_once_with("other-model")
        assert h.runtime.session is h.session
        assert h.session.history == history
        assert h.session.prompts == ["first turn"]
        h.session.disconnect.assert_not_awaited()
        await h.runtime.send("second turn")
        assert h.session.history[: len(history)] == history
        h.client.create_session.assert_awaited_once()


async def test_reset_disconnects_and_recreates_with_same_restrictions(make_runtime):
    h = make_runtime()
    replacement = FakeSession("session-2")
    h.client.create_session.side_effect = [h.session, replacement]
    async with h.runtime:
        await h.runtime.send("old conversation")
        original_config = h.client.create_session.await_args.kwargs.copy()
        old_tool = registered_tools(h)[0]
        old_call = invocation(h)
        await h.runtime.set_model("other-model")
        await h.runtime.reset()
        h.session.disconnect.assert_awaited_once_with()
        assert h.runtime.session is replacement
        assert h.runtime.model == "other-model"
        new_config = h.client.create_session.await_args.kwargs.copy()
        old_tools = original_config.pop("tools")
        new_tools = new_config.pop("tools")
        original_config["model"] = "other-model"
        assert new_config == original_config
        assert [dataclasses.replace(tool, handler=None) for tool in new_tools] == [
            dataclasses.replace(tool, handler=None) for tool in old_tools
        ]
        assert (await old_tool.handler(old_call)).result_type == "denied"
        assert replacement.history == []

        async def script(session, prompt):
            stale_result = await old_tool.handler(old_call)
            assert isinstance(stale_result, ToolResult)
            assert stale_result.result_type == "denied"
            h.approve.assert_not_awaited()
            session.finish()

        replacement.script = script
        assert await h.runtime.send("new conversation") == "answer"
        assert replacement.prompts == ["new conversation"]
        assert h.session.prompts == ["old conversation"]
        assert_unsubscribed(h.session)
        assert_unsubscribed(replacement)
    replacement.disconnect.assert_awaited_once_with()
    h.session.disconnect.assert_awaited_once_with()


async def test_failed_reset_does_not_retain_disconnected_session(make_runtime):
    h = make_runtime()
    async with h.runtime:
        h.client.create_session.side_effect = RuntimeError("creation failed")
        with pytest.raises(RuntimeError, match="creation failed"):
            await h.runtime.reset()
        assert h.runtime.session is None
        assert h.runtime.model == "catalog-model"
        h.session.disconnect.assert_awaited_once_with()
    h.session.disconnect.assert_awaited_once_with()


async def test_exceptional_context_exit_disconnects_and_preserves_exception(make_runtime):
    h = make_runtime()
    with pytest.raises(ValueError, match="caller failed"):
        async with h.runtime:
            await h.runtime.send("question")
            raise ValueError("caller failed")
    h.session.disconnect.assert_awaited_once_with()
    assert h.runtime.session is None
    assert_unsubscribed(h.session)


def test_model_serialization_uses_real_sdk_nested_dataclasses():
    model = ModelInfo(
        id="catalog-model",
        name="Catalog Model",
        capabilities=ModelCapabilities(
            supports=ModelSupports(vision=True),
            limits=ModelLimits(max_context_window_tokens=128_000),
        ),
        policy=ModelPolicy(state="enabled", terms="policy terms"),
        billing=ModelBilling(multiplier=1.5),
        supported_reasoning_efforts=["low", "high"],
    )
    serialized = serialize_model(model)
    assert serialized == dataclasses.asdict(model)
    assert serialized["capabilities"]["supports"]["vision"] is True
    assert serialized["capabilities"]["limits"]["max_context_window_tokens"] == 128_000
    assert serialized["policy"] == {"state": "enabled", "terms": "policy terms"}
    assert serialized["billing"]["multiplier"] == 1.5
    assert json.loads(json.dumps(serialized)) == serialized
