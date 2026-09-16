import json
from io import StringIO
from unittest.mock import AsyncMock, Mock

import pytest
from rich.console import Console

pytest.importorskip("copilot")

from copilot import (
    GetAuthStatusResponse,
    ModelCapabilities,
    ModelInfo,
    ModelLimits,
    ModelPolicy,
    ModelSupports,
)

from cai.copilot import CopilotError, cli, runtime
from cai.copilot.config import CopilotAccount


@pytest.fixture
def catalog():
    return [
        ModelInfo(
            id=name,
            name=f"Name of {name}",
            capabilities=ModelCapabilities(supports=ModelSupports(), limits=ModelLimits()),
        )
        for name in ("first-model", "second-model")
    ]


@pytest.fixture
def client(catalog, monkeypatch):
    monkeypatch.setattr(cli, "load_account", lambda: CopilotAccount("corporate-user", "github.com"))
    fake = Mock()
    fake.start = AsyncMock()
    fake.stop = AsyncMock()
    fake.get_auth_status = AsyncMock(
        return_value=GetAuthStatusResponse(
            isAuthenticated=True, authType="user", login="corporate-user", host="github.com"
        )
    )
    fake.list_models = AsyncMock(return_value=catalog)
    return fake


async def test_catalog_rejects_unauthenticated_account(client):
    client.get_auth_status.return_value = GetAuthStatusResponse(isAuthenticated=False)
    with pytest.raises(CopilotError, match="cai copilot login"):
        await cli._catalog(client)
    client.list_models.assert_not_awaited()


@pytest.mark.parametrize(
    ("login", "host"),
    [("personal-user", "github.com"), ("corporate-user", "different.ghe.com")],
)
async def test_unexpected_identity_stops_before_model_discovery(client, login, host):
    client.get_auth_status.return_value = GetAuthStatusResponse(
        isAuthenticated=True, login=login, host=host
    )
    with pytest.raises(CopilotError, match="identity mismatch"):
        await cli._catalog(client)
    client.list_models.assert_not_awaited()


async def test_no_account_binding_rejects_ambient_gh_auth(monkeypatch, client):
    monkeypatch.setattr(cli, "load_account", lambda: None)
    with pytest.raises(CopilotError, match="No verified corporate account binding"):
        await cli._catalog(client)
    client.list_models.assert_not_awaited()


async def test_identity_check_accepts_url_host_and_case_insensitive_login(client):
    client.get_auth_status.return_value = GetAuthStatusResponse(
        isAuthenticated=True, login="CORPORATE-USER", host="https://github.com/"
    )
    assert len(await cli._catalog(client)) == 2


async def test_login_pins_only_a_matching_identity(monkeypatch, client):
    monkeypatch.setattr(runtime, "create_client", lambda _: client)
    save = Mock()
    monkeypatch.setattr(cli, "save_account", save)
    args = cli.build_parser().parse_args(["login", "--account", "corporate-user"])
    await cli._run(args, Console(file=StringIO()))
    save.assert_called_once_with(CopilotAccount("corporate-user", "github.com"))
    client.list_models.assert_not_awaited()


async def test_wrong_login_does_not_overwrite_account_binding(monkeypatch, client):
    monkeypatch.setattr(runtime, "create_client", lambda _: client)
    save = Mock()
    monkeypatch.setattr(cli, "save_account", save)
    args = cli.build_parser().parse_args(["login", "--account", "different-user"])
    with pytest.raises(CopilotError, match="identity mismatch"):
        await cli._run(args, Console(file=StringIO()))
    save.assert_not_called()
    client.stop.assert_awaited_once()


async def test_catalog_excludes_policy_disabled_models(client, catalog):
    catalog[0].policy = ModelPolicy(state="disabled", terms="")
    assert await cli._catalog(client) == [catalog[1]]


async def test_empty_catalog_does_not_pick_a_fallback(client):
    client.list_models.return_value = []
    with pytest.raises(CopilotError, match="no models"):
        await cli._catalog(client)


async def test_json_model_output_preserves_sdk_shape(monkeypatch, client, capsys):
    monkeypatch.setattr(runtime, "create_client", lambda _: client)
    args = cli.build_parser().parse_args(["models", "--json"])
    await cli._run(args, Console())
    output = json.loads(capsys.readouterr().out)
    assert [entry["id"] for entry in output] == ["first-model", "second-model"]
    assert "capabilities" in output[0]
    assert output[0]["capabilities"]["supports"]["vision"] is False
    client.start.assert_awaited_once()
    client.stop.assert_awaited_once()


async def test_auth_status_reports_host_and_login(monkeypatch, client):
    monkeypatch.setattr(runtime, "create_client", lambda _: client)
    output = StringIO()
    await cli._run(cli.build_parser().parse_args(["status"]), Console(file=output))
    assert "corporate-user" in output.getvalue()
    assert "github.com" in output.getvalue()
    client.stop.assert_awaited_once()


async def test_failed_start_still_cleans_up_client(monkeypatch, client):
    monkeypatch.setattr(runtime, "create_client", lambda _: client)
    client.start.side_effect = RuntimeError("protocol mismatch")
    with pytest.raises(RuntimeError, match="protocol mismatch"):
        await cli._run(cli.build_parser().parse_args(["status"]), Console())
    client.stop.assert_awaited_once()


async def test_model_picker_accepts_number_and_reprompts(monkeypatch, catalog):
    prompt = Mock(prompt_async=AsyncMock(side_effect=["99", "2"]))
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(cli, "PromptSession", lambda: prompt)
    assert await cli._select_model(catalog, Console(file=StringIO())) == "second-model"
    assert prompt.prompt_async.await_count == 2


async def test_noninteractive_picker_fails_without_guessing(monkeypatch, catalog):
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: False)
    with pytest.raises(CopilotError, match="requires a terminal"):
        await cli._select_model(catalog, Console())


async def test_models_select_persists_only_selected_id(monkeypatch, client):
    monkeypatch.setattr(runtime, "create_client", lambda _: client)
    monkeypatch.setattr(cli, "_select_model", AsyncMock(return_value="second-model"))
    save = Mock()
    monkeypatch.setattr(cli, "save_model", save)
    await cli._run(cli.build_parser().parse_args(["models", "--select"]), Console(file=StringIO()))
    save.assert_called_once_with("second-model")


async def test_unavailable_chat_model_never_creates_session(monkeypatch, client):
    args = cli.build_parser().parse_args(["chat", "--model", "not-available", "--prompt", "Hello"])
    create = Mock()
    monkeypatch.setattr(runtime, "CopilotRuntime", create)
    with pytest.raises(CopilotError, match="no fallback"):
        await cli._chat(args, client, Console(file=StringIO()))
    create.assert_not_called()


@pytest.mark.parametrize(
    ("explicit", "environment", "saved", "expected"),
    [
        ("first-model", "second-model", "second-model", "first-model"),
        (None, "first-model", "second-model", "first-model"),
        (None, None, "second-model", "second-model"),
    ],
)
async def test_chat_selection_precedence(
    monkeypatch, client, explicit, environment, saved, expected
):
    args = cli.build_parser().parse_args(["chat", "--prompt", "A synthetic question", "--no-tools"])
    args.model = explicit
    if environment is None:
        monkeypatch.delenv("CAI_COPILOT_MODEL", raising=False)
    else:
        monkeypatch.setenv("CAI_COPILOT_MODEL", environment)
    monkeypatch.setenv("CAI_MODEL", "local-model-must-not-be-used")
    monkeypatch.setattr(cli, "load_model", lambda: saved)
    session = AsyncMock()
    session.__aenter__.return_value = session
    create = Mock(return_value=session)
    monkeypatch.setattr(runtime, "CopilotRuntime", create)
    await cli._chat(args, client, Console(file=StringIO()))
    assert create.call_args.args[2] == expected
    assert create.call_args.args[1].tools == []
    session.send.assert_awaited_once_with("A synthetic question", timeout=600.0)


async def test_noninteractive_tools_are_denied_even_with_yolo(monkeypatch, client):
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: False)
    monkeypatch.setenv("CAI_YOLO", "true")
    session = AsyncMock()
    session.__aenter__.return_value = session
    create = Mock(return_value=session)
    monkeypatch.setattr(runtime, "CopilotRuntime", create)
    args = cli.build_parser().parse_args(["chat", "--model", "first-model", "--prompt", "Hello"])
    await cli._chat(args, client, Console(file=StringIO()))
    approve = create.call_args.kwargs["approve"]
    assert await approve("generic_linux_command", '{"command": "echo hello"}') is False
