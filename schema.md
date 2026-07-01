# Database Schema
## Resit.my — PostgreSQL Schema
**Version:** 1.1.0  
**Engine:** PostgreSQL 15  
**ORM:** SQLAlchemy (async)  
**Migrations:** Alembic (001–009)  
**Last synced with codebase:** June 2026

---

## 1. Schema Diagram (Entity Relationships)

```
organisations
    │
    ├──< org_policies (1:1)
    │
    ├──< users (1:many, via org_id)
    │       │
    │       ├──< receipts (1:many)
    │       │       │
    │       │       ├──< receipt_flags (1:many)
    │       │       └──< receipt_line_items (1:many)
    │       │
    │       ├──< upload_sessions (1:many)  ← QR tokens
    │       ├──< claim_summaries (1:many, per tax year)
    │       ├──< notification_preferences (1:1)
    │       ├──< user_notifications (1:many)
    │       └──< spouse_links (requester / partner)
    │
    └──< invite_tokens (1:many)

relief_limits (global config — no tax_year FK; sort_order)
system_config   (non-secret key-value settings)
system_settings (encrypted secrets — OpenRouter API key, etc.)
audit_logs      (append-only)
```

---

## 2. Tables

### `organisations`

```sql
CREATE TABLE organisations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    ssm_number      VARCHAR(20) UNIQUE NOT NULL,
    email_domain    VARCHAR(100) UNIQUE NOT NULL,   -- e.g. syarikat.com.my
    domain_verified BOOLEAN DEFAULT FALSE,
    status          VARCHAR(20) DEFAULT 'active'    -- active | suspended
        CHECK (status IN ('active', 'suspended')),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_org_domain ON organisations(email_domain);
```

---

### `users`

```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,           -- bcrypt
    full_name       VARCHAR(255),
    role            VARCHAR(20) NOT NULL
        CHECK (role IN ('individual', 'employee', 'hr_admin', 'superadmin')),
    account_type    VARCHAR(20) NOT NULL DEFAULT 'individual'
        CHECK (account_type IN ('individual', 'corporate')),
    org_id          UUID REFERENCES organisations(id) ON DELETE SET NULL,
    tax_year        SMALLINT DEFAULT 2025,           -- active filing year
    tax_bracket     DECIMAL(5,2),                    -- e.g. 15.00 (%)
    email_verified  BOOLEAN DEFAULT FALSE,
    is_active       BOOLEAN DEFAULT TRUE,
    org_employee_code VARCHAR(50),                   -- kod pekerja (eksport gaji)
    forwarding_token VARCHAR(32) UNIQUE,           -- token e-mel resit (Fasa 3 asas)
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_user_org   ON users(org_id);
CREATE INDEX idx_user_role  ON users(role);
CREATE INDEX idx_users_forwarding_token ON users(forwarding_token)
    WHERE forwarding_token IS NOT NULL;
```

---

### `invite_tokens`

```sql
CREATE TABLE invite_tokens (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token           VARCHAR(128) UNIQUE NOT NULL,   -- secrets.token_urlsafe(64)
    org_id          UUID NOT NULL REFERENCES organisations(id) ON DELETE CASCADE,
    invited_email   VARCHAR(255),                   -- null = open link
    invited_by      UUID NOT NULL REFERENCES users(id),
    role            VARCHAR(20) NOT NULL DEFAULT 'employee'
        CHECK (role IN ('employee', 'hr_admin')),
    invite_type     VARCHAR(20) NOT NULL
        CHECK (invite_type IN ('email', 'link', 'csv')),
    used            BOOLEAN DEFAULT FALSE,
    used_by         UUID REFERENCES users(id),
    used_at         TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ NOT NULL,           -- 48h for HR, 7d for employee
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_invite_token  ON invite_tokens(token);
CREATE INDEX idx_invite_org    ON invite_tokens(org_id);
CREATE INDEX idx_invite_expiry ON invite_tokens(expires_at) WHERE used = FALSE;
```

---

### `receipts`

```sql
CREATE TABLE receipts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    org_id          UUID REFERENCES organisations(id) ON DELETE SET NULL,
    tax_year        SMALLINT NOT NULL DEFAULT 2025,

    -- File storage
    image_key       VARCHAR(512) NOT NULL,          -- R2/S3 object key
    image_hash      VARCHAR(64) UNIQUE NOT NULL,    -- SHA-256 for dedup
    file_name       VARCHAR(255),
    file_type       VARCHAR(10),                    -- jpg | png | pdf
    file_size_bytes INTEGER,

    -- OCR results
    merchant_name   VARCHAR(255),
    receipt_date    DATE,
    total_amount    DECIMAL(10,2),
    ocr_raw         JSONB,                          -- full OCR response
    ocr_confidence  DECIMAL(4,3),                   -- 0.000 - 1.000

    -- Classification
    category        VARCHAR(50),                    -- no DB CHECK; validated via relief_limits
    be_seksyen      VARCHAR(20),                    -- e.g. S.46(1)(b)
    claimed_amount  DECIMAL(10,2),                  -- may differ from total
    excluded_amount DECIMAL(10,2) DEFAULT 0,        -- non-claimable portion
    ai_confidence   DECIMAL(4,3),
    ai_nota         TEXT,
    notes           TEXT,                           -- nota peribadi pengguna

    -- Processing
    scan_status     VARCHAR(20) DEFAULT 'waiting'
        CHECK (scan_status IN ('waiting', 'processing', 'success', 'failed')),

    -- Status & approval
    status          VARCHAR(20) DEFAULT 'pending'
        CHECK (status IN (
            'pending', 'approved', 'rejected',
            'flagged', 'duplicate'
        )),
    reviewed_by     UUID REFERENCES users(id),
    reviewed_at     TIMESTAMPTZ,
    review_comment  TEXT,

    -- Soft delete
    deleted_at      TIMESTAMPTZ,

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_receipt_user     ON receipts(user_id);
CREATE INDEX idx_receipt_org      ON receipts(org_id);
CREATE INDEX idx_receipt_category ON receipts(category);
CREATE INDEX idx_receipt_status   ON receipts(status);
CREATE INDEX idx_receipt_year     ON receipts(tax_year);
CREATE INDEX idx_receipt_hash     ON receipts(image_hash);
CREATE INDEX idx_receipt_scan_status ON receipts(scan_status);
CREATE INDEX idx_receipt_deleted  ON receipts(deleted_at) WHERE deleted_at IS NULL;
```

---

### `receipt_line_items`

Line-item splitting for mixed receipts (pharmacy, etc.).

```sql
CREATE TABLE receipt_line_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    receipt_id      UUID NOT NULL REFERENCES receipts(id) ON DELETE CASCADE,
    sort_order      SMALLINT DEFAULT 0,
    description     VARCHAR(500) DEFAULT '',
    amount          DECIMAL(10,2) NOT NULL,
    category        VARCHAR(50) NOT NULL,
    ai_claimable    BOOLEAN DEFAULT FALSE,
    included_in_claim BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_receipt_line_items_receipt ON receipt_line_items(receipt_id);
```

---

### `receipt_flags`

```sql
CREATE TABLE receipt_flags (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    receipt_id      UUID NOT NULL REFERENCES receipts(id) ON DELETE CASCADE,
    flag_type       VARCHAR(50) NOT NULL
        CHECK (flag_type IN (
            'low_ocr_confidence',
            'low_ai_confidence',
            'mixed_items',
            'limit_exceeded',
            'duplicate_suspected',
            'manual_review'
        )),
    message         TEXT,
    resolved        BOOLEAN DEFAULT FALSE,
    resolved_by     UUID REFERENCES users(id),
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_flag_receipt ON receipt_flags(receipt_id);
```

---

### `upload_sessions` (QR Camera Handoff)

```sql
CREATE TABLE upload_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token           VARCHAR(128) UNIQUE NOT NULL,  -- secrets.token_urlsafe(32)
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    desktop_session VARCHAR(128) NOT NULL,         -- Redis session ID
    tax_year        SMALLINT DEFAULT 2025,         -- tahun cukai untuk resit QR
    status          VARCHAR(20) DEFAULT 'active'
        CHECK (status IN ('active', 'warned', 'expired', 'closed')),
    inactivity_secs INTEGER DEFAULT 600,           -- 10 minutes
    last_upload_at  TIMESTAMPTZ,
    uploads_count   INTEGER DEFAULT 0,
    mobile_ua       VARCHAR(500),                  -- User-Agent binding
    expires_at      TIMESTAMPTZ NOT NULL,          -- hard max: 24h
    closed_at       TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_upload_session_token  ON upload_sessions(token);
CREATE INDEX idx_upload_session_user   ON upload_sessions(user_id);
CREATE INDEX idx_upload_session_status ON upload_sessions(status);
```

---

### `claim_summaries`

Materialized per-user, per-year totals. Updated on every receipt status change.

```sql
CREATE TABLE claim_summaries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tax_year        SMALLINT NOT NULL,
    category        VARCHAR(50) NOT NULL,
    total_claimed   DECIMAL(10,2) DEFAULT 0,
    receipt_count   INTEGER DEFAULT 0,
    last_updated    TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, tax_year, category)
);

CREATE INDEX idx_summary_user_year ON claim_summaries(user_id, tax_year);
```

---

### `relief_limits` (Global Config)

Updatable by superadmin — **no `tax_year` column** (migration 005). Limits apply globally; user's active year is on `users.tax_year`.

```sql
CREATE TABLE relief_limits (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category        VARCHAR(50) NOT NULL UNIQUE,
    be_seksyen      VARCHAR(20),
    limit_amount    DECIMAL(10,2) NOT NULL,
    description_en  TEXT,
    description_my  TEXT,
    sort_order      SMALLINT DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    updated_by      UUID REFERENCES users(id),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Seed data (contoh)
INSERT INTO relief_limits (category, be_seksyen, limit_amount, description_my, sort_order) VALUES
('perubatan',   'S.46(1)(b)', 8000.00,  'Perubatan & Pergigian', 1),
('gaya_hidup',  'S.46(1)(k)', 3000.00,  'Gaya Hidup (buku, internet, sukan)', 2),
('sukan',       'S.46(1)(k)',  500.00,   'Peralatan Sukan (dalam had gaya hidup)', 3),
('pendidikan',  'S.46(1)(f)', 7000.00,  'Pendidikan Diri', 4),
('sspn',        'S.46(1)(l)', 8000.00,  'SSPN', 5),
('ev_charging', 'S.46(1)(p)', 2500.00,  'Pembelian / Pasang EV Charging', 6);
```

---

### `org_policies`

```sql
CREATE TABLE org_policies (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id                  UUID UNIQUE NOT NULL REFERENCES organisations(id) ON DELETE CASCADE,
    allowed_categories      VARCHAR(50)[] DEFAULT ARRAY[
        'perubatan', 'gaya_hidup', 'sukan',
        'pendidikan', 'sspn', 'ev_charging'
    ],
    require_hr_approval     BOOLEAN DEFAULT TRUE,
    max_receipts_per_month  INTEGER DEFAULT 50,
    tax_year                SMALLINT DEFAULT 2025,
    updated_by              UUID REFERENCES users(id),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);
```

---

### `audit_logs`

Append-only. Never update or delete rows.

```sql
CREATE TABLE audit_logs (
    id          BIGSERIAL PRIMARY KEY,
    user_id     UUID REFERENCES users(id) ON DELETE SET NULL,
    org_id      UUID REFERENCES organisations(id) ON DELETE SET NULL,
    action      VARCHAR(100) NOT NULL,      -- e.g. receipt.approved
    resource    VARCHAR(50),                -- e.g. receipt
    resource_id UUID,
    metadata    JSONB,                      -- before/after states
    ip_address  INET,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_user     ON audit_logs(user_id);
CREATE INDEX idx_audit_org      ON audit_logs(org_id);
CREATE INDEX idx_audit_action   ON audit_logs(action);
CREATE INDEX idx_audit_resource ON audit_logs(resource, resource_id);
CREATE INDEX idx_audit_time     ON audit_logs(created_at DESC);
```

---

### `notification_preferences`

```sql
CREATE TABLE notification_preferences (
    user_id                 UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    email_enabled           BOOLEAN DEFAULT TRUE,
    in_app_enabled          BOOLEAN DEFAULT TRUE,
    digest_frequency        VARCHAR(20) DEFAULT 'monthly'
        CHECK (digest_frequency IN ('off', 'monthly')),
    last_monthly_digest_at  TIMESTAMPTZ,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);
```

---

### `user_notifications`

```sql
CREATE TABLE user_notifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reminder_key    VARCHAR(120) NOT NULL,
    type            VARCHAR(40) NOT NULL,
    severity        VARCHAR(10) DEFAULT 'info'
        CHECK (severity IN ('info', 'warning')),
    title_my        TEXT NOT NULL,
    title_en        TEXT NOT NULL,
    message_my      TEXT NOT NULL,
    message_en      TEXT NOT NULL,
    action_href     VARCHAR(255),
    dismissed_at    TIMESTAMPTZ,
    email_sent_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    expires_at      TIMESTAMPTZ,

    UNIQUE(user_id, reminder_key)
);

CREATE INDEX idx_user_notifications_user ON user_notifications(user_id);
```

---

### `spouse_links`

```sql
CREATE TABLE spouse_links (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requester_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    partner_id      UUID REFERENCES users(id) ON DELETE SET NULL,
    partner_email   VARCHAR(255) NOT NULL,
    status          VARCHAR(20) DEFAULT 'pending'
        CHECK (status IN ('pending', 'accepted', 'rejected', 'dissolved')),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    responded_at    TIMESTAMPTZ
);

CREATE INDEX idx_spouse_links_requester ON spouse_links(requester_id);
CREATE INDEX idx_spouse_links_partner ON spouse_links(partner_id);
CREATE INDEX idx_spouse_links_partner_email ON spouse_links(partner_email);
```

---

### `system_config`

Tetapan bukan-rahsia (model AI, had muat naik, dll).

```sql
CREATE TABLE system_config (
    key             VARCHAR(100) PRIMARY KEY,
    value           TEXT NOT NULL,
    updated_by      UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

### `system_settings`

Rahsia terenkripsi (Fernet). Contoh key: `openrouter_api_key`.

```sql
CREATE TABLE system_settings (
    key             VARCHAR(100) PRIMARY KEY,
    encrypted_value TEXT NOT NULL,
    updated_by      UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 3. Key Triggers & Functions

### Auto-update `updated_at`

```sql
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Apply same trigger to: organisations, receipts, org_policies
```

### Update `claim_summaries` on receipt status change

```sql
CREATE OR REPLACE FUNCTION sync_claim_summary()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'approved' AND OLD.status != 'approved' THEN
        INSERT INTO claim_summaries (user_id, tax_year, category, total_claimed, receipt_count)
        VALUES (NEW.user_id, NEW.tax_year, NEW.category, NEW.claimed_amount, 1)
        ON CONFLICT (user_id, tax_year, category) DO UPDATE
        SET total_claimed = claim_summaries.total_claimed + NEW.claimed_amount,
            receipt_count = claim_summaries.receipt_count + 1,
            last_updated  = NOW();
    END IF;

    IF OLD.status = 'approved' AND NEW.status != 'approved' THEN
        UPDATE claim_summaries
        SET total_claimed = GREATEST(0, total_claimed - OLD.claimed_amount),
            receipt_count = GREATEST(0, receipt_count - 1),
            last_updated  = NOW()
        WHERE user_id = OLD.user_id
          AND tax_year = OLD.tax_year
          AND category = OLD.category;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_claim_summary
    AFTER UPDATE ON receipts
    FOR EACH ROW EXECUTE FUNCTION sync_claim_summary();
```

---

## 4. Data Retention Policy

```sql
-- Soft delete: mark deleted, purge after 30 days
-- Run via scheduled job (nightly)
DELETE FROM receipts
WHERE deleted_at IS NOT NULL
  AND deleted_at < NOW() - INTERVAL '30 days';

-- Upload sessions: clean expired
DELETE FROM upload_sessions
WHERE status IN ('expired', 'closed')
  AND created_at < NOW() - INTERVAL '7 days';

-- Audit logs: retain 7 years (LHDN requirement)
-- No deletion job for audit_logs
```