from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_headers

from mcp_server_email.config import Settings

from uuid import UUID

from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_headers


def user_mailbox_id() -> UUID:
    headers = get_http_headers()
    mailbox_id_value = headers.get("vyzno-mailbox-id", "").strip()

    if not mailbox_id_value:
        raise ToolError("Missing Vyzno mailbox ID.")

    try:
        mailbox_id = UUID(mailbox_id_value)
    except ValueError as error:
        raise ToolError(
            "The mailbox ID or idempotency key is not a valid UUID."
        ) from error

    if mailbox_id.version != 4:
        raise ToolError("The mailbox ID must be a UUID v4.")

    return mailbox_id


def vyzno_auth_headers(settings: Settings) -> dict[str, str]:
    headers = get_http_headers()

    cookie = headers.get("vyzno-cookie", "").strip()
    csrf_token = headers.get("vyzno-csrf-token", "").strip()
    

    if not cookie or not csrf_token:
        raise ToolError(
            "Missing Vyzno credentials. "
        )

    # try:
    #     idempotency_key = UUID(idempotency_key)
    # except ValueError as error:
    #     raise ToolError(
    #         "The mailbox ID or idempotency key is not a valid UUID."
    #     ) from error

    # if idempotency_key.version != 4:
    #     raise ToolError("The idempotency key must be a UUID v4.")


    return {
        "Cookie": cookie,
        "X-CSRF-Token": csrf_token,
        # "Idempotency-Key": str(idempotency_key),
        "Origin": settings.vyzno_origin,
    }