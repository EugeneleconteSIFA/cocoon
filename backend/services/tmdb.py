"""Client minimal pour TMDb (The Movie Database) v3.

Deux fonctions publiques :
- `search_multi(query)` : recherche live (films + séries), payload léger.
- `get_details(media_type, tmdb_id)` : détails enrichis (genres + top 3 acteurs).

Les deux renvoient un dict compatible avec `schemas.CultureCreate`, pour que
le frontend puisse POSTer le résultat directement vers `/api/culture`.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMG_BASE = "https://image.tmdb.org/t/p/w342"


# ─── HTTP client ────────────────────────────────────────────────────
def _client() -> httpx.Client:
    """Construit un client httpx authentifié.

    Priorité : Bearer token (TMDB_READ_TOKEN) > api_key en query (TMDB_API_KEY).
    """
    token = (os.getenv("TMDB_READ_TOKEN") or "").strip()
    api_key = (os.getenv("TMDB_API_KEY") or "").strip()
    if not token and not api_key:
        raise RuntimeError("Aucune clé TMDb configurée (TMDB_READ_TOKEN / TMDB_API_KEY).")

    headers = {"accept": "application/json"}
    params: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        params["api_key"] = api_key

    return httpx.Client(
        base_url=TMDB_BASE,
        headers=headers,
        params=params,
        timeout=10.0,
    )


def _lang() -> str:
    return os.getenv("TMDB_LANGUAGE", "fr-FR")


# ─── Helpers de formatage ───────────────────────────────────────────
def _poster_url(path: str | None) -> str | None:
    return f"{TMDB_IMG_BASE}{path}" if path else None


def _year(date: str | None) -> int | None:
    if not date or len(date) < 4:
        return None
    try:
        return int(date[:4])
    except ValueError:
        return None


def _rating(value: Any) -> float | None:
    if value is None:
        return None
    try:
        rounded = round(float(value), 1)
    except (TypeError, ValueError):
        return None
    return rounded if rounded > 0 else None


def _title_and_date(item: dict[str, Any], media_type: str) -> tuple[str | None, str | None]:
    if media_type == "movie":
        return item.get("title"), item.get("release_date")
    return item.get("name"), item.get("first_air_date")


# ─── API publique ───────────────────────────────────────────────────
def search_multi(query: str) -> list[dict[str, Any]]:
    """Recherche films + séries. Résultats légers, prêts à afficher en grille.

    Filtre :
    - on garde uniquement movies & tv (pas les personnes),
    - on garde uniquement les entrées qui ont un poster.
    """
    query = (query or "").strip()
    if not query:
        return []

    with _client() as c:
        r = c.get(
            "/search/multi",
            params={
                "query": query,
                "language": _lang(),
                "include_adult": "false",
                "page": 1,
            },
        )
        r.raise_for_status()
        payload = r.json()

    results: list[dict[str, Any]] = []
    for item in payload.get("results", []):
        mt = item.get("media_type")
        if mt not in ("movie", "tv"):
            continue
        if not item.get("poster_path"):
            continue
        title, date = _title_and_date(item, mt)
        if not title:
            continue
        results.append(
            {
                "type": mt,
                "tmdb_id": item.get("id"),
                "title": title,
                "year": _year(date),
                "poster_url": _poster_url(item.get("poster_path")),
                "overview": item.get("overview") or None,
                "rating": _rating(item.get("vote_average")),
            }
        )
    return results


def get_details(media_type: str, tmdb_id: int) -> dict[str, Any]:
    """Détails enrichis : ajoute les noms de genres et les 3 premiers acteurs.

    Renvoie un dict prêt à être POSTé sur `/api/culture`.
    """
    if media_type not in ("movie", "tv"):
        raise ValueError("media_type doit être 'movie' ou 'tv'")

    with _client() as c:
        lang = _lang()

        r = c.get(f"/{media_type}/{tmdb_id}", params={"language": lang})
        r.raise_for_status()
        d = r.json()

        rc = c.get(f"/{media_type}/{tmdb_id}/credits", params={"language": lang})
        rc.raise_for_status()
        cast = rc.json().get("cast", []) or []

    title, date = _title_and_date(d, media_type)
    genres = [g.get("name") for g in (d.get("genres") or []) if g.get("name")]
    actors = [c.get("name") for c in cast[:3] if c.get("name")]

    return {
        "type": media_type,
        "tmdb_id": d.get("id"),
        "title": title,
        "year": _year(date),
        "poster_url": _poster_url(d.get("poster_path")),
        "overview": d.get("overview") or None,
        "rating": _rating(d.get("vote_average")),
        "genres": genres or None,
        "actors": actors or None,
    }
