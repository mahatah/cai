# GitHub Copilot SDK execution mode

`cai copilot` uses the **official GitHub Copilot Python SDK** and its CLI agent
runtime. It is a separate execution mode, not an OpenAI-compatible provider or a
proxy for an undocumented Copilot endpoint. Copilot owns inference, conversation
state, tool selection, and context compaction. CAI supplies its specialist role
instructions and approved local tools.

Plain `cai`, LM Studio, the legacy REPL, TUI, and HTTP API retain their existing
behavior. Do not set `CAI_MODEL` to a Copilot model or point `OPENAI_API_BASE` at
GitHub. Those settings belong to the legacy runtime.

## Account and policy prerequisites

You need a **GitHub account assigned a GitHub Copilot seat** that permits Copilot
CLI/SDK use. A Microsoft 365 Copilot license, Azure subscription, or Microsoft
Entra account alone is not a GitHub Copilot entitlement. Your organization may
use Entra ID to provision a GitHub Enterprise Managed User or to authenticate
GitHub enterprise SSO. Complete that organization's identity-provider flow in
the browser when GitHub requests it.

Have your administrator confirm the correct GitHub identity, assigned seat,
Copilot CLI access, enabled models, applicable SDK terms, and organizational data
handling requirements. Using the official SDK is not, by itself, a compliance
certification. Network access, data residency, retention, model-provider policies,
and approval to send security-assessment data still require your organization's
review. Copilot usage consumes the account's applicable subscription allowances;
CAI's local-model price estimates do not apply.

## Install, authenticate, and select a model

Use **Python 3.11 or newer** for Copilot mode (legacy CAI still supports 3.10).
From this branch, install the optional extra in your CAI virtual environment:

```bash
python -m pip install -e '.[copilot]'
# Install the full official CLI using your organization's approved distribution.
# For example, with Node.js/npm:
npm install -g @github/copilot@1.0.83
cai copilot login --account YOUR_CORPORATE_GITHUB_USERNAME
cai copilot status
cai copilot models --select
cai copilot chat
```

Login delegates to the official Copilot CLI, not a CAI password form. Sign in
with the **corporate GitHub identity**, completing Microsoft/Entra SSO if your
enterprise requires it. CAI does not collect or save your Microsoft password,
GitHub token, or device code. Verify the account shown by `status` before sending
company data.

`--account` is required: supply your **GitHub username**, including a managed-user
suffix if applicable, not your Microsoft email address. After login, CAI checks
the SDK's effective username and GitHub host against your selection and saves
that non-secret identity to the owner-only `~/.cai/copilot-account.json`.
Missing or mismatched bindings block model discovery and prompts. This prevents
an unintended personal `gh` login from being used automatically when the
isolated Copilot home has no credential. The official CLI can still use `gh`
credentials for the **same explicitly selected identity**; CAI verifies the
effective account, not the credential's provenance.

This integration pins **`github-copilot-sdk==1.0.13`**, whose matching runtime is
**1.0.83**. It uses the **full official CLI on PATH** for both login and execution,
not the SDK's automatically downloaded hostless runtime. To use an
administrator-managed compatible installation, set `CAI_COPILOT_CLI_PATH` or place
`--cli-path /path/to/copilot` **before** the subcommand. Use the same executable
for login, status, and chat. `login --account USER --hostname HOST` selects an enterprise
hostname supported by the official CLI (forwarded as `login --host`); do not
supply a Microsoft tenant URL.

CAI gives this runtime its own `COPILOT_HOME` at `~/.cai/copilot-runtime`, including
its login selection and session state. Run **`cai copilot login --account USER`** even if you
have used the standalone CLI before. It deliberately does not inherit
`COPILOT_GITHUB_TOKEN`, `GH_TOKEN`, `GITHUB_TOKEN`, provider API keys, or BYOK
environment settings. Standard proxy, CA certificate, and desktop/keyring
variables are preserved. The official CLI manages credential storage (normally
the OS credential store, potentially plaintext configuration when no usable
credential store exists). Review that behavior with your administrator.

`models` obtains the catalog from the signed-in account through
`CopilotClient.list_models()`; it is not a hardcoded list. `models --select`
provides a numbered picker and saves only the model ID to
`~/.cai/copilot.json` using an atomic, owner-only file replacement.
`models --json` returns the SDK catalog for scripts. Entries explicitly disabled
by model policy are excluded. The SDK caches this catalog per connection; launch
`cai copilot models` again to obtain a new catalog after policy changes.

Model precedence is `chat --model ID`, then `CAI_COPILOT_MODEL`, then the saved
selection. If no selection exists, interactive chat offers the picker.
Non-interactive chat requires an explicit or saved selection. The selection is
revalidated against the current catalog on every launch. An unavailable model
or authentication failure stops execution; CAI does **not** fall back to
LM Studio, Alias, OpenAI, or another model. The effective GitHub identity must
match your explicitly pinned account and host.

## Run CAI tasks

```bash
# One prompt, with no tool access (use an exact ID from your model catalog)
cai copilot chat --model YOUR_MODEL_ID --no-tools \
  --prompt "Explain how to review a firewall change safely."

# Interactive defensive-security role
cai copilot chat --agent blueteam_agent

# Evidence and compliance role, ten-minute per-prompt deadline
cai copilot chat --agent compliance_agent --timeout 600
```

Available roles are `one_tool_agent` (default), `redteam_agent`,
`blueteam_agent`, `bug_bounter_agent`, `dfir_agent`, `compliance_agent`,
`network_traffic_analyzer`, and `reverse_engineering_agent`.
These reuse the corresponding CAI role templates and cyber baseline, **not**
their legacy model-configured singleton agents. They do not automatically copy
old conversations, compacted memory, CTR digests, or host inventories into the
cloud session.

The minimal role exposes CAI's existing `generic_linux_command`; other roles
also expose `fetch_url`. Their existing argument validation, sensitive-command
checks, output handling, and URL protections remain in place. Additional legacy
tools are intentionally not imported into the Copilot toolset, including tools
that call Perplexity, run nested CAI agents, or depend on legacy model state.

Each local tool call displays its exact JSON arguments and asks for approval.
Only `y` or `yes` approves; EOF, cancellation, and non-interactive input deny.
This additional approval applies even if the legacy `CAI_YOLO` setting is set.
There is no Copilot-mode YOLO flag. `--no-tools` disables all tools and is the
recommended starting point for reviewing data-handling policy.

Approvals are not a sandbox. Approved shell commands execute with the CAI
process's privileges and can access files or networks. Review their arguments,
work only on authorized targets, and use OS/network controls for enterprise
restrictions. Tool results and selected role instructions are sent to Copilot.
Do not approve reading credentials, uploading unrelated files, or invoking an
unapproved AI service through a shell command.

Interactive commands:

| Command | Effect |
| --- | --- |
| `/models` | Display the account catalog for this SDK connection |
| `/model ID` | Change this session's model while keeping its conversation |
| `/clear` | Start a fresh conversation with the current role and model |
| `/help` | Show the supported commands |
| `/exit` | Close the session and stop the SDK-managed CLI |

`/model` changes only the active session. Use `cai copilot models --select` to
change the saved default. Ctrl-C aborts the active request and exits. Timeouts
include time spent waiting for tool approval and abort the request before
shutdown; completed tool side effects cannot be undone by cancellation.

## Runtime boundaries

Copilot's built-in tools are not an alternative path around CAI approvals.
Only the explicitly registered CAI tools are made available. SDK permission
requests admit only those custom-tool callbacks, which still require human
approval; built-in, MCP, and managed-approval-required requests are rejected.
The SDK runs in `empty` mode with source-qualified custom-tool allowlists.
Ambient CLI customization is disabled for this execution
mode. Legacy CAI tracing and telemetry exporters are disabled before loading
agent/tool code; GitHub's own service diagnostics and storage remain subject to
Copilot's policies.

This mode does not automatically self-fetch SDK *managed permission settings*
from an enterprise. That SDK feature has a separate token/policy-injection
contract. Local per-call approval and rejection of requests that require managed
approval are not a substitute for your administrator's endpoint controls.

The following legacy features are **not available in this mode**: the TUI and
HTTP API, parallel/swarm orchestration, CAI handoffs, autonomous continuation,
legacy slash commands, CAI JSONL replay/resume, automatic memory/CTR context,
external MCP servers, and model-backed CAI input/output guardrails. Copilot
manages its own conversation and compaction; local command and URL safety
checks still run. Unsupported CLI flags are rejected instead of starting a
legacy provider. This explicit boundary prevents two agent loops from owning
the same conversation.

The SDK/CLI may store session data locally under their own state directory.
`/clear` starts a new conversation; it is not a secure deletion operation.
Apply your organization's endpoint storage and retention controls.

## Troubleshooting

- **SDK missing:** install `.[copilot]` using the same Python environment as
  `cai`; `cai copilot --help` works without installing the extra.
- **Wrong identity, missing account binding, or no authentication:** repeat
  `login --account YOUR_CORPORATE_GITHUB_USERNAME` (and `--hostname` when needed),
  complete the correct GitHub sign-in, and check `status`. A failed identity
  check does not overwrite a previous account binding.
- **Empty catalog, unavailable model, or access denied:** ask your administrator
  to check seat assignment, CLI access, SSO, and model policies; then rerun
  `models --select`. Being authenticated does not prove inference is permitted.
- **CLI startup/protocol error:** use the matching full CLI or an SDK-compatible,
  administrator-approved CLI via `CAI_COPILOT_CLI_PATH`.
- **Tool denied in a script:** this is intentional. Use `--no-tools` for
  unattended analysis, or run interactively to review and approve local actions.
- **Invalid preference file:** correct or remove `~/.cai/copilot.json`, then
  rerun `models --select`. Malformed preferences are reported, not ignored.

See the [pinned official SDK documentation](https://github.com/github/copilot-sdk/tree/v1.0.13/python)
and [Copilot CLI authentication documentation](https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/authenticate-copilot-cli)
for current product availability, authentication requirements, and policies.

## Development checks

Install `.[copilot,test]` and run `python -m pytest -q tests/test_copilot*.py`.
Tests use fake clients and real SDK types; they do not consume Copilot inference
allowances. An additional opt-in protocol check starts the installed full CLI in
a temporary home and verifies that no built-ins, MCP servers, or skills are
exposed, including after `/clear`. It also checks denial and approval of a
side-effect-free synthetic echo callback through the real protocol:

```bash
CAI_TEST_COPILOT_PROTOCOL=1 python -m pytest -q tests/test_copilot_protocol.py
```

That check does not send a prompt. Corporate OAuth, entitlement, and inference
must still be checked interactively with the intended account.
