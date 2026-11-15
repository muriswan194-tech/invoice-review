# GST reference and test corpus

This folder keeps public reference material and fictional invoice examples separate from the
application's generated `samples/` corpus. It is for manual exploration and controlled evaluation;
it is not a source of executable tax rules.

## Layout

```text
gst/
├── reference/                         # Official guidance used to understand invoice fields
├── layout-samples/                    # Public template layouts for OCR and visual review
├── test-invoices/
│   └── missing-fields/                # Deliberately incomplete invoice examples
└── manifest.json                      # Purpose and expected review focus per file
```

## How to use the material

- Read `reference/` before proposing a new GST-screening rule. A qualified accountant or CA must
  review and approve any rule before it becomes executable backend behaviour.
- Use `layout-samples/` to test whether document extraction copes with different table, font, and
  visual layouts. These are not proof of GST compliance.
- Use `test-invoices/missing-fields/` as exception-screening examples. They intentionally lack
  fields that the desk requires for its scoped Prism workflow, such as GSTIN and project data.
- Add newly created, entirely fictional PDFs under a specific scenario folder, for example
  `test-invoices/valid/`, `test-invoices/arithmetic-errors/`, or `test-invoices/duplicates/`.
- Update `manifest.json` whenever a document is added, moved, or removed.

## Safe use

Do not add real customer invoices, personal data, supplier bank details, credentials, or tax filings
to this repository. Before redistributing third-party templates, confirm their licence and terms at
the listed source.

## Important limitation

The desk performs evidence-based exception screening. It does not perform live GST registration
verification, provide tax/legal advice, determine input-tax-credit eligibility, calculate final TDS,
or make payment decisions.
