from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import Dict, List, Tuple


# =========================================================
# OUTILS DE BASE
# =========================================================

STOPWORDS = {
    "de", "des", "du", "la", "le", "les", "un", "une", "et", "ou", "en", "au", "aux",
    "pour", "par", "avec", "sans", "sur", "sous", "dans", "chez", "vers", "entre",
    "a", "à", "d", "l", "the", "and", "of", "to", "in", "on", "as",
    "vos", "nos", "ses", "leur", "leurs", "son", "sa",
    "ce", "cet", "cette", "ces", "qui", "que", "quoi", "dont",
    "est", "sont", "etre", "être", "avoir", "faire", "plus", "moins",
    "mission", "missions", "poste", "profil", "candidat", "candidature",
    "entreprise", "societe", "société", "structure", "service", "equipe", "équipe",
    "travail", "emploi", "experience", "expérience", "competence", "compétence",
    "formation", "projet", "projets", "activite", "activité", "annee", "année",
}


def strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text or "")
        if not unicodedata.combining(c)
    )


def normalize_text(text: str) -> str:
    text = (text or "").lower()
    text = strip_accents(text)
    text = re.sub(r"[-'’/]", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str) -> List[str]:
    norm = normalize_text(text)
    tokens = []
    for tok in norm.split():
        if len(tok) < 3:
            continue
        if tok in STOPWORDS:
            continue
        if tok.isdigit():
            continue
        tokens.append(tok)
    return tokens


# =========================================================
# FAMILLES METIER
# =========================================================

ACTIVITY_FAMILY_SIGNALS: Dict[str, Dict[str, List[str]]] = {
    "administratif_gestion": {
        "strong_signals": [
            "assistant administratif", "agent administratif", "gestion administrative",
            "secretariat", "secrétariat", "classement", "archivage", "bureautique",
            "saisie", "facturation", "gestion documentaire", "courrier"
        ],
        "context_signals": [
            "planning", "organisation", "coordination", "suivi", "dossier", "dossiers",
            "tableau", "excel", "word", "outlook", "reporting"
        ],
    },
    "relation_client_accueil": {
        "strong_signals": [
            "accueil", "agent d accueil", "charge d accueil", "relation client",
            "service client", "support client", "conseiller client"
        ],
        "context_signals": [
            "telephone", "téléphone", "public", "usagers", "visiteurs", "client", "clients"
        ],
    },
    "communication_marketing": {
        "strong_signals": [
            "communication", "communication digitale", "communication numerique",
            "communication numérique", "community manager", "reseaux sociaux",
            "réseaux sociaux", "creation de contenu", "création de contenu",
            "redaction web", "rédaction web", "newsletter", "marketing"
        ],
        "context_signals": [
            "site internet", "web", "digital", "contenu", "media", "média",
            "campagne", "visibilite", "visibilité"
        ],
    },
    "creation_artistique": {
        "strong_signals": [
            "mediation culturelle", "médiation culturelle", "projet culturel",
            "culturel", "culturelle", "patrimoine", "musee", "musée",
            "exposition", "creation", "création", "artistique"
        ],
        "context_signals": [
            "animation", "publics", "visite", "visites", "culture", "diffusion"
        ],
    },
    "analyse_pilotage": {
        "strong_signals": [
            "analyse", "pilotage", "coordination", "gestion de projet",
            "chef de projet", "indicateur", "indicateurs", "kpi", "reporting"
        ],
        "context_signals": [
            "tableau de bord", "budget", "suivi", "planification", "organisation"
        ],
    },
    "vente_commerce": {
        "strong_signals": [
            "vente", "commercial", "commerciale", "relation commerciale",
            "conseil client", "prospection", "negociation", "négociation"
        ],
        "context_signals": [
            "client", "clients", "offre", "produit", "service", "services"
        ],
    },
    "logistique": {
        "strong_signals": [
            "logistique", "stock", "gestion de stock", "gestion des stocks",
            "magasin", "reception", "réception", "expedition", "expédition",
            "preparation de commandes", "préparation de commandes"
        ],
        "context_signals": [
            "inventaire", "approvisionnement", "entrepot", "entrepôt", "flux"
        ],
    },
    "production": {
        "strong_signals": [
            "production", "fabrication", "assemblage", "chaine", "chaîne",
            "atelier", "conditionnement"
        ],
        "context_signals": [
            "machine", "machines", "cadence", "qualite", "qualité"
        ],
    },
    "maintenance": {
        "strong_signals": [
            "maintenance", "depannage", "dépannage", "reparation", "réparation",
            "technique", "installation", "equipement", "équipement"
        ],
        "context_signals": [
            "diagnostic", "panne", "materiel", "matériel", "controle"
        ],
    },
    "sante_soin": {
        "strong_signals": [
            "soin", "sante", "santé", "medical", "médical",
            "aide soignant", "aide-soignant", "infirmier", "infirmiere",
            "secretaire medical", "secrétaire médical"
        ],
        "context_signals": [
            "patient", "patients", "hospitalier", "clinique", "accompagnement"
        ],
    },
    "social_accompagnement": {
        "strong_signals": [
            "accompagnement", "social", "educatif", "éducatif",
            "insertion", "aes", "medico social", "médico social"
        ],
        "context_signals": [
            "publics fragiles", "beneficiaires", "bénéficiaires", "suivi social"
        ],
    },
    "pedagogie_formation": {
        "strong_signals": [
            "formation", "pedagogie", "pédagogie", "enseignement",
            "transmission", "animateur formation", "formateur"
        ],
        "context_signals": [
            "atelier", "apprenants", "cours", "animation"
        ],
    },
    "securite_protection": {
        "strong_signals": [
            "securite", "sécurité", "surveillance", "protection", "controle d acces",
            "contrôle d accès", "prevention", "prévention"
        ],
        "context_signals": [
            "site", "incendie", "rondes", "consignes"
        ],
    },
    "hotellerie_restauration": {
        "strong_signals": [
            "restauration", "service en salle", "cuisine", "hotel", "hôtel",
            "hebergement", "hébergement", "reception hotel", "réception hôtel"
        ],
        "context_signals": [
            "client", "clients", "service", "accueil"
        ],
    },
}


JOB_FAMILY_TO_ROLES: Dict[str, List[Tuple[str, str]]] = {
    "administratif_gestion": [
        ("assistant administratif", "administratif"),
        ("agent administratif", "administratif"),
        ("assistant de gestion", "administratif"),
        ("assistant polyvalent", "administratif"),
    ],
    "relation_client_accueil": [
        ("agent d'accueil", "relation client"),
        ("chargé d'accueil", "relation client"),
        ("conseiller client", "relation client"),
        ("support client", "relation client"),
    ],
    "communication_marketing": [
        ("chargé de communication", "communication"),
        ("chargé de communication digitale", "communication"),
        ("community manager", "communication"),
        ("créateur de contenu", "communication"),
        ("rédacteur web", "communication"),
    ],
    "creation_artistique": [
        ("médiation culturelle", "culture"),
        ("chargé de projet culturel", "culture"),
        ("assistant culturel", "culture"),
        ("chargé de diffusion", "culture"),
    ],
    "analyse_pilotage": [
        ("chargé de projet", "pilotage"),
        ("chef de projet", "pilotage"),
        ("coordinateur", "pilotage"),
        ("analyste", "analyse"),
    ],
    "vente_commerce": [
        ("assistant commercial", "commerce"),
        ("conseiller de vente", "commerce"),
        ("commercial", "commerce"),
        ("chargé de relation client", "commerce"),
    ],
    "logistique": [
        ("agent logistique", "logistique"),
        ("gestionnaire de stock", "logistique"),
        ("magasinier", "logistique"),
        ("préparateur de commandes", "logistique"),
    ],
    "production": [
        ("agent de production", "production"),
        ("opérateur de fabrication", "production"),
        ("agent de conditionnement", "production"),
    ],
    "maintenance": [
        ("technicien de maintenance", "maintenance"),
        ("agent technique", "maintenance"),
        ("technicien d'installation", "maintenance"),
    ],
    "sante_soin": [
        ("aide-soignant", "santé"),
        ("secrétaire médical", "santé"),
        ("assistant médical", "santé"),
        ("agent de service hospitalier", "santé"),
    ],
    "social_accompagnement": [
        ("accompagnant éducatif et social", "social"),
        ("intervenant social", "social"),
        ("assistant socio-éducatif", "social"),
    ],
    "pedagogie_formation": [
        ("formateur", "formation"),
        ("animateur pédagogique", "formation"),
        ("chargé de formation", "formation"),
    ],
    "securite_protection": [
        ("agent de sécurité", "sécurité"),
        ("agent de surveillance", "sécurité"),
    ],
    "hotellerie_restauration": [
        ("agent de restauration", "restauration"),
        ("employé polyvalent de restauration", "restauration"),
        ("réceptionniste", "hôtellerie"),
    ],
}


# =========================================================
# DETECTION DES FAMILLES
# =========================================================

def _count_family_signals(cv_text: str) -> Dict[str, int]:
    text_norm = normalize_text(cv_text)
    token_counts = Counter(tokenize(cv_text))

    family_scores: Dict[str, int] = {}

    for family, signals in ACTIVITY_FAMILY_SIGNALS.items():
        score = 0

        for phrase in signals.get("strong_signals", []):
            phrase_norm = normalize_text(phrase)
            if phrase_norm and phrase_norm in text_norm:
                score += 5

        for phrase in signals.get("context_signals", []):
            phrase_norm = normalize_text(phrase)
            if not phrase_norm:
                continue

            if " " in phrase_norm:
                if phrase_norm in text_norm:
                    score += 2
            else:
                score += token_counts.get(phrase_norm, 0)

        family_scores[family] = score

    return family_scores


def get_top_cv_families(cv_text: str, top_n: int = 3) -> List[str]:
    """
    Retourne les familles métier les plus probables à partir du CV.
    """
    scores = _count_family_signals(cv_text)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    results = []
    for family, score in ranked:
        if score <= 0:
            continue
        results.append(family)
        if len(results) >= top_n:
            break

    return results


# =========================================================
# INFERENCE METIER
# =========================================================

def build_job_inference_summary(
    detected_families: List[str],
    cv_terms: List[str],
    top_n: int = 3
) -> Dict[str, object]:
    """
    Construit un résumé métier simple et robuste à partir des familles détectées.
    """
    families = detected_families[:top_n] if detected_families else []

    ranked_jobs: List[Dict[str, str]] = []

    for family in families:
        for job_label, domain in JOB_FAMILY_TO_ROLES.get(family, []):
            ranked_jobs.append({
                "job": job_label,
                "domain": domain,
                "family": family,
            })

    main_job = ranked_jobs[0] if ranked_jobs else {"job": "inconnu", "domain": "inconnu", "family": ""}
    related_jobs = ranked_jobs[1:4] if len(ranked_jobs) > 1 else []

    return {
        "main_job": main_job,
        "related_jobs": related_jobs,
        "families_used": families,
        "ranked_jobs": ranked_jobs,
        "domain": main_job.get("domain", "inconnu"),
    }


# =========================================================
# REQUETES DE RECHERCHE
# =========================================================

def build_search_queries_from_job_summary(
    job_summary: Dict[str, object],
    topics: List[str],
    max_queries: int = 5
) -> List[str]:
    """
    Génère des requêtes de recherche à partir du résumé métier.
    On privilégie :
    1. métier principal
    2. métiers proches
    3. quelques topics utiles si besoin
    """
    queries: List[str] = []
    seen = set()

    def add_query(value: str) -> None:
        q = " ".join(str(value).strip().split())
        key = q.lower()
        if q and key not in seen:
            seen.add(key)
            queries.append(q)

    main_job = job_summary.get("main_job", {})
    related_jobs = job_summary.get("related_jobs", [])

    if isinstance(main_job, dict):
        add_query(main_job.get("job", ""))
        add_query(main_job.get("domain", ""))

    for item in related_jobs:
        if isinstance(item, dict):
            add_query(item.get("job", ""))

    # fallback avec topics si trop peu de requêtes
    for topic in topics[:5]:
        if len(queries) >= max_queries:
            break
        add_query(topic)

    return queries[:max_queries]