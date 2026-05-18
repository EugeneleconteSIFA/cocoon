"""Schémas Pydantic (request / response) pour les 4 piliers.

Convention :
- `*Create` : ce qu'envoie le frontend pour ajouter (le strict utile).
- `*Update` : tous champs optionnels, pour PATCH.
- `*Read`   : ce que le backend renvoie (inclut id + created_at).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

# ───────────────────────────────────────────────────────────────────
# Base commune
# ───────────────────────────────────────────────────────────────────


class _ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ───────────────────────────────────────────────────────────────────
# Auth & Cocons
# ───────────────────────────────────────────────────────────────────


class UserCreate(_ORMBase):
    email: str
    password: str = Field(..., min_length=6)
    display_name: str


class UserRead(_ORMBase):
    id: int
    email: str
    display_name: str
    created_at: str


class UserUpdate(_ORMBase):
    display_name: str | None = None
    password: str | None = Field(default=None, min_length=6)


class CoconRead(_ORMBase):
    id: int
    name: str
    code: str
    role: str
    member_count: int
    created_at: str | None = None


class CoconCreate(_ORMBase):
    name: str = Field(..., min_length=1, max_length=50)


class CoconJoin(_ORMBase):
    code: str = Field(..., min_length=8, max_length=8)


class TokenResponse(_ORMBase):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


# ───────────────────────────────────────────────────────────────────
# 1. Culture
# ───────────────────────────────────────────────────────────────────


class CultureCreate(_ORMBase):
    type: str = Field(..., pattern="^(movie|tv)$", description="'movie' ou 'tv'")
    tmdb_id: int | None = None
    title: str
    year: int | None = None
    poster_url: str | None = None
    genres: list[str] | None = None
    actors: list[str] | None = None
    overview: str | None = None
    rating: float | None = None
    note: str | None = None
    seen_at: str | None = None
    loved: bool = False
    archived: bool = False


class CultureUpdate(_ORMBase):
    type: str | None = Field(default=None, pattern="^(movie|tv)$")
    title: str | None = None
    year: int | None = None
    poster_url: str | None = None
    genres: list[str] | None = None
    actors: list[str] | None = None
    overview: str | None = None
    rating: float | None = None
    note: str | None = None
    seen_at: str | None = None
    loved: bool | None = None
    archived: bool | None = None


class CultureRead(_ORMBase):
    id: int
    type: str
    tmdb_id: int | None
    title: str
    year: int | None
    poster_url: str | None
    genres: list[str] | None
    actors: list[str] | None
    overview: str | None
    rating: float | None
    note: str | None
    seen_at: str | None
    loved: bool
    archived: bool
    created_at: str


# ───────────────────────────────────────────────────────────────────
# 2. Lieux
# ───────────────────────────────────────────────────────────────────


class LieuCreate(_ORMBase):
    gplaces_id: str | None = None
    name: str
    address: str | None = None
    city: str | None = None
    section: str = Field(default="ville", pattern="^(ville|autre_ville|voyage)$")
    category: str | None = None
    photo_url: str | None = None
    rating: float | None = None
    maps_url: str | None = None
    note: str | None = None
    visited_at: str | None = None
    loved: bool = False
    archived: bool = False


class LieuUpdate(_ORMBase):
    name: str | None = None
    address: str | None = None
    city: str | None = None
    section: str | None = Field(default=None, pattern="^(ville|autre_ville|voyage)$")
    category: str | None = None
    photo_url: str | None = None
    rating: float | None = None
    maps_url: str | None = None
    note: str | None = None
    visited_at: str | None = None
    loved: bool | None = None
    archived: bool | None = None


class LieuRead(_ORMBase):
    id: int
    gplaces_id: str | None
    name: str
    address: str | None
    city: str | None
    section: str
    category: str | None
    photo_url: str | None
    rating: float | None
    maps_url: str | None
    note: str | None
    visited_at: str | None
    loved: bool
    archived: bool
    created_at: str


# ───────────────────────────────────────────────────────────────────
# 3. Activités
# ───────────────────────────────────────────────────────────────────


class ActiviteCreate(_ORMBase):
    title: str
    emoji: str | None = None
    tags: list[str] | None = None
    note: str | None = None
    done_at: str | None = None
    loved: bool = False
    archived: bool = False


class ActiviteUpdate(_ORMBase):
    title: str | None = None
    emoji: str | None = None
    tags: list[str] | None = None
    note: str | None = None
    done_at: str | None = None
    loved: bool | None = None
    archived: bool | None = None


class ActiviteRead(_ORMBase):
    id: int
    title: str
    emoji: str | None
    tags: list[str] | None
    note: str | None
    done_at: str | None
    loved: bool
    archived: bool
    created_at: str


# ───────────────────────────────────────────────────────────────────
# 4. Cuisine
# ───────────────────────────────────────────────────────────────────


class RecetteCreate(_ORMBase):
    title: str
    source_url: str | None = None
    image_url: str | None = None
    tags: list[str] | None = None
    note: str | None = None
    cooked_at: str | None = None
    loved: bool = False
    archived: bool = False


class RecetteUpdate(_ORMBase):
    title: str | None = None
    source_url: str | None = None
    image_url: str | None = None
    tags: list[str] | None = None
    note: str | None = None
    cooked_at: str | None = None
    loved: bool | None = None
    archived: bool | None = None


class RecetteRead(_ORMBase):
    id: int
    title: str
    source_url: str | None
    image_url: str | None
    tags: list[str] | None
    note: str | None
    cooked_at: str | None
    loved: bool
    archived: bool
    created_at: str
