from mcp_server_email.schemas.drafts import CreateDraftInput
from typing import Any
from uuid import UUID

import httpx


class VyznoClient:
    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self._http_client = http_client

    async def create_draft(
        self,
        mailbox_id: UUID,
        draft: CreateDraftInput,
        idempotency_key: UUID,
    ) -> dict[str, Any]:
        if idempotency_key.version != 4:
            raise ValueError("Idempotency key must be a UUID v4.")

        payload = draft.model_dump(mode="json", by_alias=True)
        print(f"payload: {payload} ")
        response = await self._http_client.post(
            f"/v1/mailboxes/{mailbox_id}/drafts",
            json=payload,
            headers={
                "Idempotency-Key": str(idempotency_key),
            },
        )

        response.raise_for_status()
        return response.json()

    async def send_draft(
        self,
        mailbox_id: UUID,
        draft_id: UUID,
        idempotency_key: UUID,
    ) -> dict[str, Any]:
        if idempotency_key.version != 4:
            raise ValueError("Idempotency key must be a UUID v4.")

        response = await self._http_client.post(
            f"/v1/mailboxes/{mailbox_id}/drafts/{draft_id}/send",
            headers={
                "Idempotency-Key": str(idempotency_key),
            },
            timeout=90.0,
        )

        response.raise_for_status()
        return response.json()