"""Commit and push. Standing permission for this repo: straight to main, never force."""

from __future__ import annotations

import logging
import subprocess

from . import config

log = logging.getLogger(__name__)


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=config.ROOT, capture_output=True, text=True, timeout=120)


def commit_and_push(message: str, paths: tuple[str, ...] = ("data",)) -> str:
    _git("add", "--", *paths)
    staged = _git("diff", "--cached", "--quiet", "--", *paths).returncode != 0
    if staged:
        # `commit -- paths` commits only these paths, leaving any other work alone
        res = _git("commit", "-m", message, "--", *paths)
        if res.returncode != 0:
            log.error("git commit failed: %s", res.stderr.strip())
            return "commit-failed"
    # Push even with nothing new: an earlier offline run may have left commits behind.
    push = _git("push", "origin", "HEAD:main")
    if push.returncode != 0:
        log.warning("git push failed (will retry next run): %s", push.stderr.strip())
        return "committed-not-pushed" if staged else "push-failed"
    return "pushed" if staged else "nothing-to-commit"
