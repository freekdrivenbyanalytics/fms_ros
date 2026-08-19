# fms_ros

Field service planning application. This first slice provides a persisted domain model for
employees, service visits, and assignments, exposed through a FastAPI backend and a minimal
React UI that lets a planner manually assign an unassigned visit to an employee.

## Prerequisites

- Docker (for local PostgreSQL)
- Python 3.12+
- Node.js 20+

## 1. Start PostgreSQL

```sh
docker compose up -d
```

This starts Postgres on `localhost:5432` (db `fms_ros`, user `fms_ros`, password `fms_ros`).

## 2. Run the backend

```sh
cd backend
python -m venv .venv
./.venv/Scripts/activate   # on Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
copy .env.example .env     # on Windows; use `cp .env.example .env` on macOS/Linux
alembic upgrade head
python -m app.seed         # optional: inserts sample employees and service visits
uvicorn app.main:app --reload
```

The API is now available at `http://localhost:8000` (interactive docs at `/docs`).

## 3. Run the frontend

```sh
cd frontend
npm install
copy .env.example .env     # on Windows; use `cp .env.example .env` on macOS/Linux
npm run dev
```

The app is now available at `http://localhost:5173`.

## Project layout

- `backend/` — FastAPI app, SQLAlchemy models, Alembic migrations
- `frontend/` — Vite + React + TypeScript app
- `docker-compose.yml` — local PostgreSQL service
