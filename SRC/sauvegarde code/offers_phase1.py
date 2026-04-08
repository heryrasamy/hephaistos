from __future__ import annotations

from typing import Any, Dict, List, Tuple

from francetravail_api import get_access_token, search_offers, normalize_offer


def add_location_params(
    params: Dict[str, Any],
    commune_code: str | None,
    rayon_km: int | None
) -> Dict[str, Any]:
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


def fetch_offers_francetravail(
    params: Dict[str, Any],
    max_results: int = 100
) -> Tuple[List[Dict[str, Any]], str]:
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

    seen = set()
    uniq = []

    for o in offers:
        key = (
            o.get("title", "").lower().strip(),
            o.get("company", "").lower().strip(),
            o.get("location", "").lower().strip(),
        )

        if key in seen:
            continue

        seen.add(key)
        uniq.append(o)

    return uniq, content_range_last


def fetch_offers_multi_queries(
    base_params,
    queries,
    max_results_per_query=50
):
    """
    Lance plusieurs recherches d'offres à partir d'une liste de requêtes,
    fusionne les résultats et supprime les doublons.
    """
    if not queries:
        return []

    all_offers = []
    seen_keys = set()

    for query in queries:
        try:
            params = dict(base_params or {})
            params["motsCles"] = query

            offers, _ = fetch_offers_francetravail(
                params=params,
                max_results=max_results_per_query
            )

            for offer in offers:
                key = (
                    offer.get("title", "").lower().strip(),
                    offer.get("company", "").lower().strip(),
                    offer.get("location", "").lower().strip(),
                )

                if key not in seen_keys:
                    seen_keys.add(key)
                    all_offers.append(offer)

        except Exception as e:
            print(f"Erreur requête '{query}' : {e}")

    return all_offers