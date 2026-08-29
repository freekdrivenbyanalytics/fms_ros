# Starts local dev: PostgreSQL (Docker), the FastAPI backend, the solver service, and the Vite frontend.
# Usage (from the repo root):  .\start-dev.ps1

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Write-Host "Starting PostgreSQL..."
docker compose -f "$root\docker-compose.yml" up -d

Write-Host "Starting backend (http://localhost:8000)..."
Start-Process powershell -ArgumentList @(
    "-NoExit", "-ExecutionPolicy", "Bypass", "-Command",
    "cd '$root\backend'; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload"
)

Write-Host "Starting solver service (http://localhost:8100)..."
Start-Process powershell -ArgumentList @(
    "-NoExit", "-ExecutionPolicy", "Bypass", "-Command",
    "cd '$root\solver'; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8100"
)

Write-Host "Starting frontend (http://localhost:5173)..."
Start-Process powershell -ArgumentList @(
    "-NoExit", "-ExecutionPolicy", "Bypass", "-Command",
    "cd '$root\frontend'; npm run dev"
)

Write-Host ""
Write-Host "Backend, solver, and frontend are starting in their own windows. Close those windows (or Ctrl+C in each) to stop them."
