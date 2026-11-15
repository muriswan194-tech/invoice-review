# Client brief: GST Invoice Requirements Reviewer

## Demo context

Prism Projects India Pvt. Ltd. is fictional demo context only. It supplies sample copy and fictional documents; it is not a required customer, policy source, or validation input.

An accountant receives supplier invoices as digital PDFs, scans, screenshots, and phone photos. Before relying on an invoice as GST evidence, the accountant needs to identify missing applicable tax-invoice particulars and visible inconsistencies.

All product copy, source code, documentation, and teaching content is English. Only the example supplier documents vary in language.

## User story

> As an accountant, I want to upload a supplier invoice and receive an explainable GST requirements review so I can identify missing applicable invoice particulars and ask suppliers clear clarification questions.

## What's included in the build

- One PDF or image per upload, with a 4 MB limit.
- Azure AI Document Intelligence `prebuilt-invoice` extraction.
- An Azure OpenAI fallback extraction only when Document Intelligence misses core GST fields or the full GST tax breakup.
- A deterministic merge that keeps Document Intelligence values and fills only its missing fields from the LLM, with visible provenance and conflicts.
- Supplier and recipient GSTINs, place of supply, HSN/SAC, invoice number/date, taxable value, GST components, reverse-charge indicator, and total.
- Local GSTIN structure/checksum validation only; no government registration lookup.
- GST arithmetic reconciliation and tax-structure exception checks.
- Deterministic GST invoice requirement and consistency checks, with human corrections.
- SQLite, local file storage, and a guided welcome → upload/preview → process → review flow.
- Review history with explicit local deletion so the same invoice can be demonstrated again.
- Local history and a fictional GST invoice demo.

## GST-review boundary

The reviewer applies only applicable GST tax-invoice particulars and local consistency checks. Azure extracts evidence, but does not decide whether a document is legally compliant.

### Invoice requirements

The active profile is **Standard registered-recipient B2B tax invoice**. Supplier/recipient GSTINs, invoice number/date, HSN/SAC, taxable value, GST breakup, and total are applicable core particulars. A present value is shown as present; an absent applicable value is missing; a malformed GSTIN is invalid under local structure/checksum validation. Place of supply is applicable only when IGST indicates an inter-State supply and is otherwise not applicable in this screen. Reverse-charge status is screened as an applicable declared particular, but its absence is a review warning rather than a blocking legal conclusion. Extraction confidence is evidence quality, not a GST failure.

This is deliberately narrower than a complete Rule 46 review. The current model does not assess supplier/recipient addresses, supply description, goods quantity/unit, tax rate, delivery address, or supplier signature. A human must compare those remaining particulars with the source invoice where relevant.

Project codes, purchase orders, cost centres, GL coding, duplicate-payment detection, TDS, payment dates, and fixed company identity are outside this review. An organisation may add them later as separately labelled controls.

Document Intelligence is the document-type gate and stays primary. When its core extraction is complete, no OpenAI request is made. When the fallback runs, an AI value can fill a missing field, but it cannot replace a conflicting primary value, validate GST registration with a government service, calculate TDS liability, or decide approval. The accountant sees where every fallback came from.
