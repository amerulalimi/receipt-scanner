# Product Requirements Document (PRD) — v2
## Resit.my — Expanded Feature Set (Post-MVP)
**Version:** 2.0.0  
**Status:** Proposed — Phase 2 & Phase 3  
**Last Updated:** June 2025  
**Author:** Internal  
**Builds On:** prd.md (v1.0.0 — MVP Scope)

---

## 1. Purpose of This Document

This document expands on the MVP defined in `prd.md`. It does **not** repeat MVP features — refer to v1 for auth, core upload, AI pipeline, dashboards, and ZIP export basics. This document covers what comes **after** MVP validates the core loop (scan → classify → track → download).

Each feature below includes: why it matters, who uses it, and roughly when it should be built (Phase 2 = 2–4 months post-launch, Phase 3 = 5+ months / once there's traction).

---

## 2. Guiding Principle

MVP proves the AI scan-and-classify loop works. Phase 2 onward should focus on **retention and habit-forming use** — not one-off use in March when filing season hits. The biggest risk to this product is that people only remember to use it once a year. Every feature below should be evaluated against: *does this make someone open the app in July, not just March?*

---

## 3. Phase 2 Features (2–4 months post-launch)

### 3.1 Multi-Year Tax History
**Why:** Individuals file every year. Without history, the app resets to zero value annually.

- User can switch between tax years from a year selector (e.g. 2024, 2025, 2026)
- Each year maintains its own claim summary, receipt list, and limits (limits change yearly via `relief_limits` table — already supported in schema)
- "Compare to last year" view: total claimed, savings, category breakdown side by side
- Receipts auto-archive into the year they were dated, not the year they were uploaded (important: a January upload of a December receipt belongs to the previous tax year)
- Year-end reminder: "Tahun cukai 2025 akan ditutup pada 28 Februari 2026 — semak resit anda"

---

### 3.2 Smart Reminders & Notifications
**Why:** The app's value is highest when people upload receipts *as they happen*, not in a end-of-year scramble. Reminders close that gap.

- Push/email reminder when a large expense category has zero receipts close to year-end (e.g. "Anda belum upload sebarang resit pendidikan tahun ini")
- Monthly digest email: "Anda telah claim RM2,400 bulan ini. RM5,600 lagi untuk had perubatan."
- Smart nudges based on calendar — e.g. reminder in January for SSPN contribution receipts, reminder before school term for education-related claims
- Configurable notification preferences (email, in-app, frequency)
- "Receipts expiring soon" alert — for org employees, reimbursement window closing

---

### 3.3 Automatic Mixed-Item Receipt Splitting
**Why:** Flagged in MVP as manual review. This is one of the most common real-world cases (pharmacy receipts mixing medicine and toiletries) and manual review doesn't scale.

- LLM performs line-item level classification, not just whole-receipt classification
- Each line item gets its own category tag and claimable flag
- User sees an itemized breakdown with claimable items pre-checked
- User can manually toggle individual line items in/out of the claim
- Partial claim amount auto-calculated from selected items only

---

### 3.4 Spouse / Family Joint Filing Support
**Why:** Malaysian tax filing frequently involves spouses optimizing which partner claims which relief — flagged in earlier product discussions as a strong differentiator.

- Link spouse account (consent-based, both parties must approve link)
- Shared household view: combined relief usage across both accounts
- "Smart suggest" — recommends which spouse should claim a given receipt based on:
  - Who has more remaining limit in that category
  - Who is in the higher tax bracket (bigger relief value)
- Receipts can be reassigned between linked accounts before submission
- Each spouse's Borang BE remains separately filed — this is a planning tool, not a joint return

---

### 3.5 CSV / Payroll Export
**Why:** Marked "out of scope" in MVP but is a near-term necessity once corporate customers want to integrate with their existing payroll or claims process.

- Export approved claims as CSV with configurable column mapping
- Common payroll system templates (e.g. generic CSV, plus templates for common Malaysian payroll providers)
- Scheduled auto-export (e.g. HR receives CSV every 1st of the month)
- Export includes: employee ID, name, category, amount, approval date, approver

---

### 3.6 In-App Receipt Editing Tools
**Why:** OCR/AI gets it wrong sometimes. Currently MVP only allows category/amount correction — broader editing reduces support burden.

- Crop/rotate receipt image before processing (common issue: photos taken at an angle)
- Manual re-trigger OCR after crop
- Manual entry mode — fully bypass OCR for illegible receipts (e.g. faded thermal paper)
- Merge two receipt images into one record (front + back of a long receipt)
- Receipt notes field — free text for personal reference

---

### 3.7 Org Analytics Dashboard
**Why:** Marked out of scope for MVP. Once a company has multiple months of data, HR/finance want insight, not just approval queues.

- Spend by category trend over time (chart)
- Top claiming employees / departments
- Average approval turnaround time
- Rejected claim reasons breakdown (helps refine company policy)
- Forecasted year-end relief utilization across the org
- Exportable as PDF report for management

---

### 3.8 In-App Borang BE Guidance
**Why:** Users still need to manually file with LHDN (MVP explicitly excludes auto-filing). A guided summary reduces filing-day friction and reinforces the app's relevance at the moment of filing.

- "Ready to File" view — shows exactly which Borang BE fields to fill and what amount, mapped to LHDN's own form sections
- Step-by-step walkthrough matching LHDN e-Filing field order
- Printable filing checklist PDF
- Does **not** auto-submit to LHDN (no official API exists for this) — purely a guidance/reference layer

---

## 4. Phase 3 Features (5+ months / traction-dependent)

### 4.1 LHDN MyTax Integration (if/when API becomes available)
**Why:** The natural end-state of this product — but dependent entirely on LHDN exposing a public or partner API. Currently no such public API exists (verify before committing roadmap).

- Pre-fill Borang BE e-Filing fields directly via API (if LHDN provides this)
- Until then: maintain the manual "Ready to File" guide from Phase 2 as the realistic ceiling

---

### 4.2 Receipt Forwarding via Email/WhatsApp
**Why:** Reduces friction further than even QR camera upload — some users receive e-receipts directly in email or get sent receipts via WhatsApp by a spouse/assistant.

- Unique forwarding email per user (e.g. `ahmad-x7f2@receipts.resit.my`) — forward any e-receipt PDF/image and it's auto-processed
- WhatsApp Business API integration — send a photo to a dedicated number, get processed automatically
- Both methods reuse the existing OCR/classify pipeline — no new AI work needed, just new ingestion channels

---

### 4.3 Bank/E-Wallet Transaction Matching
**Why:** Helps catch missed receipts — if a user spent money at a clinic but never uploaded the receipt, the app can prompt them.

- Optional bank statement upload (CSV) or open banking connection (if available in Malaysia — limited at present)
- Match transactions to merchants likely to be tax-relief-eligible (e.g. "RM450 at Klinik Pergigian Sentosa on 3 May — upload resit?")
- Strictly opt-in, clearly separated from core receipt flow — this touches sensitive financial data and needs its own consent and security review

---

### 4.4 Multi-Company Support for Accountants/Agents
**Why:** Tax agents and bookkeepers manage filings for multiple individuals or SMEs. Currently the app assumes one org per user.

- "Agent" role — can be invited into multiple individual or org accounts with restricted access (view + prepare, not approve)
- Switch between managed clients from a single login
- Useful for small accounting firms offering this as a value-added service to clients

---

### 4.5 Custom Relief Categories for Non-BE Forms
**Why:** Borang BE is the MVP wedge, but Malaysia also has Borang B (business income) and Borang P (partnership) with different/additional relief structures. Long-term TAM expansion.

- Configurable relief category sets per form type
- User selects form type at onboarding (BE, B, P) — app adjusts categories and limits accordingly
- Requires separate rule engine config per form type (schema already supports this via `relief_limits.category` being extensible)

---

### 4.6 Gamification / Engagement Layer
**Why:** Ties back to the core retention problem — give people a reason to use this outside tax season.

- "Claim completeness" score — visual indicator of how thoroughly a user is tracking the year (not a la "credit score" but more an engagement nudge)
- Milestone notifications: "Anda telah jimat RM1,000 tahun ini!"
- Annual wrapped-style summary at year-end (shareable, tasteful — not aggressive virality bait)

---

## 5. Explicitly Not Planned

These were considered and rejected, with reasoning, to keep scope honest:

| Feature | Why Not |
|---|---|
| Automated LHDN e-Filing submission | No public LHDN API exists for this; would require manual/unofficial workarounds that carry compliance risk |
| Cryptocurrency/investment relief tracking | Outside Borang BE individual relief scope; different regulatory complexity |
| Full accounting/bookkeeping suite | Scope creep — this is a relief-tracking tool, not a general ledger |
| Native mobile app (Phase 1 reconsideration) | Web + QR handoff covers the camera use case without doubling engineering surface area; revisit only if usage data shows strong demand |

---

## 6. Feature Prioritization Summary

| Feature | Phase | User Impact | Build Complexity |
|---|---|---|---|
| Multi-year tax history | 2 | High | Low (schema already supports) |
| Smart reminders | 2 | High | Medium |
| Mixed-item splitting | 2 | High | Medium-High (LLM prompt redesign) |
| Spouse joint filing | 2 | High (differentiator) | Medium |
| CSV/payroll export | 2 | Medium (corporate-only) | Low |
| Receipt editing tools | 2 | Medium | Low |
| Org analytics dashboard | 2 | Medium (corporate-only) | Medium |
| Borang BE filing guide | 2 | High | Low-Medium |
| LHDN MyTax integration | 3 | Very High (if possible) | Unknown — external dependency |
| Email/WhatsApp forwarding | 3 | High | Medium |
| Bank transaction matching | 3 | Medium | High (security/compliance heavy) |
| Multi-company agent support | 3 | Medium (niche but high-value segment) | Medium |
| Custom relief for Borang B/P | 3 | Low (TAM expansion only) | Medium |
| Gamification layer | 3 | Low-Medium | Low |

---

## 7. Open Questions for Discussion

- Should spouse joint filing (3.4) be pulled into Phase 1.5 given it was flagged early as a strong differentiator? It may be worth prioritizing ahead of analytics/CSV export.
- Is there appetite to validate a Malaysian open banking provider for 4.3 before committing engineering time, given its complexity?
- For 4.4 (multi-company agent support) — is there interest in directly targeting small accounting firms as a B2B2C channel, or is this purely opportunistic?