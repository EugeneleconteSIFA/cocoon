"""Endpoints de recherche / proxy vers services externes.

Toutes les routes vivent sous `/api/search/...`. Le frontend appelle ces
routes pour ne **jamais** voir les clés API (côté serveur uniquement).

Chaque appel renvoie un payload directement compatible avec les schémas
`*Create` de l'app : le frontend peut POSTer le résultat tel quel.
"""

from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, HttpUrl

from ..services import gplaces, og_scraper, tmdb

router = APIRouter(prefix="/api/search", tags=["search"])


# ─── Gestion d'erreurs commune ──────────────────────────────────────
def _upstream_error_message(response: httpx.Response) -> str | None:
    try:
        data = response.json()
    except Exception:
        return None
    if isinstance(data, dict):
        err = data.get("error")
        if isinstance(err, dict) and err.get("message"):
            return str(err["message"])
        if isinstance(data.get("detail"), str):
            return data["detail"]
    return None


def _wrap_http_call(func, *args, label: str, **kwargs):
    """Wrappe un appel service pour mapper les erreurs sur des HTTPException."""
    try:
        return func(*args, **kwargs)
    except RuntimeError as exc:
        # Clé API manquante / mal configurée
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code
        extra = _upstream_error_message(exc.response)
        if label == "Google Places" and code == 403:
            detail = (
                "Google Places refuse la clé API (403). Dans Google Cloud : "
                "activer « Places API (New) », facturation activée, "
                "restriction IP du serveur (168.231.85.64 en IPv4 ; le VPS peut sortir en IPv6)."
            )
            if extra:
                detail += f" Détail Google : {extra}"
            raise HTTPException(status_code=502, detail=detail) from exc
        detail = f"{label} a répondu {code}"
        if extra:
            detail += f" — {extra}"
        raise HTTPException(status_code=502, detail=detail) from exc
    except httpx.HTTPError as exc:
        # Timeout, DNS, etc.
        raise HTTPException(status_code=502, detail=f"{label} injoignable") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# ─── Culture : TMDb ─────────────────────────────────────────────────
@router.get("/culture", summary="Rechercher un film ou une série")
def search_culture(
    q: str = Query(..., min_length=2, description="Texte de recherche (3 lettres suffisent)"),
):
    """Renvoie une liste légère, prête à afficher en vignettes.

    Chaque élément contient : `type`, `tmdb_id`, `title`, `year`,
    `poster_url`, `overview`, `rating`. Filtre les résultats sans poster.
    """
    return _wrap_http_call(tmdb.search_multi, q, label="TMDb")


@router.get(
    "/culture/{media_type}/{tmdb_id}",
    summary="Détails enrichis d'un film/série (genres + acteurs)",
)
def details_culture(
    media_type: str = Path(..., pattern="^(movie|tv)$"),
    tmdb_id: int = Path(..., gt=0),
):
    """Renvoie un objet prêt à POSTer sur `/api/culture`."""
    return _wrap_http_call(
        tmdb.get_details, media_type, tmdb_id, label="TMDb"
    )


# ─── Lieux : Google Places ──────────────────────────────────────────
@router.get("/place", summary="Rechercher un lieu (restaurant, ville, lieu, …)")
def search_place(
    q: str = Query(..., min_length=2, description="Nom, adresse ou ville"),
):
    """Renvoie une liste légère sans photo (pour live-typing)."""
    return _wrap_http_call(gplaces.search_text, q, label="Google Places")


@router.get(
    "/place/details",
    summary="Détails enrichis d'un lieu (avec photo)",
)
def details_place(
    place_id: str = Query(..., min_length=1, description="Identifiant Google (`places/ChIJ…`)"),
):
    """Renvoie un objet prêt à POSTer sur `/api/lieux`, avec photo_url.

    Query param (et non segment d'URL) : les ids Google contiennent un `/`
    (`places/ChIJ…`) qui casse le routage FastAPI/Nginx en path variable.
    """
    return _wrap_http_call(gplaces.get_details, place_id, label="Google Places")


# ─── URL → Open Graph (recettes, articles, blogs) ───────────────────
class UrlIn(BaseModel):
    url: HttpUrl


@router.post(
    "/url",
    summary="Extraire titre + image + description d'une URL (Open Graph)",
)
def search_url(payload: UrlIn):
    """Idéal pour pré-remplir une recette à partir d'un lien (Marmiton, blog, etc.)."""
    return _wrap_http_call(og_scraper.parse_url, str(payload.url), label="Page distante")
