import builtins
import subprocess
from unittest.mock import Mock

import pytest

from cai.copilot import CopilotError, runtime


def test_child_environment_does_not_inherit_provider_or_token_overrides(monkeypatch, tmp_path):
    private_settings = {
        "COPILOT_GITHUB_TOKEN": "secret",
        "GH_TOKEN": "secret",
        "GITHUB_TOKEN": "secret",
        "OPENAI_API_KEY": "secret",
        "ALIAS_API_KEY": "secret",
        "ANTHROPIC_API_KEY": "secret",
        "COPILOT_PROVIDER": "unapproved-provider",
        "COPILOT_CLI_PATH": "unapproved-cli",
        "COPILOT_HOME": "/some/other/account",
        "OPENAI_API_BASE": "http://local-model",
    }
    for key, value in private_settings.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("HTTPS_PROXY", "http://corporate-proxy")
    monkeypatch.setenv("NODE_EXTRA_CA_CERTS", "/corporate/ca.pem")
    monkeypatch.setenv("DBUS_SESSION_BUS_ADDRESS", "keyring-address")
    monkeypatch.setattr(runtime, "runtime_home", lambda: tmp_path)
    env = runtime.child_environment()
    assert env["COPILOT_HOME"] == str(tmp_path)
    assert not (set(private_settings) - {"COPILOT_HOME"}) & env.keys()
    assert env["HTTPS_PROXY"] == "http://corporate-proxy"
    assert env["NODE_EXTRA_CA_CERTS"] == "/corporate/ca.pem"
    assert env["DBUS_SESSION_BUS_ADDRESS"] == "keyring-address"
    assert runtime.os.environ["OPENAI_API_KEY"] == "secret"


def test_login_uses_same_resolved_cli_and_isolated_home(monkeypatch, tmp_path):
    resolver = Mock(return_value="/opt/corporate copilot/bin/copilot")
    run = Mock(return_value=subprocess.CompletedProcess([], 0))
    monkeypatch.setattr(runtime, "resolve_cli_path", resolver)
    monkeypatch.setattr(runtime, "runtime_home", lambda: tmp_path / "runtime")
    monkeypatch.setattr(runtime.subprocess, "run", run)
    runtime.run_login("/configured/copilot", "corporate.ghe.com")
    resolver.assert_called_once_with("/configured/copilot")
    args, kwargs = run.call_args
    assert args[0] == ["/opt/corporate copilot/bin/copilot", "login", "--host", "corporate.ghe.com"]
    assert kwargs["env"]["COPILOT_HOME"] == str(tmp_path / "runtime")
    assert "shell" not in kwargs


def test_login_failure_is_not_reported_as_success(monkeypatch, tmp_path):
    monkeypatch.setattr(runtime, "resolve_cli_path", lambda _: "copilot")
    monkeypatch.setattr(runtime, "runtime_home", lambda: tmp_path)
    monkeypatch.setattr(
        runtime.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess([], 3),
    )
    with pytest.raises(CopilotError, match="exit 3"):
        runtime.run_login(None, None)


def test_missing_cli_is_actionable(monkeypatch):
    monkeypatch.setattr(runtime.shutil, "which", lambda _: None)
    with pytest.raises(CopilotError, match="CAI_COPILOT_CLI_PATH"):
        runtime.resolve_cli_path(None)


def test_missing_optional_sdk_is_actionable(monkeypatch):
    real_import = builtins.__import__

    def without_sdk(name, *args, **kwargs):
        if name == "copilot":
            raise ModuleNotFoundError("No module named copilot", name="copilot")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_sdk)
    with pytest.raises(CopilotError, match=r"\.\[copilot\]"):
        runtime.create_client()
