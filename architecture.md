# Architecture Document
## Resit.my — System Architecture
**Version:** 1.0.0  
**Stack:** Next.js · FastAPI · PostgreSQL · Shadcn/UI

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
│  │   Google Vision API      │  │   Claude API (Haiku)     │  │
│  │   (OCR)                  │  │   (Classification)       │  │
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

### Frontend — Next.js 14 (App Router)

```
src/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/
│   │   ├── layout.tsx          # role-based sidebar
│   │   ├── dashboard/page.tsx  # personal
│   │   ├── receipts/page.tsx
│   │   ├── org/page.tsx        # hr_admin + superadmin
│   │   └── settings/page.tsx
│   └── upload/
│       └── session/[token]/page.tsx  # mobile QR page
├── components/
│   ├── ui/                     # shadcn components
│   ├── receipt/
│   ├── dashboard/
│   └── org/
├── lib/
│   ├── api.ts                  # axios instance
│   ├── session.ts              # client session utils
│   └── websocket.ts            # WS client
└── middleware.ts                # route protection
```

**Key libraries:**
- `shadcn/ui` — component library
- `react-query` (TanStack Query) — server state management
- `zustand` — client UI state
- `socket.io-client` — WebSocket for live sync
- `react-dropzone` — file upload UX
- `qrcode.react` — QR code generation
- `jszip` — client-side ZIP preview (optional)
- `axios` — HTTP client with cookie support (`withCredentials: true`)

### Backend — FastAPI

```
app/
├── main.py
├── core/
│   ├── config.py
│   ├── session.py          # Redis session middleware
│   ├── security.py         # password hash, token gen
│   └── dependencies.py     # get_current_user, require_role
├── routers/
│   ├── auth.py
│   ├── receipts.py
│   ├── org.py
│   ├── upload_session.py   # QR token endpoints
│   └── ws.py               # WebSocket manager
├── services/
│   ├── ocr_service.py      # Google Vision API
│   ├── classify_service.py # Claude Haiku integration
│   ├── rule_engine.py      # LHDN limits validation
│   ├── zip_service.py      # ZIP generation
│   └── email_service.py    # Invite emails
├── models/
│   └── (SQLAlchemy ORM models)
└── schemas/
    └── (Pydantic request/response schemas)
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

### File Storage — Cloudflare R2 (recommended over S3)

- No egress fees (important for receipt image downloads)
- S3-compatible API — easy swap if needed
- Presigned URLs for secure direct download (15-minute expiry)
- Private bucket — no public access

---

## 4. WebSocket Architecture (QR Sync)

```
Desktop Browser              FastAPI WS               Mobile Browser
      │                          │                          │
      │── WS connect ───────────►│                          │
      │   /ws/session/{sess_id}  │                          │
      │                          │                          │
      │                          │◄── POST /upload ─────────│
      │                          │    (qr_token + image)    │
      │                          │                          │
      │                          │── process receipt ───────┤
      │                          │   (OCR + classify)       │
      │                          │                          │
      │◄── WS event ─────────────│                          │
      │    {type: "receipt_added"│                          │
      │     receipt: {...}}      │                          │
      │                          │── WS event ─────────────►│
      │                          │   {type: "upload_done"   │
      │                          │    receipt_id: "..."}    │
      │                          │                          │
      │── dashboard updates ─────┤                          │
      │   (no page reload)       │                          │
```

**WebSocket events:**

| Event | Direction | Payload |
|---|---|---|
| `receipt_added` | Server → Desktop | receipt object |
| `upload_done` | Server → Mobile | `{receipt_id, kategori, jumlah}` |
| `session_warned` | Server → Mobile | `{seconds_remaining: 120}` |
| `session_expired` | Server → Both | `{reason: "inactivity"}` |
| `keep_alive` | Mobile → Server | `{}` (resets timer) |
| `session_closed` | Mobile → Server | `{}` (user tapped Done) |
| `desktop_resumed` | Server → Desktop | `{uploads_count, total_amount}` |

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
│  2. OCR — Google Vision API         │
│     Extract: merchant, amount,      │
│     date, line items                │
│     confidence_score returned       │
└──────────────┬──────────────────────┘
               │
       ┌───────▼────────┐
       │ confidence < 70%│
       │    ?            │
       └───┬─────────┬───┘
          Yes        No
           │         │
           ▼         ▼
    Flag: manual  ┌─────────────────────────────────────┐
    review        │  3. LLM — Claude Haiku               │
                  │     System: BE relief classifier     │
                  │     Input: OCR text                  │
                  │     Output: JSON {kategori, seksyen, │
                  │     jumlah_claim, confidence, nota}  │
                  └──────────────┬──────────────────────┘
                                 │
                                 ▼
                  ┌─────────────────────────────────────┐
                  │  4. Rule Engine                     │
                  │     Load limits from DB config      │
                  │     Check: current_claimed + amount │
                  │     vs category_limit               │
                  │     If exceed: flag, cap, or reject │
                  └──────────────┬──────────────────────┘
                                 │
                                 ▼
                  ┌─────────────────────────────────────┐
                  │  5. Store to DB                     │
                  │     receipt record + image_hash     │
                  │     image → R2 bucket               │
                  │     Emit WebSocket event            │
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