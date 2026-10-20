import argparse
import asyncio
from uuid import UUID

from fastmcp import Client
from fastmcp.exceptions import ToolError


async def send_saved_draft(
    mailbox_id: UUID,
    draft_id: UUID,
    idempotency_key: UUID,
) -> None:
    print("Draft ID:", draft_id)
    print("Send-operation key:", idempotency_key)

    try:
        async with Client("http://127.0.0.1:8000/mcp") as client:
            result = await client.call_tool(
                "send_draft",
                {
                    "mailbox_id": str(mailbox_id),
                    "draft_id": str(draft_id),
                    "idempotency_key": str(idempotency_key),
                },
                timeout=120.0,
            )

    except ToolError as error:
        print(f"MCP tool failed: {error}")
        print("Check the message status before retrying.")
        raise SystemExit(1) from None

    except Exception as error:
        print(f"MCP request failed: {type(error).__name__}.")
        print("The send outcome is unconfirmed.")
        print("Check the message status before retrying.")
        raise SystemExit(1) from None

    data = result.structured_content

    if not isinstance(data, dict):
        print("Unexpected response. Check the message status.")
        raise SystemExit(1)

    print("Message ID:", data.get("id"))
    print("Status:", data.get("status"))

    if data.get("status") != "sent":
        print("Sending is not confirmed. Check the message status.")
        raise SystemExit(1)

    print("Backend reports the email was sent.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Send an existing Vyzno draft through MCP."
    )
    parser.add_argument("mailbox_id", type=UUID)
    parser.add_argument("draft_id", type=UUID)
    parser.add_argument("--idempotency-key", type=UUID, required=True)
    arguments = parser.parse_args()

    asyncio.run(
        send_saved_draft(
            mailbox_id=arguments.mailbox_id,
            draft_id=arguments.draft_id,
            idempotency_key=arguments.idempotency_key,
        )
    )