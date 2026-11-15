from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas

OUTPUT = (
    Path(__file__).resolve().parents[1]
    / "samples"
    / "generated"
    / "prism-gst-exception.pdf"
)


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    canvas = Canvas(str(OUTPUT), pagesize=A4)
    _, height = A4
    lines = [
        "FICTIONAL DEMO DOCUMENT - NOT A TAX OR LEGAL RECORD",
        "Saffron Build Systems Pvt. Ltd.",
        "GSTIN: 29AABCU9603R1ZJ    PAN: AABCU9603R",
        "GST Invoice: SBS-2026-0042    Date: 01-Aug-2026",
        "Bill to: Prism Projects India Pvt. Ltd.",
        "Buyer GSTIN: 27AAPFU0939F1ZV    Place of supply: Maharashtra (27)",
        "PO: PO-PRJ-204    Project code: MISSING    Cost centre: WEST-OPS",
        "HSN/SAC: 995411",
        "Taxable value: INR 100,000.00",
        "CGST: INR 9,000.00    SGST: INR 9,000.00    IGST: INR 0.00",
        "Cess: INR 0.00",
        "Invoice total: INR 119,000.00",
        "Review note: fictional arithmetic exception and potential TDS review signal.",
    ]
    canvas.setFont("Helvetica-Bold", 14)
    canvas.drawString(54, height - 70, lines[0])
    canvas.setFont("Helvetica", 11)
    y = height - 112
    for line in lines[1:]:
        canvas.drawString(54, y, line)
        y -= 28
    canvas.save()


if __name__ == "__main__":
    main()
