import json
import sys
from types import ModuleType
from unittest.mock import Mock

import pytest

from cai.copilot import CopilotError, config
from cai.entrypoint import main


def test_missing_preferences_do_not_import_local_model(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "preferences_path", lambda: tmp_path / "copilot.json")
    monkeypatch.setenv("CAI_MODEL", "local-lm-studio-model")
    assert config.load_model() is None


def test_preferences_round_trip(monkeypatch, tmp_path):
    path = tmp_path / ".cai" / "copilot.json"
    monkeypatch.setattr(config, "preferences_path", lambda: path)
    config.save_model("catalog-model")
    assert config.load_model() == "catalog-model"
    assert json.loads(path.read_text()) == {"model": "catalog-model"}
    assert path.stat().st_mode & 0o077 == 0
    config.save_model("other-model")
    assert config.load_model() == "other-model"
    assert list(path.parent.iterdir()) == [path]


@pytest.mark.parametrize("content", ["invalid json", "[]", "{}", '{"model":42}', '{"model":""}'])
def test_invalid_preferences_fail_explicitly(monkeypatch, tmp_path, content):
    path = tmp_path / "copilot.json"
    path.write_text(content)
    monkeypatch.setattr(config, "preferences_path", lambda: path)
    with pytest.raises(CopilotError, match="preferences"):
        config.load_model()


def test_failed_save_preserves_previous_selection(monkeypatch, tmp_path):
    path = tmp_path / "copilot.json"
    monkeypatch.setattr(config, "preferences_path", lambda: path)
    config.save_model("old-model")

    def fail(*args):
        raise OSError("disk failure")

    monkeypatch.setattr(config.os, "replace", fail)
    with pytest.raises(CopilotError, match="disk failure"):
        config.save_model("new-model")
    assert config.load_model() == "old-model"
    assert list(tmp_path.iterdir()) == [path]


def test_account_binding_round_trip_is_separate_from_model(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "preferences_path", lambda: tmp_path / "copilot.json")
    assert config.load_account() is None
    config.save_model("selected-model")
    config.save_account(config.CopilotAccount("employee_CORP", "https://example.ghe.com/"))
    assert config.load_account() == config.CopilotAccount("employee_CORP", "example.ghe.com")
    assert config.load_model() == "selected-model"
    path = tmp_path / "copilot-account.json"
    assert json.loads(path.read_text()) == {"login": "employee_CORP", "host": "example.ghe.com"}
    assert path.stat().st_mode & 0o077 == 0


@pytest.mark.parametrize("host", ["github.com", "https://github.com", "https://GITHUB.com/"])
def test_auth_host_normalization(host):
    assert config.normalize_host(host) == "github.com"


@pytest.mark.parametrize(
    "host", ["http://github.com", "https://github.com/path", "https://user@github.com", ""]
)
def test_invalid_auth_hosts_are_rejected(host):
    with pytest.raises(CopilotError):
        config.normalize_host(host)


def test_invalid_account_binding_does_not_silently_select_ambient_user(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "preferences_path", lambda: tmp_path / "copilot.json")
    (tmp_path / "copilot-account.json").write_text('{"login": 4, "host": "github.com"}')
    with pytest.raises(CopilotError, match="account binding"):
        config.load_account()


@pytest.mark.parametrize(
    ("argv", "target", "expected"),
    [
        (["cai", "copilot", "models"], "cai.copilot.cli", (["models"],)),
        (["cai", "--tui"], "cai.cli", ()),
        (["cai"], "cai.cli", ()),
    ],
)
def test_entrypoint_selects_runtime(monkeypatch, argv, target, expected):
    module = ModuleType(target)
    handler = Mock()
    module.main = handler
    monkeypatch.setitem(sys.modules, target, module)
    monkeypatch.setattr(sys, "argv", argv)
    main()
    handler.assert_called_once_with(*expected)
