import argparse
import asyncio
from uuid import UUID

from fastmcp import Client
from fastmcp.exceptions import ToolError


async def check_mcp_draft(
    mailbox_id: UUID,
    recipient: str,
    idempotency_key: UUID,
) -> None:
    print(f"Operation key: {idempotency_key}")

    try:
        async with Client("http://127.0.0.1:8000/mcp") as client:
            result = await client.call_tool(
                "create_draft",
                {
                    "mailbox_id": str(mailbox_id),
                    "draft": {
                        "type": "new",
                        "to": [recipient],
                        "subject": "MCP tool draft test",
                        "bodyText": (
                            "this is a test draft created through the MCP server. "
                        ),
                        "bodyHtml": (
                            "<p>this is sent by raees..</p>"
                        ),
                    },
                    "idempotency_key": str(idempotency_key),
                },
                timeout=60.0,
            )

    except ToolError as error:
        print(f"MCP tool failed: {error}")
        raise SystemExit(1) from None

    except Exception as error:
        print(f"MCP request failed: {type(error).__name__}.")
        print("The outcome is unconfirmed. Keep the operation key.")
        raise SystemExit(1) from None

    data = result.structured_content

    if not isinstance(data, dict) or "id" not in data:
        print("Unexpected response. Keep the operation key.")
        raise SystemExit(1)

    print("Draft created through MCP.")
    print("Draft ID:", data["id"])
    print("Status:", data.get("status"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create a draft through the MCP server. but still in testing phase"
    )
    parser.add_argument("mailbox_id", type=UUID)
    parser.add_argument("recipient")
    parser.add_argument("--idempotency-key", type=UUID, required=True)
    arguments = parser.parse_args()

    asyncio.run(
        check_mcp_draft(
            mailbox_id=arguments.mailbox_id,
            recipient=arguments.recipient,
            idempotency_key=arguments.idempotency_key,
        )
    )