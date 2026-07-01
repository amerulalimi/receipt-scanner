# Product Requirements Document (PRD)
## Resit.my — Malaysian Tax Relief Receipt Scanner
**Version:** 2.1.0
**Status:** Live Document
**Last Updated:** June 2026
**Author:** Internal

---

## 1. Overview

### 1.1 Product Summary
Resit.my is a web-based application that helps Malaysian taxpayers (individuals and corporate employees) scan, classify, and manage receipts for tax relief claims under **Borang BE** (LHDN). The app uses OCR and LLM-based classification to automatically map receipts to the correct relief category and track claim limits in real time.

### 1.2 Problem Statement
Malaysian taxpayers manually collect and categorize receipts throughout the year, often losing track of claim limits, misclassifying receipts, or failing to maximize their tax relief. For corporate HR teams, managing receipt reimbursements and generating audit-ready documentation is time-consuming and error-prone.

The biggest long-term risk to this product is that users only remember to open it once a year during tax season. Every feature should be evaluated against: *does this make someone open the app in July, not just March?*

### 1.3 Target Users

| Segment | Description |
|---|---|
| Individual | Malaysian resident filing Borang BE annually |
| Corporate Employee | Staff submitting receipts for HR approval |
| HR Admin | Manages employee claims, approves/rejects, generates reports |
| Superadmin | Company owner — manages HR admins, billing, org policy |

### 1.4 Implementation Status (as of June 2026)

Ringkasan status berbanding kod semasa dalam repo ini:

| Kawasan | Status | Nota |
|---|---|---|
| Auth, sesi server-side, pengesahan e-mel | ✅ Siap | Termasuk `refresh`, `PATCH /auth/me`, urus sesi serentak |
| Muat naik tempatan + QR handoff + WebSocket | ✅ Siap | Sesi QR menyokong `tax_year`; sinkron via Redis pub/sub |
| Pipeline AI (OCR + klasifikasi) | ✅ Siap | **OpenRouter Vision LLM** (bukan Google Vision + Claude berasingan); PDF → semakan manual |
| Enjin peraturan, deduplikasi, had kategori | ✅ Siap | Had pelepasan global dalam DB (`relief_limits`) |
| Dashboard peribadi + penapis tahun cukai | ✅ Siap | Perbandingan tahun (`/claims/compare`), skor kelengkapan |
| Onboarding korporat, jemputan, HR dashboard | ✅ Siap | Kelulusan pukal, analitik org, eksport CSV gaji |
| Eksport ZIP individu | ✅ Siap | Muat turun segera (`GET /claims/export-zip`), bukan job async |
| Eksport ZIP korporat semua pekerja | ⏳ Belum | Eksport CSV gaji ada; ZIP multi-pekerja belum |
| Pengesahan domain DNS/e-mel syarikat | ⏳ Belum | `domain_verified` dalam skema; endpoint belum |
| Pecahan item bercampur (line items) | ✅ Siap | `receipt_line_items`; toggle `included_in_claim` |
| Pautan pasangan / isi rumah | ✅ Siap | `/household`, reassign resit, cadangan tuntutan |
| Peringatan & notifikasi | ✅ Sebahagian | Keutamaan in-app/e-mel, senarai notifikasi; skrip digest bulanan |
| Panduan Borang BE (Ready to File) | ✅ Siap | Halaman `/dashboard/ready-to-file` |
| Kemasukan manual + nota resit + reprocess | ✅ Siap | `POST /receipts/manual`, `notes`, `POST .../reprocess` |
| Admin sistem (AI, rahsia, had pelepasan) | ✅ Siap | `/admin` — konfigurasi OpenRouter, tetapan sistem |
| i18n BM / EN | ✅ Siap | Kamus frontend; mesej dwibahasa untuk notifikasi |
| Pemajuan e-mel resit | 🔧 Asas | `forwarding_token` + alamat dipaparkan; tiada penerimaan e-mel lagi |
| WhatsApp, perbankan, ejen cukai | ⏳ Belum | Masih dalam Fasa 3 |

### 1.5 Success Metrics

**MVP**
- Time to classify a receipt: < 10 seconds
- AI classification accuracy: > 90%
- User can download audit-ready ZIP in < 3 clicks
- Zero data loss on QR handoff session

**Phase 2**
- Monthly active users (not just March spikes)
- Spouse-linked accounts as % of total individual users
- Average receipts uploaded per user per month

---

## 2. User Personas

### 2.1 Individual User — Hafizah, 32, Accountant
- Files Borang BE annually
- Forgets to track receipts until March
- Wants to know exactly how much she can still claim
- Needs to store receipt images digitally for 7-year LHDN audit requirement

### 2.2 HR Admin — Razif, 40, HR Manager (100 employees)
- Receives receipt claims from employees monthly
- Manually verifies and approves before payroll
- Needs structured documentation for company audit
- Wants to bulk download all employee receipts organized by category

### 2.3 Corporate Employee — Siti, 28, Software Engineer
- Submits receipts for medical and lifestyle claims
- Wants quick upload via phone camera without complex forms
- Needs notification when claim limit is almost reached

---

## 3. Phase 1 — MVP (Month 1–4)

### 3.1 Authentication & Onboarding

#### Individual Registration
- Register with email + password
- Select account type: Individual or Corporate
- Email verification required before access

#### Corporate Onboarding
- Superadmin registers company with:
  - Company name
  - SSM registration number
  - Official email domain (e.g. `@syarikat.com.my`)
- Domain verified via DNS TXT record or email confirmation
- Superadmin assigns HR Admin via email invite
- HR Admin invite link: 48-hour expiry, single-use token

#### Employee Invitation (HR Admin)
Three methods:
1. **CSV upload** — bulk import name + email list
2. **Invite link** — shareable link (domain-restricted, 7-day expiry)
3. **Manual invite** — enter email one at a time

Employee registration enforces domain match. Non-matching email domains are rejected automatically.

---

### 3.2 Receipt Upload

#### Local Upload (Desktop)
- Drag and drop or file picker
- Accepted: JPG, PNG, PDF (max 10MB per file)
- Batch upload: up to 20 files at once

#### QR Camera Handoff
1. User clicks "Use Camera" on desktop
2. System generates unique session token
3. QR code + shareable link displayed on desktop
4. Mobile opens link — no login required for upload within session
5. Mobile uses native camera to capture receipt
6. Upload processed in background
7. Desktop receives receipt in real-time via WebSocket
8. Mobile prompts: "Upload another?" or "Done"
9. On "Done" — mobile shows completion screen, desktop resumes automatically

#### Session Token Rules
- **Inactivity timeout:** 10 minutes of no upload activity
- **Activity resets timer:** every successful upload resets the 10-minute countdown
- **Warning:** 2-minute warning shown on mobile before expiry
- **"Keep Active" button:** resets timer without uploading
- **On expiry:** token invalidated, desktop auto-generates new QR
- **Uploaded images:** never lost on expiry — stored to user's session regardless
- **Security:** token is single-device, bound to user session, HTTPS only

---

### 3.3 AI Processing Pipeline

#### Step 1 — Vision LLM (OpenRouter, pelaksanaan semasa)
- Model vision dikonfigurasi melalui admin (`openrouter_vision_model`, lalai `google/gemini-2.5-flash`)
- Input: imej resit (JPG/PNG/WebP) sebagai base64
- Output: merchant, tarikh, jumlah, kategori, seksyen BE, keyakinan, nota, dan **senarai line items** (jika bercampur)
- PDF: tiada OCR automatik — ditandakan `semak_manual` untuk kemasukan manual
- Jika keyakinan < 70%: bendera `low_ocr_confidence` / semakan manual

#### Step 2 — Penyimpanan & Line Items
- Resit bercampur: setiap baris disimpan dalam `receipt_line_items` dengan `ai_claimable` dan `included_in_claim`
- Pengguna boleh toggle item individu melalui `PATCH /receipts/{id}` (`line_items`)
- Jumlah `claimed_amount` dikira semula daripada item yang dipilih

#### Step 3 — Rule Engine Validation
- Validates against current LHDN relief limits (stored in DB, updatable without code change)
- Detects duplicate receipts via SHA-256 image hash
- Flags if category limit would be exceeded

#### Relief Categories Supported (Borang BE 2025)

| Category | Seksyen | Had (RM) |
|---|---|---|
| Perubatan & Pergigian | S.46(1)(b) | 8,000 |
| Gaya Hidup | S.46(1)(k) | 3,000 |
| Peralatan Sukan | S.46(1)(k) | 500 (within Gaya Hidup) |
| Pendidikan Diri | S.46(1)(f) | 7,000 |
| SSPN | S.46(1)(l) | 8,000 |
| Pembelian EV Charging | S.46(1)(p) | 2,500 |
| Tidak Layak | — | — |

---

### 3.4 Dashboard

#### Individual / Employee Dashboard
- Receipt list with status badges (Pending / Approved / Rejected / Flagged)
- Progress bar per relief category (with 80% warning threshold)
- Estimated tax savings based on tax bracket input
- Filter by category, date, status
- Quick actions: view, download, delete

#### HR Admin Dashboard
- Employee list with claim summary
- Pending approvals queue
- Approve / Reject with optional comment
- Bulk approve all pending
- Download ZIP per employee or all employees
- Policy settings tab (superadmin only)

#### Role-Based Rendering
Single codebase, single CSS design system — content gated by role:
```
individual      → personal dashboard only
employee        → personal dashboard (within org)
hr_admin        → personal + org management tabs
superadmin      → personal + org + policy + billing tabs
```

---

### 3.5 Download & Export

#### Individual
- Download single receipt (original image)
- Bulk download filtered receipts as ZIP
- ZIP structure:
```
ResitCukai_BE_2025_[Nama].zip
├── Perubatan/
│   ├── klinik-faiza-14jun.jpg
│   └── pantai-8mar.pdf
├── Gaya_Hidup/
│   └── popular-2may.jpg
└── Ringkasan_Tuntutan.pdf
```

#### Corporate (HR Admin)
- Download ZIP per employee
- Download ZIP for all employees:
```
SyarikatABC_BE_2025.zip
├── Ahmad_Mukhriz/
│   ├── Perubatan/ (3 files)
│   ├── Gaya_Hidup/ (2 files)
│   └── Ringkasan_Claim.pdf
├── Siti_Nabilah/
│   └── ...
└── Laporan_Syarikat_BE_2025.pdf
```
- `Ringkasan_Claim.pdf` per employee: list of receipts, amounts, categories, BE section
- `Laporan_Syarikat_BE_2025.pdf`: aggregate company report

---

### 3.6 MVP Non-Functional Requirements

#### Security
- Stateful server-side sessions (see architecture.md)
- HTTPS enforced everywhere
- Receipt images stored in private R2 bucket — presigned URLs only (15-min TTL)
- SHA-256 duplicate detection before storage
- Domain validation for corporate employee registration
- QR session tokens: cryptographically random, single-device, short-lived

#### Performance
- Receipt OCR + classification: < 10 seconds
- Dashboard load: < 2 seconds
- WebSocket sync latency: < 500ms

#### Data Retention
- Receipt images retained for 7 years (LHDN audit requirement)
- User can request deletion (subject to PDPA Malaysia)
- Soft delete — images marked deleted, purged after 30 days

#### Compliance
- PDPA Malaysia compliant
- Data stored in Malaysia region (or Singapore closest fallback)

---

### 3.7 MVP Release Plan

| Milestone | Timeline | Deliverable |
|---|---|---|
| M1 | Month 1 | Auth, onboarding, local upload, OCR |
| M2 | Month 2 | AI classify, rule engine, QR handoff, WebSocket, personal dashboard |
| M3 | Month 3 | Corporate onboarding, HR dashboard, ZIP export |
| M4 | Month 4 | QA, security audit, soft beta launch |

---

## 4. Phase 2 — Post-MVP (Month 5–8)

Phase 2 focuses on **retention and habit-forming use**. Features here turn Resit.my from a once-a-year tax tool into something users open throughout the year.

> **Status pelaksanaan (Jun 2026):** Kebanyakan ciri Fasa 2 sudah dibina dalam kod. Rujuk Jadual 1.4 untuk butiran. Yang belum: eksport ZIP korporat pukal, penjadualan eksport CSV automatik penuh, dan beberapa nudge kalendar pintar.

---

### 4.1 Multi-Year Tax History
**Status:** ✅ Siap
**Why:** Without history, the app resets to zero value every year. Users need continuity.

- Year selector on dashboard (e.g. 2024, 2025, 2026)
- Each year maintains its own claim summary, receipt list, and limits (already supported in schema via `relief_limits` table)
- "Compare to last year" view — total claimed, savings, category breakdown side by side
- Receipts auto-archive by receipt date, not upload date (a January upload of a December receipt belongs to the previous tax year)
- Year-end reminder: "Tahun cukai 2025 akan ditutup pada 28 Februari 2026 — semak resit anda"

---

### 4.2 Smart Reminders & Notifications
**Status:** ✅ Sebahagian (in-app + keutamaan e-mel; skrip `send_notification_digests.py`)
**Why:** Users should upload receipts as expenses happen, not in a March scramble.

- Email/in-app reminder when a category has zero receipts near year-end (e.g. "Anda belum upload sebarang resit pendidikan tahun ini")
- Monthly digest email: "Anda telah claim RM2,400 bulan ini. RM5,600 lagi untuk had perubatan."
- Smart calendar nudges — SSPN reminder in January, education-related in school term starts
- Configurable notification preferences (email, in-app, frequency)
- Corporate: "Reimbursement window closing" alert for employees

---

### 4.3 Automatic Mixed-Item Receipt Splitting
**Status:** ✅ Siap
**Why:** Pharmacy receipts mixing medicine and toiletries is one of the most common real-world cases. Manual review doesn't scale.

- LLM classifies at line-item level, not whole-receipt
- Each line item gets its own category tag and claimable flag
- User sees itemized breakdown with claimable items pre-checked
- User can toggle individual line items in/out of the claim
- Partial claim amount auto-calculated from selected items only

---

### 4.4 Spouse / Family Joint Filing Support
**Status:** ✅ Siap
**Why:** Malaysian tax filing frequently involves spouses optimizing which partner claims which relief. Strong differentiator unique to local context.

- Link spouse account — consent-based, both parties must approve the link
- Shared household view: combined relief usage across both accounts
- "Smart suggest" — recommends which spouse should claim a given receipt based on:
  - Who has more remaining limit in that category
  - Who is in the higher tax bracket (bigger savings from the relief)
- Receipts can be reassigned between linked accounts before submission
- Each spouse's Borang BE remains separately filed — this is a planning tool, not a joint return

---

### 4.5 CSV / Payroll Export
**Status:** ✅ Siap (`GET /org/export/csv`, templat `generic`; skrip `send_monthly_org_exports.py`)
**Why:** Corporate customers need to feed approved claims into payroll systems. Manual copy-paste from the app doesn't scale.

- Export approved claims as CSV with configurable column mapping
- Common payroll system templates (generic CSV + templates for common Malaysian payroll providers)
- Scheduled auto-export — HR receives CSV on the 1st of every month
- Export includes: employee ID, name, category, amount, approval date, approver name

---

### 4.6 In-App Receipt Editing Tools
**Status:** ✅ Sebahagian (manual entry, nota, reprocess, edit kategori/jumlah/line items; crop/rotate/merge belum)
**Why:** OCR/AI gets it wrong sometimes. Broader editing options reduce support requests and improve data quality.

- Crop/rotate receipt image before processing (common issue: angled photos)
- Manual re-trigger OCR after crop
- Manual entry mode — fully bypass OCR for illegible receipts (faded thermal paper)
- Merge two images into one record (front + back of a long receipt)
- Receipt notes field — free text for personal reference

---

### 4.7 Org Analytics Dashboard
**Status:** ✅ Siap (`GET /org/analytics`, UI dalam `/dashboard/org`)
**Why:** Once a company has months of data, HR and finance want trend insight, not just an approvals queue.

- Spend by category trend over time (chart)
- Top claiming employees / departments
- Average approval turnaround time
- Rejected claim reasons breakdown (helps HR refine policy)
- Forecasted year-end relief utilization across the org
- Exportable as PDF report for management presentation

---

### 4.8 In-App Borang BE Filing Guide
**Status:** ✅ Siap (`GET /claims/ready-to-file`, halaman `/dashboard/ready-to-file`)
**Why:** Users still file manually with LHDN. A guided summary at filing time reduces friction and keeps users in the app during the most critical moment.

- "Ready to File" view — shows exactly which Borang BE field to fill and what amount, mapped to LHDN e-Filing section order
- Step-by-step walkthrough matching LHDN e-Filing field order
- Printable filing checklist PDF
- Does **not** auto-submit to LHDN (no official API exists) — purely a reference/guidance layer

---

## 5. Phase 3 — Growth Features (Month 9+ / traction-dependent)

Phase 3 features are only built once Phase 1 and 2 have validated user behaviour and there is clear demand signal.

---

### 5.1 LHDN MyTax Integration
**Why:** Natural end-state of this product — dependent on LHDN exposing a public or partner API.

- Pre-fill Borang BE e-Filing fields directly via LHDN API (if available)
- Until then: Phase 2 filing guide remains the ceiling
- **Note:** Verify API availability before committing to roadmap. No public LHDN API currently exists (June 2025).

---

### 5.2 Receipt Forwarding via Email & WhatsApp
**Why:** Lowest-friction upload channel. Users receive e-receipts in email or get receipts sent by a spouse/assistant via WhatsApp.

- Unique forwarding email per user (e.g. `ahmad-x7f2@receipts.resit.my`) — forward any e-receipt and it auto-processes
- WhatsApp Business API integration — send a receipt photo to a dedicated number, auto-classified
- Both methods reuse the existing OCR/classify pipeline — no new AI work needed

---

### 5.3 Bank / E-Wallet Transaction Matching
**Why:** Catches missed receipts by prompting users when a transaction matches a likely-claimable merchant.

- Optional bank statement CSV upload or open banking connection (opt-in only)
- Match transactions to likely-eligible merchants (e.g. "RM450 at Klinik Pergigian Sentosa — upload resit?")
- Strictly opt-in, separate consent flow — this touches sensitive financial data
- Requires dedicated security and compliance review before building

---

### 5.4 Multi-Company Support for Tax Agents
**Why:** Tax agents and bookkeepers manage filings for multiple individuals or SMEs. Currently the app assumes one org per user.

- "Agent" role — invited into multiple individual or org accounts with restricted access (view + prepare, not approve)
- Switch between managed clients from a single login
- Target segment: small accounting firms offering this as value-add to clients

---

### 5.5 Custom Relief Categories for Borang B & P
**Why:** Borang BE is the MVP wedge. Borang B (business income) and Borang P (partnership) have different relief structures — long-term market expansion.

- Configurable relief category sets per form type
- User selects form type at onboarding (BE, B, P) — app adjusts categories and limits
- Schema already supports this via extensible `relief_limits.category` field

---

### 5.6 Engagement & Gamification Layer
**Status:** ✅ Asas (`GET /claims/completeness` — skor kelengkapan + mesej pencapaian)
**Why:** Gives users a reason to open the app outside tax season.

- "Claim completeness" score — visual indicator of how thoroughly a user is tracking the year
- Milestone notifications: "Anda telah jimat RM1,000 tahun ini!"
- Annual year-end summary (shareable — not aggressive virality)

---

## 6. Explicitly Not Planned

Features considered and explicitly rejected to keep scope honest:

| Feature | Reason |
|---|---|
| Automated LHDN e-Filing submission | No public LHDN API; unofficial workarounds carry compliance risk |
| Cryptocurrency / investment relief tracking | Outside Borang BE individual relief scope |
| Full accounting / bookkeeping suite | Scope creep — this is a relief-tracking tool, not a general ledger |
| Native mobile app | Web + QR handoff covers the camera use case; revisit only if usage data demands it |

---

## 7. Full Feature Prioritization

| Feature | Phase | User Impact | Complexity |
|---|---|---|---|
| Auth, upload, OCR, AI classify | 1 — MVP | Critical | Medium |
| QR camera handoff + WebSocket | 1 — MVP | Critical | Medium |
| Personal dashboard + progress bars | 1 — MVP | Critical | Low |
| Corporate onboarding + HR dashboard | 1 — MVP | Critical | Medium |
| ZIP export (individual + corporate) | 1 — MVP | Critical | Low |
| Multi-year tax history | 2 | High | Low |
| Smart reminders & notifications | 2 | High | Medium |
| Mixed-item receipt splitting | 2 | High | Medium-High |
| Spouse joint filing support | 2 | High (differentiator) | Medium |
| CSV / payroll export | 2 | Medium (corporate) | Low |
| In-app receipt editing tools | 2 | Medium | Low |
| Org analytics dashboard | 2 | Medium (corporate) | Medium |
| Borang BE filing guide | 2 | High | Low-Medium |
| LHDN MyTax integration | 3 | Very High (if possible) | Unknown |
| Email / WhatsApp forwarding | 3 | High | Medium |
| Bank transaction matching | 3 | Medium | High |
| Multi-company agent support | 3 | Medium (niche) | Medium |
| Borang B / P custom categories | 3 | Low (TAM expansion) | Medium |
| Gamification layer | 3 | Low-Medium | Low |

---

## 8. Open Questions

- Should **spouse joint filing** (4.4) be pulled earlier — possibly Phase 1.5 — given it was flagged as a strong differentiator from the start?
- Is there appetite to validate a Malaysian open banking provider for 5.3 before committing engineering time?
- For 5.4 (multi-company agent support) — is there interest in directly targeting accounting firms as a B2B2C acquisition channel?
