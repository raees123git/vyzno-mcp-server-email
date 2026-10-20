from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CreateDraftInput(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        hide_input_in_errors=True,
    )

    type: Literal["new"] = "new"

    to: list[EmailStr] = Field(min_length=1, max_length=100)
    subject: str = Field(min_length=1, max_length=998)
    body_text: str = Field(
        default=None,
        alias="bodyText",
        min_length=1,
        max_length=1_000_000,
    )
    body_html: str | None = Field(
        default=None,
        alias="bodyHtml",
        min_length=1,
        max_length=1_000_000,
    )
    