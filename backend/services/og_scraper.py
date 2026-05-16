"""Extraction de méta-données depuis une URL (Open Graph + Twitter Card + fallback).

Usage typique : l'utilisateur colle une URL de recette (Marmiton, blog…),
on récupère titre + image + description pour pré-remplir une carte cuisine.

Limites connues :
- Instagram, Pinterest et autres sites qui rendent leurs métadonnées en JS
  ne donneront pas de bons résultats. L'app demandera alors une saisie manuelle.
- Pas de protection SSRF poussée en V1 : l'app est privée et auth-gated.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36 CocoonBot/0.1"
)


def _meta(soup: BeautifulSoup, *, prop: str | None = None, name: str | None = None) -> str | None:
    """Récupère le contenu d'un <meta property="..."> ou <meta name="...">."""
    if prop:
        tag = soup.find("meta", attrs={"property": prop})
        if tag and tag.get("content"):
            return tag.get("content").strip() or None
    if name:
        tag = soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return tag.get("content").strip() or None
    return None


def parse_url(url: str, timeout: float = 10.0) -> dict[str, Any]:
    """Parse une URL et renvoie un dict prêt pour le frontend.

    Champs renvoyés (toujours présents, `None` si non trouvé) :
    - `title`
    - `image_url`
    - `description`
    - `site_name`
    - `source_url` (l'URL finale après redirections)
    """
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "fr,en;q=0.5",
    }

    with httpx.Client(
        timeout=timeout, follow_redirects=True, headers=headers
    ) as c:
        r = c.get(url)
        r.raise_for_status()
        final_url = str(r.url)
        soup = BeautifulSoup(r.text, "html.parser")

    title = (
        _meta(soup, prop="og:title")
        or _meta(soup, name="twitter:title")
        or (soup.title.string.strip() if soup.title and soup.title.string else None)
    )
    image = (
        _meta(soup, prop="og:image")
        or _meta(soup, prop="og:image:secure_url")
        or _meta(soup, name="twitter:image")
        or _meta(soup, name="twitter:image:src")
    )
    description = (
        _meta(soup, prop="og:description")
        or _meta(soup, name="twitter:description")
        or _meta(soup, name="description")
    )
    site_name = _meta(soup, prop="og:site_name")

    # Résoudre les URLs d'image relatives
    if image and not image.startswith(("http://", "https://")):
        image = urljoin(final_url, image)

    return {
        "title": title,
        "image_url": image,
        "description": description,
        "site_name": site_name,
        "source_url": final_url,
    }
