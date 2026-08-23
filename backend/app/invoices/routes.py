import traceback
from secrets import token_hex
from typing import Literal

from fastapi import APIRouter, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.accounting.catalog import is_valid_account
from app.config import APP_CONFIG, settings
from app.invoices.repository import build_repository
from app.invoices.service import (
    ReviewError,
    apply_corrections,
    decide_review,
    process_document,
    request_correction_email,
    review_payload,
    select_account,
)

ALLOWED_CONTENT_TYPES = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
}

router = APIRouter(prefix="/invoices", tags=["invoices"])
repository = build_repository(APP_CONFIG.database_url, APP_CONFIG.data_dir)


class ReviewDecision(BaseModel):
    decision: Literal["approved", "rejected", "correction_requested"]


class FieldCorrections(BaseModel):
    fields: dict[str, str | None] = Field(min_length=1)


class ChatRequest(BaseModel):
    messages: list[dict[str, str]]  # {role, content}


class AccountSelection(BaseModel):
    account_code: str


@router.post("/upload")
def upload_invoice(
    file: UploadFile,
    document_type: Literal["invoice", "receipt"] = Form("invoice"),
) -> dict[str, object]:
    extension = ALLOWED_CONTENT_TYPES.get(file.content_type or "")
    if extension is None:
        raise HTTPException(status_code=415, detail="Only PDF, PNG, and JPEG files are supported.")

    content = file.file.read(APP_CONFIG.max_upload_bytes + 1)
    if len(content) > APP_CONFIG.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Files must be 4 MB or smaller.")

    APP_CONFIG.upload_dir.mkdir(parents=True, exist_ok=True)
    saved_name = f"{token_hex(16)}{extension}"
    saved_path = APP_CONFIG.upload_dir / saved_name
    saved_path.write_bytes(content)

    try:
        return process_document(
            file_path=saved_path,
            saved_name=saved_name,
            original_filename=file.filename or saved_name,
            document_type=document_type,
            config=settings,
            repository=repository,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        traceback.print_exc()
        raise HTTPException(status_code=502, detail="Document analysis failed.") from error


@router.get("/history")
def invoice_history() -> list[dict[str, object]]:
    return [review_payload(record) for record in repository.list_reviews()]


@router.get("/{record_id}")
def get_review(record_id: int) -> dict[str, object]:
    record = repository.get_review(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="This review was not found.")
    return review_payload(record)


@router.put("/{record_id}")
def correct_review(record_id: int, corrections: FieldCorrections) -> dict[str, object]:
    try:
        return apply_corrections(record_id, corrections.fields, settings, repository)
    except ReviewError as error:
        raise HTTPException(status_code=status_for(error), detail=str(error)) from error


@router.put("/{record_id}/accounting")
def choose_account(record_id: int, selection: AccountSelection) -> dict[str, object]:
    if not is_valid_account(selection.account_code):
        raise HTTPException(
            status_code=422,
            detail="That GL account is not in the Northstar catalog.",
        )

    try:
        return select_account(record_id, selection.account_code, repository)
    except ReviewError as error:
        raise HTTPException(status_code=status_for(error), detail=str(error)) from error


@router.post("/{record_id}/decision")
def decide_invoice(record_id: int, decision: ReviewDecision) -> dict[str, object]:
    try:
        return decide_review(record_id, decision.decision, repository)
    except ReviewError as error:
        raise HTTPException(status_code=status_for(error), detail=str(error)) from error


@router.post("/{record_id}/correction-email")
def correction_email(record_id: int) -> dict[str, str]:
    try:
        draft = request_correction_email(record_id, settings, repository)
    except ReviewError as error:
        raise HTTPException(status_code=status_for(error), detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail="The draft could not be generated.") from error

    return draft.model_dump()


@router.post("/{record_id}/chat")
def chat_with_advisor_endpoint(record_id: int, request: ChatRequest) -> dict[str, str]:
    record = repository.get_review(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="This review was not found.")

    # Build context-aware messages: include document summary as system context
    supplier = record.document.get("supplier_name", record.document.get("merchant_name", "Unknown"))
    context = (
        f"Document: {record.document_type}\n"
        f"Supplier: {supplier}\n"
        f"Total: {record.document.get('total')} {record.document.get('currency', '')}\n"
        f"Status: {record.review_status}\n"
        "You are the invoice review advisor. Answer questions about this document."
    )

    # Build messages with context + user messages
    messages = [{"role": "system", "content": context}] + request.messages

    try:
        from app.document_review.models import ChatMessage
        from app.providers.azure_foundry import chat_with_advisor

        messages_parsed = [ChatMessage(**m) for m in messages]
        response = chat_with_advisor(messages_parsed, settings)
        return response.model_dump()
    except Exception as error:
        traceback.print_exc()
        raise HTTPException(status_code=502, detail="Advisor chat failed.") from error


@router.delete("/{record_id}")
def delete_invoice(record_id: int) -> dict[str, object]:
    saved_name = repository.delete_review(record_id)
    if saved_name is None:
        raise HTTPException(status_code=404, detail="This review was not found.")

    (APP_CONFIG.upload_dir / saved_name).unlink(missing_ok=True)
    return {"record_id": record_id, "status": "deleted"}


def status_for(error: ReviewError) -> int:
    """Not found is a 404; every other workflow refusal is a 409."""
    return 404 if "was not found" in str(error) else 409
