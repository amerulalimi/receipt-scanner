# Resit.my — FastAPI Backend

## Quick start

```bash
# 1. Start PostgreSQL + Redis
docker compose up -d

# 2. Copy env and install deps
cp .env.example .env
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# 3. Run migrations
alembic upgrade head

# 4. Start API server
uvicorn app.main:app --reload --port 8000
```

Health check: `GET http://localhost:8000/health`

## Structure

```
app/
├── core/          # config, database, redis
├── models/        # SQLAlchemy ORM (10 tables)
└── main.py        # FastAPI entrypoint
alembic/           # database migrations
```

## Environment

| Variable | Description |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:PASSWORD@localhost:5433/resit` (port 5433 avoids Windows PostgreSQL on 5432) |
| `REDIS_URL` | `redis://localhost:6379/0` |
| `CORS_ORIGINS` | Comma-separated allowed origins |
