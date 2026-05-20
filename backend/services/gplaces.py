"""Client minimal pour l'API Google Places (New, v1).

Deux fonctions publiques :
- `search_text(query)` : recherche par texte (sans photo, pour live-typing).
- `get_details(place_id)` : détails complets, avec URL de photo prête à l'emploi.

Les deux renvoient un dict compatible avec `schemas.LieuCreate`.

Notes Google Places (New) :
- Auth : header `X-Goog-Api-Key`.
- Field mask **obligatoire** via `X-Goog-FieldMask` (Google facture par tier de champ).
- Photos : on appelle l'endpoint `/media?skipHttpRedirect=true` pour récupérer
  une `photoUri` googleusercontent.com **sans clé dans l'URL**, qu'on peut
  ensuite stocker et servir directement au navigateur.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

PLACES_BASE = "https://places.googleapis.com/v1"

# Champs demandés en recherche (light)
_SEARCH_FIELDS = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.addressComponents",
        "places.rating",
        "places.userRatingCount",
        "places.types",
        "places.googleMapsUri",
    ]
)

# Champs demandés en détails (avec photos)
_DETAILS_FIELDS = ",".join(
    [
        "id",
        "displayName",
        "formattedAddress",
        "addressComponents",
        "rating",
        "userRatingCount",
        "types",
        "googleMapsUri",
        "photos",
    ]
)


# ─── Auth ───────────────────────────────────────────────────────────
def _api_key() -> str:
    k = (os.getenv("GOOGLE_MAPS_API_KEY") or "").strip()
    if not k:
        raise RuntimeError("GOOGLE_MAPS_API_KEY manquante.")
    return k


def _http_client(**kwargs: Any) -> httpx.Client:
    """Client sortant en IPv4 (le VPS Hostinger utilise IPv6 par défaut).

    Sans ça, Google voit 2a02:4780:7:753::1 alors que la clé est restreinte
    à 168.231.85.64 → 403.
    """
    return httpx.Client(timeout=10.0, local_address="0.0.0.0", **kwargs)


# ─── Helpers ────────────────────────────────────────────────────────
# Mapping Places `types` → catégorie lisible en français.
# On garde les plus utiles, le reste tombera en fallback formaté.
_TYPE_LABELS: dict[str, str] = {
    "restaurant": "restaurant",
    "cafe": "café",
    "bar": "bar",
    "bakery": "boulangerie",
    "pastry_shop": "pâtisserie",
    "ice_cream_shop": "glacier",
    "meal_takeaway": "à emporter",
    "museum": "musée",
    "art_gallery": "galerie d'art",
    "movie_theater": "cinéma",
    "library": "bibliothèque",
    "book_store": "librairie",
    "park": "parc",
    "tourist_attraction": "attraction touristique",
    "lodging": "logement",
    "shopping_mall": "centre commercial",
    "store": "boutique",
    "clothing_store": "boutique de vêtements",
    "spa": "spa",
    "gym": "salle de sport",
    "stadium": "stade",
    "night_club": "club",
}

# Types trop génériques qu'on saute pour trouver mieux derrière
_TYPE_SKIP = {"point_of_interest", "establishment", "food"}


def _category(types: list[str] | None) -> str | None:
    if not types:
        return None
    for t in types:
        if t in _TYPE_SKIP:
            continue
        return _TYPE_LABELS.get(t, t.replace("_", " "))
    return None


def _name(display_name: dict[str, Any] | None) -> str | None:
    return (display_name or {}).get("text") if display_name else None


def _city(components: list[dict[str, Any]] | None) -> str | None:
    """Extrait la ville : 'locality' d'abord, fallback 'administrative_area_level_*'."""
    if not components:
        return None
    by_type: dict[str, str] = {}
    for comp in components:
        text = comp.get("longText") or comp.get("shortText")
        if not text:
            continue
        for t in comp.get("types", []):
            by_type.setdefault(t, text)
    for key in (
        "locality",
        "postal_town",
        "administrative_area_level_2",
        "administrative_area_level_1",
    ):
        if key in by_type:
            return by_type[key]
    return None


def _place_detail_url(place_id: str) -> str:
    """URL GET Place Details — l'API renvoie des id au format `places/ChIJ…`."""
    pid = (place_id or "").strip()
    if not pid:
        raise ValueError("place_id manquant")
    if pid.startswith("places/"):
        return f"{PLACES_BASE}/{pid}"
    return f"{PLACES_BASE}/places/{pid}"


def _rating(value: Any) -> float | None:
    if value is None:
        return None
    try:
        rounded = round(float(value), 1)
    except (TypeError, ValueError):
        return None
    return rounded if rounded > 0 else None


# ─── Photo URL resolution ───────────────────────────────────────────
def _resolve_photo_uri(
    client: httpx.Client, photo_name: str, max_width: int = 800
) -> str | None:
    """Résout l'URL canonique de la photo (sans exposer la clé)."""
    url = f"{PLACES_BASE}/{photo_name}/media"
    try:
        r = client.get(
            url,
            params={
                "key": _api_key(),
                "maxWidthPx": max_width,
                "skipHttpRedirect": "true",
            },
            timeout=5.0,
        )
        if r.status_code == 200:
            return r.json().get("photoUri")
    except httpx.HTTPError:
        return None
    return None


# ─── API publique ───────────────────────────────────────────────────
def search_text(query: str) -> list[dict[str, Any]]:
    """Recherche par texte. Résultats légers, sans photo."""
    query = (query or "").strip()
    if not query:
        return []

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": _api_key(),
        "X-Goog-FieldMask": _SEARCH_FIELDS,
    }
    body = {"textQuery": query, "languageCode": "fr"}

    with _http_client() as c:
        r = c.post(f"{PLACES_BASE}/places:searchText", headers=headers, json=body)
        r.raise_for_status()
        payload = r.json()

    results: list[dict[str, Any]] = []
    for p in payload.get("places", []) or []:
        name = _name(p.get("displayName"))
        if not name:
            continue
        results.append(
            {
                "gplaces_id": p.get("id"),
                "name": name,
                "address": p.get("formattedAddress"),
                "city": _city(p.get("addressComponents")),
                "category": _category(p.get("types")),
                "rating": _rating(p.get("rating")),
                "maps_url": p.get("googleMapsUri"),
                "photo_url": None,
            }
        )
    return results


def get_details(place_id: str) -> dict[str, Any]:
    """Détails enrichis, avec photo (1ʳᵉ disponible)."""
    headers = {
        "X-Goog-Api-Key": _api_key(),
        "X-Goog-FieldMask": _DETAILS_FIELDS,
    }

    with _http_client() as c:
        r = c.get(
            _place_detail_url(place_id),
            headers=headers,
            params={"languageCode": "fr"},
        )
        r.raise_for_status()
        p = r.json()

        photo_url: str | None = None
        photos = p.get("photos") or []
        if photos:
            photo_name = (photos[0] or {}).get("name")
            if photo_name:
                photo_url = _resolve_photo_uri(c, photo_name)

    name = _name(p.get("displayName"))
    if not name:
        raise ValueError("Lieu introuvable ou sans nom.")

    return {
        "gplaces_id": p.get("id"),
        "name": name,
        "address": p.get("formattedAddress"),
        "city": _city(p.get("addressComponents")),
        "category": _category(p.get("types")),
        "rating": _rating(p.get("rating")),
        "maps_url": p.get("googleMapsUri"),
        "photo_url": photo_url,
    }
