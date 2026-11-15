# GST Invoice Requirements Reviewer

A small local application for reviewing supplier invoices against a defined GST
invoice-screening profile. It helps an accountant find missing particulars and
visible inconsistencies, then compare the extracted result with the original
document.

Prism is fictional demo context only. The application does not assume a company
name, GSTIN, project code, purchase order, GL chart, TDS workflow, or approval
policy.

## What it does

- Accepts one PDF, PNG, or JPEG invoice up to 4 MB.
- Uses Azure AI Document Intelligence `prebuilt-invoice` as the primary extractor
  and invoice gate.
- Calls Azure OpenAI only if primary extraction misses core GST fields or the full
  GST tax breakup. AI values fill gaps only; they never replace a conflicting
  primary value.
- Runs local, deterministic checks for missing configured particulars, GSTIN
  structure/checksum, GST arithmetic, available tax structure, and extraction
  confidence.
- Shows field provenance, the original invoice, a downloadable missing-data
  checklist, local review history, and a fictional offline demo.

## What it does not do

- It does not verify an active GST registration with a government service.
- It does not provide tax or legal advice, determine input-tax-credit eligibility,
  calculate TDS, select GL accounts, detect duplicate payments, or approve payment.
- It does not treat internal company controls as GST invoice requirements.
- It is a local, single-user teaching application, not a hosted production system.

## Review flow

```text
Upload invoice
→ Document Intelligence extraction
→ optional OpenAI gap-fill only when needed
→ deterministic GST screening
→ human comparison with the source and supplier follow-up
```

The configured screening profile covers supplier and recipient GSTINs, invoice
number and date, HSN/SAC, taxable value, GST breakup, total, conditional
place-of-supply checks, local GSTIN validation, and arithmetic reconciliation.
It is a documented screening profile, not a claim that every field is universally
applicable in every GST scenario.

