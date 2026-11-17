"""Cocon — entrée FastAPI.

Démarrage local :
    uvicorn backend.main:app --reload --host 127.0.0.1 --port 8765

À l'ouverture, la base SQLite est créée si elle n'existe pas. Le dossier
`frontend/` est monté à la racine pour servir l'app statique (utile en dev ;
en prod, Nginx prend le relais).
"""

from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, Response

from .database import init_db
from .routers import (
    activites,
    admin,
    cuisine,
    culture,
    lieux,
    search,
    auth as auth_router,
    cocons as cocons_router,
)


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


class _NoCacheShellMiddleware(BaseHTTPMiddleware):
    """Empêche navigateur + CDN de figer index.html / app.js / style.css / sw.js."""

    _SHELL = frozenset({"/", "/index.html", "/app.js", "/style.css", "/sw.js"})

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        if request.url.path in self._SHELL:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
        return response


app.add_middleware(_NoCacheShellMiddleware)

# ─── Routers API ──────────────────────────────────────────────────
app.include_router(auth_router.router)
app.include_router(cocons_router.router)
app.include_router(culture.router)
app.include_router(lieux.router)
app.include_router(activites.router)
app.include_router(cuisine.router)
app.include_router(search.router)
app.include_router(admin.router)


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


# ─── Page 404 jouable (commune aux sites Kernse) ──────────────────
# Une page introuvable demandée par un navigateur reçoit le petit jeu de Kernse (service kernse-studio,
# même VPS), aux couleurs de Cocon : la page choisit son thème selon le domaine. Gardée 10 min en mémoire.
# Les appels /api gardent leur 404 JSON ; si Kernse ne répond pas, la 404 d'origine reste.
KERNSE_PERDU_URL = os.getenv("KERNSE_PERDU_URL", "http://127.0.0.1:8110/perdu")
_perdu: dict = {"t": 0.0, "html": None}


async def _page_perdu() -> str | None:
    if _perdu["html"] and time.time() - _perdu["t"] < 600:
        return _perdu["html"]
    try:
        async with httpx.AsyncClient(timeout=2) as c:
            r = await c.get(KERNSE_PERDU_URL, headers={"Host": "cocon.sbs"})
        if r.status_code == 200 and "<canvas" in r.text:
            _perdu.update(t=time.time(), html=r.text)
    except Exception:
        pass
    return _perdu["html"]


@app.exception_handler(StarletteHTTPException)
async def _http_error(request: Request, exc: StarletteHTTPException):
    if (exc.status_code == 404 and request.method in ("GET", "HEAD")
            and not request.url.path.startswith("/api/")
            and "text/html" in request.headers.get("accept", "")):
        jeu = await _page_perdu()
        if jeu:
            return HTMLResponse(jeu, status_code=404, headers={"X-Robots-Tag": "noindex, nofollow"})
    return await http_exception_handler(request, exc)


# ─── Frontend statique ────────────────────────────────────────────
# Monté en dernier pour ne pas masquer les routes `/api/...`.
_FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if _FRONTEND_DIR.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(_FRONTEND_DIR), html=True),
        name="frontend",
    )
