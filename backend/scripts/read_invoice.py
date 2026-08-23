import argparse
from pathlib import Path

from app.config import APP_CONFIG, settings
from app.invoices.validation import (
    check_confidence,
    check_date_order,
    check_positive_total,
    check_purchase_order,
    check_required_fields,
    check_total,
    check_vat_numbers,
)
from app.providers.azure_document_intelligence import read_document


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read one invoice with Azure Document Intelligence."
    )
    parser.add_argument("file", type=Path, help="Path to a PDF or image invoice")
    parser.add_argument(
        "--type",
        choices=("invoice", "receipt"),
        default="invoice",
        help="Document type to send to Azure",
    )
    parser.add_argument(
        "--check-total",
        action="store_true",
        help="Check whether subtotal plus VAT matches the total",
    )
    parser.add_argument(
        "--check-required",
        action="store_true",
        help="Check whether required document information is present",
    )
    parser.add_argument(
        "--check-vat",
        action="store_true",
        help="Check invoice VAT number formats and checksums",
    )
    parser.add_argument(
        "--check-positive-total",
        action="store_true",
        help="Check whether the document total is greater than zero",
    )
    parser.add_argument(
        "--check-date-order",
        action="store_true",
        help="Check whether the due date follows the invoice date",
    )
    parser.add_argument(
        "--check-purchase-order",
        action="store_true",
        help="Check whether a purchase order reference is present",
    )
    parser.add_argument(
        "--check-confidence",
        action="store_true",
        help="Check the primary extraction confidence against the review threshold",
    )
    arguments = parser.parse_args()

    extraction = read_document(arguments.file, settings, arguments.type)
    extracted = extraction.document
    for name, value in extracted.model_dump().items():
        print(f"{name}: {value}")
    print(f"primary_confidence: {extraction.confidence}")

    if arguments.check_total:
        result = check_total(extracted)
        print(f"total_check: {result.status}")
        print(f"difference: {result.difference}")
        print(f"message: {result.message}")

    if arguments.check_required:
        result = check_required_fields(extracted)
        print(f"required_check: {result.status}")
        print(f"missing: {result.missing}")
        print(f"message: {result.message}")

    if arguments.check_vat:
        if arguments.type != "invoice":
            parser.error("--check-vat can only be used with --type invoice")
        result = check_vat_numbers(extracted, APP_CONFIG.customer_vat_id)
        print(f"vat_check: {result.status}")
        print(f"supplier_vat_valid: {result.supplier_valid}")
        print(f"customer_vat_valid: {result.customer_valid}")
        print(f"customer_vat_matches: {result.customer_matches}")
        print(f"message: {result.message}")

    if arguments.check_positive_total:
        result = check_positive_total(extracted)
        print(f"positive_total_check: {result.status}")
        print(f"message: {result.message}")

    if arguments.check_date_order:
        if arguments.type != "invoice":
            parser.error("--check-date-order can only be used with --type invoice")
        result = check_date_order(extracted)
        print(f"date_order_check: {result.status}")
        print(f"message: {result.message}")

    if arguments.check_purchase_order:
        if arguments.type != "invoice":
            parser.error("--check-purchase-order can only be used with --type invoice")
        result = check_purchase_order(extracted)
        print(f"purchase_order_check: {result.status}")
        print(f"message: {result.message}")

    if arguments.check_confidence:
        result = check_confidence(extraction.confidence, APP_CONFIG.low_confidence_threshold)
        print(f"confidence_check: {result.status}")
        print(f"confidence: {result.confidence}")
        print(f"message: {result.message}")


if __name__ == "__main__":
    main()