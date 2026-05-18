"""Connexion SQLite + helpers SQLAlchemy.

La base est créée à la racine du projet dans `data/jttof.db`, sauf si
la variable d'environnement DATABASE_URL fournit une autre destination.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

log = logging.getLogger(__name__)

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
    migrate_db()


# Tables piliers créées avant le multi-cocon (sans cocon_id / loved / …)
_PILLAR_TABLES = ("culture", "lieux", "activites", "cuisine")
_MIXIN_COLUMNS: tuple[tuple[str, str], ...] = (
    ("cocon_id", "INTEGER"),
    ("note", "TEXT"),
    ("loved", "INTEGER NOT NULL DEFAULT 0"),
    ("archived", "INTEGER NOT NULL DEFAULT 0"),
    ("created_at", "TEXT"),
)


def _table_columns(conn, table: str) -> set[str]:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return {row[1] for row in rows}


def migrate_db() -> None:
    """Ajoute les colonnes manquantes sur une base créée avant auth / multi-cocon."""
    insp = inspect(engine)
    with engine.begin() as conn:
        default_cocon_id: int | None = None
        if insp.has_table("cocons"):
            row = conn.execute(text("SELECT id FROM cocons ORDER BY id LIMIT 1")).fetchone()
            if row:
                default_cocon_id = int(row[0])

        now = datetime.now(timezone.utc).isoformat()
        migrated = False

        for table in _PILLAR_TABLES:
            if not insp.has_table(table):
                continue
            existing = _table_columns(conn, table)
            for col, ddl in _MIXIN_COLUMNS:
                if col in existing:
                    continue
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}"))
                migrated = True
                log.info("Migration %s : colonne %s ajoutée", table, col)

            if "cocon_id" in _table_columns(conn, table) and default_cocon_id is not None:
                conn.execute(
                    text(f"UPDATE {table} SET cocon_id = :cid WHERE cocon_id IS NULL"),
                    {"cid": default_cocon_id},
                )
            if "created_at" in _table_columns(conn, table):
                conn.execute(
                    text(f"UPDATE {table} SET created_at = :now WHERE created_at IS NULL"),
                    {"now": now},
                )

        if migrated:
            log.info("Migration SQLite terminée (schéma multi-cocon)")

        if insp.has_table("users"):
            user_cols = {
                "first_name": "TEXT",
                "last_name": "TEXT",
                "birth_date": "TEXT",
            }
            existing = _table_columns(conn, "users")
            for col, ddl in user_cols.items():
                if col in existing:
                    continue
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {ddl}"))
                log.info("Migration users : colonne %s ajoutée", col)
