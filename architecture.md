# Architecture Document
## Resit.my — System Architecture
**Version:** 1.1.0  
**Stack:** Next.js 15 · React 19 · FastAPI · PostgreSQL · Redis · Shadcn/UI  
**Last synced with codebase:** June 2026

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                         │
│                                                             │
│   ┌──────────────────────┐   ┌───────────────────────────┐  │
│   │   Next.js Web App    │   │  Mobile Browser (QR)      │  │
│   │   (Desktop/Laptop)   │   │  /upload/session/:token   │  │
│   │   Shadcn/UI          │   │  No login required        │  │
│   └──────────┬───────────┘   └────────────┬──────────────┘  │
└──────────────┼─────────────────────────────┼────────────────┘
               │ HTTPS + WSS                 │ HTTPS
┌──────────────▼─────────────────────────────▼────────────────┐
│                      API GATEWAY (FastAPI)                   │
│                                                             │
│   ┌────────────────────────────────────────────────────┐    │
│   │  Session Middleware (stateful, server-side)        │    │
│   │  Rate Limiter · CORS · Request Validator           │    │
│   └────────────────────────────────────────────────────┘    │
│                                                             │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐   │
│   │   Auth   │ │ Receipt  │ │   Org    │ │  WebSocket  │   │
│   │  Router  │ │  Router  │ │  Router  │ │   Manager   │   │
│   └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬──────┘   │
└────────┼────────────┼────────────┼───────────────┼──────────┘
         │            │            │               │
┌────────▼────────────▼────────────▼───────────────▼──────────┐
│                     SERVICE LAYER                            │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐   │
│  │AuthService  │  │ReceiptService│  │   OrgService      │   │
│  │SessionStore │  │OCRService    │  │   InviteService   │   │
│  └──────┬──────┘  │ClassifyServ  │  └─────────┬─────────┘   │
│         │         │RuleEngine    │            │              │
│         │         └──────┬───────┘            │              │
└─────────┼────────────────┼────────────────────┼─────────────┘
          │                │                    │
┌─────────▼────────────────▼────────────────────▼─────────────┐
│                    INFRASTRUCTURE LAYER                      │
│                                                             │
│  ┌──────────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐   │
│  │  PostgreSQL  │  │  Redis   │  │ S3 / R2  │  │ SMTP   │   │
│  │  (primary)   │  │(sessions │  │(receipt  │  │(email  │   │
│  │              │  │+ queues) │  │ images)  │  │invite) │   │
│  └──────────────┘  └──────────┘  └──────────┘  └────────┘   │
│                                                             │
│  ┌──────────────────────────┐  ┌──────────────────────────┐  │
│  │   OpenRouter Vision API  │  │   (via openrouter.ai)    │  │
│  │   OCR + Classification   │  │   Model: gemini-2.5-flash│  │
│  │   (single multimodal LLM)│  │   (configurable in admin)│  │
│  └──────────────────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Session Strategy — Stateful Server-Side Sessions

### Why Stateful Over Stateless (JWT)

| Concern | JWT (Stateless) | Stateful Sessions |
|---|---|---|
| Revocation | Cannot revoke before expiry | Instant revoke — delete from Redis |
| Security on logout | Token still valid until expiry | Session destroyed immediately |
| Compromised token | No recourse | Invalidate server-side |
| Concurrent session control | Complex | Simple — list active sessions per user |
| QR token management | Awkward | Natural — store arbitrary session data |

For this app specifically — HR admin approving claims, medical data, QR handoff tokens — **stateful sessions are the correct choice.**

### Session Implementation

```
Client              Next.js              FastAPI              Redis
  │                    │                    │                   │
  │── POST /login ────►│                    │                   │
  │                    │── validate creds ─►│                   │
  │                    │                    │── SET session ───►│
  │                    │                    │   key: sess:{id}  │
  │                    │                    │   TTL: 8 hours    │
  │                    │◄── session_id ─────│                   │
  │◄── Set-Cookie ─────│                    │                   │
  │    HttpOnly        │                    │                   │
  │    Secure          │                    │                   │
  │    SameSite=Lax    │                    │                   │
  │                    │                    │                   │
  │── GET /dashboard ─►│                    │                   │
  │    Cookie: sess_id │── forward cookie ─►│                   │
  │                    │                    │── GET sess:{id} ─►│
  │                    │                    │◄── session data ──│
  │◄── 200 OK ─────────│◄── user context ───│                   │
```

### Session Data Structure (Redis)

```json
{
  "session_id": "uuid-v4",
  "user_id": "uuid",
  "role": "hr_admin",
  "org_id": "uuid | null",
  "email": "user@syarikat.com.my",
  "created_at": "2025-06-14T08:00:00Z",
  "last_active": "2025-06-14T09:30:00Z",
  "ip": "203.x.x.x",
  "user_agent": "Mozilla/5.0..."
}
```

### Session Configuration

```python
SESSION_TTL          = 8 hours        # idle expiry
SESSION_RENEW_WINDOW = 30 minutes     # renew if active within last 30min
SESSION_COOKIE       = "resit_sess"
COOKIE_FLAGS         = HttpOnly + Secure + SameSite=Lax
MAX_SESSIONS_PER_USER = 3             # concurrent device limit
```

### QR Upload Session (Separate from Auth Session)

QR tokens are **separate** from user auth sessions — stored in Redis with their own TTL and inactivity logic:

```json
{
  "qr_token": "cryptorandom-32bytes",
  "user_id": "uuid",
  "desktop_session_id": "uuid",
  "created_at": "...",
  "last_upload_at": "...",
  "inactivity_timeout": 600,
  "status": "active | warned | expired",
  "uploads_count": 4
}
```

Inactivity reset: every successful upload → `last_upload_at = now()` → Redis TTL reset to 600s.

---

## 3. Tech Stack Detail

### Frontend — Next.js 15 (App Router)

```
frontend/src/
├── app/
│   ├── (auth)/login, register/
│   ├── (dashboard)/
│   │   ├── dashboard/          # ringkasan + penapis tahun
│   │   ├── receipts/           # senarai + muat naik
│   │   ├── ready-to-file/      # panduan Borang BE
│   │   ├── household/          # pautan pasangan (individu)
│   │   ├── org/                # HR admin
│   │   └── settings/           # profil, notifikasi, forwarding
│   ├── (admin)/admin/          # superadmin: ai, secrets, system
│   ├── upload/session/[token]/ # halaman kamera QR (mobile)
│   ├── join/[token]/           # penerimaan jemputan
│   └── verify-email/
├── components/                   # shadcn + domain components
├── actions/                    # Server Actions (mutasi data)
├── lib/
│   ├── api/                    # klien fetch server-side ke FastAPI
│   ├── i18n/                   # BM / EN dictionaries
│   └── validations/            # skema Zod dikongsi
└── middleware.ts                 # perlindungan laluan + cookie sesi
```

**Key libraries (pelaksanaan semasa):**
- `shadcn/ui` + Radix — komponen UI
- `react-hook-form` + `zod` — borang & validasi
- `nuqs` — penapis URL (tahun cukai, kategori, status)
- `qrcode.react` — penjanaan QR
- Server Actions + `fetch` — **tiada** axios / TanStack Query / socket.io-client
- WebSocket native (`/ws/dashboard`) untuk sinkron QR

**Corak data:**
- Data awal halaman: Server Components → `lib/api/*`
- Mutasi: Server Actions → FastAPI `/api/v1/*`
- Cookie `resit_sess` diurus oleh FastAPI; Next.js middleware semak kehadiran cookie

### Backend — FastAPI

```
backend/app/
├── main.py                     # lifespan, CORS, /health, /ws/dashboard
├── api/v1/
│   ├── router.py
│   └── routes/
│       ├── auth.py
│       ├── claims.py           # summary, compare, ready-to-file, export-zip
│       ├── household.py        # spouse links
│       ├── notifications.py
│       ├── receipts.py
│       ├── org.py              # employees, analytics, CSV export
│       ├── invites.py
│       ├── upload_sessions.py
│       ├── config_admin.py     # relief limits, audit, retention
│       ├── config_settings.py
│       └── config_secrets.py   # OpenRouter key (encrypted)
├── core/                       # config, session, security, redis, storage
├── repositories/               # akses DB
├── services/
│   ├── vision_llm.py           # OpenRouter multimodal classify
│   ├── receipt_processor.py    # pipeline pemprosesan resit
│   ├── rule_engine.py
│   ├── borang_be.py            # ready-to-file mapping
│   ├── household.py
│   ├── org_analytics.py
│   ├── engagement.py           # completeness score
│   ├── export.py               # ZIP + CSV
│   ├── notifications.py
│   ├── job_queue.py            # Redis queue + WS pub/sub
│   └── storage/                # local (dev) | s3/r2 (prod)
├── models/
└── schemas/
```

### Database — PostgreSQL 15

- Primary data store
- Connection pooling via `asyncpg` + `SQLAlchemy async`
- Migrations via `Alembic`

### Redis

- Auth session store (TTL-based)
- QR upload session store
- Background job queue (receipt processing)
- Rate limiting counters

### File Storage — Local (dev) or S3/R2 (production)

- `STORAGE_BACKEND=local` — fail disimpan di `./storage/receipts` (pembangunan)
- `STORAGE_BACKEND=s3` — S3-compatible (Cloudflare R2 disyorkan untuk produksi)
- Akses fail: proxy melalui `GET /receipts/{id}/file` dan `/thumbnail` (bukan presigned URL dalam senarai)
- `GET /receipts/{id}/download` masih menyediakan URL muat turun jika diperlukan

---

## 4. WebSocket Architecture (QR Sync)

Pemproses resit menerbitkan acara ke saluran Redis (`ws_events_channel`). Proses FastAPI melanggan dan menghantar ke desktop melalui `WS /ws/dashboard`.

```
Receipt worker ──publish──► Redis pub/sub ──subscribe──► FastAPI WS ──► Desktop
Mobile upload ──► FastAPI ──► Redis queue ──► receipt_processor ──► DB + WS event
```

**WebSocket events:**

| Event | Direction | Payload |
|---|---|---|
| `receipt_added` | Server → Desktop | receipt object |
| `receipt_scan_updated` | Server → Desktop | `{receipt_id, scan_status}` |
| `session_warned` | Server → Both | `{seconds_remaining: 120}` |
| `session_expired` | Server → Both | `{reason: "inactivity"}` |
| `session_closed` | Server → Desktop | `{uploads_count, total_amount}` |
| `receipt_failed` | Server → Desktop | `{job_id, reason}` |

Mobile menggunakan REST (`keep-alive`, `close`) — bukan WS client events.

---

## 5. AI Processing Pipeline

```
Receipt Image
      │
      ▼
┌─────────────────────────────────────┐
│  1. Duplicate Check                 │
│     SHA-256(image bytes)            │
│     → Query receipts table          │
│     → If match: reject + notify     │
└──────────────┬──────────────────────┘
               │ unique
               ▼
┌─────────────────────────────────────┐
│  2. Vision LLM — OpenRouter         │
│     Model: openrouter_vision_model  │
│     (default: google/gemini-2.5-    │
│      flash) — multimodal            │
│     Extract + classify in one call  │
│     PDF → skip, flag manual review  │
└──────────────┬──────────────────────┘
               │
       ┌───────▼────────┐
       │ confidence < 70%│
       │ or mixed items  │
       └───┬─────────┬───┘
          Yes        No
           │         │
           ▼         ▼
    Flag: manual  ┌─────────────────────────────────────┐
    review        │  3. Line Items (if mixed receipt)    │
                  │     receipt_line_items rows          │
                  │     ai_claimable + included_in_claim │
                  └──────────────┬──────────────────────┘
                                 │
                                 ▼
                  ┌─────────────────────────────────────┐
                  │  4. Rule Engine                     │
                  │     Load limits from relief_limits  │
                  │     Check category caps             │
                  └──────────────┬──────────────────────┘
                                 │
                                 ▼
                  ┌─────────────────────────────────────┐
                  │  5. Store to DB                     │
                  │     scan_status: success|failed     │
                  │     image → local or S3/R2          │
                  │     Publish WS event via Redis      │
                  └─────────────────────────────────────┘
```

---

## 6. Security Layers

### Authentication & Authorization
- Passwords: `bcrypt` (cost factor 12)
- Session cookie: `HttpOnly`, `Secure`, `SameSite=Lax`
- Role enforcement: FastAPI dependency `require_role(["hr_admin", "superadmin"])`
- Concurrent session limit: 3 active sessions per user

### File Security
- Images stored in **private** R2 bucket
- Access via presigned URLs (15-minute TTL)
- File type validation: magic bytes check (not just extension)
- Max file size: 10MB enforced at API layer

### QR Token Security
- Token: `secrets.token_urlsafe(32)` (256-bit entropy)
- Single device binding (User-Agent check on mobile)
- Desktop-only QR generation (User-Agent gate on desktop)
- Token cannot be reused after expiry or session close

### Rate Limiting (Redis)
- Login: 5 attempts per 15 minutes per IP
- Upload: 60 files per hour per user
- QR generate: 10 per hour per user
- AI classify: 100 per hour per user

### CORS
```python
origins = [
    "https://resit.my",
    "https://www.resit.my",
]
# Development only:
# "http://localhost:3000"
```

---

## 7. Deployment Architecture

```
┌────────────────────────────────────────┐
│           Cloudflare (CDN + WAF)       │
└─────────────────┬──────────────────────┘
                  │
┌─────────────────▼──────────────────────┐
│              VPS / Cloud               │
│                                        │
│  ┌──────────────┐  ┌────────────────┐  │
│  │  Next.js     │  │  FastAPI       │  │
│  │  (port 3000) │  │  (port 8000)   │  │
│  │  PM2 / Docker│  │  Uvicorn+Gunicorn  │
│  └──────────────┘  └────────────────┘  │
│                                        │
│  ┌──────────────┐  ┌────────────────┐  │
│  │  PostgreSQL  │  │  Redis         │  │
│  │  (port 5432) │  │  (port 6379)   │  │
│  └──────────────┘  └────────────────┘  │
└────────────────────────────────────────┘
                  │
┌─────────────────▼──────────────────────┐
│         Cloudflare R2 (file storage)   │
└────────────────────────────────────────┘
```

**Recommended hosting for MVP:** Railway.app or Render.com — simpler ops, auto SSL, easy PostgreSQL + Redis provisioning.

---

## 8. Admin & Configuration (Superadmin)

Panel `/admin` dalam Next.js (superadmin sahaja):

| Halaman | Fungsi |
|---|---|
| `/admin/ai` | Model vision OpenRouter, tetapan klasifikasi |
| `/admin/secrets` | API keys terenkripsi (`system_settings` + Fernet) |
| `/admin/system` | Ringkasan sistem, purge retention, audit |

Rahsia API disimpan dalam jadual `system_settings` (nilai `encrypted_value`). Tetapan bukan-rahsia dalam `system_config`.

Skrip operasi (`backend/scripts/`):
- `send_notification_digests.py` — e-mel digest bulanan
- `send_monthly_org_exports.py` — eksport CSV gaji berjadual
- `requeue_receipts.py` — semula proses resit gagal
- `check_openrouter_health.py` — ujian sambungan AI

---

## 9. Internationalization (i18n)

- Bahasa: **Bahasa Malaysia** (lalai) dan **English**
- Kamus: `frontend/src/lib/i18n/dictionaries/{ms,en}.json`
- Notifikasi dwibahasa: `title_my` / `title_en`, `message_my` / `message_en` dalam `user_notifications`