import os
from requests.auth import HTTPBasicAuth
import requests
import time
from dotenv import load_dotenv


# =========================================================
# CONFIG — À PERSONNALISER AVEC TES IDENTIFIANTS
# =========================================================

TOKEN_URL = (
    "https://entreprise.francetravail.fr/connexion/oauth2/"
    "access_token?realm=/partenaire"
)
OFFERS_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
COMMUNES_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/referentiel/communes"
SCOPE = "o2dsoffre api_offresdemploiv2"
load_dotenv()

# =========================================================
# GESTION DU TOKEN (avec cache)
# =========================================================
_token_cache = {
    "access_token": None,
    "expires_at": 0
}

def get_access_token(scope: str | None = None) -> str:
    """
    Récupère un token OAuth2 France Travail.
    Utilise un cache pour éviter les appels inutiles.
    """
    now = time.time()

    # Token encore valide ?
    if _token_cache["access_token"] and now < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    client_id = os.getenv("FT_CLIENT_ID")
    client_secret = os.getenv("FT_CLIENT_SECRET")

    requested_scope = scope or os.getenv("FT_SCOPE", SCOPE)

    data = {
        "grant_type": "client_credentials",
        "scope": requested_scope
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    resp = requests.post(
        TOKEN_URL,
        data=data,
        headers=headers,
        auth=HTTPBasicAuth(client_id, client_secret),
        timeout=30,
    )

    if resp.status_code != 200:
        raise Exception(f"Erreur token : {resp.text}")

    token_data = resp.json()
    access_token = token_data.get("access_token")
    expires_in = token_data.get("expires_in", 3600)

    _token_cache["access_token"] = access_token
    _token_cache["expires_at"] = now + expires_in - 30

    return access_token


# =========================================================
# RECHERCHE D’OFFRES
# =========================================================
def search_offers(token: str, params: dict, range_query: str = "0-49"):
    """
    Appelle l’API France Travail pour récupérer des offres.
    Retourne (json, content-range)
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Range": f"items={range_query}"
    }

    resp = requests.get(OFFERS_URL, headers=headers, params=params)

    if resp.status_code not in (200, 206):
        raise Exception(f"Erreur API offres : {resp.status_code} — {resp.text}")

    content_range = resp.headers.get("Content-Range", "")
    return resp.json(), content_range


# =========================================================
# RECHERCHE DE COMMUNES
# =========================================================
def search_communes(token: str):
    """
    Récupère la liste complète des communes France Travail.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    resp = requests.get(COMMUNES_URL, headers=headers)

    if resp.status_code != 200:
        raise Exception(f"Erreur API communes : {resp.text}")

    return resp.json()


# =========================================================
# NORMALISATION DES OFFRES
# =========================================================
def normalize_offer(o: dict) -> dict:
    """
    Nettoie et simplifie une offre France Travail.
    """
    if not isinstance(o, dict):
        return {}

    return {
        "id": o.get("id"),
        "title": o.get("intitule", "").strip(),
        "company": (o.get("entreprise") or {}).get("nom", "").strip(),
        "location": (o.get("lieuTravail") or {}).get("libelle", "").strip(),
        "text": o.get("description", "").strip(),
        "url": o.get("origineOffre", {}).get("urlOrigine", ""),
        "raw": o
    }
def search_rome_appellations(query: str) -> dict:
    """
    Recherche des appellations métier dans l'API ROME Métiers.
    Exemple : "formateur", "développeur", "chef de projet".
    """
    token = get_access_token(
        scope="api_rome-metiersv1 nomenclatureRome"
    )

    url = "https://api.francetravail.io/partenaire/rome-metiers/v1/metiers/appellation/requete"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    params = {
        "q": query
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=15,
    )

    response.raise_for_status()
    return response.json()
def normalize_rome_appellations(data: dict) -> list[dict]:
    """
    Transforme la réponse brute ROME en liste simple exploitable.
    """
    results = data.get("resultats", [])

    normalized = []

    for item in results:
        metier = item.get("metier", {})

        normalized.append({
            "appellation_code": item.get("code"),
            "appellation_libelle": item.get("libelle"),
            "metier_code": metier.get("code"),
            "metier_libelle": metier.get("libelle"),
        })

    return normalized
def extract_unique_rome_jobs(appellations: list[dict]) -> list[dict]:
    """
    Extrait les métiers ROME uniques à partir des appellations normalisées.
    """
    jobs = {}

    for item in appellations:
        metier_code = item.get("metier_code")
        metier_libelle = item.get("metier_libelle")

        if not metier_code:
            continue

        if metier_code not in jobs:
            jobs[metier_code] = {
                "metier_code": metier_code,
                "metier_libelle": metier_libelle,
            }

    return list(jobs.values())
def search_unique_rome_jobs(query: str) -> list[dict]:
    """
    Recherche les métiers ROME uniques correspondant à une requête.
    """
    data = search_rome_appellations(query)
    appellations = normalize_rome_appellations(data)

    return extract_unique_rome_jobs(appellations)


def test_rome_metiers_api():
    token = get_access_token(
        scope="api_rome-metiersv1 nomenclatureRome"
    )

    url = "https://api.francetravail.io/partenaire/rome-metiers/v1/metiers/appellation/requete"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    params = {
        "q": "formateur"
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=15,
    )

    print("Status code :", response.status_code)
    print("Headers :", dict(response.headers))
    print("Body :", response.text)

    return response