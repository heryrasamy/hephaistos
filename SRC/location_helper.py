from __future__ import annotations
from typing import List, Dict

import requests


def search_communes_geo_api(query: str) -> List[Dict]:
    """
    Recherche les communes via l'API publique geo.api.gouv.fr.
    Aucun token France Travail nécessaire.
    """
    q = (query or "").strip()
    if not q:
        return []

    url = "https://geo.api.gouv.fr/communes"

    params = {
        "fields": "nom,codesPostaux,code,codeDepartement",
        "format": "json",
    }

    if q.isdigit() and len(q) == 2:
        params["codeDepartement"] = q
    elif q.isdigit():
        params["codePostal"] = q
    else:
        params["nom"] = q

    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()

    communes = []

    for item in resp.json():
        codes_postaux = item.get("codesPostaux") or [""]

        for cp in codes_postaux:
            commune_code = item.get("code", "")

            # Paris : 75001 à 75020 → 75101 à 75120
            if cp.isdigit() and 75001 <= int(cp) <= 75020:
                arrondissement = int(cp) - 75000
                commune_code = f"751{arrondissement:02d}"
            # Lyon : 69001 à 69009 → 69381 à 69389
            elif cp.isdigit() and 69001 <= int(cp) <= 69009:
                arrondissement = int(cp) - 69000
                commune_code = f"6938{arrondissement}"
            # Marseille : 13001 à 13016 → 13201 à 13216
            elif cp.isdigit() and 13001 <= int(cp) <= 13016:
                arrondissement = int(cp) - 13000
                commune_code = f"132{arrondissement:02d}"

            communes.append({
                "libelle": item.get("nom", ""),
                "codePostal": cp,
                "codeDepartement": item.get("codeDepartement", ""),
                "code": commune_code,
            })

    return communes

def filter_communes(communes: List[Dict], query: str, limit: int = 20) -> List[Dict]:
    """
    Filtre les communes selon:
    - début de code postal
    - nom de commune
    - département
    """
    q = (query or "").strip().lower()
    if not q:
        return []

    results = []

    for c in communes:
        libelle = str(c.get("libelle", "")).lower()
        code_postal = str(c.get("codePostal", ""))
        code_dep = str(c.get("codeDepartement", ""))
        code_insee = str(c.get("code", ""))

        if (
            q in libelle
            or code_postal.startswith(q)
            or code_dep.startswith(q)
            or code_insee.startswith(q)
        ):
            results.append(c)

    results.sort(
        key=lambda c: (
            0 if str(c.get("codePostal", "")).startswith(q) else 1,
            str(c.get("codePostal", "")),
            str(c.get("libelle", "")),
        )
    )

    return results[:limit]


def format_commune_label(c: Dict) -> str:
    libelle = c.get("libelle", "")
    cp = c.get("codePostal", "")
    dep = c.get("codeDepartement", "")
    return f"{libelle} ({cp}) — dep {dep}"