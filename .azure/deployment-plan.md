# Azure Deployment Plan

> **Status:** Approved

Generated: 2026-08-23

---

## 1. Project Overview

**Goal:** Deploy the Invoice Review trial demonstration using only the Azure for Students subscription and free App Service capacity in UAE North. The deployment must not require a payment method, Pay-As-You-Go conversion, or paid Azure resource.

**Path:** Modernize Existing

---

## 2. Requirements

| Attribute | Value |
|-----------|-------|
| Classification | Portfolio / trial demonstration |
| Scale | Small — one reviewer and occasional sample uploads |
| Budget | Strict free-tier only; stop if a paid SKU is required |
| Subscription | Azure for Students (`ddb20c37-b7f8-4d97-9834-afa830563657`) |
| Location | UAE North (`uaenorth`) |
| Data residency | UAE North for the hosted application; existing AI resources remain where already provisioned |
| Billing constraint | No Pay-As-You-Go upgrade, no payment method, no paid supporting resources |

**Policy constraints:** Read-only subscription check found zero policy assignments.

---

## 3. Components Detected

| Component | Type | Technology | Path |
|-----------|------|------------|------|
| review-api | API and static-site host | Python 3.12, FastAPI, Uvicorn | `backend/` |
| review-ui | SPA build served by API | React 19, Vite, TypeScript | `frontend/` |
| Azure AI integrations | External managed services | Document Intelligence, Azure OpenAI, Azure Foundry | Existing configured endpoints |

Current deployment tooling: Azure CLI is installed and signed in. Azure Developer CLI is not installed. No existing `azure.yaml`, infrastructure directory, Dockerfile, or CI workflow exists.

---

## 4. Recipe Selection

**Selected:** Azure CLI from the VS Code integrated terminal.

**Rationale:** The project has no existing Azure Developer CLI configuration, and the trial must use only a verified F1 App Service plan. Azure CLI can create the explicit free plan, deploy a prepared combined application artifact, configure `/health`, and abort if Azure proposes another SKU.

---

## 5. Architecture

**Stack:** App Service

The React production build will be served by the existing FastAPI application from one Linux App Service. This avoids a second hosting product, keeps the frontend and API on one origin, and avoids Azure Static Web Apps, which is not available in UAE North.

### Service Mapping

| Component | Azure Service | SKU |
|-----------|---------------|-----|
| Combined React UI + FastAPI API | Linux Azure App Service and one App Service Plan | F1 Free only |
| Uploaded files and review history | App Service local filesystem and SQLite | Demo-only; no paid storage/database |
| AI processing | Existing Azure AI endpoints | Existing credentials and student-credit usage only |

### Explicitly excluded

- Azure Static Web Apps (not available in UAE North)
- Azure Container Registry, Container Apps, Azure SQL, Blob Storage, Key Vault, Application Insights, Log Analytics, and Azure OpenAI/Document Intelligence provisioning
- Paid App Service SKUs (B1 or above)
- Payment method or Pay-As-You-Go conversion

### Security and configuration

- HTTPS only.
- App Service health path: `/health`.
- Azure service credentials remain environment variables; they are never committed, read from source control, or printed.
- Before live AI processing works, the app must be given the existing `AZURE_DOCUMENT_INTELLIGENCE_*`, `AZURE_OPENAI_*`, and `FOUNDRY_*` settings through App Service configuration by the account owner.
- Local SQLite and files are ephemeral demo data; do not upload real invoices or private data.

---

## 6. Provisioning Limit Checklist

| Resource Type | Number to Deploy | Total After Deployment | Limit/Quota | Notes |
|---------------|------------------|------------------------|-------------|-------|
| Microsoft.Web/serverfarms (F1 Free) | 1 | 1 | Free App Service allowance: up to 10 web/API apps, 1 GB storage, and 1 hour/day | Official Azure for Students benefit; current UAE North plans: 0 |
| Microsoft.Web/sites | 1 | 1 | Included in the same free App Service allowance | Official Azure for Students benefit; current UAE North sites: 0 |

**Capacity result:** Suitable for the planned one-app trial demo, subject to Azure offering F1 in UAE North at creation time.

**Quota API note:** The required `az quota list` check was attempted. The subscription is not registered for `Microsoft.Quota`; registration would modify subscription state and is deliberately not performed without separate approval. Fallback read-only resource counts found 0 UAE North App Service sites and 0 plans. The plan relies on the official Azure for Students free App Service allowance and will stop if the portal/CLI cannot select F1.

---

## Research Summary

- App Service supports Linux-hosted Python; the app will use the existing `/health` endpoint and HTTPS.
- UAE North does not support Azure Static Web Apps, so the compiled React files are staged into
  `backend/static/` and served by FastAPI on the same origin.
- The free F1 tier is only for development/testing. It is suitable for this trial, but local SQLite and
  uploaded files are ephemeral demo data.
- Existing Document Intelligence and OpenAI API keys remain App Service environment settings entered by the
  account owner; they are never read from or written to repository files.
- The specialized Python App Service deployment helper was not used because it requires a paid P0v3 plan,
  which conflicts with the approved F1-only constraint.

---

## 7. Execution Checklist

### Phase 1: Planning

- [x] Analyze workspace
- [x] Gather requirements
- [x] Confirm subscription and UAE North location
- [x] Scan codebase
- [x] Select recipe
- [x] Plan architecture
- [x] Check policy assignments and fallback App Service capacity
- [x] User approved this plan

### Phase 2: Execution after approval

- [x] Make FastAPI serve the compiled React assets on the same origin
- [x] Build and technically verify frontend and backend locally
- [ ] Complete user manual UI walkthrough
- [ ] Create one F1 Linux App Service Plan and one web app in UAE North
- [ ] Deploy the combined application artifact
- [ ] Configure health check and HTTPS
- [ ] User adds existing AI environment variables in Azure App Service configuration
- [ ] Verify `/health`, landing page, and a controlled sample-upload request
- [ ] Update status to `Ready for Validation`

### Phase 3: Validation

- [ ] Invoke azure-validate
- [ ] Record validation proof

### Phase 4: Deployment

- [ ] Invoke azure-deploy
- [ ] Report deployed HTTPS URL

---

## 8. Validation Proof

Not yet validated.

## Functional Verification

- **Technical package check:** Passed on 2026-08-23.
- **Backend lint:** `uv run --locked --no-sync ruff check app scripts` — passed.
- **Frontend build:** `pnpm build` — passed and staged into `backend/static/`.
- **Combined route check:** FastAPI TestClient `GET /` returned `200 text/html`.
- **Health check:** FastAPI TestClient `GET /health` returned `200 {"status":"ok"}`.
- **Manual UI walkthrough:** Pending user confirmation.

---

## 9. Files to Generate

| File | Purpose | Status |
|------|---------|--------|
| `.azure/deployment-plan.md` | Deployment source of truth | Approved |
| `backend/app/main.py` | Serve compiled React assets while preserving API routes | Complete |
| `scripts/stage-appservice.ps1` | Create the generated static-assets deployment package | Complete |
| `scripts/deploy-free-tier.ps1` | F1-only Azure CLI deployment | Complete |

---

## 10. Next Steps

Current phase: Functional verification.

1. Complete a local manual UI walkthrough.
2. Validate the prepared deployment package.
3. Provision and deploy only if Azure accepts the F1 Free SKU in UAE North.
