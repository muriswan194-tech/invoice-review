from typing import Final

from pydantic import BaseModel


class GstSource(BaseModel):
    id: str
    name: str
    authority: str
    category: str
    purpose: str
    url: str
    related_rules: list[str]
    last_checked: str
    status: str
    limitation: str


GST_SOURCES: Final[list[GstSource]] = [
    GstSource(
        id="cbic-gst",
        name="CBIC GST portal",
        authority="Central Board of Indirect Taxes and Customs",
        category="Acts, rules, circulars, and notifications",
        purpose=(
            "Primary reference for central GST legislation, rules, circulars, and official "
            "clarifications."
        ),
        url="https://cbic-gst.gov.in/",
        related_rules=["invoice_fields", "tax_structure", "reverse_charge_review"],
        last_checked="2026-09-06",
        status="reference_only",
        limitation="Opening this portal does not validate an invoice or determine tax liability.",
    ),
    GstSource(
        id="gst-portal",
        name="GST Portal",
        authority="Goods and Services Tax Network / Government of India",
        category="Taxpayer services and advisories",
        purpose=(
            "Reference for GST services, advisories, help material, and links to GST law resources."
        ),
        url="https://www.gst.gov.in/",
        related_rules=["supplier_gstin", "buyer_gstin", "invoice_fields"],
        last_checked="2026-09-06",
        status="reference_only",
        limitation="The desk does not perform a live GST registration or taxpayer-status lookup.",
    ),
    GstSource(
        id="einvoice-portal",
        name="e-Invoice portal",
        authority="GSTN / National Informatics Centre",
        category="e-Invoice and IRP guidance",
        purpose=(
            "Reference for e-Invoice reporting, IRN, QR-code guidance, schemas, and advisories."
        ),
        url="https://einvoice.gst.gov.in/",
        related_rules=["invoice_fields", "einvoice_reference"],
        last_checked="2026-09-06",
        status="reference_only",
        limitation="The desk does not generate or verify an IRN or e-Invoice QR code.",
    ),
    GstSource(
        id="india-code",
        name="India Code",
        authority="Legislative Department, Government of India",
        category="Acts",
        purpose="Searchable official copies of the CGST and IGST Acts.",
        url="https://indiacode.gov.in/",
        related_rules=["invoice_fields", "tax_structure", "place_of_supply"],
        last_checked="2026-09-06",
        status="reference_only",
        limitation="Legal interpretation remains outside this application's scope.",
    ),
    GstSource(
        id="egazette",
        name="e-Gazette of India",
        authority="Government of India",
        category="Notifications and amendments",
        purpose=(
            "Reference for official notifications, amendments, and published government "
            "instruments."
        ),
        url="https://egazette.nic.in/",
        related_rules=["tax_structure", "reverse_charge_review", "einvoice_reference"],
        last_checked="2026-09-06",
        status="reference_only",
        limitation=(
            "The source must be reviewed by a qualified person before policy changes are made."
        ),
    ),
]


def source_catalog() -> list[GstSource]:
    return GST_SOURCES
