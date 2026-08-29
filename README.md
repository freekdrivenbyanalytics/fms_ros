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

## 4. Run the solver service

The "Optimize" view calls a separate solver microservice that runs [Timefold Solver](https://timefold.ai)
to match employees to unassigned visits. It's a standalone FastAPI service with its own virtualenv.

```sh
cd solver
python -m venv .venv
./.venv/Scripts/activate   # on Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8100
```

The solver API is now available at `http://localhost:8100`.

**Note:** Timefold's Python package wraps the real Java Timefold Solver via JPype and requires a
JVM at runtime. No system-wide Java install is needed — `jdk4py` (pinned in `requirements.txt`)
bundles a JDK as a regular pip package, and `solver/app/jvm.py` points `JAVA_HOME`/`PATH` at it
automatically before Timefold is imported.

The backend calls this service at `solver_base_url` (`http://localhost:8100` by default, see
`backend/app/config.py`), so it must be running for `POST /optimize/propose` to succeed.

## Convenience: start everything at once

```powershell
.\start-dev.ps1
```

Starts PostgreSQL (Docker), the backend, the solver service, and the frontend, each in their own
window (Windows/PowerShell only; assumes each `.venv`/`node_modules` is already set up as above).

## Project layout

- `backend/` — FastAPI app, SQLAlchemy models, Alembic migrations
- `solver/` — standalone FastAPI + Timefold Solver microservice for route optimization
- `frontend/` — Vite + React + TypeScript app
- `docker-compose.yml` — local PostgreSQL service
