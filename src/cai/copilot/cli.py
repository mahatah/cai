"""Interactive and one-shot CAI interface for the official Copilot SDK."""

from __future__ import annotations

import argparse
import asyncio
import math
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from rich.console import Console
from rich.table import Table

from cai.copilot import CopilotError
from cai.copilot.config import (
    CopilotAccount,
    load_account,
    load_model,
    normalize_host,
    save_account,
    save_model,
)

if TYPE_CHECKING:
    from copilot import CopilotClient, GetAuthStatusResponse, ModelInfo


def _positive_timeout(value: str) -> float:
    try:
        timeout = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("timeout must be a positive number of seconds") from exc
    if not math.isfinite(timeout) or timeout <= 0:
        raise argparse.ArgumentTypeError("timeout must be a positive, finite number of seconds")
    return timeout


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cai copilot",
        description="Use GitHub Copilot's SDK agent runtime with CAI roles and tools.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--cli-path",
        default=os.getenv("CAI_COPILOT_CLI_PATH"),
        help="Full official Copilot CLI executable (default: copilot on PATH)",
    )
    commands = parser.add_subparsers(dest="command")
    login = commands.add_parser("login", help="Sign in using the official Copilot CLI")
    login.add_argument(
        "--account",
        required=True,
        help="Expected corporate GitHub username (not Microsoft email); pinned after login",
    )
    login.add_argument("--hostname", "--host", help="GitHub hostname for your enterprise account")
    commands.add_parser("status", help="Show the SDK's current GitHub authentication status")
    models = commands.add_parser("models", help="List models available to the signed-in account")
    output = models.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="Print the SDK model catalog as JSON")
    output.add_argument("--select", action="store_true", help="Choose and save a default model")
    chat = commands.add_parser("chat", help="Start a CAI Copilot session (default command)")
    chat.add_argument("--model", help="Exact model ID from 'cai copilot models'")
    chat.add_argument(
        "--agent",
        default=os.getenv("CAI_COPILOT_AGENT", "one_tool_agent"),
        help="CAI role (default: one_tool_agent); see docs/copilot.md for supported roles",
    )
    chat.add_argument("--prompt", help="Run one prompt and exit instead of starting the REPL")
    chat.add_argument("--no-tools", action="store_true", help="Disable all local tool execution")
    chat.add_argument(
        "--timeout",
        type=_positive_timeout,
        default=600.0,
        help="Maximum seconds per prompt, including approvals (default: 600)",
    )
    return parser


def _show_models(models: list[ModelInfo], console: Console) -> None:
    table = Table(title="GitHub Copilot models available to this account")
    table.add_column("#", justify="right")
    table.add_column("Model ID")
    table.add_column("Name")
    for index, model in enumerate(models, 1):
        table.add_row(str(index), model.id, model.name)
    console.print(table)


async def _select_model(models: list[ModelInfo], console: Console) -> str:
    if not sys.stdin.isatty():
        raise CopilotError(
            "Model selection requires a terminal. Use --model with an ID from 'cai copilot models'."
        )
    _show_models(models, console)
    prompt: PromptSession[str] = PromptSession()
    while True:
        value = (await prompt.prompt_async("Select model number or exact ID: ")).strip()
        if value.isdecimal() and 1 <= int(value) <= len(models):
            return models[int(value) - 1].id
        if value in {model.id for model in models}:
            return value
        console.print("Invalid selection; choose an entry from the catalog.", style="yellow")


def _verify_account(
    status: GetAuthStatusResponse, expected: CopilotAccount | None = None
) -> CopilotAccount:
    if not status.isAuthenticated or not status.login or not status.host:
        raise CopilotError(
            "Copilot is not authenticated. Run 'cai copilot login --account USER' "
            "with the GitHub account assigned your corporate Copilot seat."
        )
    expected = expected or load_account()
    if expected is None:
        raise CopilotError(
            "No verified corporate account binding. Run 'cai copilot login --account USER' "
            "before listing models or sending company data."
        )
    actual = CopilotAccount(status.login, normalize_host(status.host))
    if actual.login.casefold() != expected.login.casefold() or actual.host != normalize_host(
        expected.host
    ):
        raise CopilotError(
            f"Copilot identity mismatch: authenticated as {actual.login}@{actual.host}, "
            f"expected {expected.login}@{expected.host}. No new prompt was sent."
        )
    return actual


async def _catalog(client: CopilotClient) -> list[ModelInfo]:
    _verify_account(await client.get_auth_status())
    models = [
        model
        for model in await client.list_models()
        if model.policy is None or model.policy.state != "disabled"
    ]
    if not models:
        raise CopilotError(
            "Copilot returned no models. Ask your administrator to verify your Copilot seat, "
            "CLI access, and model policies."
        )
    return models


async def _chat(args: argparse.Namespace, client: CopilotClient, console: Console) -> None:
    from cai.agents.copilot_agent import create_copilot_agent
    from cai.copilot.runtime import CopilotRuntime

    agent = create_copilot_agent(args.agent, tools_enabled=not args.no_tools)
    models = await _catalog(client)
    identity = await client.get_auth_status()
    _verify_account(identity)
    console.print(f"GitHub account: {identity.login} ({identity.host})", markup=False)
    selected = args.model or os.getenv("CAI_COPILOT_MODEL") or load_model()
    if selected is None:
        selected = await _select_model(models, console)
        save_model(selected)
    if selected not in {model.id for model in models}:
        raise CopilotError(
            f"Model '{selected}' is not in this account's current Copilot catalog. "
            "Run 'cai copilot models --select'; no fallback model was used."
        )

    prompt: PromptSession[str] | None = PromptSession() if sys.stdin.isatty() else None
    approval_lock = asyncio.Lock()

    async def approve(name: str, arguments: str) -> bool:
        async with approval_lock:
            console.print(f"\nCAI tool: {name}\nArguments: {arguments}", markup=False)
            if not sys.stdin.isatty():
                console.print("Denied: local tools require interactive approval.", style="yellow")
                return False
            try:
                assert prompt is not None
                answer = await prompt.prompt_async("Allow this tool call? [y/N] ")
            except (EOFError, KeyboardInterrupt):
                return False
            return answer.strip().lower() in {"y", "yes"}

    def emit(text: str) -> None:
        console.print(text, end="", markup=False, highlight=False, soft_wrap=True)

    async with CopilotRuntime(client, agent, selected, approve=approve, emit=emit) as runtime:
        console.print(
            f"CAI / Copilot SDK | {agent.name} | {selected}\n"
            "Copilot owns the agent loop. Local tools require approval; no legacy AI fallback.",
            markup=False,
        )
        if args.prompt is not None:
            if not args.prompt.strip():
                raise CopilotError("--prompt must not be empty.")
            await runtime.send(args.prompt, timeout=args.timeout)
            console.print()
            return
        if not sys.stdin.isatty():
            raise CopilotError("Use 'chat --prompt TEXT' for non-interactive execution.")
        assert prompt is not None
        console.print("Commands: /help, /models, /model ID, /clear, /exit. Ctrl-C exits.")
        while True:
            try:
                text = (await prompt.prompt_async("CAI Copilot> ")).strip()
            except EOFError:
                break
            if not text:
                continue
            if text in {"/exit", "/quit"}:
                break
            if text == "/help":
                console.print(
                    "/models lists the current account catalog; /model ID changes models "
                    "without discarding the conversation; /clear starts a fresh session; "
                    "/exit exits. Legacy CAI slash commands are not available."
                )
            elif text == "/models":
                _show_models(await _catalog(client), console)
            elif text.startswith("/model "):
                model = text[len("/model ") :].strip()
                if model not in {entry.id for entry in await _catalog(client)}:
                    console.print("Unknown/unavailable model; session unchanged.", style="yellow")
                    continue
                await runtime.set_model(model)
                console.print(f"Session model: {model}", markup=False)
            elif text == "/clear":
                await runtime.reset()
                console.print("Started a new Copilot conversation.")
            elif text.startswith("/"):
                console.print("Unsupported command. Use /help.", style="yellow")
            else:
                await runtime.send(text, timeout=args.timeout)
                console.print()


async def _run(args: argparse.Namespace, console: Console) -> None:
    import json

    from cai.copilot.runtime import create_client, serialize_model

    client = create_client(args.cli_path)
    try:
        await client.start()
        if args.command == "login":
            account = _verify_account(
                await client.get_auth_status(),
                CopilotAccount(args.account, normalize_host(args.hostname or "github.com")),
            )
            save_account(account)
            console.print(f"Pinned Copilot account: {account.login}@{account.host}", markup=False)
        elif args.command == "status":
            status = await client.get_auth_status()
            console.print(
                f"Authenticated: {status.isAuthenticated}\n"
                f"GitHub account: {status.login or '(none)'}\n"
                f"GitHub host: {status.host or '(none)'}\n"
                f"Authentication: {status.authType or '(none)'}",
                markup=False,
            )
            _verify_account(status)
        elif args.command == "models":
            models = await _catalog(client)
            if args.json:
                print(json.dumps([serialize_model(model) for model in models], indent=2))
            elif args.select:
                selected = await _select_model(models, console)
                save_model(selected)
                console.print(f"Saved Copilot model: {selected}", markup=False)
            else:
                _show_models(models, console)
        else:
            await _chat(args, client, console)
    finally:
        await client.stop()


def main(argv: Sequence[str] | None = None) -> None:
    load_dotenv(Path.cwd() / ".env", override=False)
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        args = parser.parse_args(
            [*(["--cli-path", args.cli_path] if args.cli_path else []), "chat"]
        )
    # This mode must never start CAI's legacy telemetry or model-trace exporters.
    os.environ["CAI_TRACING"] = "false"
    os.environ["CAI_TELEMETRY"] = "false"
    console = Console()
    try:
        if args.command == "login":
            from cai.copilot.runtime import run_login

            run_login(args.cli_path, args.hostname)
            asyncio.run(_run(args, console))
        else:
            asyncio.run(_run(args, console))
    except (EOFError, KeyboardInterrupt):
        console.print("\nCopilot session closed.")
        raise SystemExit(130) from None
    except (RuntimeError, OSError, ValueError) as exc:
        Console(stderr=True).print(f"Copilot error: {exc}", style="red", markup=False)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
