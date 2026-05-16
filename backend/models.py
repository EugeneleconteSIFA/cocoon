"""Modèles SQLAlchemy pour les 4 piliers de Cocon.

Convention : tous les modèles héritent d'un mixin `CocoonMixin` qui ajoute
les champs partagés (id, note libre, aimé, archivé, date de création).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def _now_iso() -> str:
    """Date ISO 8601 UTC pour `created_at`."""
    return datetime.now(timezone.utc).isoformat()


class CocoonMixin:
    """Champs communs à toutes les entrées du carnet."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    loved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[str] = mapped_column(String, default=_now_iso, nullable=False)


# ─── 1. Culture (films & séries) ───────────────────────────────────
class Culture(CocoonMixin, Base):
    __tablename__ = "culture"

    type: Mapped[str] = mapped_column(String, nullable=False)  # 'movie' | 'tv'
    tmdb_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    poster_url: Mapped[str | None] = mapped_column(String, nullable=True)
    genres: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    actors: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    overview: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    seen_at: Mapped[str | None] = mapped_column(String, nullable=True)


# ─── 2. Lieux ──────────────────────────────────────────────────────
class Lieu(CocoonMixin, Base):
    __tablename__ = "lieux"

    gplaces_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    # 'ville' (notre ville) | 'autre_ville' | 'voyage'
    section: Mapped[str] = mapped_column(String, default="ville", nullable=False)
    category: Mapped[str | None] = mapped_column(String, nullable=True)  # restaurant, cafe…
    photo_url: Mapped[str | None] = mapped_column(String, nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    maps_url: Mapped[str | None] = mapped_column(String, nullable=True)
    visited_at: Mapped[str | None] = mapped_column(String, nullable=True)


# ─── 3. Activités ──────────────────────────────────────────────────
class Activite(CocoonMixin, Base):
    __tablename__ = "activites"

    title: Mapped[str] = mapped_column(String, nullable=False)
    emoji: Mapped[str | None] = mapped_column(String, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    done_at: Mapped[str | None] = mapped_column(String, nullable=True)


# ─── 4. Cuisine (recettes) ─────────────────────────────────────────
class Recette(CocoonMixin, Base):
    __tablename__ = "cuisine"

    title: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    cooked_at: Mapped[str | None] = mapped_column(String, nullable=True)
