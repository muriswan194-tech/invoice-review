# ruff: noqa: E501
import argparse
import json
import sys
from collections import Counter
from datetime import date as Date
from decimal import Decimal, InvalidOperation
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import APP_CONFIG, settings
from app.invoices.models import InvoiceDocument, ReceiptDocument
from app.invoices.service import run_checks
from app.invoices.validation import collect_issues


def document_from_manifest(
    expected: dict[str, object],
    doc_type: str,
) -> InvoiceDocument | ReceiptDocument:
    """Build a typed document from the manifest's expected values, used for --offline checks."""

    def parse_date(value: object) -> Date | None:
        if not isinstance(value, str):
            return None
        try:
            return Date.fromisoformat(value)
        except ValueError:
            return None

    def parse_decimal(value: object) -> Decimal | None:
        if not isinstance(value, str):
            return None
        try:
            return Decimal(value)
        except (InvalidOperation, ValueError):
            return None

    if doc_type == "receipt":
        return ReceiptDocument(
            merchant_name=expected.get("vendor_name"),  # type: ignore[arg-type]
            date=parse_date(expected.get("invoice_date")),
            subtotal=parse_decimal(expected.get("subtotal")),
            vat_total=parse_decimal(expected.get("total_tax")),
            total=parse_decimal(expected.get("invoice_total")),
            currency=expected.get("currency"),  # type: ignore[arg-type]
        )

    return InvoiceDocument(
        supplier_name=expected.get("vendor_name"),  # type: ignore[arg-type]
        supplier_vat_id=expected.get("vendor_vat_id"),  # type: ignore[arg-type]
        customer_vat_id=expected.get("customer_vat_id"),  # type: ignore[arg-type]
        invoice_number=expected.get("invoice_number"),  # type: ignore[arg-type]
        purchase_order=expected.get("purchase_order"),  # type: ignore[arg-type]
        date=parse_date(expected.get("invoice_date")),
        due_date=parse_date(expected.get("due_date")),
        subtotal=parse_decimal(expected.get("subtotal")),
        vat_total=parse_decimal(expected.get("total_tax")),
        total=parse_decimal(expected.get("invoice_total")),
        currency=expected.get("currency"),  # type: ignore[arg-type]
    )


def live_document(
    file_path: Path,
    doc_type: str,
) -> tuple[InvoiceDocument | ReceiptDocument, float | None]:
    """Read one document with Azure Document Intelligence, returning the document and confidence."""
    from app.providers.azure_document_intelligence import read_document

    extraction = read_document(file_path, settings, doc_type)  # type: ignore[arg-type]
    return extraction.document, extraction.confidence


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Score the pipeline against samples/manifest.json.",
    )
    parser.add_argument("--manifest", type=Path, default=Path("samples/manifest.json"))
    parser.add_argument("--samples-dir", type=Path, default=Path("samples/generated"))
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Build documents from the manifest's expected values instead of calling Azure.",
    )
    arguments = parser.parse_args()

    project_root = Path(__file__).resolve().parents[2]
    manifest_path = (
        arguments.manifest
        if arguments.manifest.is_absolute()
        else project_root / arguments.manifest
    )
    samples_dir = (
        arguments.samples_dir
        if arguments.samples_dir.is_absolute()
        else project_root / arguments.samples_dir
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, list):
        raise SystemExit("The manifest must be a list of entries.")

    seen: set[str] = set()
    passed = 0
    failed = 0
    counter: Counter[str] = Counter()

    print(f"Manifest: {manifest_path}")
    print(f"Samples:  {samples_dir}  (offline={arguments.offline})")
    print(f"Policy:   customer VAT {APP_CONFIG.customer_vat_id}, confidence {APP_CONFIG.low_confidence_threshold}")
    print()

    header = f"{'File':<26} {'Expected':<30} {'Found':<30} {'Result'}"
    print(header)
    print("-" * len(header))

    for entry in manifest:
        filename = entry["filename"]
        doc_type = entry.get("document_type", "invoice")
        expected_codes = sorted(entry.get("expected_issue_codes") or [])
        file_path = samples_dir / filename

        if arguments.offline:
            document = document_from_manifest(entry["expected"], doc_type)
            confidence: float | None = 0.95
        else:
            if not file_path.exists():
                print(f"{filename:<26} {'(missing file)':<30} {'-':<30} MISSING")
                failed += 1
                continue
            try:
                document, confidence = live_document(file_path, doc_type)
            except Exception as error:
                print(f"{filename:<26} {','.join(expected_codes):<30} {'error: ' + str(error)[:24]:<30} ERROR")
                failed += 1
                continue

        # Duplicate is stateful: an identity seen earlier in this run counts as already_seen.
        identity: str | None = None
        if isinstance(document, InvoiceDocument) and document.supplier_name and document.invoice_number:
            identity = f"{document.supplier_name.strip().casefold()}::{document.invoice_number.strip().casefold()}"
        already_seen = identity in seen if identity is not None else False

        checks = run_checks(document, already_seen, confidence)
        issues = collect_issues(document, checks)
        found_codes = sorted(issue.code for issue in issues)
        counter.update(found_codes)

        ok = found_codes == expected_codes
        result = "OK" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
        if identity is not None and identity not in seen:
            seen.add(identity)

        print(f"{filename:<26} {','.join(expected_codes) or '-':<30} {','.join(found_codes) or '-':<30} {result}")

    print()
    print(f"Score: {passed}/{passed + failed} passed")
    if counter:
        print("Issue counts:", ", ".join(f"{code}={count}" for code, count in sorted(counter.items())))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
