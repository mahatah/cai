"""Context-window lookup must not depend on the directory `cai` is launched from."""

MODEL_ID = "venice/openai-gpt-6-astra"


def test_context_window_resolves_from_package_pricing_when_cwd_is_elsewhere(tmp_path, monkeypatch):
    """A launch outside the repo used to fall back to the 128K heuristic; the package
    pricing file (the one the cost tracker reads) must serve the window too."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CAI_PRICINGS_DIR", raising=False)
    monkeypatch.delenv("CAI_MODEL_MAX_INPUT_TOKENS", raising=False)
    from cai.util.tokens import get_model_input_tokens
    from cai.sdk.agents.models.chatcompletions.auto_compactor import get_model_max_tokens

    assert get_model_input_tokens(MODEL_ID) == 922_000
    assert get_model_max_tokens(MODEL_ID) == 922_000
