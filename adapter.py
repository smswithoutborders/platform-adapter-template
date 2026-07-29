# SPDX-License-Identifier: GPL-3.0-only
"""
Template for platform-specific protocol adapters.

To implement a new adapter:
1. Subclass the matching interface from `protocol_interfaces.py`, e.g.
   `OAuth2ProtocolInterface`, named `<Platform><Protocol>Adapter`.
2. Implement all its abstract methods.
3. Load credentials with `load_credentials()` from `config.py`.
4. Validate required kwargs with `require()` from `utils.py`.

The interface also exposes `.manifest` and `.config`, parsed from
`manifest.ini` and `config.ini`. See the sample `GmailOAuth2Adapter` below.
"""

from typing import Any, Dict

from config import Credentials, load_credentials
from logutils import get_logger
from protocol_interfaces import OAuth2ProtocolInterface
from utils import require

logger = get_logger(__name__)


class GmailOAuth2Adapter(OAuth2ProtocolInterface):
    """Sample OAuth2 adapter. Use as a reference for your own platform."""

    def __init__(self):
        self.credentials: Credentials = load_credentials(self.config)
        # TODO: construct any provider-specific API client(s) here, e.g.:
        # self.api = HTTPClient(base_url="https://oauth2.googleapis.com")

    def get_authorization_url(self, **kwargs) -> Dict[str, Any]:
        (redirect_uri,) = require(kwargs, "redirect_uri")
        # TODO: build and return the provider's authorization URL using
        # self.credentials.CLIENT_ID, self.credentials.scopes, redirect_uri, etc.
        raise NotImplementedError("TODO: implement get_authorization_url")

    def exchange_code_and_fetch_user_info(
        self, code: str, **kwargs
    ) -> Dict[str, Dict[str, Any]]:
        # TODO: exchange `code` for a token (e.g. via self.api), then fetch user
        # info. Return {"token": {...}, "userinfo": {"account_identifier": ...}}.
        raise NotImplementedError("TODO: implement exchange_code_and_fetch_user_info")

    def revoke_token(self, token: Dict[str, str], **kwargs) -> bool:
        # TODO: call the provider's token-revocation endpoint.
        raise NotImplementedError("TODO: implement revoke_token")

    def send_message(self, token: Dict[str, str], **kwargs) -> Dict[str, Any]:
        (message,) = require(kwargs, "message")
        # TODO: refresh `token` if expired, then send `message` via the
        # provider API. Return {"success": ..., "refreshed_token": token}.
        raise NotImplementedError("TODO: implement send_message")
