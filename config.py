# SPDX-License-Identifier: GPL-3.0-only
"""
Loads and validates credentials.json into a typed Credentials instance.

`Credentials` here is a generic OAuth2 shape, matching the sample
`credentials.json` in the README. Customize its fields to match your own
platform, see the existing adapters for real-world examples:
https://github.com/smswithoutborders?q=-adapters&type=public&language=&sort=
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from logutils import get_logger

logger = get_logger(__name__)

DEFAULT_SCOPE = ""


@dataclass
class Credentials:
    """Typed view over the adapter's `credentials.json`."""

    CLIENT_ID: str
    REDIRECT_URIS: List[str]
    CLIENT_SECRET: Optional[str] = None
    SCOPE: str = DEFAULT_SCOPE

    @property
    def redirect_uri(self) -> str:
        return self.REDIRECT_URIS[0]

    @property
    def scopes(self) -> List[str]:
        return self.SCOPE.split()


_REQUIRED_FIELDS = {"client_id", "redirect_uris"}


def _resolve_creds_path(configs: Dict[str, Any]) -> Path:
    creds_config = configs.get("credentials", {})
    raw_path = creds_config.get("path", "")
    if not raw_path:
        raise ValueError("Missing 'credentials.path' in configuration.")

    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = Path(__file__).parent / path
    return path


def _validate_creds(creds: Dict[str, Any]) -> None:
    missing = _REQUIRED_FIELDS - creds.keys()
    if missing:
        raise ValueError(
            f"Missing required credential fields: {', '.join(sorted(missing))}"
        )

    if not isinstance(creds["client_id"], str) or not creds["client_id"].strip():
        raise ValueError("'client_id' must be a non-empty string.")

    redirect_uris = creds["redirect_uris"]
    if (
        not isinstance(redirect_uris, list)
        or not redirect_uris
        or not all(isinstance(uri, str) and uri.strip() for uri in redirect_uris)
    ):
        raise ValueError("'redirect_uris' must be a non-empty list of strings.")

    client_secret = creds.get("client_secret")
    if client_secret is not None and (
        not isinstance(client_secret, str) or not client_secret.strip()
    ):
        raise ValueError("'client_secret' must be a non-empty string when provided.")

    if "scope" in creds and not isinstance(creds["scope"], str):
        raise ValueError("'scope' must be a string when provided.")


def load_credentials(configs: Dict[str, Any]) -> Credentials:
    """Load, validate, and return a Credentials instance from the specified path."""
    path = _resolve_creds_path(configs)
    logger.debug("Loading credentials from %s", path)

    try:
        with path.open(encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Credentials file not found: {path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Credentials file is not valid JSON: {e}")

    _validate_creds(raw)

    return Credentials(
        CLIENT_ID=raw["client_id"],
        REDIRECT_URIS=raw["redirect_uris"],
        CLIENT_SECRET=raw.get("client_secret"),
        SCOPE=raw.get("scope", DEFAULT_SCOPE),
    )
