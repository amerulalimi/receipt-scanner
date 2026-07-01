# API Specification
## Resit.my — FastAPI Endpoint Reference
**Version:** 1.1.0  
**Base URL:** `{host}/api/v1` (contoh produksi: `https://api.resit.my/api/v1`)  
**Auth:** Stateful server-side session via `resit_sess` cookie  
**Format:** JSON (application/json)  
**Last synced with codebase:** June 2026

---

## 0. Implementation Notes

Perbezaan utama antara spesifikasi asal dan pelaksanaan semasa:

| Item | Spesifikasi asal | Pelaksanaan semasa |
|---|---|---|
| Eksport ZIP individu | Job async + poll | `GET /claims/export-zip` — muat turun segera |
| Kelulusan HR | `PATCH /org/receipts/{id}/review` | `POST /receipts/{id}/review` |
| Senarai resit HR | `GET /org/receipts` | `GET /org/pending-receipts` |
| Kelulusan pukal | `POST /org/receipts/bulk-review` | `POST /org/pending-receipts/bulk-approve` |
| Eksport ZIP korporat | `POST /org/bulk-download` | **Belum dilaksanakan** |
| Pengesahan domain | `POST /org/verify-domain` | **Belum dilaksanakan** |
| Thumbnail / fail resit | Presigned URL dalam JSON | `GET /receipts/{id}/file` dan `/thumbnail` — proxy terus |
| Muat naik dengan tahun | — | `tax_year` pada `POST /receipts/upload` dan sesi QR |

Endpoint tambahan yang wujud dalam kod tetapi tiada dalam spesifikasi asal: lihat Bahagian 12–17.

**Health check (tiada auth):** `GET /health` → `{ "data": { "status": "ok" }, "error": null }`

---

## 1. Convention

### Request Headers
```
Content-Type: application/json
Cookie: resit_sess=<session_id>       # all authenticated routes
```

### Standard Response Envelope
```json
{
  "success": true,
  "data": { ... },
  "message": null
}
```

### Error Response
```json
{
  "success": false,
  "data": null,
  "message": "Keterangan ralat",
  "code": "ERROR_CODE"
}
```

### Common Error Codes
| Code | HTTP | Meaning |
|---|---|---|
| `UNAUTHORIZED` | 401 | No valid session |
| `FORBIDDEN` | 403 | Insufficient role |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Request body invalid |
| `DUPLICATE_RECEIPT` | 409 | Image hash already exists |
| `SESSION_EXPIRED` | 401 | QR upload session expired |
| `LIMIT_EXCEEDED` | 409 | Category relief limit reached |
| `RATE_LIMITED` | 429 | Too many requests |

---

## 2. Auth Endpoints

### `POST /auth/register`
Register new user (individual or corporate).

**Request:**
```json
{
  "email": "user@example.com",
  "password": "min8chars",
  "full_name": "Ahmad Mukhriz",
  "account_type": "individual"    // "individual" | "corporate"
}
```

**Response `201`:**
```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "email": "user@example.com",
    "email_verified": false
  },
  "message": "E-mel pengesahan telah dihantar"
}
```

---

### `POST /auth/login`
Authenticate and create server session.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "role": "hr_admin",
    "org_id": "uuid | null",
    "full_name": "Ahmad Mukhriz"
  }
}
```
**Set-Cookie:** `resit_sess=<session_id>; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=28800`

**Rate limit:** 5 requests / 15 min / IP

---

### `POST /auth/refresh`
Perbaharui TTL sesi aktif. Set semula cookie `resit_sess`.

**Response `200`:**
```json
{ "success": true, "data": null, "message": null }
```

---

### `PATCH /auth/me`
Kemas kini profil pengguna (nama, tahun cukai, bracket cukai).

**Request:**
```json
{
  "full_name": "Ahmad Mukhriz",
  "tax_year": 2025,
  "tax_bracket": 15.0
}
```

---

### `POST /auth/resend-verification`
Hantar semula e-mel pengesahan. Memerlukan sesi aktif.

**Response `200`:**
```json
{ "success": true, "data": null, "message": "E-mel pengesahan telah dihantar semula" }
```

---

### `POST /auth/logout`
Destroy server session.

**Response `200`:**
```json
{ "success": true, "data": null, "message": "Logged out" }
```
**Clears cookie** and deletes session from Redis.

---

### `GET /auth/me`
Get current authenticated user.

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "email": "user@example.com",
    "full_name": "Ahmad Mukhriz",
    "role": "hr_admin",
    "org_id": "uuid | null",
    "org_name": "Syarikat ABC Sdn Bhd | null",
    "tax_year": 2025,
    "tax_bracket": 15.0
  }
}
```

---

### `POST /auth/verify-email`
Verify email with token from inbox.

**Request:**
```json
{ "token": "verification-token-from-email" }
```

**Response `200`:**
```json
{ "success": true, "data": { "email_verified": true } }
```

---

### `GET /auth/sessions`
List active sessions for current user (for security/concurrent session management).

**Response `200`:**
```json
{
  "success": true,
  "data": [
    {
      "session_id": "masked-uuid",
      "ip": "203.x.x.x",
      "user_agent": "Mozilla/5.0 (Windows...)",
      "created_at": "2025-06-14T08:00:00Z",
      "last_active": "2025-06-14T09:30:00Z",
      "is_current": true
    }
  ]
}
```

---

### `DELETE /auth/sessions/{session_id}`
Revoke a specific session (log out other device).

**Response `200`:**
```json
{ "success": true, "data": null, "message": "Sesi telah ditamatkan" }
```

---

## 3. Organisation Endpoints

### `POST /org/register`
Register a new organisation. Caller becomes superadmin.

**Request:**
```json
{
  "name": "Syarikat ABC Sdn Bhd",
  "ssm_number": "202301012345",
  "email_domain": "syarikat.com.my"
}
```

**Response `201`:**
```json
{
  "success": true,
  "data": {
    "org_id": "uuid",
    "name": "Syarikat ABC Sdn Bhd",
    "email_domain": "syarikat.com.my",
    "domain_verified": false
  }
}
```

---

### `POST /org/verify-domain`
Confirm domain ownership (via DNS TXT or email).

**Request:**
```json
{ "method": "email" }    // "email" | "dns"
```

---

### `GET /org/me`
Get current user's organisation details.

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "org_id": "uuid",
    "name": "Syarikat ABC Sdn Bhd",
    "ssm_number": "202301012345",
    "email_domain": "syarikat.com.my",
    "domain_verified": true,
    "total_employees": 48,
    "policy": {
      "allowed_categories": ["perubatan", "gaya_hidup", "pendidikan"],
      "require_hr_approval": true,
      "max_receipts_per_month": 50,
      "tax_year": 2025
    }
  }
}
```

---

### `PATCH /org/policy`
Update organisation policy. **Superadmin only.**

**Request:**
```json
{
  "allowed_categories": ["perubatan", "pendidikan"],
  "require_hr_approval": true,
  "max_receipts_per_month": 30
}
```

---

### `GET /org/employees`
List all employees in org. **HR Admin + Superadmin.**

**Query params:** `?page=1&limit=20&search=ahmad&status=active`

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "user_id": "uuid",
        "full_name": "Ahmad Mukhriz",
        "email": "ahmad@syarikat.com.my",
        "role": "employee",
        "is_active": true,
        "receipts_count": 12,
        "total_claimed": 5760.00,
        "pending_count": 3
      }
    ],
    "total": 48,
    "page": 1,
    "limit": 20
  }
}
```

---

### `PATCH /org/employees/{user_id}`
Activate or deactivate employee. **HR Admin + Superadmin.**

**Request:**
```json
{ "is_active": false }
```

---

## 4. Invite Endpoints

### `POST /invites/hr-admin`
Send HR admin invite. **Superadmin only.**

**Request:**
```json
{ "email": "hr@syarikat.com.my" }
```

**Response `201`:**
```json
{
  "success": true,
  "data": {
    "invite_id": "uuid",
    "email": "hr@syarikat.com.my",
    "expires_at": "2025-06-16T08:00:00Z"
  }
}
```

---

### `POST /invites/employees`
Invite employees. **HR Admin + Superadmin.**

**Request (manual):**
```json
{
  "type": "email",
  "emails": ["siti@syarikat.com.my", "razif@syarikat.com.my"]
}
```

**Request (link — open invite):**
```json
{ "type": "link" }
```

**Request (CSV):**
```
Content-Type: multipart/form-data
file: employees.csv
```

**Response `201`:**
```json
{
  "success": true,
  "data": {
    "type": "link",
    "invite_url": "https://resit.my/join/abc123xyz",
    "expires_at": "2025-06-21T08:00:00Z",
    "invited_count": 1
  }
}
```

---

### `POST /invites/accept`
Accept an invite and complete registration.

**Request:**
```json
{
  "token": "invite-token-from-link",
  "email": "pekerja@syarikat.com.my",
  "password": "password123",
  "full_name": "Siti Nabilah"
}
```

**Response `201`:** — creates user + auth session (logged in immediately)

---

### `GET /invites/validate/{token}`
Check if invite token is valid (before showing registration form).

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "valid": true,
    "org_name": "Syarikat ABC Sdn Bhd",
    "role": "employee",
    "invited_email": null,
    "expires_at": "2025-06-21T08:00:00Z"
  }
}
```

---

## 5. Receipt Endpoints

### `POST /receipts/upload`
Upload receipt from local storage (desktop).

**Request:**
```
Content-Type: multipart/form-data
files: [file1.jpg, file2.pdf]     // max 20 files, 10MB each
tax_year: 2025                    // optional form field
```

**Response `202`:** (processing async)
```json
{
  "success": true,
  "data": {
    "job_ids": ["uuid1", "uuid2"],
    "message": "2 resit sedang diproses"
  }
}
```

---

### `GET /receipts`
List user's receipts with filters.

**Query params:**
```
?tax_year=2025
&category=perubatan       // filter by category
&status=pending           // pending|approved|rejected|flagged
&page=1
&limit=20
&sort=created_at:desc
```

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "merchant_name": "Klinik Faiza Sdn Bhd",
        "receipt_date": "2025-06-14",
        "total_amount": 320.00,
        "claimed_amount": 320.00,
        "category": "perubatan",
        "be_seksyen": "S.46(1)(b)",
        "status": "approved",
        "scan_status": "success",
        "ai_confidence": 0.97,
        "file_type": "jpg",
        "thumbnail_url": "https://...",   // presigned, 15-min TTL
        "created_at": "2025-06-14T10:00:00Z"
      }
    ],
    "total": 23,
    "page": 1,
    "limit": 20
  }
}
```

---

### `GET /receipts/{receipt_id}`
Get single receipt detail.

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "merchant_name": "Klinik Faiza Sdn Bhd",
    "receipt_date": "2025-06-14",
    "total_amount": 320.00,
    "claimed_amount": 320.00,
    "excluded_amount": 0,
    "category": "perubatan",
    "be_seksyen": "S.46(1)(b)",
    "status": "approved",
    "scan_status": "success",
    "ai_confidence": 0.97,
    "ai_nota": "Klinik persendirian, consultation + ubat",
    "notes": "Nota peribadi pengguna",
    "line_items": [
      {
        "id": "uuid",
        "description": "Ubat",
        "amount": 120.00,
        "category": "perubatan",
        "ai_claimable": true,
        "included_in_claim": true,
        "sort_order": 0
      }
    ],
    "ocr_confidence": 0.94,
    "image_url": "https://...",       // presigned, 15-min TTL
    "flags": [],
    "reviewed_by": null,
    "reviewed_at": null,
    "created_at": "2025-06-14T10:00:00Z"
  }
}
```

---

### `PATCH /receipts/{receipt_id}`
Edit category, claimed amount, notes, or line-item inclusion.

**Request:**
```json
{
  "category": "gaya_hidup",
  "claimed_amount": 150.00,
  "notes": "Nota peribadi",
  "line_items": [
    { "id": "uuid", "included_in_claim": true, "category": "perubatan" }
  ]
}
```

---

### `POST /receipts`
Create receipt record with pre-uploaded storage key (advanced / internal flow).

---

### `POST /receipts/manual`
Manual entry — bypass OCR for illegible receipts.

**Request:**
```json
{
  "merchant_name": "Klinik Faiza",
  "receipt_date": "2025-06-14",
  "total_amount": 320.00,
  "category": "perubatan",
  "claimed_amount": 320.00,
  "notes": "Resit kertas thermal pudar",
  "tax_year": 2025
}
```

---

### `POST /receipts/{receipt_id}/reprocess`
Re-queue receipt for AI classification (after admin fixes model config).

---

### `POST /receipts/{receipt_id}/review`
Approve or reject receipt. **HR Admin + Superadmin.**

**Request:**
```json
{
  "action": "approve",
  "comment": "Resit jelas, layak dituntut"
}
```

---

### `GET /receipts/{receipt_id}/file`
Stream original receipt image/PDF (authenticated proxy).

---

### `GET /receipts/{receipt_id}/thumbnail`
Stream receipt thumbnail image.

---

### `DELETE /receipts/{receipt_id}`
Soft delete a receipt.

**Response `200`:**
```json
{ "success": true, "data": null, "message": "Resit dipadam" }
```

---

### `GET /receipts/{receipt_id}/download`
Get presigned download URL for original image.

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "download_url": "https://r2.resit.my/...",
    "expires_in": 900,    // seconds (15 min)
    "file_name": "klinik-faiza-14jun.jpg"
  }
}
```

---

### `POST /receipts/bulk-download`
> **Belum dilaksanakan.** Guna `GET /claims/export-zip` untuk eksport ZIP individu segera.

---

### `GET /claims/export-zip`
Generate and download ZIP for user's receipts in a tax year. **Synchronous.**

**Query:** `?tax_year=2025`

**Response `200`:** `application/zip` attachment

---

### `GET /claims/compare`
Year-over-year claim comparison.

**Query:** `?tax_year=2025` (tahun semasa; tahun sebelumnya auto)

---

### `GET /claims/ready-to-file`
Borang BE filing guide — field mapping, checklist, jumlah tuntutan.

**Query:** `?tax_year=2025`

---

### `GET /claims/completeness`
Claim completeness score and milestone message (engagement).

**Query:** `?tax_year=2025`

---

## 6. Claim Summary Endpoints

### `GET /claims/summary`
Get user's claim totals per category for a tax year.

**Query params:** `?tax_year=2025`

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "tax_year": 2025,
    "tax_bracket": 15.0,
    "estimated_savings": 1236.00,
    "categories": [
      {
        "category": "perubatan",
        "be_seksyen": "S.46(1)(b)",
        "limit": 8000.00,
        "claimed": 4800.00,
        "remaining": 3200.00,
        "percentage": 60.0,
        "receipt_count": 6,
        "status": "ok"         // ok | warning | full
      },
      {
        "category": "gaya_hidup",
        "be_seksyen": "S.46(1)(k)",
        "limit": 3000.00,
        "claimed": 2700.00,
        "remaining": 300.00,
        "percentage": 90.0,
        "receipt_count": 5,
        "status": "warning"
      }
    ]
  }
}
```

---

## 7. HR Approval Endpoints

### `GET /org/pending-receipts`
List pending employee receipts. **HR Admin + Superadmin.**

**Query params:** `?tax_year=2025&page=1&limit=20`

---

### `POST /org/pending-receipts/bulk-approve`
Approve all pending receipts in org (optionally filtered by tax year). **HR Admin + Superadmin.**

**Query:** `?tax_year=2025`

**Response `200`:**
```json
{
  "success": true,
  "data": { "approved_count": 12, "skipped_count": 2 }
}
```

---

### `GET /org/analytics`
Org spend trends, top claimers, approval turnaround. **HR Admin + Superadmin.**

**Query:** `?tax_year=2025`

---

### `GET /org/export/csv`
Export approved claims as payroll CSV.

**Query:** `?tax_year=2025&template=generic`

**Response `200`:** `text/csv` attachment

---

### `POST /org/employees/bulk-import`
Bulk import employees by email list (JSON body, not multipart CSV).

**Request:**
```json
{
  "employees": [
    { "email": "siti@syarikat.com.my", "full_name": "Siti", "employee_code": "E001" }
  ]
}
```

---

### `DELETE /org/employees/{user_id}`
Remove employee from organisation. **HR Admin + Superadmin.**

---

### Endpoints asal (rujukan — belum / berbeza)

`GET /org/receipts`, `PATCH /org/receipts/{id}/review`, `POST /org/receipts/bulk-review`, `POST /org/bulk-download` — **tidak wujud**; guna endpoint di atas.

---

## 8. QR Upload Session Endpoints

### `POST /upload-sessions`
Generate QR token for mobile camera handoff. **Authenticated desktop user.**

**Request (optional body):**
```json
{ "tax_year": 2025 }
```

**Response `201`:**
```json
{
  "success": true,
  "data": {
    "token": "abc123...",
    "upload_url": "https://resit.my/upload/session/abc123...",
    "qr_data": "https://resit.my/upload/session/abc123...",
    "inactivity_timeout": 600,
    "expires_at": "2025-06-15T08:00:00Z"    // hard max 24h
  }
}
```

---

### `GET /upload-sessions/{token}/validate`
Mobile validates token before showing camera UI. **No auth required.**

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "valid": true,
    "user_name": "Ahmad",
    "uploads_so_far": 3,
    "inactivity_remaining": 487    // seconds
  }
}
```

**Response `401`:** (expired)
```json
{
  "success": false,
  "data": null,
  "code": "SESSION_EXPIRED",
  "message": "Sesi telah tamat. Sila imbas QR baru."
}
```

---

### `POST /upload-sessions/{token}/upload`
Mobile uploads receipt image. **No auth — token-gated.**

**Request:**
```
Content-Type: multipart/form-data
file: receipt.jpg
```

**Response `202`:**
```json
{
  "success": true,
  "data": {
    "job_id": "uuid",
    "session_inactivity_reset": true,
    "new_inactivity_remaining": 600
  }
}
```

---

### `POST /upload-sessions/{token}/keep-alive`
Reset inactivity timer without uploading. **No auth — token-gated.**

**Response `200`:**
```json
{
  "success": true,
  "data": { "inactivity_remaining": 600 }
}
```

---

### `POST /upload-sessions/{token}/close`
Mobile user taps "Done" — signals desktop to resume. **No auth — token-gated.**

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "uploads_count": 5,
    "message": "Sesi selesai. Sambung di desktop anda."
  }
}
```

---

## 9. WebSocket

### `WS /ws/dashboard`
Real-time updates for desktop during QR session. **Authenticated.**

**Client sends (on connect):**
```json
{ "type": "subscribe", "upload_session_token": "abc123..." }
```

**Server → Client events:**

```json
// New receipt processed
{ "type": "receipt_added", "data": { "receipt": { ...receipt_object } } }

// Inactivity warning (2 min remaining)
{ "type": "session_warned", "data": { "seconds_remaining": 120 } }

// Session expired
{ "type": "session_expired", "data": { "reason": "inactivity" } }

// Mobile closed session (Done button)
{ "type": "session_closed", "data": { "uploads_count": 5, "total_amount": 1240.00 } }

// Processing failed
{ "type": "receipt_failed", "data": { "job_id": "uuid", "reason": "low_confidence" } }
```

---

## 10. Config Endpoints (Superadmin)

### `GET /config/relief-categories`
Senarai kategori pelepasan aktif. **Semua pengguna authenticated.**

---

### `GET /config/relief-limits`
Get all relief limits (global, tanpa `tax_year`). **Superadmin.**

---

### `POST /config/relief-limits`
Create new relief limit category. **Superadmin.**

---

### `PATCH /config/relief-limits/{category}`
Update a relief limit. **Superadmin.**

**Request:**
```json
{
  "limit_amount": 9000.00,
  "description_my": "Perubatan & Pergigian (dikemaskini)",
  "is_active": true,
  "sort_order": 1
}
```

---

### `DELETE /config/relief-limits/{category}`
Deactivate relief limit. **Superadmin.**

---

### `GET /config/audit-logs`
Senarai audit log (paginated). **Superadmin.**

**Query:** `?action=receipt.approved&page=1&limit=50`

---

### `GET /config/system/overview`
Ringkasan sistem (pengguna, resit, storan). **Superadmin.**

---

### `POST /config/system/purge-retention`
Jalankan pembersihan data lepas tempoh retention. **Superadmin.**

---

### `GET /config/settings`
Senarai tetapan sistem (bukan rahsia). **Superadmin.**

### `PUT /config/settings/{key}` / `PATCH /config/settings`
Urus tetapan seperti model AI, had muat naik, dll.

---

### `GET /config/secrets`
Senarai rahsia (nilai dimask). **Superadmin.**

### `PUT /config/secrets/{key}` / `PATCH /config/secrets`
Urus rahsia terenkripsi (`openrouter_api_key`, dll).

### `GET /config/secrets/openrouter/health`
Uji sambungan OpenRouter + model vision aktif.

---

## 11. Household Endpoints (Spouse Linking)

### `GET /household`
Overview isi rumah — pasangan dipaut, ringkasan gabungan, permintaan menunggu.

---

### `POST /household/spouse-link`
Minta pautan pasangan melalui e-mel.

**Request:** `{ "partner_email": "pasangan@example.com" }`

---

### `POST /household/spouse-link/{link_id}/respond`
Terima atau tolak permintaan. **Request:** `{ "action": "accept" | "reject" }`

---

### `DELETE /household/spouse-link/{link_id}`
Putuskan pautan pasangan.

---

### `POST /household/receipts/{receipt_id}/reassign`
Pindahkan resit kepada pasangan yang dipaut.

**Request:** `{ "target_user_id": "uuid" }`

---

### `GET /household/receipts/{receipt_id}/claim-suggestion`
Cadangan siapa patut menuntut resit (baki had + bracket cukai).

---

## 12. Notification Endpoints

### `GET /notifications/preferences`
### `PATCH /notifications/preferences`

**Preference fields:** `email_enabled`, `in_app_enabled`, `digest_frequency` (`off` | `monthly`)

---

### `GET /notifications`
Senarai notifikasi in-app (auto-sync peringatan tahun/bulan).

---

### `POST /notifications/{notification_id}/dismiss`
Tutup notifikasi.

---

## 13. Rate Limits Summary

| Endpoint | Limit |
|---|---|
| `POST /auth/login` | 5 / 15 min / IP |
| `POST /receipts/upload` | 60 files / hour / user |
| `POST /upload-sessions` | 10 / hour / user |
| `POST /upload-sessions/:token/upload` | 60 / hour / token |
| `POST /org/receipts/bulk-review` | 100 / hour / user |
| All others | 300 / min / user |