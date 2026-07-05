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

def get_access_token() -> str:
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

    data = {
        "grant_type": "client_credentials",
        "scope": os.getenv("FT_SCOPE", SCOPE)
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
