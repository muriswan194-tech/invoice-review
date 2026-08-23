from dataclasses import asdict, is_dataclass
from datetime import date as Date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Literal

from pydantic import ValidationError

from app.config import APP_CONFIG, Settings
from app.correction_email.eligibility import is_eligible, supplier_fixable_issues
from app.correction_email.models import CorrectionEmailContext, CorrectionEmailDraft
from app.document_review.models import AiExtractionResult
from app.invoices.models import (
    FinancialDocument,
    InvoiceDocument,
    ReceiptDocument,
    invoice_key_parts,
)
from app.invoices.repository import DocumentRecord, DocumentRepository
from app.invoices.validation import (
    Issue,
    check_confidence,
    check_date_order,
    check_duplicate,
    check_positive_total,
    check_purchase_order,
    check_required_fields,
    check_total,
    check_vat_numbers,
    collect_issues,
)
from app.providers.azure_document_intelligence import read_document
from app.providers.azure_foundry import advise_invoice_review
from app.providers.azure_openai import (
    classify_document,
    draft_correction_email,
    extract_document_fields,
    suggest_gl_account,
)

DECIDED_STATUSES = frozenset({"approved", "rejected", "correction_requested"})

EDITABLE_INVOICE_FIELDS = frozenset(
    {
        "supplier_name",
        "supplier_vat_id",
        "customer_vat_id",
        "invoice_number",
        "purchase_order",
        "date",
        "due_date",
        "subtotal",
        "vat_total",
        "total",
        "currency",
    }
)

EDITABLE_RECEIPT_FIELDS = frozenset(
    {"merchant_name", "date", "subtotal", "vat_total", "total", "currency"}
)


class ReviewError(Exception):
    """A workflow rule stopped this request."""


def process_document(
    file_path: Path,
    saved_name: str,
    original_filename: str,
    document_type: Literal["invoice", "receipt"],
    config: Settings,
    repository: DocumentRepository,
) -> dict[str, object]:
    """Read one uploaded document, apply policy, store the review, and return it."""
    classification = classify_document(file_path, config)
    extraction = read_document(file_path, config, document_type)
    ai_extraction = extract_document_fields(file_path, config)
    document, field_sources, conflicts = merge_missing_fields(extraction.document, ai_extraction)
    gl_suggestion = suggest_gl_account(document.model_dump(mode="json"), config)

    supplier_key, invoice_key = (
        invoice_key_parts(document) if isinstance(document, InvoiceDocument) else (None, None)
    )
    already_seen = (
        repository.invoice_exists(document) if isinstance(document, InvoiceDocument) else False
    )
    checks = run_checks(document, already_seen, extraction.confidence)
    issues = collect_issues(document, checks)
    advisor = advise_invoice_review(
        document=document.model_dump(mode="json"),
        checks=serialize_checks(checks),
        issues=[asdict(issue) for issue in issues],
        conflicts=conflicts,
        gl_suggestion=gl_suggestion.model_dump(mode="json"),
        config=config,
    )

    if already_seen and supplier_key is not None and invoice_key is not None:
        repository.count_repeat_upload(supplier_key, invoice_key)

    record = repository.save_review(
        {
            "document_type": document.document_type,
            "supplier_key": supplier_key,
            "invoice_key": invoice_key,
            "supplier_name": display_name(document),
            "invoice_number": getattr(document, "invoice_number", None),
            "saved_name": saved_name,
            "original_filename": original_filename,
            "review_status": "pending",
            "upload_count": 1,
            "primary_confidence": extraction.confidence,
            "selected_account_code": None,
            "document": document.model_dump(mode="json"),
            "field_sources": field_sources,
            "conflicts": conflicts,
            "classification": classification.model_dump(mode="json"),
            "gl_suggestion": gl_suggestion.model_dump(mode="json"),
            "advisor": advisor.model_dump(mode="json"),
            "checks": serialize_checks(checks),
            "issues": [asdict(issue) for issue in issues],
        }
    )
    return review_payload(record)


def apply_corrections(
    record_id: int,
    edits: dict[str, str | None],
    config: Settings,
    repository: DocumentRepository,
) -> dict[str, object]:
    """Store reviewer corrections, mark those fields human-sourced, and re-run policy."""
    record = repository.get_review(record_id)
    if record is None:
        raise ReviewError("This review was not found.")
    if record.review_status in DECIDED_STATUSES:
        raise ReviewError("A decided document can no longer be edited.")

    editable = (
        EDITABLE_INVOICE_FIELDS if record.document_type == "invoice" else EDITABLE_RECEIPT_FIELDS
    )
    unknown = sorted(set(edits) - editable)
    if unknown:
        raise ReviewError(f"These fields cannot be edited: {', '.join(unknown)}.")
    if not edits:
        raise ReviewError("No field corrections were supplied.")

    stored = dict(record.document)
    field_sources = dict(record.field_sources)
    for field_name, raw_value in edits.items():
        value = raw_value.strip() if isinstance(raw_value, str) else raw_value
        stored[field_name] = value or None
        field_sources[field_name] = "human" if value else "missing"

    try:
        document = build_document(record.document_type, stored)
    except ValidationError as error:
        raise ReviewError("A corrected value has the wrong format.") from error

    supplier_key, invoice_key = (
        invoice_key_parts(document) if isinstance(document, InvoiceDocument) else (None, None)
    )
    already_seen = duplicate_of_another_review(record, supplier_key, invoice_key, repository)
    checks = run_checks(document, already_seen, record.primary_confidence)
    issues = collect_issues(document, checks)
    advisor = advise_invoice_review(
        document=document.model_dump(mode="json"),
        checks=serialize_checks(checks),
        issues=[asdict(issue) for issue in issues],
        conflicts=record.conflicts,
        gl_suggestion=record.gl_suggestion,
        config=config,
    )

    updated = repository.apply_corrections(
        record_id=record_id,
        document=document.model_dump(mode="json"),
        field_sources=field_sources,
        checks=serialize_checks(checks),
        issues=[asdict(issue) for issue in issues],
        advisor=advisor.model_dump(mode="json"),
        supplier_name=display_name(document),
        invoice_number=getattr(document, "invoice_number", None),
    )
    if updated is None:
        raise ReviewError("This review was not found.")
    return review_payload(updated)


def decide_review(
    record_id: int,
    decision: Literal["approved", "rejected", "correction_requested"],
    repository: DocumentRepository,
) -> dict[str, object]:
    """Save a reviewer decision, refusing approval while blocking issues remain."""
    record = repository.get_review(record_id)
    if record is None:
        raise ReviewError("This review was not found.")
    if decision == "approved":
        if stored_issues_block_approval(record):
            raise ReviewError("This document cannot be approved while errors remain open.")
        if record.selected_account_code is None:
            raise ReviewError("A GL account must be selected before approval.")

    updated = repository.update_status(record_id, decision)
    if updated is None:
        raise ReviewError("This review was not found.")
    return review_payload(updated)


def select_account(
    record_id: int,
    account_code: str,
    repository: DocumentRepository,
) -> dict[str, object]:
    """Confirm or override the GL account for one review."""
    record = repository.get_review(record_id)
    if record is None:
        raise ReviewError("This review was not found.")
    if record.review_status in DECIDED_STATUSES:
        raise ReviewError("A decided document can no longer be changed.")

    updated = repository.update_account(record_id, account_code)
    if updated is None:
        raise ReviewError("This review was not found.")
    return review_payload(updated)


def request_correction_email(
    record_id: int,
    config: Settings,
    repository: DocumentRepository,
) -> CorrectionEmailDraft:
    """Draft a supplier correction request, but only for issues a supplier can fix."""
    record = repository.get_review(record_id)
    if record is None:
        raise ReviewError("This review was not found.")

    fixable = supplier_fixable_issues(record.issues)
    if not fixable:
        raise ReviewError("This document has no issues the supplier can correct.")

    context = CorrectionEmailContext(
        supplier_name=record.supplier_name or "Supplier",
        invoice_number=record.invoice_number or "unknown",
        document_type=record.document_type,
        issue_messages=[str(issue.get("message", "")) for issue in fixable],
    )
    return draft_correction_email(context, config)


def run_checks(
    document: FinancialDocument,
    already_seen: bool,
    primary_confidence: float | None,
) -> dict[str, object]:
    """Run every deterministic Northstar check that applies to this document."""
    checks: dict[str, object] = {
        "required": check_required_fields(document),
        "total": check_total(document),
        "positive_total": check_positive_total(document),
        "confidence": check_confidence(primary_confidence, APP_CONFIG.low_confidence_threshold),
    }

    if isinstance(document, InvoiceDocument):
        checks["vat"] = check_vat_numbers(document, APP_CONFIG.customer_vat_id)
        checks["date_order"] = check_date_order(document)
        checks["purchase_order"] = check_purchase_order(document)
        checks["duplicate"] = check_duplicate(document, already_seen)

    return checks


def review_payload(record: DocumentRecord) -> dict[str, object]:
    """Render one stored review as the application-facing response."""
    return {
        "record_id": record.id,
        "document_type": record.document_type,
        "filename": record.original_filename,
        "saved_name": record.saved_name,
        "review_status": record.review_status,
        "upload_count": record.upload_count,
        "can_approve": not stored_issues_block_approval(record)
        and record.selected_account_code is not None,
        "can_edit": record.review_status not in DECIDED_STATUSES,
        "can_request_correction": is_eligible(record.issues),
        "primary_confidence": record.primary_confidence,
        "selected_account_code": record.selected_account_code,
        "classification": record.classification,
        "field_sources": record.field_sources,
        "conflicts": record.conflicts,
        "gl_suggestion": record.gl_suggestion,
        "advisor": record.advisor,
        "document": record.document,
        "checks": record.checks,
        "issues": record.issues,
    }


def stored_issues_block_approval(record: DocumentRecord) -> bool:
    """Read severities back out of the stored issue list."""
    return any(
        isinstance(issue, dict) and issue.get("severity") == "error" for issue in record.issues
    )


def duplicate_of_another_review(
    record: DocumentRecord,
    supplier_key: str | None,
    invoice_key: str | None,
    repository: DocumentRepository,
) -> bool:
    """A corrected invoice duplicates only when another review already holds its identity."""
    if supplier_key is None or invoice_key is None:
        return False

    return any(
        other.id != record.id
        and other.supplier_key == supplier_key
        and other.invoice_key == invoice_key
        for other in repository.list_reviews()
    )


def build_document(document_type: str, values: dict[str, Any]) -> FinancialDocument:
    """Rebuild a typed document from stored JSON or corrected values."""
    if document_type == "invoice":
        return InvoiceDocument.model_validate(values)
    return ReceiptDocument.model_validate(values)


def display_name(document: FinancialDocument) -> str | None:
    """The party a reviewer recognizes, whichever document type this is."""
    if isinstance(document, InvoiceDocument):
        return document.supplier_name
    if isinstance(document, ReceiptDocument):
        return document.merchant_name
    return None


def serialize_checks(checks: dict[str, object]) -> dict[str, object]:
    """Render check dataclasses as JSON-safe dictionaries."""
    serialized: dict[str, object] = {}
    for name, check in checks.items():
        if is_dataclass(check) and not isinstance(check, type):
            serialized[name] = {
                key: str(value) if isinstance(value, Decimal) else value
                for key, value in asdict(check).items()
            }
    return serialized


def review_issues(
    document: FinancialDocument,
    already_seen: bool,
    confidence: float | None,
) -> list[Issue]:
    """Re-run policy for a document, used by the corpus evaluators."""
    return collect_issues(document, run_checks(document, already_seen, confidence))


def merge_missing_fields(
    document: FinancialDocument,
    ai_extraction: AiExtractionResult,
) -> tuple[FinancialDocument, dict[str, str], list[str]]:
    primary = document.model_dump()
    fallback = ai_extraction.model_dump()
    date_field = "invoice_date" if document.document_type == "invoice" else "transaction_date"
    fallback["date"] = fallback.get(date_field)
    updates: dict[str, object] = {}
    provenance: dict[str, str] = {}
    conflicts: list[str] = []
    for field_name, primary_value in primary.items():
        ai_value = fallback.get(field_name)
        if primary_value is None and ai_value is not None:
            updates[field_name] = ai_value
            provenance[field_name] = "azure_openai_fallback"
        elif primary_value is not None:
            provenance[field_name] = "document_intelligence"
            if ai_value is not None and not equivalent_values(primary_value, ai_value):
                conflicts.append(field_name)

    merged = type(document).model_validate({**primary, **updates})
    for field_name in primary:
        provenance.setdefault(field_name, "missing")
    return merged, provenance, conflicts


def equivalent_values(primary_value: object, ai_value: object) -> bool:
    if isinstance(primary_value, Decimal):
        try:
            return primary_value == Decimal(str(ai_value))
        except (InvalidOperation, ValueError):
            return False
    if isinstance(primary_value, Date):
        return str(primary_value) == str(ai_value)
    if isinstance(primary_value, str):
        return primary_value.strip().casefold() == str(ai_value).strip().casefold()
    return primary_value == ai_value
