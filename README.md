# Platform Adapter Template

## Overview

This template provides a standardized foundation for developing platform-specific adapters.

---

## Getting Started

Fetch the template into a new directory:

```bash
curl -fsSL https://raw.githubusercontent.com/smswithoutborders/platform-adapter-template/main/create-adapter.sh | bash -s -- my-new-adapter
```

Already have a repo cloned or initialized? Run it from inside that directory to just pull in the template's files:

```bash
curl -fsSL https://raw.githubusercontent.com/smswithoutborders/platform-adapter-template/main/create-adapter.sh | bash
```

Existing files are skipped, not overwritten, add `--force` to overwrite them. If `git` is available, the directory isn't already a repo, and you're running interactively, the script offers to `git init` and set a remote for you; otherwise it prints the manual steps. Requires `curl` and `tar`; `git` is optional.

---

## Requirements

- Python >= 3.10, [download here](https://www.python.org/downloads/)
- Familiarity with [Python virtual environments](https://docs.python.org/3/tutorial/venv.html)

## Dependencies

### On Ubuntu

```bash
sudo apt install build-essential python3-dev
```

## Installation

1. Create a virtual environment:

   ```bash
   python3 -m venv venv
   ```

2. Activate the virtual environment:

   ```bash
   source venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

---

## Directory Structure

The template includes the following files:

| File                     | Description                                                                                                                              |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `adapter.py`             | Core implementation of the platform-specific adapter. Developers subclass a protocol interface and define required methods here.         |
| `protocol_interfaces.py` | Abstract base classes that define the protocol contracts (e.g., `OAuth2ProtocolInterface`). Adapters must implement these.               |
| `config.py`              | Defines the `Credentials` dataclass and `load_credentials()`, which read and validate `credentials.json` per the path in `config.ini`.   |
| `httpclient.py`          | Small reusable `requests.Session` wrapper (`HTTPClient`/`HTTPError`) for building provider-specific API clients.                          |
| `utils.py`               | Small helpers shared across adapter method implementations, e.g. `require()` for validating required keyword arguments.                  |
| `ipc_service.py`         | Manages IPC between the host program and the adapter. It routes incoming requests to the appropriate adapter method and returns results. |
| `main.py`                | Adapter entry point. It initializes the adapter and starts the IPC listener.                                                             |
| `manifest.ini`           | Describes the adapter with metadata such as its display name, platform ID, category, and icons.                                          |
| `config.ini`             | Contains adapter configuration, including paths to credential files.                                                                     |
| `credentials.json`       | Stores authentication credentials (e.g., client ID/secret for OAuth2), referenced by `config.ini`.                                       |
| `requirements.txt`       | Lists Python dependencies required to run the adapter.                                                                                   |
| `tests/client.py`        | Interactive REPL for manually exercising the adapter's interface methods while you build it out.                                         |
| `create-adapter.sh`      | Fetches this template into a working directory, see [Getting Started](#getting-started).                                                 |

---

## Quick Start

### Step 1: Implement the Adapter

> [!WARNING]
>
> Avoid modifying `protocol_interfaces.py` or `ipc_service.py` unless necessary. Changes may cause incompatibilities with the host system.

1. Open `adapter.py`.
2. Identify and subclass the correct protocol interface from `protocol_interfaces.py`.
   Example: For OAuth2-based platforms, use `OAuth2ProtocolInterface`.
3. Implement all required abstract methods:

```python
class GmailOAuth2Adapter(OAuth2ProtocolInterface):
    def get_authorization_url(self, **kwargs) -> Dict[str, Any]:
        # Return the authorization URL and PKCE/state metadata.

    def exchange_code_and_fetch_user_info(self, code: str, **kwargs) -> Dict[str, Dict[str, Any]]:
        # Exchange the auth code for a token and fetch the user's account info.

    def revoke_token(self, token: Dict[str, str], **kwargs) -> bool:
        # Invalidate the access token.

    def send_message(self, token: Dict[str, str], **kwargs) -> Dict[str, Any]:
        # Send a message using the platform's API (message arrives via kwargs).
```

> [!NOTE]
>
> For phone-number-based auth platforms (no OAuth2), subclass `PNBAProtocolInterface` instead. See its abstract methods in `protocol_interfaces.py`.

### Step 2: Configure Adapter Metadata

Edit the following configuration files:

#### `manifest.ini`

Defines core metadata about the adapter.

```ini
[platform]
display_name = Gmail
name = gmail
proto_id = 0
cat_id = 0
supports_offline_first = false
icon_svg = https://raw.githubusercontent.com/smswithoutborders/gmail-oauth2-adapter/main/icons/gmail.svg
icon_png = https://raw.githubusercontent.com/smswithoutborders/gmail-oauth2-adapter/main/icons/gmail.png
```

> [!NOTE]
>
> `proto_id` and `cat_id` are set by you, based on your adapter's protocol and category:
>
> - `proto_id`: `0` = OAuth2, `1` = PNBA
> - `cat_id`: `0` = Email, `1` = Message, `2` = Text, `3` = Bridge
>
> Some adapters also add an `auth_provider` key under `[platform]` to name an external OTP/auth provider they delegate to (e.g. `auth_provider = shortmesh-authy`), only add it if it applies to your platform.

#### `config.ini`

Points to authentication credentials.

```ini
[credentials]
path = ./credentials.json
```

---

## Configuration

`config.py` defines a `Credentials` dataclass and a `load_credentials()` loader. `load_credentials()` resolves `config.ini`'s `[credentials].path`, then parses and validates the JSON file it points to, returning a typed `Credentials` instance:

```python
self.credentials: Credentials = load_credentials(self.config)
```

`Credentials` mixes required fields (no default) with optional fields (sensible defaults), plus lowercase computed helpers like `redirect_uri` (first of `REDIRECT_URIS`) and `scopes` (`SCOPE` split into a list).

Sample `credentials.json`:

```json
{
  "client_id": "your-oauth2-client-id",
  "client_secret": "your-oauth2-client-secret",
  "redirect_uris": ["https://app.example.com/oauth/callback"],
  "scope": "email profile"
}
```

| Field           | Required | Default | Description                                                                                    |
| --------------- | -------- | ------- | ------------------------------------------------------------------------------------------------ |
| `client_id`     | Yes      | -       | OAuth2 client ID issued by the provider.                                                        |
| `redirect_uris` | Yes      | -       | Non-empty list of allowed OAuth2 redirect URIs; the first is used as the default `redirect_uri`. |
| `client_secret` | No       | `null`  | OAuth2 client secret, if the provider requires one (some public clients don't).                  |
| `scope`         | No       | `""`    | Space-separated OAuth2 scopes requested during authorization (split into `scopes`).              |

> [!NOTE]
>
> Customize `Credentials`' fields to match your platform's `credentials.json`. For full working examples, see the [existing adapters](https://github.com/smswithoutborders?q=-adapters&type=public&language=&sort=).

## HTTP Client

`httpclient.py` provides a small, reusable transport to build provider-specific API clients on top of:

- `HTTPClient(base_url, headers=None, timeout=30)`, wraps a `requests.Session`, with `.get(path)`, `.post(path, payload)`, and `.delete(path)` verb methods.
- `HTTPError`, raised uniformly for HTTP-status errors and network-level failures (timeouts, connection errors), with the message extracted from the response body where possible.

```python
from httpclient import HTTPClient

api = HTTPClient(base_url="https://api.example.com", headers={"Authorization": f"Bearer {token}"})
data = api.get("/v1/me")
```

---

## Running & Testing the Adapter

### Quick manual smoke test

You can test the adapter using standard IPC messages sent through stdin:

```bash
echo '{"method": "get_authorization_url", "params": {}}' | python3 main.py
```

> [!NOTE]
>
> Replace `get_authorization_url` with other supported methods (`exchange_code_and_fetch_user_info`, `revoke_token`, `send_message`), and update `params` accordingly.

### Interactive Test Client

For exercising a multi-step flow without hand-crafting IPC JSON each time, use the interactive REPL in `tests/client.py`. The token is persisted to `tests/session.json`:

```bash
python -m tests.client
```

> [!NOTE]
>
> This REPL's commands match `OAuth2ProtocolInterface`'s methods, mirroring the `GmailOAuth2Adapter` sample. If you're building a `PNBAProtocolInterface` adapter instead, adapt the commands to your own methods (`send_authorization_code`, `validate_code_and_fetch_user_info`, etc.). See a PNBA adapter's `tests/client.py` among the [existing adapters](https://github.com/smswithoutborders?q=-adapters&type=public&language=&sort=) for a worked example.

| Command        | Arguments   | Description                                       |
| -------------- | ----------- | -------------------------------------------------- |
| `auth_url`     | -           | Generate the OAuth2 authorization URL              |
| `exchange`     | `<code>`    | Exchange an authorization code for a token + info  |
| `send_message` | `<message>` | Send a message using the stored token              |
| `revoke`       | -           | Revoke the stored token                            |
| `help`         | `[command]` | Show available commands, or detail for one command |
| `quit`         | -           | Exit the client                                    |

Example session against the unmodified template stub, commands fail until you implement `adapter.py`, either with a validation error from a missing parameter, or `NotImplementedError` once validation passes:

```
Platform adapter test client. Type help or ? for a list of commands.
adapter> auth_url
Error: Missing required parameter(s): redirect_uri
adapter> exchange some-code
Error: TODO: implement exchange_code_and_fetch_user_info
adapter> quit
```

---

## Keeping Interfaces Up to Date

If you suspect that `protocol_interfaces.py` is outdated or inconsistent with the host platform, sync it using:

```bash
curl -fsSL -o protocol_interfaces.py https://raw.githubusercontent.com/smswithoutborders/RelaySMS-Publisher/main/platforms/protocol_interfaces.py
```
