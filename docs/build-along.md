# Build-along guide

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

- `app/config.py` gained `AppConfig` for fixed Northstar policy: own VAT number, total tolerance, and the
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
- [x] A customer VAT number that is not Northstar's reports `customer_vat_id_mismatch`.
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
- [x] The server refuses approval until a valid Northstar GL account is selected.
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
cannot approve an invoice or alter Northstar policy.

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
- [ ] Azure OpenAI suggests only a fixed Northstar GL account.
- [ ] Locked backend and frontend installs succeed.
- [ ] Backend lint passes.
- [ ] Frontend type-check, lint, and production build pass.
- [ ] `./scripts/dev.sh --check` reports that Invoice Review is ready to start.
- [ ] The health endpoint and starter screen load locally.

Continue with the [online tutorial](https://learn.datalumina.com/docs/invoice-review).
