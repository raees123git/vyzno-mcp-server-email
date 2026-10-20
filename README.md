````markdown
# Vyzno Mail MCP Server

A Python MCP server that exposes Vyzno email operations as tools.

Currently, it supports:

- Creating an email draft.
- Sending an existing draft.

The server uses FastMCP for MCP communication, Pydantic for input validation, and HTTPX to call the Vyzno backend.

## How it works

```text
MCP client
    |
    | Calls an MCP tool over HTTP
    v
MCP server
    |
    | Validates the tool inputs
    v
Vyzno HTTP client
    |
    | Calls the authenticated Vyzno API
    v
Vyzno backend
    |
    | Calls the internal mail service
    v
Texinity Mail
```

Sending an email requires two separate tool calls:

```text
1. Call create_draft with the recipients and message.
2. Read the draft ID from the response.
3. Call send_draft with that draft ID.
```

Creating a draft does not automatically send it. The caller must perform the second step.

A future LangGraph application will coordinate this sequence. LangGraph integration is not implemented in this repository yet.

## Requirements

- Python 3.11 or newer.
- uv.
- Access to the Vyzno API.
- A Vyzno mailbox that the authenticated user can send from.
- Valid Vyzno session cookies and a matching CSRF token for local testing.

## Project structure

```text
mcp-server-email/
├── pyproject.toml
├── uv.lock
├── README.md
├── .gitignore
├── .env                         # Local configuration; excluded from Git
├── server-check.py
├── mcp-draft-check.py
├── mcp-send-check.py
└── src/
    └── mcp_server_email/
        ├── server.py
        ├── config.py
        ├── auth.py
        ├── clients/
        │   └── vyzno.py
        ├── schemas/
        │   └── drafts.py
        └── tools/
            └── drafts.py
```

Package directories also contain `__init__.py` files.

### Responsibilities

| File | Purpose |
| --- | --- |
| `server.py` | Creates the MCP server, registers tools, and starts the HTTP transport. |
| `config.py` | Defines configuration fields and reads environment variables. |
| `auth.py` | Builds the authentication headers used for Vyzno requests. |
| `clients/vyzno.py` | Makes HTTP requests to the Vyzno API. |
| `schemas/drafts.py` | Defines and validates draft input fields. |
| `tools/drafts.py` | Exposes MCP tools and translates HTTP failures into tool errors. |
| `server-check.py` | Connects to the MCP server and lists its tools. |
| `mcp-draft-check.py` | Creates a real draft through MCP. |
| `mcp-send-check.py` | Sends a real saved draft through MCP. |

The scripts at the repository root are development clients. The HTTP client inside `clients/vyzno.py` connects the MCP server to Vyzno and remains part of the application.

## Installation

Run the following from the repository root:

```powershell
uv sync
```

## Configuration

Create a `.env` file in the repository root:

```dotenv
MCP_HOST=127.0.0.1
MCP_PORT=8000

VYZNO_BASE_URL=https://api.vyzno.io
VYZNO_ORIGIN=https://vyzno.io

VYZNO_COOKIE_HEADER="PASTE_YOUR_AUTHENTICATED_COOKIE_HEADER"
VYZNO_CSRF_TOKEN="PASTE_YOUR_MATCHING_CSRF_TOKEN"
```

Use the full `Cookie` request-header value and the matching
`X-CSRF-Token` value from an authenticated Vyzno API request.

Keep credentials in `.env`; do not commit them or place them in source code.

This is a temporary authentication setup for local testing. The server currently uses one configured Vyzno session, rather than receiving a separate authenticated user context for each MCP caller.

## Start the server

From the repository root:

```powershell
uv run python -m mcp_server_email.server
```

The default MCP endpoint is:

```text
http://127.0.0.1:8000/mcp
```

Keep this terminal running and use another terminal for the check scripts.

This endpoint uses the MCP protocol. It is not a website or Swagger documentation page, so opening it directly in a browser is not a reliable connection test.

Restart the server after changing the Python code or configuration.

## Available tools

### create_draft

Creates an unsent draft.

Inputs:

| Field | Description |
| --- | --- |
| `mailbox_id` | UUID v4 identifying the existing sender mailbox. |
| `draft` | Recipients, subject, and message content. |
| `idempotency_key` | UUID v4 identifying this draft-creation operation. |

Example tool arguments:

```json
{
  "mailbox_id": "YOUR_MAILBOX_UUID",
  "draft": {
    "type": "new",
    "to": ["recipient@example.com"],
    "subject": "Meeting update",
    "bodyText": "Our meeting starts at 10 AM.",
    "bodyHtml": "<p>Our meeting starts at 10 AM.</p>"
  },
  "idempotency_key": "YOUR_CREATE_OPERATION_UUID"
}
```

Vyzno endpoint:

```text
POST /v1/mailboxes/{mailbox_id}/drafts
```

The response includes the saved draft ID, which is needed by `send_draft`.

### send_draft

Sends an existing draft using its saved recipients and content.

Inputs:

| Field | Description |
| --- | --- |
| `mailbox_id` | UUID v4 identifying the sender mailbox. |
| `draft_id` | UUID v4 returned when the draft was created. |
| `idempotency_key` | UUID v4 identifying this send operation. |

Vyzno endpoint:

```text
POST /v1/mailboxes/{mailbox_id}/drafts/{draft_id}/send
```

The MCP server does not implement the frontend's undo timer. Calling this tool requests sending immediately.

## Message body formats

Supply both versions of the same message:

- `bodyText`: plain text.
- `bodyHtml`: HTML.

The current backend sends the HTML body, and the web composer uses the HTML body when reopening a draft. Supplying both supports these paths.

The current Python client forwards these fields; it does not automatically generate HTML from plain text.

## Check the connection

With the server running, open a second terminal:

```powershell
uv run python server-check.py
```

Expected tool list:

```text
Available tools: ['create_draft', 'send_draft']
```

## Create a test draft

The draft-check script contains a hardcoded subject and message bodies.
Review them before running it, and keep the plain-text and HTML content consistent.

In PowerShell:

```powershell
$mailboxId = "YOUR_EXISTING_MAILBOX_UUID"
$recipient = "YOUR_TEST_RECIPIENT"
$createKey = [guid]::NewGuid().ToString()

uv run python mcp-draft-check.py $mailboxId $recipient --idempotency-key $createKey
```

This creates a real draft. Copy the draft ID printed by the script.

## Send the test draft

This command sends the saved email to its recipients.

```powershell
$draftId = "DRAFT_UUID_FROM_THE_CREATE_RESPONSE"
$sendKey = [guid]::NewGuid().ToString()

uv run python mcp-send-check.py $mailboxId $draftId --idempotency-key $sendKey
```

A successful response reports:

```text
Status: sent
Backend reports the email was sent.
```

This reports the backend's send result; it does not confirm delivery to the recipient's inbox.

## Idempotency keys

An idempotency key identifies one operation so the backend can recognize repeated requests.

Use:

- One key for creating the draft.
- A separate key for sending the draft.
- The same key and request data when retrying the same operation.
- A new key for a new intentional operation.

The check scripts receive their keys through command-line arguments. In the examples above, PowerShell generates them.

The MCP server forwards each key using the `Idempotency-Key` HTTP header. The Vyzno backend manages the idempotency records.

A key does not explain user intent by itself. The calling application must decide whether it is starting a new operation or retrying an existing one.

After a timeout or uncertain send result, check the message status in Vyzno before retrying. Keep the original draft ID and send key.

## Troubleshooting

| Result | What to check |
| --- | --- |
| HTTP 401 | The configured session may have expired. Obtain fresh authenticated cookies and restart the server. |
| HTTP 403 | Check the matching CSRF token, configured origin, and mailbox permissions. |
| HTTP 409 | Check for an operation already in progress or reuse of a key with different request data. |
| HTTP 502 | Check Vyzno and its upstream services. It does not necessarily indicate expired credentials. |
| Input validation error | Check field names, UUID versions, email addresses, and the running server's schema. |
| Connection refused | Check that the MCP server is running at the address used by the check scripts. |

## Current scope

Implemented:

- HTTP MCP server.
- Draft creation.
- Sending saved drafts.
- Input validation.
- Forwarding idempotency keys.
- Local development clients.

Not yet implemented:

- LangGraph orchestration.
- Natural-language intent handling.
- Per-user authentication for MCP callers.
- Persistent workflow state and operation keys.
- A tool for checking message status.
````
