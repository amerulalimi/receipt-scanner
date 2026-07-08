# Resit.my

Malaysian tax receipt scanner SaaS monorepo with:

- `frontend/`: Next.js 15 App Router app
- `backend/`: FastAPI API, worker, and async SQLAlchemy
- `docker-compose.yml`: full stack local Docker setup

## What this app does

Resit.my helps users upload receipts, classify them, review tax-related claims, and prepare records for filing. The current stack includes:

- Next.js frontend on port `3000`
- FastAPI backend on port `8000`
- PostgreSQL on port `5433`
- Redis on the internal Docker network
- Separate worker container for background receipt processing

## Prerequisites

For Docker usage:

- Docker Desktop
- Docker Compose

For non-Docker local development:

- Node.js 20+
- Python 3.12+

## Quick Start With Docker

This is the easiest way to run the full app locally.

### 1. Create env files

Copy the provided examples:

```powershell
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

Or on macOS/Linux:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 2. Review the minimum values

The defaults are enough to boot the app locally with Docker. You only need to change values if you want real integrations.

Most important files:

- `backend/.env`
- `frontend/.env`

Important notes:

- `backend/.env` uses `localhost` for local development outside containers.
- In Docker, `docker-compose.yml` overrides service-to-service URLs automatically.
- `OPENROUTER_API_KEY` is optional for booting the stack, but AI receipt features will be limited without it.

### 3. Build and start everything

```powershell
docker compose up --build
```

Run detached if you prefer:

```powershell
docker compose up --build -d
```

### 4. Open the app

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend API: [http://localhost:8000](http://localhost:8000)
- Backend health check: [http://localhost:8000/health](http://localhost:8000/health)

## Docker Services

The root `docker-compose.yml` starts:

- `postgres`: PostgreSQL database
- `redis`: Redis cache / queue
- `backend`: FastAPI API service
- `worker`: background receipt worker
- `frontend`: Next.js production build

Useful commands:

```powershell
docker compose up --build
docker compose up -d
docker compose down
docker compose down -v
docker compose logs -f backend
docker compose logs -f worker
docker compose logs -f frontend
```

Notes:

- `docker compose down -v` also removes the PostgreSQL volume.
- Uploaded local files are stored under `backend/storage/`.
- Redis is intentionally not published to the host to avoid port conflicts with other local Redis containers or services.

## How Docker Works In This Repo

### Frontend

- Built from `frontend/Dockerfile`
- Uses a multi-stage Next.js standalone build
- Receives required build-time env values from `docker-compose.yml`

### Backend

- Built from `backend/Dockerfile`
- Runs FastAPI on `0.0.0.0:8000`
- Applies Alembic migrations on startup

### Worker

- Reuses the backend image
- Runs `python -m app.worker`
- Processes queued receipt jobs separately from the API container

## Local Development Without Docker

If you only want infra in Docker:

```powershell
docker compose up postgres redis -d
```

Then start the backend:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

And the frontend:

```powershell
cd frontend
npm install
npm run dev
```

## Environment Files

Example env files are now included here:

- `backend/.env.example`
- `frontend/.env.example`

Do not commit real `.env` files.

Key frontend variables:

- `FASTAPI_URL`: server-side URL used by Next.js to talk to FastAPI
- `NEXT_PUBLIC_API_URL`: browser-visible backend URL
- `NEXT_PUBLIC_APP_URL`: public frontend URL

Key backend variables:

- `DATABASE_URL`
- `REDIS_URL`
- `FRONTEND_URL`
- `CORS_ORIGINS`
- `SESSION_SECRET`
- `OPENROUTER_API_KEY`
- `STORAGE_BACKEND`

## Common Docker Troubleshooting

### Port already in use

If a port is already taken, stop the existing process or change the port mapping in `docker-compose.yml`.

### Frontend builds but API calls fail

Check:

- `backend` container is healthy
- `FASTAPI_URL` is still `http://backend:8000` inside Docker
- `NEXT_PUBLIC_API_URL` points to `http://localhost:8000` for browser access

### Need a clean rebuild

```powershell
docker compose down -v
docker compose build --no-cache
docker compose up
```
