"""Connexion SQLite + helpers SQLAlchemy.

La base est créée à la racine du projet dans `data/jttof.db`, sauf si
la variable d'environnement DATABASE_URL fournit une autre destination.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# ─── Charger .env (chemin absolu, peu importe le cwd) ──────────────
_BACKEND_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _BACKEND_DIR.parent
load_dotenv(_BACKEND_DIR / ".env")

# ─── Localisation de la base ───────────────────────────────────────
_DATA_DIR = _PROJECT_ROOT / "data"
_DATA_DIR.mkdir(parents=True, exist_ok=True)
_DEFAULT_DB_URL = f"sqlite:///{_DATA_DIR / 'jttof.db'}"

DATABASE_URL: str = os.getenv("DATABASE_URL") or _DEFAULT_DB_URL

# ─── Engine & session ──────────────────────────────────────────────
# `check_same_thread=False` pour autoriser plusieurs threads (uvicorn).
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base déclarative pour tous les modèles."""


# ─── Dépendance FastAPI ────────────────────────────────────────────
def get_db():
    """Yield une session SQLAlchemy, fermée proprement à la fin."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Init au démarrage ─────────────────────────────────────────────
def init_db() -> None:
    """Crée les tables si elles n'existent pas.

    Si la variable d'environnement RESET_DB=1 est définie, toutes les
    tables existantes sont supprimées avant d'être recréées (utile pour
    repartir d'un schéma propre après une migration cassante).
    """
    # Import tardif pour éviter les imports circulaires
    from . import models  # noqa: F401

    if os.getenv("RESET_DB", "0").strip() == "1":
        Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)
