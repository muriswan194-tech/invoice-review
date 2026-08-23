from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from stdnum.eu import vat

from app.invoices.models import (
    FinancialDocument,
    InvoiceDocument,
    ReceiptDocument,
    invoice_key_parts,
)

Severity = Literal["error", "warning"]

INVOICE_REQUIRED_CODES: dict[str, str] = {
    "supplier_name": "vendor_name_required",
    "supplier_vat_id": "vendor_vat_id_required",
    "customer_vat_id": "customer_vat_id_required",
    "invoice_number": "invoice_number_required",
    "date": "invoice_date_required",
    "currency": "currency_required",
    "total": "invoice_total_required",
}

RECEIPT_REQUIRED_CODES: dict[str, str] = {
    "merchant_name": "merchant_name_required",
    "date": "transaction_date_required",
    "currency": "currency_required",
    "total": "receipt_total_required",
    "vat_total": "receipt_vat_total_required",
}


@dataclass(frozen=True)
class Issue:
    """One coded policy finding a reviewer can act on."""

    code: str
    severity: Severity
    message: str
    field: str | None = None


@dataclass(frozen=True)
class TotalCheck:
    status: str
    difference: Decimal | None
    message: str


@dataclass(frozen=True)
class RequiredFieldsCheck:
    status: str
    missing: tuple[str, ...]
    message: str


@dataclass(frozen=True)
class VatCheck:
    status: str
    supplier_valid: bool | None
    customer_valid: bool | None
    customer_matches: bool | None
    message: str


@dataclass(frozen=True)
class PositiveTotalCheck:
    status: str
    message: str


@dataclass(frozen=True)
class DateOrderCheck:
    status: str
    message: str


@dataclass(frozen=True)
class DuplicateCheck:
    status: str
    key: str | None
    message: str


@dataclass(frozen=True)
class PurchaseOrderCheck:
    status: str
    message: str


@dataclass(frozen=True)
class ConfidenceCheck:
    status: str
    confidence: float | None
    message: str


def check_total(document: FinancialDocument) -> TotalCheck:
    if document.subtotal is None or document.vat_total is None or document.total is None:
        return TotalCheck(
            status="warning",
            difference=None,
            message="Subtotal, VAT, and total are all needed for this check.",
        )

    difference = (document.subtotal + document.vat_total - document.total).copy_abs()
    if difference <= Decimal("0.01"):
        return TotalCheck(
            status="passed",
            difference=difference,
            message="Subtotal and VAT match the total.",
        )

    return TotalCheck(
        status="failed",
        difference=difference,
        message="Subtotal and VAT do not match the total.",
    )


def check_positive_total(document: FinancialDocument) -> PositiveTotalCheck:
    if document.total is None:
        return PositiveTotalCheck(
            status="warning",
            message="A total is needed for this check.",
        )

    if document.total > Decimal("0"):
        return PositiveTotalCheck(
            status="passed",
            message="The total is greater than zero.",
        )

    return PositiveTotalCheck(
        status="failed",
        message="The total must be greater than zero.",
    )


def check_date_order(document: InvoiceDocument) -> DateOrderCheck:
    if document.date is None or document.due_date is None:
        return DateOrderCheck(
            status="warning",
            message="Invoice date and due date are both needed for this check.",
        )

    if document.due_date >= document.date:
        return DateOrderCheck(
            status="passed",
            message="The due date is on or after the invoice date.",
        )

    return DateOrderCheck(
        status="failed",
        message="The due date cannot be earlier than the invoice date.",
    )


def check_duplicate(document: InvoiceDocument, already_seen: bool) -> DuplicateCheck:
    """Report duplicate status from an identity the caller already looked up."""
    supplier_key, invoice_key = invoice_key_parts(document)
    if supplier_key is None or invoice_key is None:
        return DuplicateCheck(
            status="warning",
            key=None,
            message="Supplier name and invoice number are needed for this check.",
        )

    key = f"{supplier_key}::{invoice_key}"
    if already_seen:
        return DuplicateCheck(
            status="failed",
            key=key,
            message="This supplier invoice has already been seen.",
        )

    return DuplicateCheck(
        status="passed",
        key=key,
        message="This supplier invoice has not been seen before.",
    )


def check_required_fields(document: FinancialDocument) -> RequiredFieldsCheck:
    required = required_field_values(document)
    missing = tuple(name for name, value in required.items() if value is None or value == "")
    if missing:
        return RequiredFieldsCheck(
            status="failed",
            missing=missing,
            message="Required information is missing.",
        )

    return RequiredFieldsCheck(
        status="passed",
        missing=(),
        message="Required information is present.",
    )


def required_field_values(document: FinancialDocument) -> dict[str, object]:
    """Return the fields Northstar policy requires for this document type."""
    if isinstance(document, InvoiceDocument):
        return {
            "supplier_name": document.supplier_name,
            "supplier_vat_id": document.supplier_vat_id,
            "customer_vat_id": document.customer_vat_id,
            "invoice_number": document.invoice_number,
            "date": document.date,
            "total": document.total,
            "currency": document.currency,
        }
    if isinstance(document, ReceiptDocument):
        return {
            "merchant_name": document.merchant_name,
            "date": document.date,
            "currency": document.currency,
            "total": document.total,
            "vat_total": document.vat_total,
        }
    return {}


def check_vat_numbers(document: InvoiceDocument, expected_customer_vat_id: str) -> VatCheck:
    supplier_valid = validate_vat(document.supplier_vat_id)
    customer_valid = validate_vat(document.customer_vat_id)
    customer_matches = compare_vat(document.customer_vat_id, expected_customer_vat_id)

    if customer_matches is False:
        return VatCheck(
            status="failed",
            supplier_valid=supplier_valid,
            customer_valid=customer_valid,
            customer_matches=False,
            message="The customer VAT number is not Northstar's own VAT number.",
        )

    if supplier_valid is None or customer_valid is None:
        return VatCheck(
            status="warning",
            supplier_valid=supplier_valid,
            customer_valid=customer_valid,
            customer_matches=customer_matches,
            message="Both VAT numbers are needed for this check.",
        )

    if supplier_valid and customer_valid:
        return VatCheck(
            status="passed",
            supplier_valid=True,
            customer_valid=True,
            customer_matches=customer_matches,
            message="Both VAT numbers have a valid format and checksum.",
        )

    return VatCheck(
        status="failed",
        supplier_valid=supplier_valid,
        customer_valid=customer_valid,
        customer_matches=customer_matches,
        message="At least one VAT number has an invalid format or checksum.",
    )


def check_purchase_order(document: InvoiceDocument) -> PurchaseOrderCheck:
    if document.purchase_order and document.purchase_order.strip():
        return PurchaseOrderCheck(
            status="passed",
            message="A purchase order reference is present.",
        )

    return PurchaseOrderCheck(
        status="warning",
        message="No purchase order reference was found on this invoice.",
    )


def check_confidence(confidence: float | None, threshold: float) -> ConfidenceCheck:
    if confidence is None:
        return ConfidenceCheck(
            status="warning",
            confidence=None,
            message="The primary extraction did not report a confidence score.",
        )

    if confidence >= threshold:
        return ConfidenceCheck(
            status="passed",
            confidence=confidence,
            message="The primary extraction is confident about this document.",
        )

    return ConfidenceCheck(
        status="warning",
        confidence=confidence,
        message="The primary extraction confidence is below the review threshold.",
    )


def normalize_vat(value: str | None) -> str | None:
    """Strip separators and casing so two spellings of one VAT number compare equal."""
    if not value:
        return None

    return "".join(character for character in value if character.isalnum()).upper()


def compare_vat(value: str | None, expected: str) -> bool | None:
    normalized = normalize_vat(value)
    if normalized is None:
        return None

    return normalized == normalize_vat(expected)


def validate_vat(value: str | None) -> bool | None:
    if not value:
        return None

    try:
        vat.validate(value)
    except (vat.InvalidChecksum, vat.InvalidFormat, vat.InvalidLength):
        return False
    except Exception:
        return False
    return True


def collect_issues(
    document: FinancialDocument,
    checks: dict[str, object],
) -> list[Issue]:
    """Translate check results into the coded issue vocabulary the corpus manifest uses."""
    issues: list[Issue] = []
    required_codes = (
        INVOICE_REQUIRED_CODES if document.document_type == "invoice" else RECEIPT_REQUIRED_CODES
    )

    required = checks.get("required")
    if isinstance(required, RequiredFieldsCheck):
        for field_name in required.missing:
            code = required_codes.get(field_name)
            if code is not None:
                issues.append(
                    Issue(
                        code=code,
                        severity="error",
                        message=f"{field_label(field_name)} is required.",
                        field=field_name,
                    )
                )

    vat_check = checks.get("vat")
    if isinstance(vat_check, VatCheck):
        if vat_check.supplier_valid is False:
            issues.append(
                Issue(
                    code="vendor_vat_id_invalid",
                    severity="error",
                    message="The supplier VAT number has an invalid format or checksum.",
                    field="supplier_vat_id",
                )
            )
        if vat_check.customer_matches is False:
            issues.append(
                Issue(
                    code="customer_vat_id_mismatch",
                    severity="error",
                    message="The customer VAT number is not Northstar's own VAT number.",
                    field="customer_vat_id",
                )
            )
        elif vat_check.customer_valid is False:
            issues.append(
                Issue(
                    code="customer_vat_id_invalid",
                    severity="error",
                    message="The customer VAT number has an invalid format or checksum.",
                    field="customer_vat_id",
                )
            )

    total = checks.get("total")
    if isinstance(total, TotalCheck) and total.status == "failed":
        code = (
            "invoice_total_mismatch"
            if document.document_type == "invoice"
            else "receipt_total_mismatch"
        )
        issues.append(Issue(code=code, severity="error", message=total.message, field="total"))

    positive_total = checks.get("positive_total")
    if isinstance(positive_total, PositiveTotalCheck) and positive_total.status == "failed":
        issues.append(
            Issue(
                code="total_not_positive",
                severity="error",
                message=positive_total.message,
                field="total",
            )
        )

    date_order = checks.get("date_order")
    if isinstance(date_order, DateOrderCheck) and date_order.status == "failed":
        issues.append(
            Issue(
                code="due_date_before_invoice_date",
                severity="error",
                message=date_order.message,
                field="due_date",
            )
        )

    duplicate = checks.get("duplicate")
    if isinstance(duplicate, DuplicateCheck) and duplicate.status == "failed":
        issues.append(
            Issue(
                code="duplicate_invoice",
                severity="error",
                message=duplicate.message,
                field="invoice_number",
            )
        )

    purchase_order = checks.get("purchase_order")
    if isinstance(purchase_order, PurchaseOrderCheck) and purchase_order.status == "warning":
        issues.append(
            Issue(
                code="purchase_order_missing",
                severity="warning",
                message=purchase_order.message,
                field="purchase_order",
            )
        )

    confidence = checks.get("confidence")
    if isinstance(confidence, ConfidenceCheck) and confidence.status == "warning":
        issues.append(
            Issue(
                code="low_extraction_confidence",
                severity="warning",
                message=confidence.message,
                field=None,
            )
        )

    return issues


def field_label(field_name: str) -> str:
    """Turn a field name into reviewer-facing wording."""
    labels = {
        "supplier_name": "Supplier name",
        "supplier_vat_id": "Supplier VAT number",
        "customer_vat_id": "Customer VAT number",
        "invoice_number": "Invoice number",
        "merchant_name": "Merchant name",
        "purchase_order": "Purchase order",
        "date": "Document date",
        "due_date": "Due date",
        "subtotal": "Subtotal",
        "vat_total": "VAT total",
        "total": "Total",
        "currency": "Currency",
    }
    return labels.get(field_name, field_name.replace("_", " ").capitalize())


def has_blocking_issues(issues: list[Issue]) -> bool:
    """Approval is blocked while any error-severity issue remains open."""
    return any(issue.severity == "error" for issue in issues)
