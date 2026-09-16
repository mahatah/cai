"""Official SDK lifecycle and a fail-closed bridge to CAI FunctionTools."""

from __future__ import annotations

import asyncio
import dataclasses
import json
import logging
import math
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Awaitable, Callable
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Any

from cai.copilot import CopilotError

if TYPE_CHECKING:
    from copilot import (
        CopilotClient,
        CopilotSession,
        ModelInfo,
        PermissionRequest,
        PermissionRequestResult,
    )
    from copilot.tools import Tool, ToolInvocation, ToolResult

    from cai.sdk.agents import Agent, FunctionTool, RunContextWrapper

logger = logging.getLogger(__name__)

# Do not inherit CAI provider keys, GitHub token overrides, BYOK settings, or
# runtime/config overrides. Retain desktop/keyring, proxy, CA and remote-login support.
_ENV_KEYS = {
    "PATH",
    "HOME",
    "USER",
    "LOGNAME",
    "USERNAME",
    "USERPROFILE",
    "APPDATA",
    "LOCALAPPDATA",
    "SYSTEMROOT",
    "SystemRoot",
    "COMSPEC",
    "ComSpec",
    "PATHEXT",
    "TEMP",
    "TMP",
    "TMPDIR",
    "LANG",
    "LANGUAGE",
    "TERM",
    "COLORTERM",
    "SHELL",
    "DISPLAY",
    "WAYLAND_DISPLAY",
    "XDG_RUNTIME_DIR",
    "XDG_CONFIG_HOME",
    "XDG_DATA_HOME",
    "XDG_CACHE_HOME",
    "DBUS_SESSION_BUS_ADDRESS",
    "SSH_CONNECTION",
    "SSH_CLIENT",
    "SSH_TTY",
    "CI",
    "CODESPACES",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "no_proxy",
    "NODE_EXTRA_CA_CERTS",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "COPILOT_GH_HOST",
}


def runtime_home() -> Path:
    return Path.home() / ".cai" / "copilot-runtime"


def child_environment() -> dict[str, str]:
    environment = {
        key: value for key, value in os.environ.items() if key in _ENV_KEYS or key.startswith("LC_")
    }
    environment["COPILOT_HOME"] = str(runtime_home())
    return environment


def resolve_cli_path(configured: str | None) -> str:
    candidate = os.path.expanduser(configured) if configured else "copilot"
    executable = shutil.which(candidate)
    if executable is None:
        raise CopilotError(
            "Official Copilot CLI not found. Install an SDK-compatible GitHub Copilot CLI "
            "(1.0.83 or compatible), or set CAI_COPILOT_CLI_PATH to its executable."
        )
    # Preserve executable symlinks: some packaged CLI launchers resolve assets beside them.
    return os.path.abspath(executable)


def run_login(cli_path: str | None, hostname: str | None) -> None:
    runtime_home().mkdir(mode=0o700, parents=True, exist_ok=True)
    command = [resolve_cli_path(cli_path), "login"]
    if hostname:
        command.extend(["--host", hostname])
    result = subprocess.run(command, env=child_environment(), check=False)
    if result.returncode:
        raise CopilotError(f"Copilot CLI login failed (exit {result.returncode}).")


def create_client(cli_path: str | None = None) -> CopilotClient:
    if sys.version_info < (3, 11):
        raise CopilotError(
            "Copilot mode requires Python 3.11 or newer; legacy CAI still supports 3.10."
        )
    try:
        from copilot import CopilotClient, RuntimeConnection
    except ModuleNotFoundError as exc:
        if exc.name != "copilot":
            raise
        raise CopilotError(
            "The Copilot SDK is not installed. Run python -m pip install -e '.[copilot]' "
            "in your CAI environment."
        ) from exc

    runtime_home().mkdir(mode=0o700, parents=True, exist_ok=True)
    return CopilotClient(
        connection=RuntimeConnection.for_stdio(
            path=resolve_cli_path(cli_path),
            args=["--disable-builtin-mcps", "--no-custom-instructions"],
        ),
        mode="empty",
        base_directory=str(runtime_home()),
        working_directory=str(Path.cwd()),
        env=child_environment(),
        use_logged_in_user=True,
        builtin_plugin_directories=[],
        enable_remote_sessions=False,
    )


def serialize_model(model: ModelInfo) -> dict[str, Any]:
    return dataclasses.asdict(model)


class CopilotRuntime:
    """A single Copilot session. No CAI Runner or model provider is invoked."""

    def __init__(
        self,
        client: CopilotClient,
        agent: Agent[Any],
        model: str,
        *,
        approve: Callable[[str, str], Awaitable[bool]],
        emit: Callable[[str], None],
    ) -> None:
        self.client = client
        self.agent = agent
        self.model = model
        self.approve = approve
        self.emit = emit
        self.session: CopilotSession | None = None
        self._accept_tools = False
        self._turn_lock = asyncio.Lock()
        self._tool_lock = asyncio.Lock()
        self._tool_tasks: set[asyncio.Task[Any]] = set()
        self._context: RunContextWrapper[Any] | None = None

    def _validate_agent(self) -> None:
        from cai.sdk.agents import FunctionTool

        unsupported = []
        for name in ("handoffs", "mcp_servers", "input_guardrails", "output_guardrails", "hooks"):
            if getattr(self.agent, name):
                unsupported.append(name)
        if self.agent.output_type is not None:
            unsupported.append("output_type")
        if self.agent.tool_use_behavior != "run_llm_again":
            unsupported.append("tool_use_behavior")
        if unsupported:
            raise CopilotError(
                "Copilot mode cannot preserve these CAI Runner features: " + ", ".join(unsupported)
            )
        names: set[str] = set()
        for tool in self.agent.tools:
            if not isinstance(tool, FunctionTool):
                raise CopilotError("Copilot mode supports CAI FunctionTools only.")
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", tool.name) or tool.name in names:
                raise CopilotError(f"Invalid or duplicate CAI tool name: {tool.name}")
            names.add(tool.name)

    def _permission_gate(
        self, request: PermissionRequest, invocation: object
    ) -> PermissionRequestResult:
        from copilot.rpc import PermissionDecisionApproveOnce, PermissionDecisionReject
        from copilot.session_events import PermissionRequestCustomTool

        if (
            self._accept_tools
            and isinstance(request, PermissionRequestCustomTool)
            and request.tool_name in {tool.name for tool in self.agent.tools}
            and not request.managed_approval_required
        ):
            # This admits only the callback; human approval inside it is still mandatory.
            return PermissionDecisionApproveOnce()
        return PermissionDecisionReject(feedback="Not permitted by CAI Copilot mode.")

    def _bridge_tool(self, tool: FunctionTool) -> Tool:
        from copilot.tools import Tool, ToolResult
        from jsonschema import Draft202012Validator
        from jsonschema.exceptions import ValidationError

        from cai.sdk.agents.exceptions import AgentsException, UserCancelledCommand

        Draft202012Validator.check_schema(tool.params_json_schema)
        validator = Draft202012Validator(tool.params_json_schema)

        async def invoke(call: ToolInvocation) -> ToolResult:
            task = asyncio.current_task()
            if task is not None:
                self._tool_tasks.add(task)
            try:
                async with self._tool_lock:
                    if (
                        not self._accept_tools
                        or self.session is None
                        or call.session_id != self.session.session_id
                        or call.tool_name != tool.name
                    ):
                        return ToolResult(
                            text_result_for_llm="No active authorized CAI tool request.",
                            result_type="denied",
                        )
                    arguments = call.arguments if call.arguments is not None else {}
                    try:
                        validator.validate(arguments)
                        encoded = json.dumps(arguments, ensure_ascii=True, allow_nan=False)
                    except (ValidationError, ValueError, TypeError) as exc:
                        logger.warning("Invalid arguments for Copilot tool %s: %s", tool.name, exc)
                        return ToolResult(
                            text_result_for_llm=f"Invalid arguments for {tool.name}: {exc}",
                            result_type="failure",
                        )
                    try:
                        approved = await self.approve(tool.name, encoded)
                        if approved is not True or not self._accept_tools:
                            return ToolResult(
                                text_result_for_llm=(
                                    "The operator denied this tool call. Do not retry."
                                ),
                                result_type="denied",
                            )
                        assert self._context is not None
                        result = await tool.on_invoke_tool(self._context, encoded)
                    except (UserCancelledCommand, EOFError):
                        return ToolResult(
                            text_result_for_llm="The operator cancelled this command.",
                            result_type="denied",
                        )
                    except (
                        AgentsException,
                        OSError,
                        ValueError,
                        TypeError,
                        RuntimeError,
                        LookupError,
                    ) as exc:
                        logger.error("Copilot CAI tool %s failed: %s", tool.name, exc)
                        return ToolResult(
                            text_result_for_llm=f"CAI tool {tool.name} failed: {exc}",
                            result_type="failure",
                        )
                    content = (
                        json.dumps(result, ensure_ascii=True)
                        if isinstance(result, (dict, list))
                        else str(result)
                    )
                    return ToolResult(text_result_for_llm=content, result_type="success")
            finally:
                if task is not None:
                    self._tool_tasks.discard(task)

        return Tool(
            name=tool.name,
            description=tool.description,
            parameters=tool.params_json_schema,
            handler=invoke,
            skip_permission=False,
            overrides_built_in_tool=False,
            defer="never",
        )

    async def _create_session(self) -> None:
        from cai.sdk.agents import FunctionTool, RunContextWrapper

        self._validate_agent()
        self._context = RunContextWrapper(context=None)
        instructions = await self.agent.get_system_prompt(self._context)
        if not instructions:
            raise CopilotError("The CAI agent must have a nonempty system prompt.")
        tools = [
            self._bridge_tool(tool) for tool in self.agent.tools if isinstance(tool, FunctionTool)
        ]
        self.session = await self.client.create_session(
            model=self.model,
            tools=tools,
            available_tools=[f"custom:{tool.name}" for tool in tools],
            excluded_tools=["builtin:*", "mcp:*"],
            system_message={"mode": "replace", "content": instructions},
            streaming=True,
            on_permission_request=self._permission_gate,
            enable_config_discovery=False,
            skip_custom_instructions=True,
            organization_custom_instructions="",
            enable_on_demand_instruction_discovery=False,
            enable_file_hooks=False,
            enable_host_git_operations=False,
            enable_skills=False,
            included_builtin_skills=[],
            skill_directories=[],
            instruction_directories=[],
            plugin_directories=[],
            custom_agents=[],
            mcp_servers={},
            request_extensions=False,
            enable_session_store=False,
            memory={"enabled": False},
            enable_session_telemetry=False,
            enable_experimental_mode=False,
        )

    async def __aenter__(self) -> CopilotRuntime:
        await self._create_session()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._accept_tools = False
        await self._cancel_tools()
        if self.session is not None:
            await self.session.disconnect()
            self.session = None

    async def _cancel_tools(self) -> None:
        tasks = tuple(self._tool_tasks)
        for task in tasks:
            task.cancel()
        if tasks:
            # Observe cancellation/errors from all callbacks; none may outlive this turn.
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.error("Copilot tool cleanup failed: %s", result)

    async def send(self, prompt: str, *, timeout: float = 600.0) -> str:
        from copilot.session_events import (
            AssistantMessageData,
            AssistantMessageDeltaData,
            SessionErrorData,
            SessionEvent,
            SessionIdleData,
        )

        if not prompt.strip():
            raise CopilotError("Cannot send an empty prompt.")
        if not math.isfinite(timeout) or timeout <= 0:
            raise CopilotError("The prompt timeout must be positive and finite.")
        async with self._turn_lock:
            if self.session is None:
                raise CopilotError("No active Copilot session.")
            session = self.session
            done: asyncio.Future[None] = asyncio.get_running_loop().create_future()
            streamed: set[str] = set()
            final = ""

            def on_event(event: SessionEvent) -> None:
                nonlocal final
                if done.done():
                    return
                data = event.data
                if isinstance(data, AssistantMessageDeltaData):
                    streamed.add(data.message_id)
                    self.emit(data.delta_content)
                elif isinstance(data, AssistantMessageData):
                    final = data.content
                    if data.message_id not in streamed:
                        self.emit(data.content)
                    if data.content:
                        self.emit("\n")
                elif isinstance(data, SessionErrorData):
                    done.set_exception(CopilotError(f"{data.error_type}: {data.message}"))
                elif isinstance(data, SessionIdleData):
                    if data.aborted:
                        done.set_exception(CopilotError("Copilot aborted the request."))
                    else:
                        done.set_result(None)

            unsubscribe = session.on(on_event)
            self._accept_tools = True

            async def run_turn() -> None:
                await session.send(prompt)
                await done

            completed = False
            try:
                await asyncio.wait_for(run_turn(), timeout=timeout)
                if not final:
                    raise CopilotError("Copilot finished without an assistant response.")
                completed = True
                return final
            except TimeoutError as exc:
                raise CopilotError(f"Copilot request timed out after {timeout:g} seconds.") from exc
            finally:
                self._accept_tools = False
                unsubscribe()
                if not done.done():
                    done.cancel()
                else:
                    # Consume errors even if send() failed before awaiting the idle event.
                    if not done.cancelled():
                        done.exception()
                try:
                    if not completed:
                        await asyncio.wait_for(session.abort(), timeout=5.0)
                finally:
                    await self._cancel_tools()

    async def set_model(self, model: str) -> None:
        async with self._turn_lock:
            if self.session is None:
                raise CopilotError("No active Copilot session.")
            await self.session.set_model(model)
            self.model = model

    async def reset(self) -> None:
        async with self._turn_lock:
            if self.session is not None:
                await self.session.disconnect()
                self.session = None
            await self._create_session()
