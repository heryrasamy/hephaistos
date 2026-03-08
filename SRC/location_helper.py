from __future__ import annotations
from typing import List, Dict


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

    # tri simple: d'abord les correspondances exactes code postal, puis alpha
    results.sort(
        key=lambda c: (
            0 if str(c.get("codePostal", "")).startswith(q) else 1,
            str(c.get("libelle", "")),
            str(c.get("codePostal", "")),
        )
    )

    return results[:limit]


def format_commune_label(c: Dict) -> str:
    libelle = c.get("libelle", "")
    cp = c.get("codePostal", "")
    dep = c.get("codeDepartement", "")
    return f"{libelle} ({cp}) — dep {dep}"