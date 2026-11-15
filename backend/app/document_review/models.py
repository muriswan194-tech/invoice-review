from typing import Literal

from pydantic import BaseModel

class AiExtractionResult(BaseModel):
    document_type: Literal["invoice", "receipt"]
    supplier_name: str | None = None
    supplier_gstin: str | None = None
    buyer_gstin: str | None = None
    supplier_pan: str | None = None
    place_of_supply: str | None = None
    hsn_sac: str | None = None
    invoice_number: str | None = None
    taxable_value: str | None = None
    cgst: str | None = None
    sgst_or_utgst: str | None = None
    igst: str | None = None
    cess: str | None = None
    reverse_charge: bool | None = None
    purchase_order: str | None = None
    project_code: str | None = None
    cost_centre: str | None = None
    invoice_date: str | None = None
    due_date: str | None = None
    merchant_name: str | None = None
    transaction_date: str | None = None
    subtotal: str | None = None
    vat_total: str | None = None
    total: str | None = None
    currency: str | None = None
