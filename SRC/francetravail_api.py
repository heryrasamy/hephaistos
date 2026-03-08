from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple

import requests

TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=/partenaire"
BASE_URL = "https://api.francetravail.io/partenaire/offresdemploi"
SEARCH_URL = f"{BASE_URL}/v2/offres/search"


def get_env(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        raise RuntimeError(f"Variable manquante: {name}")
    return v


def get_access_token() -> str:
    client_id = get_env("FT_CLIENT_ID")
    client_secret = get_env("FT_CLIENT_SECRET")
    scope = get_env("FT_SCOPE")  # ex: "o2dsoffre api_offresdemploiv2"

    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": scope,
    }

    r = requests.post(
        TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=data,
        timeout=30,
    )

    if r.status_code != 200:
        raise RuntimeError(f"Token error {r.status_code}: {r.text}")

    return r.json()["access_token"]


def search_offers(token: str, params: dict, range_query: str):
    url = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"  # garde ton URL si elle diffère

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Range": f"items={range_query}",
    }

    r = requests.get(url, headers=headers, params=params, timeout=20)

    # 1) Si erreur HTTP, on sort avec un message lisible
    if r.status_code >= 400:
        snippet = (r.text or "")[:600]
        raise RuntimeError(
            f"FranceTravail API error {r.status_code}\n"
            f"URL: {r.url}\n"
            f"Headers Content-Type: {r.headers.get('Content-Type')}\n"
            f"Body (first 600 chars): {snippet}"
        )

    # 2) Si le content-type n'est pas du JSON, pareil
    ctype = (r.headers.get("Content-Type") or "").lower()
    if "json" not in ctype:
        snippet = (r.text or "")[:600]
        raise RuntimeError(
            f"FranceTravail API returned non-JSON content\n"
            f"URL: {r.url}\n"
            f"Content-Type: {r.headers.get('Content-Type')}\n"
            f"Body (first 600 chars): {snippet}"
        )

    # 3) JSON OK
    return r.json(), r.headers.get("Content-Range")
def normalize_offer(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalise une offre France Travail v2 vers le format Hephaistos.
    """
    entreprise = raw.get("entreprise") or {}
    lieu = raw.get("lieuTravail") or {}
    origine = raw.get("origineOffre") or {}

    return {
        "id": raw.get("id", ""),
        "title": raw.get("intitule", ""),
        "company": entreprise.get("nom", "") if isinstance(entreprise, dict) else str(entreprise),
        "location": lieu.get("libelle", "") if isinstance(lieu, dict) else str(lieu),
        "contract": raw.get("typeContratLibelle", raw.get("typeContrat", "")),
        "published_at": raw.get("dateCreation", raw.get("dateActualisation", "")),
        "url": origine.get("urlOrigine", "") if isinstance(origine, dict) else "",
        "text": raw.get("description", "") or "",
    }
REFERENTIEL_COMMUNES_URL = f"{BASE_URL}/v2/referentiel/communes"


def search_communes(token: str) -> list[dict]:
    """
    Récupère le référentiel des communes.
    Le référentiel renvoie une liste d'objets avec:
    - code (code INSEE)
    - libelle (nom commune)
    - codePostal
    - codeDepartement
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    r = requests.get(REFERENTIEL_COMMUNES_URL, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()
