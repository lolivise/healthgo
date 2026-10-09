"""Secrets from 1Password (vault HealthGo, item `secrets`) via a service account.

The service-account token is exported as HEALTHGO_OP_SERVICE_ACCOUNT_TOKEN in ~/.zshrc.
launchd jobs never source ~/.zshrc, so when the variable is absent we read that one
line out of the file. The token stays in a single place and rotating it there is enough.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

TOKEN_VAR = "HEALTHGO_OP_SERVICE_ACCOUNT_TOKEN"
ITEM_REF = "op://HealthGo/secrets"
_EXPORT = re.compile(rf"""^\s*export\s+{TOKEN_VAR}=(["']?)([^"'\s]+)\1\s*$""", re.M)


class VaultError(RuntimeError):
    pass


def _service_token() -> str:
    token = os.environ.get(TOKEN_VAR)
    if token:
        return token
    zshrc = Path.home() / ".zshrc"
    match = _EXPORT.search(zshrc.read_text()) if zshrc.exists() else None
    if not match:
        raise VaultError(f"{TOKEN_VAR} not set and not found in ~/.zshrc")
    return match.group(2)


def _op() -> str:
    found = shutil.which("op") or next(
        (p for p in ("/opt/homebrew/bin/op", "/usr/local/bin/op") if Path(p).exists()), None
    )
    if not found:
        raise VaultError("1Password CLI `op` not found")
    return found


@lru_cache
def read(field: str) -> str:
    """field is `SECTION/FIELD`, e.g. `GARMIN/USERNAME`."""
    env = {**os.environ, "OP_SERVICE_ACCOUNT_TOKEN": _service_token()}
    result = subprocess.run(
        [_op(), "read", "--no-newline", f"{ITEM_REF}/{field}"],
        env=env, capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        # stderr from `op` never contains the secret value itself
        raise VaultError(f"op read {field} failed: {result.stderr.strip()}")
    return result.stdout
