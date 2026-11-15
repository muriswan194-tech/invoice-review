from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from app.config import APP_CONFIG
from app.invoices.models import InvoiceDocument

Severity = Literal["error", "warning"]

SCREENING_PROFILE_NAME = "Standard registered-recipient B2B tax invoice"


@dataclass(frozen=True)
class Issue:
    """One GST invoice requirement or consistency finding."""

    code: str
    severity: Severity
    message: str
    field: str | None = None
    evidence: dict[str, str] | None = None
    route: str = "Supplier clarification"
    next_action: str = "Check the source invoice and correct the applicable GST particular."


@dataclass(frozen=True)
class RequiredFieldsCheck:
    status: str
    missing: tuple[str, ...]
    message: str


@dataclass(frozen=True)
class ScreeningProfileCheck:
    """State the scope behind this limited, inspectable invoice screen."""

    status: str
    name: str
    assessments: dict[str, dict[str, str]]
    message: str


@dataclass(frozen=True)
class GstinCheck:
    status: str
    supplier_valid: bool | None
    buyer_valid: bool | None
    message: str


@dataclass(frozen=True)
class TotalCheck:
    status: str
    difference: Decimal | None
    message: str


@dataclass(frozen=True)
class TaxStructureCheck:
    status: str
    message: str


@dataclass(frozen=True)
class ConfidenceCheck:
    status: str
    confidence: float | None
    message: str


def required_field_values(document: InvoiceDocument) -> dict[str, object]:
    """Core particulars in the configured registered-recipient B2B profile."""
    tax_breakup = any(
        value is not None
        for value in (document.cgst, document.sgst_or_utgst, document.igst, document.cess)
    )
    return {
        "supplier_name": document.supplier_name,
        "supplier_gstin": document.supplier_gstin,
        "buyer_gstin": document.buyer_gstin,
        "invoice_number": document.invoice_number,
        "date": document.date,
        "hsn_sac": document.hsn_sac,
        "taxable_value": document.taxable_value,
        "tax_breakup": tax_breakup,
        "total": document.total,
    }


def check_screening_profile(document: InvoiceDocument) -> ScreeningProfileCheck:
    """Make applicability explicit instead of treating every absent value as a failure."""
    assessments: dict[str, dict[str, str]] = {}
    for field_name, value in required_field_values(document).items():
        assessments[field_name] = {
            "applicability": "applicable",
            "state": "present" if value is not None and value != "" else "missing",
        }
    for field_name in ("supplier_gstin", "buyer_gstin"):
        if assessments[field_name]["state"] == "present" and not validate_gstin(
            getattr(document, field_name)
        ):
            assessments[field_name]["state"] = "invalid"

    inter_state = document.igst is not None and document.igst > Decimal("0")
    place_of_supply_state = "not_assessed"
    if inter_state:
        place_of_supply_state = "present" if document.place_of_supply else "missing"
    assessments["place_of_supply"] = {
        "applicability": "applicable" if inter_state else "not_applicable",
        "state": place_of_supply_state,
    }
    assessments["reverse_charge"] = {
        "applicability": "applicable",
        "state": "present" if document.reverse_charge is not None else "missing",
    }
    return ScreeningProfileCheck(
        "passed",
        SCREENING_PROFILE_NAME,
        assessments,
        "Core particulars are screened for a registered-recipient B2B tax invoice. "
        "Place of supply is assessed only when IGST is present.",
    )


def check_required_fields(document: InvoiceDocument) -> RequiredFieldsCheck:
    missing = tuple(
        name
        for name, value in required_field_values(document).items()
        if value is None or value == ""
    )
    if missing:
        return RequiredFieldsCheck(
            "failed", missing, "Applicable GST invoice particulars are missing."
        )
    return RequiredFieldsCheck("passed", (), "Base GST invoice particulars are present.")


def check_gstins(document: InvoiceDocument) -> GstinCheck:
    supplier_valid = validate_gstin(document.supplier_gstin)
    buyer_valid = validate_gstin(document.buyer_gstin)
    if supplier_valid is None or buyer_valid is None:
        return GstinCheck(
            "warning",
            supplier_valid,
            buyer_valid,
            "Both GSTINs are needed for a local format check.",
        )
    if supplier_valid and buyer_valid:
        return GstinCheck(
            "passed",
            True,
            True,
            "Both GSTINs pass local structure and checksum validation; "
            "no government lookup was performed.",
        )
    return GstinCheck(
        "failed",
        supplier_valid,
        buyer_valid,
        "At least one GSTIN failed local structure or checksum validation.",
    )


def check_total(document: InvoiceDocument) -> TotalCheck:
    if document.taxable_value is None or document.total is None:
        return TotalCheck(
            "warning", None, "Taxable value and total are needed for GST arithmetic reconciliation."
        )
    expected = document.taxable_value + sum(
        (
            value or Decimal("0")
            for value in (document.cgst, document.sgst_or_utgst, document.igst, document.cess)
        ),
        Decimal("0"),
    )
    difference = (expected - document.total).copy_abs()
    if difference <= APP_CONFIG.total_tolerance:
        return TotalCheck(
            "passed",
            difference,
            "Taxable value plus available GST components matches the invoice total.",
        )
    return TotalCheck(
        "failed", difference, "Taxable value plus GST components does not match the invoice total."
    )


def check_tax_structure(document: InvoiceDocument) -> TaxStructureCheck:
    intra_state_tax = any(
        value is not None and value > Decimal("0")
        for value in (document.cgst, document.sgst_or_utgst)
    )
    inter_state_tax = document.igst is not None and document.igst > Decimal("0")
    if intra_state_tax and inter_state_tax:
        return TaxStructureCheck(
            "failed", "CGST/SGST and IGST appear together; verify the tax structure."
        )
    if inter_state_tax and not document.place_of_supply:
        return TaxStructureCheck(
            "failed", "Place of supply is required when IGST indicates an inter-State supply."
        )
    if document.reverse_charge is None:
        return TaxStructureCheck(
            "warning",
            "Reverse-charge status was not found; compare the source invoice before relying on it.",
        )
    return TaxStructureCheck(
        "passed", "The available GST tax structure has no immediate local exception."
    )


def check_confidence(confidence: float | None) -> ConfidenceCheck:
    if confidence is None:
        return ConfidenceCheck(
            "warning", None, "Primary extraction did not report a confidence score."
        )
    if confidence >= APP_CONFIG.low_confidence_threshold:
        return ConfidenceCheck(
            "passed", confidence, "Primary extraction confidence is sufficient for review."
        )
    return ConfidenceCheck(
        "warning",
        confidence,
        "Primary extraction confidence is low; compare fields with the source document.",
    )


def validate_gstin(value: str | None) -> bool | None:
    if not value:
        return None
    normalized = "".join(character for character in value if character.isalnum()).upper()
    if len(normalized) != 15 or not normalized[:2].isdigit() or normalized[13] != "Z":
        return False
    if not (
        normalized[2:7].isalpha() and normalized[7:11].isdigit() and normalized[11:13].isalnum()
    ):
        return False
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    try:
        checksum = 0
        for index, character in enumerate(normalized[:14]):
            product = alphabet.index(character) * (1 if index % 2 == 0 else 2)
            checksum += product // 36 + product % 36
        return alphabet[(36 - checksum % 36) % 36] == normalized[-1]
    except ValueError:
        return False


def collect_issues(document: InvoiceDocument, checks: dict[str, object]) -> list[Issue]:
    issues: list[Issue] = []
    required = checks["required_particulars"]
    if isinstance(required, RequiredFieldsCheck):
        for field_name in required.missing:
            issues.append(
                Issue(
                    f"{field_name}_required",
                    "error",
                    f"{field_label(field_name)} is required for this GST invoice review.",
                    field_name,
                )
            )
    gstins = checks["gstins"]
    if isinstance(gstins, GstinCheck):
        if gstins.supplier_valid is False:
            issues.append(
                Issue(
                    "supplier_gstin_invalid",
                    "error",
                    "Supplier GSTIN failed local structure or checksum validation.",
                    "supplier_gstin",
                )
            )
        if gstins.buyer_valid is False:
            issues.append(
                Issue(
                    "buyer_gstin_invalid",
                    "error",
                    "Recipient GSTIN failed local structure or checksum validation.",
                    "buyer_gstin",
                )
            )
    total = checks["gst_arithmetic"]
    if isinstance(total, TotalCheck) and total.status == "failed":
        issues.append(Issue("invoice_total_mismatch", "error", total.message, "total"))
    tax_structure = checks["tax_structure"]
    if isinstance(tax_structure, TaxStructureCheck) and tax_structure.status == "failed":
        issues.append(
            Issue("tax_structure_inconsistent", "error", tax_structure.message, "place_of_supply")
        )
    return issues


def field_label(field_name: str) -> str:
    return {
        "supplier_name": "Supplier name",
        "supplier_gstin": "Supplier GSTIN",
        "buyer_gstin": "Recipient GSTIN",
        "invoice_number": "Invoice number",
        "date": "Invoice date",
        "hsn_sac": "HSN/SAC",
        "taxable_value": "Taxable value",
        "tax_breakup": "GST tax breakup",
        "total": "Invoice total",
    }.get(field_name, field_name.replace("_", " ").capitalize())


def run_checks(document: InvoiceDocument, primary_confidence: float | None) -> dict[str, object]:
    return {
        "screening_profile": check_screening_profile(document),
        "required_particulars": check_required_fields(document),
        "gstins": check_gstins(document),
        "gst_arithmetic": check_total(document),
        "tax_structure": check_tax_structure(document),
        "extraction_confidence": check_confidence(primary_confidence),
    }
