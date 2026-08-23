from datetime import date as Date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class FinancialDocument(BaseModel):
    document_type: Literal["invoice", "receipt"]
    date: Date | None = None
    subtotal: Decimal | None = None
    vat_total: Decimal | None = None
    total: Decimal | None = None
    currency: str | None = None


class InvoiceDocument(FinancialDocument):
    document_type: Literal["invoice"] = "invoice"
    supplier_name: str | None = None
    supplier_vat_id: str | None = None
    customer_vat_id: str | None = None
    invoice_number: str | None = None
    purchase_order: str | None = None
    due_date: Date | None = None


class ReceiptDocument(FinancialDocument):
    document_type: Literal["receipt"] = "receipt"
    merchant_name: str | None = None


def invoice_key_parts(document: InvoiceDocument) -> tuple[str | None, str | None]:
    """Derive the supplier and invoice-number identity used for duplicate detection."""
    if not document.supplier_name or not document.invoice_number:
        return None, None

    return (
        document.supplier_name.strip().casefold(),
        document.invoice_number.strip().casefold(),
    )