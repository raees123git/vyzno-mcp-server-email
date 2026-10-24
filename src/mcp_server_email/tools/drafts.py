from typing import Any
import httpx
from fastmcp.exceptions import ToolError
from fastmcp.tools import tool
from mcp_server_email.auth import vyzno_auth_headers, user_mailbox_id
from mcp_server_email.config import Settings
from mcp_server_email.schemas.drafts import CreateDraftInput


@tool()
async def create_draft( draft: CreateDraftInput ) -> dict[str, Any]:
    """ This tool will save an draft of the email. Use this tool to create a draft of an email. """
    settings = Settings()
    mailbox_id = user_mailbox_id()

    try:
        async with httpx.AsyncClient(
            base_url=str(settings.vyzno_base_url),
            timeout=30.0,
            follow_redirects=False,
        ) as http_client:

            response = await http_client.post(
                    f"/v1/mailboxes/{mailbox_id}/drafts",
                json=draft.model_dump(mode="json", by_alias=True),
                headers={
                    **vyzno_auth_headers(settings),
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


# @tool()
# async def send_email(
#     mailbox_id: UUID4,
#     draft_id: UUID4,
#     idempotency_key: UUID4,
# ) -> dict[str, Any]:
#     """this tool is for sending an email. Before sending an
#     """
#     settings = Settings()

#     try:
#         async with httpx.AsyncClient(
#             base_url=str(settings.vyzno_base_url),
#             headers=build_vyzno_auth_headers(settings),
#             timeout=90.0,
#             follow_redirects=False,
#         ) as http_client:
#             vyzno = VyznoClient(http_client)

#             return await vyzno.send_draft(
#                 mailbox_id=mailbox_id,
#                 draft_id=draft_id,
#                 idempotency_key=idempotency_key,
#             )

#     except httpx.HTTPStatusError as error:
#         status = error.response.status_code

#         if status >= 500:
#             raise ToolError(
#                 f"Vyzno returned HTTP {status}. "
#                 "The send outcome is unconfirmed. "
#                 "Check the message status before retrying."
#             ) from None

#         raise ToolError(
#             f"Vyzno rejected the send request: HTTP {status}."
#         ) from None

#     except httpx.RequestError:
#         raise ToolError(
#             "The Vyzno request could not complete. "
#             "The email may already have been sent. "
#             "Check its status before retrying, and reuse "
#             "the same draft ID and send-operation key."
#         ) from None