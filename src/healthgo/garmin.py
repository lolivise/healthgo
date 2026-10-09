"""Garmin Connect session with a hard cap of one credential login per 24 hours.

Fresh logins are what get an account rate-limited (HTTP 429, sometimes blocked by
client fingerprint for a day or more). Daily runs therefore use the saved token,
which refreshes itself; a credential login happens only when the token is gone,
and never more than once a day unless forced by hand.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectTooManyRequestsError,
)

from . import config, store, vault

log = logging.getLogger(__name__)
LOGIN_COOLDOWN = timedelta(hours=24)


class LoginBlocked(RuntimeError):
    """A credential login is needed but the 24h cooldown has not passed."""


def connect(state: dict, *, force_login: bool = False) -> Garmin:
    config.TOKENSTORE.mkdir(mode=0o700, exist_ok=True)
    tokenstore = str(config.TOKENSTORE)

    if not force_login:
        try:
            client = Garmin()
            client.login(tokenstore)
            return client
        except GarminConnectAuthenticationError as e:
            log.warning("saved Garmin token unusable: %s", e)

    last = state.get("last_login_attempt_at")
    if not force_login and last:
        since = config.now() - datetime.fromisoformat(last)
        if since < LOGIN_COOLDOWN:
            raise LoginBlocked(
                f"credential login already attempted {since} ago; next allowed after "
                f"{datetime.fromisoformat(last) + LOGIN_COOLDOWN:%Y-%m-%d %H:%M}"
            )

    # Record the attempt before making it, so a crash mid-login still counts.
    state["last_login_attempt_at"] = config.now().isoformat(timespec="seconds")
    store.save_state(state)
    log.info("logging in to Garmin with credentials from 1Password")
    client = Garmin(email=vault.read("GARMIN/USERNAME"), password=vault.read("GARMIN/PASSWORD"))
    try:
        client.login(tokenstore)
    except Exception as e:
        state["last_login_result"] = type(e).__name__
        store.save_state(state)
        raise
    state["last_login_result"] = "ok"
    store.save_state(state)
    return client


__all__ = [
    "connect",
    "LoginBlocked",
    "GarminConnectAuthenticationError",
    "GarminConnectTooManyRequestsError",
]
