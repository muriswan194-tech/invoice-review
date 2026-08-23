from typing import Any, Final

SUPPLIER_FIXABLE_CODES: Final[frozenset[str]] = frozenset(
    {
        "vendor_name_required",
        "vendor_vat_id_required",
        "vendor_vat_id_invalid",
        "customer_vat_id_required",
        "customer_vat_id_invalid",
        "customer_vat_id_mismatch",
        "invoice_number_required",
        "invoice_date_required",
        "invoice_total_required",
        "invoice_total_mismatch",
        "receipt_total_mismatch",
        "currency_required",
        "total_not_positive",
        "due_date_before_invoice_date",
        "duplicate_invoice",
        "purchase_order_missing",
    }
)
"""Issue codes a supplier can act on. Blurry scans and low extraction confidence are ours."""


def supplier_fixable_issues(issues: list[Any]) -> list[dict[str, Any]]:
    """Select only the stored issues a supplier could actually correct."""
    return [
        issue
        for issue in issues
        if isinstance(issue, dict) and issue.get("code") in SUPPLIER_FIXABLE_CODES
    ]


def is_eligible(issues: list[Any]) -> bool:
    """A correction request is offered only when the supplier has something to fix."""
    return len(supplier_fixable_issues(issues)) > 0
