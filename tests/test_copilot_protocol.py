"""Opt-in checks against an installed full CLI; never issue an inference request."""

import asyncio
import os

import pytest

pytest.importorskip("copilot")

from copilot.rpc import ToolsExecuteRequest

from cai.copilot import runtime
from cai.sdk.agents import Agent, function_tool

pytestmark = pytest.mark.skipif(
    os.getenv("CAI_TEST_COPILOT_PROTOCOL") != "1",
    reason="Set CAI_TEST_COPILOT_PROTOCOL=1 to start the installed official Copilot CLI.",
)


async def test_real_sdk_cli_exposes_only_registered_tools(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runtime, "runtime_home", lambda: tmp_path / "runtime")
    env = runtime.child_environment()
    env.update(HOME=str(tmp_path), XDG_CONFIG_HOME=str(tmp_path / "config"))
    monkeypatch.setattr(runtime, "child_environment", lambda: env)

    calls = []
    approved = False

    @function_tool
    def cai_echo(text: str) -> str:
        """Echo synthetic test text without side effects."""
        calls.append(text)
        return text

    async def approve(name, arguments):
        assert name == "cai_echo"
        assert arguments == '{"text": "synthetic hello"}'
        return approved

    client = runtime.create_client(os.getenv("CAI_COPILOT_CLI_PATH"))
    try:
        await asyncio.wait_for(client.start(), timeout=30)
        status = await client.get_status()
        assert status.protocol_version in (2, 3)
        for tools in ([], [cai_echo]):
            agent = Agent(name="Protocol test", instructions="Protocol check only.", tools=tools)
            async with runtime.CopilotRuntime(
                client, agent, "gpt-4.1", approve=approve, emit=lambda _: None
            ) as session:
                for reset in (False, True):
                    if reset:
                        await session.reset()
                    assert session.session is not None
                    metadata = await session.session.rpc.tools.get_current_metadata()
                    assert [tool.name for tool in metadata.tools] == [tool.name for tool in tools]
                    servers = await session.session.rpc.mcp.list()
                    assert servers.servers == []
                    assert servers.host.clients == []
                    assert servers.host.pending_connections == []
                    skills = await session.session.rpc.skills.list()
                    assert skills.skills == []
                if tools:
                    # Exercise the SDK callback round trip without an LLM request.
                    session._accept_tools = True
                    request = ToolsExecuteRequest(
                        name="cai_echo", arguments={"text": "synthetic hello"}
                    )
                    denied = await session.session.rpc.tools.execute(request, timeout=15)
                    assert denied["resultType"] == "denied"
                    assert calls == []
                    approved = True
                    result = await session.session.rpc.tools.execute(request, timeout=15)
                    assert result["resultType"] == "success"
                    assert result["textResultForLlm"] == "synthetic hello"
                    assert calls == ["synthetic hello"]
                    session._accept_tools = False
    finally:
        await client.stop()
