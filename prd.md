# Product Requirements Document (PRD)
## Resit.my — Malaysian Tax Relief Receipt Scanner
**Version:** 1.0.0  
**Status:** MVP Scope  
**Last Updated:** June 2025  
**Author:** Internal

---

## 1. Overview

### 1.1 Product Summary
Resit.my is a web-based application that helps Malaysian taxpayers (individuals and corporate employees) scan, classify, and manage receipts for tax relief claims under **Borang BE** (LHDN). The app uses OCR and LLM-based classification to automatically map receipts to the correct relief category and track claim limits in real time.

### 1.2 Problem Statement
Malaysian taxpayers manually collect and categorize receipts throughout the year, often losing track of claim limits, misclassifying receipts, or failing to maximize their tax relief. For corporate HR teams, managing receipt reimbursements and generating audit-ready documentation is time-consuming and error-prone.

### 1.3 Target Users

| Segment | Description |
|---|---|
| Individual | Malaysian resident filing Borang BE annually |
| Corporate Employee | Staff submitting receipts for HR approval |
| HR Admin | Manages employee claims, approves/rejects, generates reports |
| Superadmin | Company owner — manages HR admins, billing, org policy |

### 1.4 Success Metrics (MVP)
- Time to classify a receipt: < 10 seconds
- AI classification accuracy: > 90%
- User can download audit-ready ZIP in < 3 clicks
- Zero data loss on QR handoff session

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

## 3. Features — MVP Scope

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

#### Step 1 — OCR (Google Vision API)
- Extracts: merchant name, total amount, date, line items
- Confidence score returned per field
- If overall confidence < 70%: flagged for manual review

#### Step 2 — LLM Classification (Claude Haiku)
- Input: OCR extracted text
- Output: structured JSON
```json
{
  "kategori": "perubatan",
  "seksyen": "S.46(1)(b)",
  "jumlah_claim": 320.00,
  "jumlah_tidak_layak": 0,
  "confidence": 0.97,
  "nota": "Klinik persendirian, consultation + ubat"
}
```
- Mixed receipts (partially claimable): flagged for HR review

#### Step 3 — Rule Engine Validation
- Validates against current LHDN relief limits (stored in DB, updatable)
- Detects duplicate receipts via SHA-256 image hash
- Flags if category limit would be exceeded

#### Relief Categories Supported (Borang BE 2024)

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
Single codebase, content gated by role:
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

## 4. Non-Functional Requirements

### 4.1 Security
- Stateful server-side sessions (see Architecture doc)
- HTTPS enforced everywhere
- Receipt images stored in private S3/R2 bucket — presigned URLs only
- SHA-256 duplicate detection before storage
- Domain validation for corporate employee registration
- QR session tokens: cryptographically random, single-device, short-lived

### 4.2 Performance
- Receipt OCR + classification: < 10 seconds
- Dashboard load: < 2 seconds
- WebSocket sync latency: < 500ms

### 4.3 Data Retention
- Receipt images retained for 7 years (LHDN audit requirement)
- User can request deletion (subject to PDPA Malaysia)
- Soft delete — images marked deleted, purged after 30 days

### 4.4 Compliance
- PDPA Malaysia compliant
- Data stored in Malaysia region (or Singapore closest fallback)

---

## 5. Out of Scope (MVP)

- Mobile native app (iOS/Android)
- Google SSO / social login
- Split mixed-item receipts automatically
- CSV export for payroll integration
- HR system API integration
- Analytics dashboard for org
- Multi-year tax filing history
- Automated Borang BE form filling

---

## 6. Release Plan

| Milestone | Timeline | Deliverable |
|---|---|---|
| M1 | Month 1 | Auth, onboarding, local upload, OCR |
| M2 | Month 2 | AI classify, rule engine, QR handoff, WebSocket, personal dashboard |
| M3 | Month 3 | Corporate onboarding, HR dashboard, ZIP export |
| M4 | Month 4 | QA, security audit, soft beta launch |