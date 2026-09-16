# Venice.ai

[Venice.ai](https://venice.ai) exposes an OpenAI-compatible chat API
(`https://api.venice.ai/api/v1/chat/completions`) behind an API key. CAI addresses it
with the `venice/` model prefix:

```bash
CAI_MODEL=venice/openai-gpt-6-astra
VENICE_API_KEY=<your Venice API key>
# Optional — defaults to https://api.venice.ai/api/v1
# VENICE_API_BASE=https://api.venice.ai/api/v1
```

`VENICE_API_KEY` is the only credential used for `venice/` models; `OPENAI_API_KEY`,
`ALIAS_API_KEY`, `OPENAI_API_BASE` and `CAI_FORCE_HTTPX` are ignored for them. Use the
model id exactly as Venice lists it (for example `openai-gpt-6-astra`), prefixed with
`venice/`. You can switch at runtime with `/model venice/<model>` (applies on the next
agent interaction).

## What CAI sends

- The request goes through CAI's direct HTTP client (not LiteLLM, which has no Venice
  provider), with the `venice/` prefix stripped from the model id and
  `Authorization: Bearer $VENICE_API_KEY`.
- `venice_parameters.include_venice_system_prompt` is sent as `false`: Venice otherwise
  merges its own system prompt into every request, on top of the agent's instructions.
  Set `VENICE_INCLUDE_SYSTEM_PROMPT=true` to let Venice add it.
- Venice rejects unknown request fields, so no other provider-specific fields are added.

## Pricing and context window

An entry for `venice/openai-gpt-6-astra` (per-token cost and the 1050K context window,
922K input / 128K output) ships in both pricing files CAI consults:

- `src/cai/pricings/pricing.json` feeds the cost tracker (cost footer, `CAI_PRICE_LIMIT`).
- `pricings/pricing.json`, read relative to the directory you launch `cai` from, feeds
  the context-window gauge and the auto-compaction threshold. Launch from the repository
  root (or set `CAI_MODEL_MAX_INPUT_TOKENS=922000`) so the 922K window is used instead of
  the 128K heuristic default.

For other Venice models add an entry keyed by the full `venice/<model>` id to both files.

## Notes

- The TUI's agent-creator and meta-agent helpers call LiteLLM with the raw `CAI_MODEL`
  and do not route through the Venice provider.
- Function calling and streaming are supported for models Venice flags with function
  calling (GPT-6 Astra is one of them).
