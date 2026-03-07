from __future__ import annotations

from typing import Any, Dict, List, Tuple

from francetravail_api import get_access_token, search_offers, normalize_offer


def add_location_params(params: Dict[str, Any], commune_code: str | None, rayon_km: int | None) -> Dict[str, Any]:
    """
    Ajoute les paramètres de localisation pour l'API France Travail.
    Ne modifie pas le dict original.
    """
    p = dict(params)

    if commune_code:
        p["lieux"] = commune_code

        if rayon_km is not None:
            p["distance"] = int(rayon_km)

    return p


def fetch_offers_francetravail(params: Dict[str, Any], max_results: int = 100) -> Tuple[List[Dict[str, Any]], str]:
    """
    Récupère jusqu'à max_results offres via pagination range.
    Retourne (offers, content_range_last)
    """

    token = get_access_token()

    offers: List[Dict[str, Any]] = []
    content_range_last = ""

    page_size = 50
    max_results = max(1, min(max_results, 150))

    for start in range(0, max_results, page_size):

        end = min(start + page_size - 1, max_results - 1)

        data, cr = search_offers(
            token,
            params=params,
            range_query=f"{start}-{end}"
        )

        content_range_last = cr or ""

        raw_list = data.get("resultats", []) or []

        offers.extend([normalize_offer(o) for o in raw_list])

        if len(raw_list) < (end - start + 1):
            break

    # dédoublonnage simple
    seen = set()
    uniq = []

    for o in offers:

        key = (
            o["title"].lower().strip(),
            o["company"].lower().strip(),
            o["location"].lower().strip(),
        )

        if key in seen:
            continue

        seen.add(key)
        uniq.append(o)

    return uniq, content_range_last