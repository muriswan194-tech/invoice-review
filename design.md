# GST Invoice Exception Desk — UI Design Brief

## Purpose

Keep the calm, guided reviewer experience while presenting a distinct portfolio product for Prism Projects India Pvt. Ltd. The desk surfaces GST/document exceptions and routes them to a human accountant. It is not a tax-advice product and does not make autonomous payment decisions.

## Product principle

The application prepares evidence; a finance reviewer makes the decision. The interface should make one next action obvious at every stage, use restrained visual styling, and explain AI activity without making the AI appear to be the decision-maker.

## Visual direction

- Minimal, quiet, professional finance tool.
- White page background with near-black text, soft gray borders, and subtle shadows.
- A narrow, centered content column; avoid a dashboard or dense control-room layout.
- Use one primary black button, secondary white outlined buttons, a muted gray destructive action, and clear semantic issue colours.
- Use a small, consistent top navigation bar with the product name and organization.
- Prefer ordinary forms, cards, dividers, and generous whitespace over decorative gradients, large metrics, or permanent sidebars.

## Information architecture

Use separate pages or explicit application states instead of showing intake, review, and history all at once.

```text
Landing
  ├── New review
  │     ├── Step 1: Upload and preview
  │     ├── Step 2: Processing progress
  │     └── Step 3: Review and decision
  └── History
        └── Open a prior review
```

The existing API can remain the source of truth. The UI owns navigation and temporary upload/progress state.

## Screen specifications

### 1. Landing page

Show a centered card approximately 650–700 px wide.

- Small organization label: `Finance workspace`
- Title: `Document review`
- Short description: upload an invoice or receipt, run the review pipeline, inspect the prepared result before bookkeeping.
- Primary action: `Review a document`
- Secondary action: `View history`
- Below a divider, show a three-row `How it works` explanation:
  1. Upload a document
  2. Run the pipeline
  3. Inspect the result

### 2. Shared top bar

For all review and history screens, show a slim top bar.

- Left: `Document review` with `Finance workspace` beneath it.
- Right: `History`, primary `New review`, and optionally `Sign out` only if authentication is deliberately added later.
- Do not implement authentication as part of this redesign; it is outside the current project boundary.

### 3. Step 1 — Upload and preview

Place a back action above the content and use a restrained centered column.

- Label: `Step 1 of 3`
- Heading: `Choose an invoice or receipt`
- Helper: the file is only sent to Azure after confirmation.
- Large dashed drop zone for PDF, PNG, and JPEG files, maximum 4 MB.
- After a file is chosen, show its filename, type, size, and a simple local preview when supported.
- Let the reviewer choose or confirm `Invoice` / `Receipt` before submission. Until automatic routing is implemented, keep this explicit choice.
- Primary action: `Run review`.

### 4. Step 2 — Processing

Show a compact centered processing card rather than a generic spinner.

- Label: `Step 2 of 3`
- Heading: `Processing document`
- State which filename is being processed.
- Display four ordered pipeline rows:
  1. `Classify document` — recognizes whether the upload is an invoice or receipt.
  2. `Extract and cross-check` — runs Document Intelligence and the independent LLM reading.
   3. `Validate GST and policy` — checks GSTIN structure, INR arithmetic, project references, and duplicate status.
  4. `Suggest GL account` — maps normalized fields to the fixed account catalog.
- Each row must visibly be pending, active, complete, or failed. Do not claim a completed stage before its response is available.
- On failure, explain the stage that failed and offer retry/back actions.

### 5. Step 3 — Review and decision

Organize the page as a vertical, readable review, not a multi-column dashboard.

1. **Review extracted fields**
   - Explain that changes rerun the checks.
   - Group form fields into Invoice details, GST identity, project references, and INR tax amounts.
   - Use a two-column form on wide screens and one column on narrow screens.
   - Mark field provenance discreetly: Document Intelligence, LLM fallback, Human, or Missing.
   - Primary save action: `Save and rerun checks`.

2. **Invoice or receipt summary**
   - Display the normalized values used for the review in a compact bordered grid.
   - Values should use accessible labels and tabular figures for monetary totals.

3. **Automatic checks**
   - Display errors and warnings separately.
   - Error issues block approval; warnings are advisory.
   - State the reason in plain language and retain the deterministic issue code only as secondary detail if helpful.

4. **Supplier action**
   - Display this section only when supplier-fixable issues exist.
   - Offer `Draft correction email`.
   - The dialog must say that nothing is sent from the application, and offer Copy and Close actions.

5. **Independent LLM review**
   - Explain that Document Intelligence remains primary.
   - Show any fields filled by the LLM and any conflicts where the primary source was retained.
   - Keep this evidence section below the policy and human-editing sections so it never appears to control approval.

6. **GL account and decision bar**
   - Show the AI suggestion and the fixed GL-account selector.
   - Keep `Approve` disabled until there are no blocking issues and a valid account is selected.
   - Provide `Reject`; show `Request correction` only when eligible.
   - Once decided, render the saved decision prominently and lock edits.

### 6. History

Make history its own screen.

- Heading: `Review history`
- Show newest reviews first.
- Each row shows supplier/merchant, invoice number when available, filename, total/currency, status, and issue count.
- Selecting a row opens the Step 3 review view for that saved review.
- Keep deletion explicit and secondary, with a confirmation affordance.
- Include an empty state that leads to `New review`.

## Responsive and accessibility requirements

- Work from 320 px upward; forms stack on small screens.
- Use semantic landmarks, descriptive labels, visible keyboard focus, and real buttons.
- Do not communicate error/warning state with colour alone.
- Respect reduced-motion preferences; progress state changes should not require animation to understand.
- Preserve logical focus when navigating between wizard steps and when opening/closing the correction-email dialog.

## Out of scope

- Authentication and password screens
- Sending email
- Accounting-system integrations
- Queues, background workers, or batch review
- Changing Azure provider boundaries or deterministic policy rules

## Acceptance checklist

- [ ] Landing, upload, processing, review, and history are distinct UI states/pages.
- [ ] The default screen resembles the supplied Datalumina landing card, not a dashboard.
- [ ] Processing shows real ordered pipeline stages with clear failure handling.
- [ ] Review fields, summary, automatic checks, AI evidence, GL selection, and decisions remain available.
- [ ] Approval remains server-enforced and requires no errors plus a valid selected GL account.
- [ ] The UI works on mobile and supports keyboard-only use.
- [ ] Existing backend lint, offline corpus evaluation, frontend type-check, lint, and build continue to pass.
