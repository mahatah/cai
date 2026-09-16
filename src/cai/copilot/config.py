"""Non-secret Copilot preferences, independent of CAI's local-model settings."""

import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from cai.copilot import CopilotError


def preferences_path() -> Path:
    return Path.home() / ".cai" / "copilot.json"


@dataclass(frozen=True)
class CopilotAccount:
    login: str
    host: str


def normalize_host(host: str) -> str:
    parsed = urlsplit(host if "://" in host else f"https://{host}")
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise CopilotError("Expected a GitHub HTTPS hostname, not a tenant URL or path.")
    return parsed.hostname.casefold()


def _account(login: str, host: str) -> CopilotAccount:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}", login):
        raise CopilotError(
            "Expected a GitHub username (including any managed-user suffix), not email."
        )
    return CopilotAccount(login=login, host=normalize_host(host))


def load_account() -> CopilotAccount | None:
    path = preferences_path().with_name("copilot-account.json")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as exc:
        raise CopilotError(f"Cannot read Copilot account binding at {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise CopilotError(f"Invalid Copilot account binding at {path}.")
    login, host = data.get("login"), data.get("host")
    if not isinstance(login, str) or not isinstance(host, str):
        raise CopilotError(f"Invalid Copilot account binding at {path}.")
    return _account(login, host)


def save_account(account: CopilotAccount) -> None:
    validated = _account(account.login, account.host)
    _save_json(
        preferences_path().with_name("copilot-account.json"),
        {"login": validated.login, "host": validated.host},
    )


def load_model() -> str | None:
    path = preferences_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as exc:
        raise CopilotError(f"Cannot read Copilot preferences at {path}: {exc}") from exc
    model = data.get("model") if isinstance(data, dict) else None
    if not isinstance(model, str) or not model.strip():
        raise CopilotError(f"Invalid Copilot preferences at {path}: expected a nonempty 'model'.")
    return model


def save_model(model: str) -> None:
    if not model.strip():
        raise CopilotError("Cannot save an empty Copilot model ID.")
    _save_json(preferences_path(), {"model": model})


def _save_json(path: Path, data: dict[str, str]) -> None:
    temporary: str | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=".copilot-", delete=False
        ) as stream:
            temporary = stream.name
            json.dump(data, stream)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        raise CopilotError(f"Cannot save Copilot preferences at {path}: {exc}") from exc
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)
