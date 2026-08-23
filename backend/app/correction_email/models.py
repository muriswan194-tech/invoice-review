from pydantic import BaseModel


class CorrectionEmailDraft(BaseModel):
    """A provider-independent draft the reviewer copies. The app never sends mail."""

    subject: str
    body: str


class CorrectionEmailContext(BaseModel):
    """Everything the drafting model is allowed to see."""

    supplier_name: str
    invoice_number: str
    document_type: str
    issue_messages: list[str]
