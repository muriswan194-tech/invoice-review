from collections.abc import Iterator
from dataclasses import asdict, is_dataclass
from datetime import date as Date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Literal

from pydantic import ValidationError

from app.config import APP_CONFIG, Settings
from app.document_review.models import AiExtractionResult
from app.invoices.models import (
    FinancialDocument,
    InvoiceDocument,
)
from app.invoices.repository import DocumentRecord, DocumentRepository
from app.invoices.validation import (
    Issue,
    collect_issues,
    run_checks,
)
from app.providers.azure_document_intelligence import read_document
from app.providers.azure_openai import extract_document_fields

DECIDED_STATUSES = frozenset({"approved", "rejected", "correction_requested"})
DEMO_SAMPLE_FILENAME = "prism-gst-exception.pdf"

EDITABLE_INVOICE_FIELDS = frozenset(
    {
        "supplier_name",
        "supplier_gstin",
        "buyer_gstin",
        "place_of_supply",
        "hsn_sac",
        "invoice_number",
        "taxable_value",
        "cgst",
        "sgst_or_utgst",
        "igst",
        "cess",
        "reverse_charge",
        "date",
        "total",
    }
)

AI_FALLBACK_FIELDS = (
    "supplier_name",
    "supplier_gstin",
    "buyer_gstin",
    "invoice_number",
    "date",
    "hsn_sac",
    "taxable_value",
    "total",
)

class ReviewError(Exception):
    """A workflow rule stopped this request."""


def process_document_events(
    file_path: Path,
    saved_name: str,
    original_filename: str,
    document_type: Literal["invoice", "receipt"],
    config: Settings,
    repository: DocumentRepository,
) -> Iterator[dict[str, object]]:
    """Run one review pipeline and yield truthful progress events between operations."""
    yield {"event": "progress", "stage": "extract"}
    extraction = read_document(file_path, config, document_type)
    if not isinstance(extraction.document, InvoiceDocument):
        raise ValueError("This GST invoice reviewer accepts invoices only.")

    document = extraction.document
    field_sources = document_intelligence_sources(document)
    conflicts: list[str] = []
    ai_fallback_used = needs_ai_fallback(document)
    if ai_fallback_used:
        ai_extraction = extract_document_fields(file_path, config)
        document, field_sources, conflicts = merge_missing_fields(document, ai_extraction)

    yield {"event": "progress", "stage": "validate"}
    checks = run_checks(document, extraction.confidence)
    issues = collect_issues(document, checks)

    record = repository.save_review(
        {
            "document_type": document.document_type,
            "supplier_name": display_name(document),
            "invoice_number": getattr(document, "invoice_number", None),
            "saved_name": saved_name,
            "original_filename": original_filename,
            "review_status": "pending",
            "upload_count": 1,
            "primary_confidence": extraction.confidence,
            "document": document.model_dump(mode="json"),
            "field_sources": field_sources,
            "conflicts": conflicts,
            # The upload workflow accepts invoices only. Document Intelligence is the
            # single document-type gate, so no separate AI classification is needed.
            "classification": {
                "document_type": "invoice",
                "source": "document_intelligence_with_ai_fallback"
                if ai_fallback_used
                else "document_intelligence",
            },
            "checks": serialize_checks(checks),
            "issues": [asdict(issue) for issue in issues],
        }
    )
    yield {"event": "complete", "review": review_payload(record)}


def process_document(
    file_path: Path,
    saved_name: str,
    original_filename: str,
    document_type: Literal["invoice", "receipt"],
    config: Settings,
    repository: DocumentRepository,
) -> dict[str, object]:
    """Run the pipeline without streaming, for callers that need one final payload."""
    for event in process_document_events(
        file_path,
        saved_name,
        original_filename,
        document_type,
        config,
        repository,
    ):
        if event["event"] == "complete":
            review = event["review"]
            if isinstance(review, dict):
                return review
    raise RuntimeError("The review pipeline ended without producing a review.")


def create_demo_review(repository: DocumentRepository) -> dict[str, object]:
    """Create one fictional, fully offline review for presentations and local walkthroughs."""
    source_path = APP_CONFIG.data_dir.parent.parent / "samples" / "generated" / DEMO_SAMPLE_FILENAME
    if not source_path.is_file():
        raise ReviewError("The local demo sample is not available.")

    APP_CONFIG.upload_dir.mkdir(parents=True, exist_ok=True)
    for saved_name in repository.delete_demo_reviews():
        (APP_CONFIG.upload_dir / saved_name).unlink(missing_ok=True)

    saved_name = f"demo-{DEMO_SAMPLE_FILENAME}"
    target_path = APP_CONFIG.upload_dir / saved_name
    target_path.write_bytes(source_path.read_bytes())
    document = InvoiceDocument(
        supplier_name="Saffron Build Systems Pvt. Ltd.",
        supplier_gstin="29AABCU9603R1ZJ",
        buyer_gstin="27AAPFU0939F1ZV",
        supplier_pan="AABCU9603R",
        place_of_supply="Maharashtra (27)",
        hsn_sac="995411",
        invoice_number="SBS-2026-0042",
        taxable_value=Decimal("100000.00"),
        cgst=Decimal("9000.00"),
        sgst_or_utgst=Decimal("9000.00"),
        igst=None,
        cess=Decimal("0.00"),
        reverse_charge=False,
        date=Date(2026, 8, 1),
        total=Decimal("119000.00"),
    )
    checks = run_checks(document, primary_confidence=0.99)
    issues = collect_issues(document, checks)
    record = repository.save_review(
        {
            "document_type": "invoice",
            "supplier_name": document.supplier_name,
            "invoice_number": document.invoice_number,
            "saved_name": saved_name,
            "original_filename": "Fictional GST invoice exception sample.pdf",
            "review_status": "pending",
            "is_demo": True,
            "upload_count": 1,
            "primary_confidence": 0.99,
            "document": document.model_dump(mode="json"),
            "field_sources": {name: "demo_fixture" for name in document.model_dump()},
            "conflicts": [],
            "classification": {"document_type": "invoice", "confidence": 0.99},
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

    editable = EDITABLE_INVOICE_FIELDS
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

    if not isinstance(document, InvoiceDocument):
        raise ReviewError("This GST invoice reviewer accepts invoices only.")
    checks = run_checks(document, record.primary_confidence)
    issues = collect_issues(document, checks)

    updated = repository.apply_corrections(
        record_id=record_id,
        document=document.model_dump(mode="json"),
        field_sources=field_sources,
        checks=serialize_checks(checks),
        issues=[asdict(issue) for issue in issues],
        supplier_name=display_name(document),
        invoice_number=getattr(document, "invoice_number", None),
    )
    if updated is None:
        raise ReviewError("This review was not found.")
    return review_payload(updated)


def review_payload(record: DocumentRecord) -> dict[str, object]:
    """Render one stored review as the application-facing response."""
    return {
        "record_id": record.id,
        "document_type": record.document_type,
        "filename": record.original_filename,
        "saved_name": record.saved_name,
        "review_status": record.review_status,
        "is_demo": record.is_demo,
        "upload_count": record.upload_count,
        "can_edit": record.review_status not in DECIDED_STATUSES,
        "primary_confidence": record.primary_confidence,
        "classification": record.classification,
        "field_sources": record.field_sources,
        "conflicts": record.conflicts,
        "document": record.document,
        "checks": record.checks,
        "issues": record.issues,
    }


def build_document(document_type: str, values: dict[str, Any]) -> FinancialDocument:
    """Rebuild a typed document from stored JSON or corrected values."""
    if document_type == "invoice":
        return InvoiceDocument.model_validate(values)
    raise ReviewError("This GST invoice reviewer accepts invoices only.")


def display_name(document: FinancialDocument) -> str | None:
    """The party a reviewer recognizes, whichever document type this is."""
    return document.supplier_name if isinstance(document, InvoiceDocument) else None


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


def review_issues(document: InvoiceDocument, confidence: float | None) -> list[Issue]:
    """Re-run policy for a document, used by the corpus evaluators."""
    return collect_issues(document, run_checks(document, confidence))


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


def needs_ai_fallback(document: InvoiceDocument) -> bool:
    """Only spend an AI call when the primary extractor missed core GST evidence."""
    if any(getattr(document, field_name) in (None, "") for field_name in AI_FALLBACK_FIELDS):
        return True
    return not any(
        value is not None
        for value in (document.cgst, document.sgst_or_utgst, document.igst, document.cess)
    )


def document_intelligence_sources(document: InvoiceDocument) -> dict[str, str]:
    """Give complete primary results the same field-level provenance as merged results."""
    return {
        field_name: "document_intelligence" if value is not None else "missing"
        for field_name, value in document.model_dump().items()
    }


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
