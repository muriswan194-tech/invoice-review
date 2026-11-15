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
    supplier_gstin: str | None = None
    buyer_gstin: str | None = None
    supplier_pan: str | None = None
    place_of_supply: str | None = None
    hsn_sac: str | None = None
    invoice_number: str | None = None
    taxable_value: Decimal | None = None
    cgst: Decimal | None = None
    sgst_or_utgst: Decimal | None = None
    igst: Decimal | None = None
    cess: Decimal | None = None
    reverse_charge: bool | None = None
    purchase_order: str | None = None
    project_code: str | None = None
    cost_centre: str | None = None
    due_date: Date | None = None


class ReceiptDocument(FinancialDocument):
    document_type: Literal["receipt"] = "receipt"
    merchant_name: str | None = None


def invoice_key_parts(document: InvoiceDocument) -> tuple[str | None, str | None]:
    """Derive the supplier GSTIN and invoice-number identity for duplicates."""
    if not document.supplier_gstin or not document.invoice_number:
        return None, None

    return (
        document.supplier_gstin.strip().casefold(),
        document.invoice_number.strip().casefold(),
    )
