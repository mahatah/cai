import argparse

import pytest

from cai.copilot.cli import _positive_timeout, build_parser


@pytest.mark.parametrize("value", ["0", "-1", "nan", "inf", "-inf", "not-a-number"])
def test_invalid_timeouts_are_rejected(value):
    with pytest.raises(argparse.ArgumentTypeError):
        _positive_timeout(value)


def test_positive_timeout():
    assert _positive_timeout("0.5") == 0.5


@pytest.mark.parametrize("flag", ["--tui", "--api", "--yolo", "--unrestricted", "--yaml"])
def test_legacy_modes_cannot_accidentally_run_in_copilot(flag):
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(["chat", flag])
    assert exc.value.code == 2


def test_copilot_model_is_separate_from_lm_studio(monkeypatch):
    monkeypatch.setenv("CAI_MODEL", "lm-studio-model")
    monkeypatch.setenv("CAI_AGENT_TYPE", "selection_agent")
    monkeypatch.delenv("CAI_COPILOT_AGENT", raising=False)
    args = build_parser().parse_args(["chat"])
    assert args.model is None
    assert args.agent == "one_tool_agent"


def test_cli_path_is_passed_as_one_argument():
    args = build_parser().parse_args(
        ["--cli-path", "/opt/copilot cli/copilot", "login", "--account", "corp-user"]
    )
    assert args.cli_path == "/opt/copilot cli/copilot"


def test_model_output_modes_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["models", "--json", "--select"])
