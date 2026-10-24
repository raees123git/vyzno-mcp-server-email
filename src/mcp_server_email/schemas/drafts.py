from typing import Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    model_validator,
)


class CreateDraftInput(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        hide_input_in_errors=True,
    )

    type: Literal["new"] = "new"

    to: list[EmailStr] = Field(
        default_factory=list,
        max_length=100,
    )
    subject: str | None = Field(
        default=None,
        max_length=998,
    )
    body_text: str | None = Field(
        default=None,
        alias="bodyText",
        max_length=1_000_000,
    )
    body_html: str | None = Field(
        default=None,
        alias="bodyHtml",
        max_length=1_000_000,
    )

    @model_validator(mode="after")
    def require_content(self) -> Self:
        has_content = bool(
            self.to
            or (self.subject or "").strip()
            or (self.body_text or "").strip()
            or (self.body_html or "").strip()
        )

        if not has_content:
            raise ValueError(
                "Provide a recipient, subject, or message content."
            )

        return self