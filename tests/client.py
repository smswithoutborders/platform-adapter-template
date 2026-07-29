# SPDX-License-Identifier: GPL-3.0-only
"""
Interactive test client for the adapter.

Run it with:

    python -m tests.client

Against the unmodified template stub, commands fail until you implement
`adapter.py`. Use this harness to exercise your implementation as you build
it out. The token is persisted to `tests/session.json`.
"""

import cmd
import json
from pathlib import Path
from typing import Any, Dict, Optional

SESSION_FILE = Path(__file__).parent / "session.json"


def _load_token() -> Optional[Dict[str, Any]]:
    try:
        with SESSION_FILE.open(encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def _save_token(token: Dict[str, Any]) -> None:
    with SESSION_FILE.open("w", encoding="utf-8") as f:
        json.dump(token, f, indent=2)


def _clear_token() -> None:
    SESSION_FILE.unlink(missing_ok=True)


class OAuth2AdapterClient(cmd.Cmd):
    intro = "Platform adapter test client. Type help or ? for a list of commands."
    prompt = "adapter> "

    def __init__(self, adapter):
        super().__init__()
        self.adapter = adapter
        self.token = _load_token()

    def _call(self, fn, *args, on_success=None, **kwargs):
        """Invoke an adapter method, pretty-print the result, and run an
        optional on_success(result) callback for side effects like updating
        the stored token. Adapter errors are caught and printed, not raised,
        so the REPL keeps running.
        """
        try:
            result = fn(*args, **kwargs)
        except Exception as e:
            print(f"Error: {e}")
            return
        print(json.dumps(result, indent=2))
        if on_success:
            on_success(result)

    def do_auth_url(self, line):
        """auth_url - Generate the OAuth2 authorization URL."""
        self._call(self.adapter.get_authorization_url)

    def do_exchange(self, line):
        """exchange <code> - Exchange an authorization code for a token and user info."""
        code = line.strip()
        if not code:
            print("Usage: exchange <code>")
            return

        def store_token(result):
            if "token" in result:
                self.token = result["token"]
                _save_token(self.token)

        self._call(
            self.adapter.exchange_code_and_fetch_user_info, code, on_success=store_token
        )

    def do_send_message(self, line):
        """send_message <message> - Send a message using the stored token."""
        message = line.strip()
        if not message:
            print("Usage: send_message <message>")
            return
        if self.token is None:
            print("No token stored. Run 'exchange <code>' first.")
            return

        def update_token(result):
            if result.get("refreshed_token"):
                self.token = result["refreshed_token"]
                _save_token(self.token)

        self._call(
            self.adapter.send_message,
            token=self.token,
            message=message,
            on_success=update_token,
        )

    def do_revoke(self, line):
        """revoke - Revoke the stored token."""
        if self.token is None:
            print("No token stored. Run 'exchange <code>' first.")
            return

        def clear_token(result):
            if result:
                self.token = None
                _clear_token()

        self._call(self.adapter.revoke_token, token=self.token, on_success=clear_token)

    def do_quit(self, _):
        """Exit the client."""
        return True

    do_EOF = do_quit


if __name__ == "__main__":
    from adapter import GmailOAuth2Adapter

    OAuth2AdapterClient(GmailOAuth2Adapter()).cmdloop()
