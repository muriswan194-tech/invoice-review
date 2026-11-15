from dataclasses import dataclass
from datetime import date as Date
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

from app.config import Settings, require_setting
from app.invoices.models import InvoiceDocument, ReceiptDocument


@dataclass(frozen=True)
class PrimaryExtraction:
    """A normalized primary reading plus the confidence Azure reported for it."""

    document: InvoiceDocument | ReceiptDocument
    confidence: float | None


def read_document(
    file_path: Path,
    config: Settings,
    document_type: Literal["invoice", "receipt"] = "invoice",
) -> PrimaryExtraction:
    client = DocumentIntelligenceClient(
        endpoint=require_setting(
            config.document_intelligence_endpoint, "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"
        ),
        credential=AzureKeyCredential(
            require_setting(config.document_intelligence_key, "AZURE_DOCUMENT_INTELLIGENCE_KEY")
        ),
    )

    with file_path.open("rb") as document:
        poller = client.begin_analyze_document(
            model_id=f"prebuilt-{document_type}",
            body=document,
        )
        result = poller.result()

    if not result.documents:
        raise ValueError(f"Azure did not find a {document_type} in this document.")

    analyzed = result.documents[0]
    fields = analyzed.fields
    confidence = getattr(analyzed, "confidence", None)
    if document_type == "receipt":
        return PrimaryExtraction(
            document=ReceiptDocument(
                merchant_name=field_content(fields, "MerchantName"),
                date=field_date(fields, "TransactionDate"),
                subtotal=field_amount(fields, "Subtotal"),
                vat_total=field_amount(fields, "TotalTax"),
                total=field_amount(fields, "Total"),
                currency=field_currency(fields, "Total"),
            ),
            confidence=confidence,
        )

    return PrimaryExtraction(
        document=InvoiceDocument(
            supplier_name=field_content(fields, "VendorName"),
            supplier_gstin=field_content(fields, "VendorTaxId"),
            buyer_gstin=field_content(fields, "CustomerTaxId"),
            invoice_number=field_content(fields, "InvoiceId"),
            purchase_order=field_content(fields, "PurchaseOrder"),
            date=field_date(fields, "InvoiceDate"),
            due_date=field_date(fields, "DueDate"),
            taxable_value=field_amount(fields, "SubTotal"),
            total=field_amount(fields, "InvoiceTotal"),
            currency=field_currency(fields, "InvoiceTotal"),
            cgst=field_amount(fields, "CGST"),
            sgst_or_utgst=field_amount(fields, "SGST"),
            igst=field_amount(fields, "IGST"),
            cess=field_amount(fields, "Cess"),
            place_of_supply=field_content(fields, "PlaceOfSupply"),
            hsn_sac=field_content(fields, "HSNSAC"),
            project_code=field_content(fields, "ProjectCode"),
            cost_centre=field_content(fields, "CostCentre"),
        ),
        confidence=confidence,
    )


def field_content(fields: dict[str, Any], field_name: str) -> str | None:
    field = fields.get(field_name)
    if field is None:
        return None

    return getattr(field, "content", None)


def field_date(fields: dict[str, Any], field_name: str) -> Date | None:
    field = fields.get(field_name)
    if field is None:
        return None

    value = getattr(field, "value_date", None)
    if isinstance(value, Date):
        return value

    content = getattr(field, "content", None)
    if content:
        for date_format in ("%Y-%m-%d", "%d-%m-%Y"):
            try:
                return Date.strptime(content, date_format)
            except ValueError:
                continue

    return None


def field_amount(fields: dict[str, Any], field_name: str) -> Decimal | None:
    field = fields.get(field_name)
    if field is None:
        return None

    currency_value = getattr(field, "value_currency", None)
    amount = getattr(currency_value, "amount", None)
    if amount is not None:
        return Decimal(str(amount))

    return None


def field_currency(fields: dict[str, Any], field_name: str) -> str | None:
    field = fields.get(field_name)
    if field is None:
        return None

    currency_value = getattr(field, "value_currency", None)
    return getattr(currency_value, "currency_code", None)
