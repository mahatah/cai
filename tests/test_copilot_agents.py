import pytest

from cai.agents.copilot_agent import COPILOT_PROFILES, create_copilot_agent


@pytest.mark.parametrize("profile", COPILOT_PROFILES)
def test_copilot_roles_have_no_legacy_runtime_or_external_ai_tools(profile):
    agent = create_copilot_agent(profile)
    assert agent.model is None
    assert agent.handoffs == []
    assert agent.input_guardrails == []
    assert agent.output_guardrails == []
    assert agent.mcp_servers == []
    assert isinstance(agent.instructions, str)
    assert "CAI Copilot SDK execution mode" in agent.instructions
    assert {tool.name for tool in agent.tools} <= {"generic_linux_command", "fetch_url"}
    assert "generic_linux_command" in {tool.name for tool in agent.tools}


def test_copilot_role_does_not_render_ambient_host_or_memory(monkeypatch):
    monkeypatch.setenv("CAI_ENV_CONTEXT", "true")
    monkeypatch.setenv("CAI_MEMORY", "true")
    agent = create_copilot_agent("blueteam_agent")
    assert "Attacker machine information" not in agent.instructions
    assert "<compacted_context>" not in agent.instructions
    assert "<ctr_security_intelligence>" not in agent.instructions


def test_no_tools_mode_exposes_no_tools():
    assert create_copilot_agent("blueteam_agent", tools_enabled=False).tools == []


def test_unsupported_role_is_not_silently_replaced():
    with pytest.raises(ValueError, match="Unsupported Copilot CAI role"):
        create_copilot_agent("selection_agent")
