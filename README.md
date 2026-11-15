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

The review labels a field as **applicable** or **not applicable** before interpreting
it as **present**, **missing**, or locally **invalid**. For example, place of supply
is applicable in this profile when IGST is detected; it is otherwise not applicable
in this screen. An absent reverse-charge declaration is shown for human review, not
as an automatic legal conclusion.

## Run locally

Prerequisites: Python 3.12+, uv, Node.js 22+, and pnpm 11.

```bash
cd backend
uv sync --locked

cd ../frontend
pnpm install --frozen-lockfile
```

For a live invoice review, configure Azure values in `backend/.env`:

```text
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=
AZURE_DOCUMENT_INTELLIGENCE_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_DEPLOYMENT=
AZURE_OPENAI_API_KEY=
```

Start the backend and frontend using the project development script, or run the
backend directly:

```bash
cd backend
uv run --locked --no-sync uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000/> when serving the staged frontend. The fictional demo
does not use Azure credentials.

## Deploy the frontend to Cloudflare Workers

The Cloudflare deployment serves the built React frontend from `frontend/dist`.
Configure the Cloudflare Worker build with:

```text
Build command: pnpm --dir frontend install --frozen-lockfile && pnpm --dir frontend build
Deploy command: pnpm exec wrangler deploy
```

The repository root is the Wrangler project directory. Set
`VITE_API_BASE_URL` to the public HTTPS URL of the separately hosted FastAPI
backend before the build. The backend must allow the Cloudflare origin in its
CORS configuration; Cloudflare hosts the frontend only and does not run the
Python API or its SQLite storage.

## Verify

```bash
cd backend
uv run --locked --no-sync ruff check app
uv run --locked --no-sync python -m compileall -q app

cd ../frontend
pnpm exec tsc -b --pretty false
pnpm lint
pnpm build
```

See [the client brief](docs/client-brief.md), [architecture](docs/architecture.md),
and [build-along guide](docs/build-along.md) for the product boundary and teaching
checkpoints.
