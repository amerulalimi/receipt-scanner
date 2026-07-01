# Resit.my

Malaysian tax receipt scanner SaaS — monorepo for Next.js frontend and FastAPI backend.

## Structure

```
resit-my/
├── frontend/          # Next.js 15 (App Router)
├── backend/           # FastAPI + SQLAlchemy async
├── docker-compose.yml
├── .env.example
└── README.md
```

## Prerequisites

- Node.js 20+
- Python 3.12+
- Docker & Docker Compose (optional, for full stack)

## Quick start (local)

1. Copy environment variables:

   ```bash
   cp .env.example .env
   ```

2. Start PostgreSQL and Redis:

   ```bash
   docker compose up postgres redis -d
   ```

3. Backend:

   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   # source .venv/bin/activate   # macOS/Linux
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

4. Frontend:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Full stack (Docker)

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Health check: http://localhost:8000/health

## Environment

See `.env.example` for all variables. Never commit `.env` files.

Server-side Next.js calls use `FASTAPI_URL`. Browser-facing API base URL uses `NEXT_PUBLIC_API_URL`.
