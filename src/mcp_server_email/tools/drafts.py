from typing import Any
import httpx
from html import escape
from uuid import uuid4, UUID
from fastmcp.exceptions import ToolError
from fastmcp.tools import tool
from mcp_server_email.auth import vyzno_auth_headers, user_mailbox_id
from mcp_server_email.config import Settings
from mcp_server_email.schemas.drafts import CreateDraftInput


@tool()
async def create_draft( draft: CreateDraftInput ) -> dict[str, Any]:
    """
    Create and save an email draft in the user's Vyzno mailbox.

    Requirements:
    - The user must provide a subject or message body, or both.
    - If only the body is provided, generate a concise, relevant
      subject based on the message content.
    - If the subject is provided, preserve the user's intended subject.
    - If the user provides a recipient email address, include it. Otherwise, leave the recipient list empty.
    - Do not invent recipient email addresses or missing message content.
    - If neither a subject nor message content is provided, ask the user for more information before calling this tool. Subject or message content (any of them) is required to create a draft.
    """

    settings = Settings()
    mailbox_id = user_mailbox_id()
    idempotency_key = str(uuid4())
    payload = draft.model_dump(mode="json", by_alias=True)

    if draft.body_text is not None:
        html_body = escape(draft.body_text)
        html_body = html_body.replace("\n", "<br>")
        payload["bodyHtml"] = f"<p>{html_body}</p>"
    else:
        payload["bodyHtml"] = None

    try:
        print(f"the draft prepared by llm is {draft}")

        async with httpx.AsyncClient(
            base_url=str(settings.vyzno_base_url),
            timeout=30.0,
            follow_redirects=False,
        ) as http_client:

            response = await http_client.post(
                    f"/v1/mailboxes/{mailbox_id}/drafts",
                json=payload,
                headers={
                    **vyzno_auth_headers(settings),
                    "Idempotency-Key": idempotency_key,
                },
            )

            response.raise_for_status()
            return response.json()
        

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
async def send_email(
    email: CreateDraftInput,
) -> dict[str, Any]:
    """
      Create and send an email from the user's Vyzno mailbox.
         Requirements:
        - Call only when the user explicitly requests sending an email.
        - At least one recipient email address is required.
        - A subject or message body, or both, must be provided.
        - If only the body is provided, generate a concise, relevant subject.
        - If a subject is provided, preserve the user's intended subject.
        - Compose the message from the user's instructions, preserving their intended meaning and tone.
        - Never invent recipient addresses, facts, or missing message content.
        - If required information is missing, ask the user before calling.
        - Do not use this tool when the user only wants to create a draft.
    """

    if not email.to:
        raise ToolError(
            "Provide at least one recipient email address before sending."
        )

    settings = Settings()
    mailbox_id = user_mailbox_id()
    idempotency_key = str(uuid4())

    headers = {
        **vyzno_auth_headers(settings),
        "Idempotency-Key": str(idempotency_key),
    }

    payload = email.model_dump(
        mode="json",
        by_alias=True,
        exclude_none=True,
    )

    if email.body_text is not None:
        text = email.body_text.replace("\r\n", "\n").replace("\r", "\n")
        html_body = escape(text).replace("\n", "<br>")
        payload["bodyHtml"] = f"<p>{html_body}</p>"


    try:
        async with httpx.AsyncClient(
            base_url=str(settings.vyzno_base_url),
            headers=headers,
            timeout=90.0,
            follow_redirects=False,
        ) as http_client:

            draft_response = await http_client.post(
                f"/v1/mailboxes/{mailbox_id}/drafts",
                json=payload,
            )

            draft_response.raise_for_status()

            try:
                draft_data = draft_response.json()
                draft_id = UUID(draft_data["id"])

                print(f"Draft created with ID: {draft_id}")

                if draft_id.version != 4:
                    raise ValueError("Invalid draft ID")

            except (ValueError, KeyError, TypeError, AttributeError):
                raise ToolError(
                    "Vyzno did not return a valid draft ID. "
                    "Sending was not attempted. "
                    "Reuse the same idempotency key and email data "
                    "if retrying."
                ) from None


            send_response = await http_client.post(
                f"/v1/mailboxes/{mailbox_id}/drafts/{draft_id}/send",
            )

            send_response.raise_for_status()

            try:
                result = send_response.json()
            except ValueError:
                raise ToolError(
                    f"The sending result could not be read. "
                    f"Draft ID: {draft_id}. "
                    "Check its status before retrying."
                ) from None

            if not isinstance(result, dict) or result.get("status") != "sent":
                raise ToolError(
                    f"Sending was not confirmed. Draft ID: {draft_id}. "
                    "Check its status before retrying."
                )

            return result

    except httpx.HTTPStatusError:

        raise ToolError(
            "If sending was attempted, check the message status before retrying. Reuse the same idempotency key and email data."
        ) from None

    