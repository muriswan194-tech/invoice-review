# Build-along guide

## Slice: GST-only invoice requirements reviewer

### Outcome

The active review flow is now a generic GST invoice requirements reviewer. It checks only applicable GST invoice particulars, local GSTIN structure/checksum, tax arithmetic, and available tax structure. Prism remains fictional demo context rather than a hard-coded business policy.

### Why

Project codes, purchase orders, GL accounts, duplicate-payment controls, TDS, payment decisions, and a specific buyer identity are valuable organisation controls, but they are not GST invoice requirements. Presenting them as GST failures obscures the actual tax-invoice review.

### Commands

```bash
cd backend
uv run --locked --no-sync ruff check app/invoices/validation.py app/invoices/service.py app/invoices/routes.py app/config.py
uv run --locked --no-sync python -m compileall -q app

cd ../frontend
pnpm exec tsc -b --pretty false
pnpm lint
pnpm build
```

### Observable result

The upload flow accepts invoices only. Processing ends after classification, extraction, and GST validation. The review page presents invoice particulars, GST requirements, GST arithmetic, tax structure, and extraction confidence beside the original source. It does not show GL selection, approval/rejection, project, PO, cost centre, TDS, duplicate, or company-policy findings.

### Checkpoint

- [x] GST requirements and internal accounting controls are no longer mixed in the active review flow.
- [x] No fixed company GSTIN is used to validate a recipient.
- [x] GL suggestion, advisor, duplicate, project, PO, cost-centre, TDS, and decision stages do not run for a review.
- [x] Extraction confidence is visible evidence, not a GST exception.
- [x] Missing particulars, verification items, and the concise check summary use the same white-glass visual language without weakening their status cues.
- [x] On desktop, the review uses a wide two-pane workspace so the source document and extracted fields can be compared without wasting the available screen width.
- [x] The global workspace menu stays at the far right of the desktop viewport rather than leaving the outer navigation space unused.
- [x] The landing screen prioritises starting a review; saved reviews remain available from the workspace menu.
- [x] The source pane identifies the uploaded invoice and provides compact download and open controls before the embedded document viewer.
- [x] The review now leads with the GST outcome and next actions, then provides a two-pane source-and-correction workspace without a duplicate invoice-particulars table.
- [x] Live invoice reviews no longer make a separate Azure OpenAI classification call; the invoice-only upload workflow uses Document Intelligence as its document-type gate.
- [x] The remaining Azure OpenAI extraction is now conditional: a complete primary extraction proceeds directly to local GST validation, while missing core fields or a missing GST tax breakup trigger the fallback.
- [x] The README and active code surface now describe only the GST invoice reviewer; inactive GL, advisor/chat, correction-email, batch-review, and internal-policy modules have been removed.
- [x] The GST screen now declares its registered-recipient B2B profile and distinguishes applicable core particulars, conditional place of supply, reverse-charge review, missing values, locally invalid GSTINs, and fields outside this screen's scope.

## Slice: India GST Exception Desk adaptation

### Outcome

The application is now branded as GST Invoice Exception Desk for Prism Projects India Pvt. Ltd. Invoice reviews use typed GSTIN, PAN, place-of-supply, HSN/SAC, INR tax, project, and cost-centre fields. Deterministic rules surface GST arithmetic, tax-structure, project-reference, duplicate, and potential TDS-review signals with a human route and next action.

### Why

The portfolio version demonstrates a realistic Indian finance workflow without claiming tax advice or autonomous compliance. AI extracts and explains evidence; local rules expose inspectable exceptions; an accountant makes the final decision.

### Commands

```bash
uv run --locked --no-sync python scripts/generate_prism_demo.py
uv run --locked --no-sync ruff check app scripts

cd ../frontend
pnpm exec tsc -b --pretty false
pnpm lint
pnpm build
```

### Observable result

`Open fictional GST demo` opens a fully offline INR invoice for Saffron Build Systems Pvt. Ltd. and shows a missing project code, an invoice-total mismatch, and a potential TDS review signal. Findings route to Project manager, Supplier clarification, or Accountant / TDS review. No Azure credentials are needed until a live upload, advisor chat, or AI email draft is invoked.

### Checkpoint

- [x] Product identity and UI copy use GST Invoice Exception Desk and Prism Projects India Pvt. Ltd.
- [x] GST invoice fields are typed, editable, and provider-independent.
- [x] GSTIN checks are local structure/checksum checks only.
- [x] Findings contain severity, evidence, route, and next action.
- [x] Offline demo works without Azure environment variables.

## Slice: Excel batch exception review

### Outcome

The desk now has a separate `.xlsx` workflow for one-sheet invoice batches. It maps common invoice headers, evaluates every row with the existing GST rules, and presents row-level status, exception codes, route, and next action in a table.

### Why

An Excel workbook contains many invoice records rather than one document. Keeping it separate from the PDF/image workflow preserves the detailed document review while adding a useful batch-exception path without duplicating GST policy logic.

### Commands

```bash
uv run --locked --no-sync python scripts/generate_prism_batch_demo.py
uv run --locked --no-sync ruff check app scripts

cd ../frontend
pnpm exec tsc -b --pretty false
pnpm lint
pnpm build
```

### Observable result

The `Review Excel batch` action opens a fictional four-row INR workbook. Rows show GST arithmetic, mixed tax structure, missing project code, supplier GSTIN, and duplicate exceptions with routes to Supplier clarification, Project manager, Accountant / TDS review, or AP reviewer.

### Checkpoint

- [x] `.xlsx` upload is separate from PDF/image review.
- [x] The first worksheet is parsed without adding a dependency.
- [x] Common invoice headers are normalized into typed row records.
- [x] Existing GST checks are reused for every row.
- [x] The batch table makes risk, route, and next action visible.

## Slice: Editable GST rule catalogue

### Outcome

The workspace menu now opens an editable GST rule catalogue with policy version, rule IDs, severity, fields, logic, source reference, limitation, route, and next action. Edits persist in the current browser through local storage.

### Why

Reviewers and portfolio evaluators can inspect the policy vocabulary without reading the code. The catalogue is deliberately metadata-only: editing it does not silently change executable validation rules.

### Checkpoint

- [x] Rule metadata is editable and resettable.
- [x] The policy version is visible.
- [x] Every entry states its source and limitation.
- [x] The screen warns that executable policy changes require qualified review.

## Slice: Editable company policy catalogue

### Outcome

The workspace now includes a separate Company policy catalogue for Prism's internal controls: project references, duplicate handling, supplier clarification, TDS-review routing, and the human approval gate.

### Why

Internal workflow policy should not be mixed with official GST references. The catalogue lets a company maintain policy metadata, ownership, routing, and limitations in one place.

### Checkpoint

- [x] Company policies are separate from GST rules and official sources.
- [x] Policy metadata is editable and resettable in the current browser.
- [x] Each policy shows an owner, route, next action, and limitation.
- [x] The UI explains that executable backend behavior requires approved promotion.

## Slice: Company policy document library

### Outcome

The Company policy catalogue now accepts PDF and DOCX policy documents. Files are stored locally, metadata is persisted in SQLite, and uploaded documents can be opened from the catalogue for human review.

### Why

Policy metadata explains what the company expects; approved documents provide the evidence behind those expectations. Keeping documents separate from GST source links makes internal policy auditable without presenting it as law.

### Checkpoint

- [x] PDF and DOCX policy documents can be uploaded.
- [x] File metadata is persisted in the existing SQLite repository.
- [x] Uploaded documents appear in the Company policy catalogue.
- [x] Documents can be opened without invoking Azure or automatically changing executable policy.

## Slice: GST reference and test-corpus organisation

### Outcome

Public GST reference PDFs, public layout templates, and fictional invoice examples are now separated
under `gst/`. A `README.md` explains the intended use and limitations of each group, while
`gst/manifest.json` records sources, scenario purpose, and future controlled-test cases.

### Why

A believable document-review demo needs varied layouts and known exception scenarios, but downloaded
examples must not be mistaken for authoritative tax policy or valid client data. Keeping references,
layouts, and deliberately incomplete invoice examples separate makes the evaluation material easier
to inspect and safer to extend.

### Checkpoint

- [x] Official references are separate from upload test material.
- [x] Public layout templates are labelled as OCR/visual exploration material, not compliance proof.
- [x] Downloaded fictional invoices are labelled as missing-field exception scenarios.
- [x] The corpus manifest records source URLs, limitations, and planned test scenarios.

## Slice: Missing-data checklist

### Outcome

The GST and policy exceptions heading now contains a local-only `Download missing-data checklist`
action. It creates a text file that lists only policy issues caused by absent source data, together
with the relevant route and next action.

### Why

Reviewers often need to ask a supplier, project manager, or accountant for several missing details.
A compact checklist prevents them from manually copying every finding while avoiding an unnecessary
full export of invoice data.

### Checkpoint

- [x] The action is beside the GST and policy exceptions summary.
- [x] The file is generated in the browser and is not sent to an external service.
- [x] Each checklist item includes the missing field, why it matters, route, and next action.
- [x] Invalid or mismatched values are excluded; the checklist is limited to absent source data.

The complete guided build lives at <https://learn.datalumina.com/docs/invoice-review>. This local guide records the first checkpoint represented by the `main` branch.

## Starter outcome

The repository installs reproducibly, starts a minimal FastAPI service and React interface, and includes the business brief plus fictional source documents.

## Why this boundary exists

The starter removes the completed workflow while preserving every prerequisite needed to build it. You begin with the user, the source documents, and explicit service boundaries instead of reverse-engineering a finished application.

## Commands

```bash
cd backend
uv sync --locked

cd ../frontend
pnpm install --frozen-lockfile

cd ..
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
./scripts/dev.sh --check
./scripts/dev.sh
```

## Important locations

- `docs/client-brief.md`: the recurring finance problem and definition of done
- `docs/architecture.md`: the intended boundaries and data flow
- `samples/`: the fictional evaluation corpus and manifest
- `backend/app/main.py`: the initial API boundary
- `frontend/src/App.tsx`: the initial interface boundary

## What you should observe

- `GET http://localhost:8000/health` returns `{"status":"ok"}`.
- `http://localhost:5173` shows the Invoice Review starter screen.
- No Azure request occurs at this checkpoint.

## Slice: coded policy issues

### Outcome

Every deterministic check now also produces a coded issue with a severity, so the pipeline speaks the same
vocabulary as `samples/manifest.json`. Approval is blocked while any error-severity issue is open, and a
reviewer can delete a stored review to demonstrate the same document again.

### Why

The corpus manifest records `expected_issue_codes` per document. Free-text check messages could not be
compared against it, so there was no way to score the pipeline. Codes turn "make review work" into a
checkable target, and severity is what separates a blocking error from an advisory warning.

### What changed

- `app/config.py` gained `AppConfig` for fixed company policy: own VAT number, total tolerance, and the
  0.80 confidence threshold. These are policy, not environment values.
- `app/invoices/models.py` gained `purchase_order` and now owns `invoice_key_parts`, so validation no longer
  imports the repository.
- `app/invoices/validation.py` gained `Issue`, `collect_issues`, `has_blocking_issues`, and three new checks:
  `check_purchase_order`, `check_confidence`, and customer-VAT comparison inside `check_vat_numbers`.
  `check_duplicate` is now pure and receives an `already_seen` boolean instead of the repository.
- `app/invoices/repository.py` gained `remember_invoice` and `delete_invoice`; persistence moved out of the
  rules and into the caller.
- `app/providers/azure_document_intelligence.py` returns `PrimaryExtraction`, adding the confidence Azure
  reported so the low-confidence warning has evidence.
- `app/invoices/service.py` orchestrates lookup, checks, issue collection, and persistence, and returns
  `issues`, `can_approve`, and `primary_confidence`.
- The frontend renders the coded issue list, disables Approve while errors remain, and can delete history.

### Commands

```bash
cd backend
uv run --locked --no-sync ruff check app scripts

cd ../frontend
pnpm exec tsc -b --pretty false
pnpm lint
pnpm build
```

### Observable result

Policy was exercised against the manifest scenarios with in-memory documents:

| Scenario | Codes produced | Approval |
| --- | --- | --- |
| `01-en-happy-classic` | none | allowed |
| `05-nl-missing-vendor-vat` | `vendor_vat_id_required` | blocked |
| `06-de-invalid-vendor-vat` | `vendor_vat_id_invalid` | blocked |
| `07-fr-wrong-customer-vat` | `customer_vat_id_mismatch` | blocked |
| `08-en-total-mismatch` | `invoice_total_mismatch` | blocked |
| `09-nl-missing-po` | `purchase_order_missing` | allowed |
| `10-de-duplicate` | `duplicate_invoice` | blocked |
| low primary confidence | `low_extraction_confidence` | allowed |
| `13-nl-fuel-receipt` | none | allowed |

### Checkpoint

- [x] Deterministic checks produce coded issues with error or warning severity.
- [x] Missing purchase order reports `purchase_order_missing` as a warning.
- [x] Primary confidence below 0.80 reports `low_extraction_confidence` as a warning.
- [x] A customer VAT number that does not match the company's reports `customer_vat_id_mismatch`.
- [x] Duplicate detection is a pure rule; the service owns persistence.
- [x] Approval is blocked while any error-severity issue is open.
- [x] A stored review can be deleted so the same document can be demonstrated again.
- [x] Backend lint passes.
- [x] Frontend type-check, lint, and production build pass.

## Slice: reviewer corrections and gated approval

### Outcome

A review now lives in the database as a full record, a reviewer can correct any extracted field, corrected
fields are marked `human`, policy re-runs immediately, and the server itself refuses to approve a document
that still has open errors or no selected GL account.

### Why

Approval gating enforced only by a disabled button is decoration. The rule belongs on the server, next to the
issues it depends on. Storing the whole review, rather than only the invoice identity, is what makes both
correction and re-inspection possible: the document, its field sources, its checks, and its issues all need a
home before a reviewer can change one value and see the consequences.

### What changed

- `app/config.py` now also owns storage paths, the database URL, and the 4 MB upload limit.
- `app/invoices/repository.py` replaces the identity-only `invoices` table with a `documents` table that keeps
  each stage in its own JSON column, plus `apply_corrections`, `update_account`, and `delete_review`.
- `app/invoices/service.py` gained `apply_corrections`, `decide_review`, `select_account`, and `review_payload`,
  and raises `ReviewError` for workflow refusals. Editable fields are an explicit allowlist per document type.
- `app/invoices/routes.py` now exposes `GET/PUT /invoices/{id}`, `PUT /invoices/{id}/accounting`,
  `POST /invoices/{id}/decision`, and `DELETE /invoices/{id}`, translating `ReviewError` into 404 or 409.
- `app/accounting/` gained `is_valid_account`, `catalog_entries`, and a `GET /accounting/gl-accounts` route.
- The frontend split into `components/FieldEditor.tsx`, `AccountSelector.tsx`, and `ReviewFindings.tsx`, with
  shared field metadata in `lib/fields.ts`. History rows can now be reopened or deleted.

### Commands

```bash
cd backend
uv run --locked --no-sync ruff check app scripts

cd ../frontend
pnpm exec tsc -b --pretty false
pnpm lint
pnpm build
```

### Observable result

A stored review of `05-nl-missing-vendor-vat.pdf` was walked through the whole workflow:

| Step | Result |
| --- | --- |
| Stored review | `vendor_vat_id_required`, approval refused |
| Approve | refused: errors remain open |
| Correct `supplier_vat_id` | issue cleared, field source becomes `human` |
| Approve | refused: no GL account selected |
| Select account `6110` | approval now allowed |
| Approve | status becomes `approved` |
| Edit after decision | refused: a decided document cannot be edited |
| Delete | review and stored file removed |

The API surface is now `POST /invoices/upload`, `GET /invoices/history`, `GET/PUT/DELETE /invoices/{id}`,
`PUT /invoices/{id}/accounting`, `POST /invoices/{id}/decision`, `GET /accounting/gl-accounts`, and `GET /health`.

### Checkpoint

- [x] A review is stored with its document, field sources, checks, and issues.
- [x] A reviewer can correct any editable field, and the corrected field is marked `human`.
- [x] Policy re-runs after a correction, so a resolved error disappears.
- [x] The server refuses approval while error-severity issues remain open.
- [x] The server refuses approval until a valid GL account is selected.
- [x] A decided document can no longer be edited or re-categorized.
- [x] Deleting a review also removes its stored upload.
- [x] Backend lint passes.
- [x] Frontend type-check, lint, and production build pass.

## Slice: supplier correction requests

### Outcome

The app now offers a correction request only when the supplier actually has something to fix, and Azure OpenAI
words the request instead of a fixed template. The draft appears with Copy and Close; the app never sends mail.

### Why

Previously any rejection produced a template email, so the app would happily prepare a "please correct this"
note when nothing was the supplier's fault. Eligibility is a business decision, so it belongs in code as a
fixed set of issue codes, not in model judgment. Wording a polite paragraph is the part a model is good at,
so that is the only part it owns.

### What changed

- `app/correction_email/eligibility.py` holds `SUPPLIER_FIXABLE_CODES` plus `supplier_fixable_issues` and
  `is_eligible`. Codes such as `low_extraction_confidence` are deliberately absent: a poor scan is ours, not
  the supplier's.
- `app/correction_email/models.py` defines the provider-independent `CorrectionEmailContext` and
  `CorrectionEmailDraft`.
- `app/providers/azure_openai.py` gained `draft_correction_email`, using strict structured output for a
  subject and body, and instructed not to invent amounts, deadlines, or contact details.
- `app/invoices/service.py` gained `request_correction_email`, which refuses when nothing is supplier-fixable
  and passes only the matched issue messages to the model. `review_payload` now reports
  `can_request_correction`.
- `app/invoices/routes.py` exposes `POST /invoices/{id}/correction-email`.
- The frontend gained `components/CorrectionEmailDialog.tsx` with Copy and Close, and both the draft button
  and the Request correction decision are disabled when nothing is the supplier's to fix.

### Commands

```bash
cd backend
uv run --locked --no-sync ruff check app scripts

cd ../frontend
pnpm exec tsc -b --pretty false
pnpm lint
pnpm build
```

### Observable result

Eligibility was exercised against the manifest issue codes:

| Document state | Eligible | Issues sent to the model |
| --- | --- | --- |
| Clean invoice | no | none; the request is refused |
| Low extraction confidence only | no | none; a poor scan is ours to handle |
| Missing supplier VAT | yes | `vendor_vat_id_required` |
| Invalid supplier VAT | yes | `vendor_vat_id_invalid` |
| Wrong customer VAT | yes | `customer_vat_id_mismatch` |
| Total mismatch | yes | `invoice_total_mismatch` |
| Missing purchase order | yes | `purchase_order_missing` |
| Duplicate invoice | yes | `duplicate_invoice` |
| Low confidence plus total mismatch | yes | only `invoice_total_mismatch` |

### Checkpoint

- [x] A fixed code list, not the model, decides whether a correction request is possible.
- [x] Issues that are not the supplier's fault never reach the drafting model.
- [x] The draft endpoint refuses when nothing is supplier-fixable.
- [x] Azure OpenAI returns a structured subject and body.
- [x] The reviewer can copy the draft and close it; the app never sends mail.
- [x] Backend lint passes.
- [x] Frontend type-check, lint, and production build pass.

## Slice: local run and offline evaluation

### Outcome

The project can now be started with one command and checked against the corpus without spending Azure
credits. `scripts/dev.sh` runs the backend and frontend together, `backend/scripts/evaluate_corpus.py`
scores the deterministic policy against the manifest, and the rule-violating `app/test.py` is gone.

### Why

`./scripts/dev.sh` is the command the starter promised but never shipped, and an offline score is the
fastest way to catch a policy regression. Running the manifest against in-memory documents derived from its
`expected` values proves the rules themselves are correct; a later live run with real Azure extraction then
tests only the extraction, not the policy.

### What changed

- `scripts/dev.sh` starts `uvicorn app.main:app` and `pnpm dev` together and stops both on exit.
- `backend/scripts/evaluate_corpus.py` loads `samples/manifest.json`, builds each expected document,
  runs `run_checks` and `collect_issues`, and compares the found codes with `expected_issue_codes`. The
  `--offline` flag avoids any Azure call; without it the script reads each file with `read_document`.
- `backend/app/test.py` was removed: it called `os.environ` and `load_dotenv` directly, bypassing
  `app/config.py`, and imported `dotenv`, which is not a pinned dependency.

### Commands

```bash
cd backend
uv run --locked --no-sync ruff check app scripts
uv run --locked --no-sync python scripts/evaluate_corpus.py --offline

cd ../frontend
pnpm exec tsc -b --pretty false
pnpm lint
pnpm build

# from the project root
./scripts/dev.sh
# then open http://localhost:5173 and http://localhost:8000/docs
```

### Observable result

Offline evaluation against the 13-document corpus:

```
01-en-happy-classic.pdf       -                           -                           OK
02-nl-happy-compact.pdf       -                           -                           OK
03-de-happy-modern.pdf        -                           -                           OK
04-fr-happy-classic.pdf       -                           -                           OK
05-nl-missing-vendor-vat.pdf  vendor_vat_id_required      vendor_vat_id_required      OK
06-de-invalid-vendor-vat.pdf  vendor_vat_id_invalid       vendor_vat_id_invalid       OK
07-fr-wrong-customer-vat.pdf  customer_vat_id_mismatch    customer_vat_id_mismatch    OK
08-en-total-mismatch.pdf      invoice_total_mismatch      invoice_total_mismatch      OK
09-nl-missing-po.pdf          purchase_order_missing      purchase_order_missing      OK
10-de-duplicate.pdf           duplicate_invoice           duplicate_invoice           OK
11-fr-scan-quality.png        -                           -                           OK
12-en-two-page.pdf            -                           -                           OK
13-nl-fuel-receipt.png        -                           -                           OK
Score: 13/13 passed
```

Local run was verified with `GET http://localhost:8000/health` returning `{"status":"ok"}` and
`http://localhost:5173` returning 200.

### Checkpoint

- [x] `scripts/dev.sh` starts the backend and frontend together.
- [x] `backend/scripts/evaluate_corpus.py --offline` scores 13/13 against the manifest.
- [x] `backend/app/test.py` no longer violates the config boundary.
- [x] Backend lint passes.
- [x] Frontend type-check, lint, and production build pass.

## Slice: production-grade review console

### Outcome

The interface was reimagined as a finance console rather than a demo page: a sticky product bar with service
health, a masthead with live queue metrics, a drag-and-drop intake, a review panel that separates blocking
issues from advisory ones, a document inbox, and real loading, empty, and error states throughout.

### Why

The first interface proved the workflow but read as a landing page: one long column, browser-default controls,
no loading or empty states, and no way to tell a blocking error from an advisory warning at a glance. A person
who reviews documents all day needs queue context, scannable severity, and controls that respond.

### What changed

- `src/index.css` was rebuilt around design tokens: a warm paper palette, Fraunces for display and Geist plus
  Geist Mono for interface and figures, tabular numerals, tinted shadows, a fixed grain overlay, and a reduced
  motion block. Buttons gained hover, active, and visible focus states.
- `src/components/UploadStep.tsx` adds drag-and-drop with type filtering.
- `src/components/ProcessingSkeleton.tsx` replaces the spinner with layout-shaped placeholders.
- `src/components/DocumentInbox.tsx` lists reviews with status tags, issue counts, and a composed empty state.
- `src/components/ui/Notice.tsx` and `ui/Tag.tsx` are the shared feedback and state primitives.
- `AccountSelector`, `FieldEditor`, and `ReviewFindings` were restructured into labelled sections. Edited
  fields are highlighted before saving, human-sourced fields are marked, and issues are labelled blocking or
  advisory instead of raw severity words.
- `App.tsx` gained queue metrics, backend reachability, a skip link, semantic landmarks, and a footer.
- `index.html` gained a description, an inline SVG favicon, and a fuller title.
- `vite.config.ts` moves the dev server to port 5174 because 5173 is occupied by another local project, and
  the backend CORS list now allows both origins.

### Commands

```bash
cd frontend
pnpm exec tsc -b --pretty false
pnpm lint
pnpm build
```

### Observable result

`http://127.0.0.1:5174` returns 200 and `GET http://localhost:8000/health` returns `{"status":"ok"}`.
The production build emits 20.50 kB of CSS and 211.83 kB of JavaScript.

### Checkpoint

- [x] Every interactive control has hover, active, and visible focus states.
- [x] Processing shows layout-shaped skeletons rather than a spinner.
- [x] An empty inbox shows a composed getting-started state.
- [x] Blocking and advisory issues are visually distinct.
- [x] Unsaved field edits are visible before saving, and human-sourced fields stay marked.
- [x] Backend reachability is visible in the product bar.
- [x] The page uses semantic landmarks and offers a skip link.
- [x] Frontend type-check, lint, and production build pass.

## Checkpoint

## Slice: Datalumina-style guided review interface

### Outcome

The frontend now presents the existing review workflow as a landing page, explicit upload confirmation,
processing screen, prepared-review page, and separate history page. The API, provider boundaries, policy
checks, and server-side approval gate are unchanged.

### Why

The finance console made every capability visible at once, but the intended Datalumina workflow helps Maya
focus on one next action. Separating the stages makes cloud processing and the human decision easier to
understand without weakening the evidence available during review.

### What changed

- `frontend/src/App.tsx` now owns landing, upload, processing, review, and history states.
- File selection is local until Maya presses `Run review`; dropping a file no longer starts an Azure request.
- The processing screen explains the ordered review pipeline and remains clear that work is in progress.
- Review history moved out of a persistent sidebar into its own screen, while reopening and deletion remain.
- The review screen retains field editing, policy checks, AI evidence, correction-email drafting, GL selection,
  and server-enforced decisions.
- `design.md` records the visual and interaction specification used for the redesign.

### Commands

```bash
cd frontend
pnpm exec tsc -b --pretty false
pnpm lint
pnpm build
```

### Observable result

The application opens at a `Document review` landing card. `Review a document` leads to upload confirmation,
`Run review` shows the processing stage, and a completed review opens in the editable Step 3 screen. `History`
opens the separate saved-review list.

### Checkpoint

- [x] Landing, upload, processing, review, and history are distinct application states.
- [x] File selection requires explicit confirmation before the upload API call.
- [x] Existing approval, correction, GL-account, history, and deletion workflows remain connected.

## Slice: free-tier App Service demo package

### Outcome

The React production build can be staged into the FastAPI application and served from the same origin. This
produces one deployable Linux App Service package for a constrained student demonstration, without adding a
database, storage account, or second hosting product.

### Why

Azure Static Web Apps is not available in the requested UAE North region. Serving the compiled SPA from
FastAPI keeps the API and browser on one HTTPS origin and permits the trial to use a single F1 App Service
plan. The local SQLite database and upload directory remain demo-only and must never contain real invoices.

### Commands

```powershell
./scripts/stage-appservice.ps1

cd backend
uv run --locked --no-sync ruff check app scripts

cd ../frontend
pnpm exec tsc -b --pretty false
pnpm lint
pnpm build
```

### Observable result

When `backend/static/` holds a staged frontend build, FastAPI serves the React entry point at `/` and its
Vite assets at `/assets/`, while API routes and `/health` keep their existing behavior. The staging directory
is ignored by Git because it is a deployment artifact.

### Checkpoint

- [x] FastAPI can serve a compiled frontend from the same origin.
- [x] Staging the frontend is explicit and repeatable.
- [x] The F1-only deployment script does not define a paid SKU.
- [x] Azure AI credentials remain App Service environment settings, not repository files.

## Slice: Foundry invoice review advisor

### Outcome

The review console now asks the `invoice-review-advisor` prompt agent in Microsoft Foundry to explain the
already-computed evidence and recommend a next action. The recommendation is visible in each review, but it
cannot approve an invoice or alter company policy.

### Why

Document Intelligence and deterministic code remain responsible for evidence and approval gates. The Foundry
agent adds a short, reviewer-friendly explanation of the extracted fields, checks, policy issues, conflicts,
and GL suggestion.

### Configuration

Add these values to `backend/.env` after creating the agent in Foundry:

```text
FOUNDRY_PROJECT_ENDPOINT=https://invoice-review-foundry-claw.services.ai.azure.com/api/projects/invoice-review-foundry-claw
FOUNDRY_AGENT_NAME=invoice-review-advisor
FOUNDRY_AGENT_VERSION=2
```

For local development, sign in with `az login` so `DefaultAzureCredential` can obtain a Microsoft Entra token.
The signed-in identity needs permission to invoke the Foundry agent.

### What changed

- `azure-ai-projects==2.1.0` calls the Foundry agent using the project endpoint and `DefaultAzureCredential`.
- `app/providers/azure_foundry.py` is the only Foundry SDK boundary.
- `app/invoices/service.py` sends only existing review evidence and stores the structured advisor output.
- The React review panel renders an AI review advisor card while leaving the existing approval gate unchanged.

### Commands

```bash
cd backend
uv sync --locked
uv run --locked --no-sync ruff check app scripts

cd ../frontend
pnpm exec tsc -b --pretty false
pnpm lint
pnpm build
```

### Checkpoint

- [x] The advisor receives extracted fields and deterministic evidence.
- [x] The advisor recommendation is displayed without controlling approval.
- [x] Foundry authentication remains server-side.

## Slice: contextual advisor conversation

### Outcome

The prepared-review screen now presents the Foundry agent as an invoice advisor, not a general chatbot. Maya first sees its recommendation and evidence-led reasons, then can open **Ask about this review** for focused questions about that exact document.

### Why

The human decision remains the centre of the workflow. A generic chat window has no useful starting context and encourages unsupported questions. The conversation now receives the saved document fields, deterministic checks, coded issues, conflicts, and GL suggestion, and is instructed to explain evidence rather than make approval decisions.

### What changed

- The advisor card has a clear action and the conversation includes suggested questions from the agent, with safe defaults when a previous review has no saved recommendation.
- `ChatPanel` sends the ongoing conversation through the shared API client, so local and deployed environments use the configured API base URL.
- `POST /invoices/{id}/chat` supplies a server-created evidence context and rejects client-created system messages.
- The Foundry agent is explicitly instructed not to invent facts or control approval, rejection, or correction decisions.

### Commands

```bash
cd backend
uv run --locked --no-sync ruff check app scripts

cd ../frontend
pnpm exec tsc -b --pretty false
pnpm lint
pnpm build
```

### Observable result

After a document finishes processing, select **Ask about this review** beneath the AI review advisor. Choose a suggested question such as “Why is this document blocked?” or write a focused question. The response is displayed in the review page and explains the current document's evidence only.

### Checkpoint

- [x] The review screen gives the Foundry agent a clear, contextual role.
- [x] Suggested questions help the reviewer start a relevant conversation.
- [x] Chat includes the existing review evidence, not a generic empty prompt.
- [x] The agent cannot become the policy or decision maker.

## Slice: original-document preview

### Outcome

The prepared-review page now keeps the original PDF or image beside the extracted fields, checks, AI guidance, and accounting decision. Maya can compare a suspect value with its source without leaving the review flow.

### Why

The reviewer needs evidence, not just extracted text. A preview makes the human verification step tangible and keeps the AI in an advisory role. The browser receives a document through a review-specific endpoint; it never receives the local upload directory path.

### What changed

- `GET /invoices/{id}/document` resolves only the stored filename for that review, validates that it stays within the upload directory, and returns PDF, PNG, or JPEG content inline.
- `DocumentPreview` renders PDFs in an iframe and images in an accessible image panel, with an option to open the original in a separate tab.
- The review screen uses a two-column evidence workspace on desktop; on narrow screens the source document appears above the fields.

### Commands

```bash
cd backend
uv run --locked --no-sync ruff check app scripts

cd ../frontend
pnpm exec tsc -b --pretty false
pnpm lint
pnpm build
```

### Observable result

Open a stored review. The **Original document** panel displays its source file next to the prepared result. A missing review or missing locally stored source returns a clear `404` response instead of exposing a filesystem path.

### Checkpoint

- [x] Reviewers can compare extracted values with the original PDF or image.
- [x] The browser uses a review-specific endpoint, not a public upload folder.
- [x] The preview is responsive and remains available in a separate tab.

## Slice: truthful processing progress

### Outcome

The processing screen now advances only when the server begins each real review operation. It shows classification, extraction, deterministic policy validation, GL suggestion, and advisor preparation as separate stages.

### Why

A timed progress animation suggests work that may not have happened. This flow sends server-streamed events from the same request that processes the upload, so the reviewer can see where cloud processing is spending time without introducing a queue, worker, or background job.

### What changed

- `process_document_events` yields a progress event before each provider or deterministic stage, then one completed-review event after persistence.
- `POST /invoices/upload/stream` returns those events as a server-sent event stream; existing `POST /invoices/upload` remains available for a non-streaming API consumer.
- The React API client reads the stream and moves the processing screen to the reported stage. Completed stages gain a check mark; an error event returns the reviewer to upload with a useful message.

### Commands

```bash
cd backend
uv run --locked --no-sync ruff check app scripts

cd ../frontend
pnpm exec tsc -b --pretty false
pnpm lint
pnpm build
```

### Observable result

Upload a document and watch the processing screen. A stage is marked complete only after the backend has begun the next operation; the current stage reflects the operation actually in progress.

### Checkpoint

- [x] Processing stages correspond to real backend operations.
- [x] The browser receives progress from the same upload request.
- [x] No worker, queue, or timed fake progress was added.

## Slice: credit-safe demo mode

### Outcome

The landing and upload screens offer **Open demo invoice**. It opens one fictional Bright Spark Europe invoice with an offline extraction, policy result, GL suggestion, and advisor explanation. The demo never calls Document Intelligence, Azure OpenAI, or Foundry.

### Why

A portfolio or classroom presentation should be reliable and should not spend Azure student credits. A clearly labelled fixture makes it possible to demonstrate review fields, evidence preview, findings, GL selection, and approval without pretending that an AI request occurred.

### What changed

- `POST /invoices/demo` copies the fictional sample into safe local upload storage and prepares its review from fixed, inspectable data.
- Demo records are explicitly marked in SQLite and excluded from duplicate-invoice detection. Opening the demo again first removes only the previous demo record and its copied file.
- The review displays a **Demo mode** notice. Advisor chat and correction-email drafting are unavailable because either would make a cloud request.

### Commands

```bash
cd backend
uv run --locked --no-sync ruff check app scripts

cd ../frontend
pnpm exec tsc -b --pretty false
pnpm lint
pnpm build
```

### Observable result

Select **Open demo invoice** from the landing page. A prepared fictional review opens immediately with its source PDF. The browser makes no Azure request; you can select the suggested GL account and record an approval as part of the walkthrough.

### Checkpoint

- [x] A full fictional review can be demonstrated with no Azure calls or credit usage.
- [x] The original source PDF still appears in the review workspace.
- [x] Demo data cannot cause a duplicate warning on real uploads.
- [x] Controls that would call an LLM are disabled in demo mode.

## Slice: clickable advisor evidence

### Outcome

Every AI advisor recommendation now includes an **Evidence used** trail. The reviewer can select its links to jump directly to the original document, extracted fields, policy checks, open issues, or GL suggestion that underpin the guidance.

### Why

An explanation is useful only when Maya can inspect its basis. The link targets come from deterministic review data, not model-generated citations, so the interface never pretends that the agent verified a field it did not receive.

### What changed

- The review workspace gives its document, fields, policy issues, deterministic checks, and general-ledger sections stable in-page anchors.
- The advisor card derives an evidence trail from the saved review state and renders it as clear, keyboard-focusable links.
- The compact links preserve the minimal review layout while making the source of the advisor's reasoning inspectable.

### Commands

```bash
cd frontend
pnpm exec tsc -b --pretty false
pnpm lint
pnpm build
```

### Observable result

Open the demo invoice or any prepared review. Under the advisor’s reasons, select **Original document**, **Extracted fields**, **policy checks**, **policy issues** when present, or **GL suggestion**. The page scrolls to that source section.

### Checkpoint

- [x] Advisor evidence can be inspected without a second AI request.
- [x] Evidence links come from saved review data, not unverified model citations.
- [x] Every anchor remains keyboard accessible and has scroll spacing below the application navigation.

## Slice: remove the legacy cloud smoke script

### Outcome

The obsolete `backend/app/test.py` script has been removed. It loaded environment variables outside the application settings module and sent an unrelated model prompt, which made it unsuitable for a credit-safe local project.

### Why

Supported verification is explicit: backend lint, the offline 13-document policy evaluation, frontend checks, the local health endpoint, and the deliberately labelled demo mode. A hidden one-off script should not be able to spend Azure credits or bypass the provider and configuration boundaries.

### Commands

```bash
cd backend
uv run --locked --no-sync ruff check app scripts
uv run --locked --no-sync python scripts/evaluate_corpus.py --offline
```

### Checkpoint

- [x] No legacy smoke script reads secrets outside `app/config.py`.
- [x] Offline verification remains available without any Azure request.

## Slice: broader GL account selection

### Outcome

The fixed GL catalog now covers common premises, professional, technology, project, operational, and administrative spend in addition to the original cleaning, maintenance, utilities, travel, and equipment accounts.

### Why

A compact catalog made otherwise distinct supplier invoices compete for the same generic account. The broader fixed list gives the reviewer and AI suggestion a more accurate set of allowed choices while the reviewer remains responsible for the final selection.

### Commands

```bash
cd backend
uv run --locked --no-sync ruff check app scripts
```

### Observable result

The account selector and `GET /accounting/gl-accounts` offer rent and utilities, professional services, IT and software, insurance, construction materials, subcontractors, freight, office supplies, and other general expense categories. The server continues to reject any code outside this fixed list.

### Checkpoint

- [x] General expense categories are available to reviewers and GL suggestions.
- [x] The catalog remains the single source of allowed account codes.
- [x] Server-side account validation remains fixed and deterministic.

- [ ] The first sample invoice can be read with Azure Document Intelligence.
- [ ] Invoice and receipt results have a shared typed financial-document format.
- [ ] Azure results are normalized into typed dates, decimal amounts, and currency codes.
- [ ] The deterministic subtotal plus VAT total check reports passed, failed, or warning.
- [ ] Invoice and receipt required-field checks report missing information.
- [ ] Azure invoice VAT fields are mapped into the typed invoice model.
- [ ] Invoice VAT format and checksum checks report valid, invalid, or missing values.
- [ ] Positive-total checks reject zero and negative document totals.
- [ ] Invoice date-order checks reject a due date before the invoice date.
- [ ] Duplicate checks identify a previously seen supplier and invoice-number pair.
- [ ] SQLite stores invoice identities so duplicate checks survive between runs.
- [ ] The backend accepts and safely saves one PDF, PNG, or JPEG upload up to 4 MB.
- [ ] An upload is analyzed by Azure, checked by Python, and returned with its results.
- [ ] The React upload control sends a document to FastAPI and displays the processing summary.
- [ ] Reviewers can save approved, rejected, or correction-requested status for invoices.
- [ ] Saved invoice history is available through the backend and visible in the frontend.
- [ ] Request correction saves its status and shows a copyable local draft without sending email.
- [ ] Azure OpenAI classifies a document with strict invoice-or-receipt output.
- [ ] Upload results show the Azure OpenAI classification suggestion and confidence.
- [ ] Azure OpenAI fills only missing fields, while primary values and conflicts remain visible.
- [ ] The frontend shows the source of each extracted field.
- [ ] Azure OpenAI suggests only a fixed GL account.
- [ ] Locked backend and frontend installs succeed.
- [ ] Backend lint passes.
- [ ] Frontend type-check, lint, and production build pass.
- [ ] `./scripts/dev.sh --check` reports that Invoice Review is ready to start.
- [ ] The health endpoint and starter screen load locally.

Continue with the [online tutorial](https://learn.datalumina.com/docs/invoice-review).
