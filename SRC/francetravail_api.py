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
SCOPE = "o2dsoffre api_offresdemploiv2 api_referentielspartenairev1"
load_dotenv()

# =========================================================
# GESTION DU TOKEN (avec cache)
# =========================================================
_token_cache = {}


def get_access_token(scope: str | None = None) -> str:
    """
    Récupère un token OAuth2 France Travail.
    Le cache est séparé par scope.
    """
    now = time.time()

    requested_scope = scope or os.getenv("FT_SCOPE", SCOPE)

    cached_token = _token_cache.get(requested_scope)

    if cached_token and now < cached_token["expires_at"]:
        return cached_token["access_token"]

    client_id = os.getenv("FT_CLIENT_ID")
    client_secret = os.getenv("FT_CLIENT_SECRET")

    data = {
        "grant_type": "client_credentials",
        "scope": requested_scope,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    resp = requests.post(
        TOKEN_URL,
        data=data,
        headers=headers,
        auth=HTTPBasicAuth(client_id, client_secret),
        timeout=30,
    )

    if resp.status_code != 200:
        raise Exception(
            f"Erreur token : status={resp.status_code} | body={resp.text}"
        )

    token_data = resp.json()
    access_token = token_data.get("access_token")
    expires_in = token_data.get("expires_in", 3600)

    _token_cache[requested_scope] = {
        "access_token": access_token,
        "expires_at": now + expires_in - 30,
    }

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
        raise Exception(f"Erreur API communes : status={resp.status_code} | body={resp.text}")

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
    if response.status_code == 429:
        return {"resultats": []}

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

def get_rome_job_profile(
    rome_code: str,
    fields: list[str] | None = None
) -> dict:
    """
    Lit la fiche détaillée d'un métier ROME à partir de son code.
    Exemple : M1607, E1104, H2906.
    """
    if not rome_code:
        return {}

    token = get_access_token(
        scope="api_rome-fiches-metiersv1 nomenclatureRome"
    )

    url = (
        "https://api.francetravail.io/partenaire/"
        f"rome-fiches-metiers/v1/fiches-rome/fiche-metier/{rome_code}"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    params = {}

    if fields:
        params["champs"] = ",".join(fields)

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30,
    )

    if response.status_code == 429:
        return {}

    if response.status_code != 200:
        raise Exception(
            "Erreur API fiche métier ROME : "
            f"status={response.status_code} | body={response.text}"
        )

    return response.json()
def extract_rome_competences(profile: dict) -> list[dict]:
    """
    Extrait toutes les compétences d'une fiche métier ROME
    dans un format simple exploitable par Héphaïstos.
    """

    competences = []

    for groupe in profile.get("groupesCompetencesMobilisees", []):

        enjeu = groupe.get("enjeu", {})
        enjeu_code = enjeu.get("code", "")
        enjeu_libelle = enjeu.get("libelle", "")

        for comp in groupe.get("competences", []):

            competences.append({
                "enjeu_code": enjeu_code,
                "enjeu": enjeu_libelle,
                "type": comp.get("type", ""),
                "code": comp.get("code", ""),
                "libelle": comp.get("libelle", ""),
            })

    return competences


def extract_rome_savoirs(profile: dict) -> list[dict]:
    """
    Extrait les savoirs d'une fiche métier ROME
    dans un format simple exploitable par Héphaïstos.
    """

    savoirs = []

    for groupe in profile.get("groupesSavoirs", []):
        categorie = groupe.get("categorieSavoirs", {})
        categorie_code = categorie.get("code", "")
        categorie_libelle = categorie.get("libelle", "")

        for savoir in groupe.get("savoirs", []):
            savoirs.append({
                "categorie_code": categorie_code,
                "categorie": categorie_libelle,
                "type": savoir.get("type", ""),
                "code": savoir.get("code", ""),
                "libelle": savoir.get("libelle", ""),
            })

    return savoirs


def build_rome_job_reference(profile: dict) -> dict:
    """
    Construit une référence métier ROME simple et exploitable.

    Sépare :
    - les compétences ;
    - les savoirs ;
    - les certifications et habilitations.
    """
    if not profile:
        return {
            "code": "",
            "libelle": "",
            "competences": [],
            "savoirs": [],
            "certifications": [],
        }

    metier = profile.get("metier", {}) or {}

    competences = extract_rome_competences(profile)
    all_savoirs = extract_rome_savoirs(profile)

    savoirs = []
    certifications = []

    for savoir in all_savoirs:
        if savoir.get("categorie") == "Certifications et habilitations":
            certifications.append(savoir)
        else:
            savoirs.append(savoir)

    return {
        "code": profile.get("code", "") or metier.get("code", ""),
        "libelle": metier.get("libelle", ""),
        "competences": competences,
        "savoirs": savoirs,
        "certifications": certifications,
    }


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
    if response.status_code == 429:
        return {"resultats": []}

    response.raise_for_status()
    return response.json()


