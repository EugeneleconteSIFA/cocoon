"""Cocon — entrée FastAPI.

Démarrage local :
    uvicorn backend.main:app --reload --host 127.0.0.1 --port 8765

À l'ouverture, la base SQLite est créée si elle n'existe pas. Le dossier
`frontend/` est monté à la racine pour servir l'app statique (utile en dev ;
en prod, Nginx prend le relais).
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import init_db
from .routers import activites, cuisine, culture, lieux, search, auth as auth_router, cocons as cocons_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialise la base au démarrage."""
    init_db()
    yield


app = FastAPI(
    title="Cocon",
    description="Notre carnet à deux. Backend FastAPI + SQLite.",
    version="0.1.0",
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────
# Local : permissif. Prod derrière Nginx (même origine) : liste vide par défaut.
# Optionnel : CORS_ORIGINS=https://jttof.example.com,https://...
def _cors_origins() -> list[str]:
    if os.getenv("APP_ENV", "local") == "local":
        return ["*"]
    raw = (os.getenv("CORS_ORIGINS") or "").strip()
    if not raw:
        return []
    return [o.strip() for o in raw.split(",") if o.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers API ──────────────────────────────────────────────────
app.include_router(auth_router.router)
app.include_router(cocons_router.router)
app.include_router(culture.router)
app.include_router(lieux.router)
app.include_router(activites.router)
app.include_router(cuisine.router)
app.include_router(search.router)


@app.get("/api/health", tags=["meta"])
def health() -> dict:
    """Sanity check."""
    return {
        "ok": True,
        "app": "cocon",
        "version": app.version,
        "env": os.getenv("APP_ENV", "local"),
        "secret_key_set": bool((os.getenv("SECRET_KEY") or "").strip()),
    }


# ─── Frontend statique ────────────────────────────────────────────
# Monté en dernier pour ne pas masquer les routes `/api/...`.
_FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if _FRONTEND_DIR.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(_FRONTEND_DIR), html=True),
        name="frontend",
    )
