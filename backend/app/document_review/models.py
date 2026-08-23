from typing import Literal

from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    document_type: Literal["invoice", "receipt"]
    confidence: float = Field(ge=0, le=1)


class AiExtractionResult(BaseModel):
    document_type: Literal["invoice", "receipt"]
    supplier_name: str | None = None
    supplier_vat_id: str | None = None
    customer_vat_id: str | None = None
    invoice_number: str | None = None
    purchase_order: str | None = None
    invoice_date: str | None = None
    due_date: str | None = None
    merchant_name: str | None = None
    transaction_date: str | None = None
    subtotal: str | None = None
    vat_total: str | None = None
    total: str | None = None
    currency: str | None = None


class GlSuggestion(BaseModel):
    account_code: str
    account_name: str
    confidence: float = Field(ge=0, le=1)


class AdvisorRecommendation(BaseModel):
    """The Foundry advisor's explanation; it never controls the approval gate."""

    recommendation: Literal["APPROVE", "CORRECTION_REQUIRED", "ESCALATE"]
    summary: str
    reasons: list[str]
    questions_for_reviewer: list[str]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatResponse(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: str
