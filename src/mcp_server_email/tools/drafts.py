from typing import Any

import httpx
from fastmcp.exceptions import ToolError
from fastmcp.tools import tool
from pydantic import UUID4

from mcp_server_email.auth import build_vyzno_auth_headers
from mcp_server_email.clients.vyzno import VyznoClient
from mcp_server_email.config import Settings
from mcp_server_email.schemas.drafts import CreateDraftInput


@tool()
async def create_draft(
    mailbox_id: UUID4,
    draft: CreateDraftInput,
    idempotency_key: UUID4,
) -> dict[str, Any]:
    """Create an unsent email draft in an authorized mailbox.

    Reuse the same key and draft data when retrying an operation.
    """
    settings = Settings()

    try:
        async with httpx.AsyncClient(
            base_url=str(settings.vyzno_base_url),
            headers=build_vyzno_auth_headers(settings),
            timeout=30.0,
            follow_redirects=False,
        ) as http_client:
            vyzno = VyznoClient(http_client)

            return await vyzno.create_draft(
                mailbox_id=mailbox_id,
                draft=draft,
                idempotency_key=idempotency_key,
            )

    except httpx.HTTPStatusError as error:
        raise ToolError(
            f"Vyzno returned HTTP {error.response.status_code}."
        ) from None

    except httpx.RequestError:
        raise ToolError(
            "The Vyzno request could not complete. "
            "The draft outcome is unconfirmed. "
            "Retry with the same idempotency key and draft data."
        ) from None


@tool()
async def send_draft(
    mailbox_id: UUID4,
    draft_id: UUID4,
    idempotency_key: UUID4,
) -> dict[str, Any]:
    """Send an existing draft to its saved recipients.

    Use the same draft ID and send-operation key for retries.
    After an uncertain outcome, check the message status first.
    """
    settings = Settings()

    try:
        async with httpx.AsyncClient(
            base_url=str(settings.vyzno_base_url),
            headers=build_vyzno_auth_headers(settings),
            timeout=90.0,
            follow_redirects=False,
        ) as http_client:
            vyzno = VyznoClient(http_client)

            return await vyzno.send_draft(
                mailbox_id=mailbox_id,
                draft_id=draft_id,
                idempotency_key=idempotency_key,
            )

    except httpx.HTTPStatusError as error:
        status = error.response.status_code

        if status >= 500:
            raise ToolError(
                f"Vyzno returned HTTP {status}. "
                "The send outcome is unconfirmed. "
                "Check the message status before retrying."
            ) from None

        raise ToolError(
            f"Vyzno rejected the send request: HTTP {status}."
        ) from None

    except httpx.RequestError:
        raise ToolError(
            "The Vyzno request could not complete. "
            "The email may already have been sent. "
            "Check its status before retrying, and reuse "
            "the same draft ID and send-operation key."
        ) from None