from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import Dict, List, Tuple

from francetravail_api import search_unique_rome_jobs
from francetravail_api import (
    get_rome_job_profile,
    build_rome_job_reference,
)


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
def filter_rome_candidate_terms(terms: List[str]) -> List[str]:
    """
    Construit des expressions métier pertinentes à partir des termes du CV.

    Priorité :
    1. expressions de 2 ou 3 mots ;
    2. termes professionnels isolés ;
    3. suppression des coordonnées, rubriques et éléments parasites.
    """

    blacklist = {
        "besoin", "besoins", "concret", "concrete",
        "mission", "missions", "activite", "activites",
        "experience", "experiences",
        "competence", "competences",
        "telephone", "email", "adresse",
        "identite", "professionnelle", "professionnel",
        "profil", "contact", "coordonnees",
        "depuis", "plus", "vingt", "parcours",
        "autour", "meme","besoin", "besoins", "concret", "concrete",
        "mission", "missions", "activite", "activites",
        "experience", "experiences",
        "competence", "competences",
        "telephone", "email", "mail", "adresse",
        "identite", "professionnelle", "professionnel",
        "profil", "contact", "coordonnees",
        "depuis", "plus", "vingt", "parcours",
        "autour", "meme",
        "entrepreneur", "independant", "independante",
        "toulouse","parcours",
        "parcours",
        "savoir-faire",
        "formation",
        "formations",
        "candidature",
        "poste",
        "universite",
        "université",
    }

    connectors = {
        "de", "du", "des", "d", "en", "et", "a", "au",
    }

    separators = {
        "•", "-", "|", "/", "–", "—",
    }

    segments: List[List[str]] = []
    current_segment: List[str] = []

    for term in terms:
        original = str(term).strip()

        if not original:
            continue

        if original in separators:
            if current_segment:
                segments.append(current_segment)
                current_segment = []
            continue

        clean = normalize_text(original)

        if not clean:
            continue

        # Les titres entièrement en majuscules sont généralement
        # des rubriques, des noms ou des éléments administratifs.
        if original.isupper() and len(original) > 2:
            continue

        if clean in blacklist:
            continue

        if clean.isdigit():
            continue

        if "@" in original:
            continue

        current_segment.append(original)

    if current_segment:
        segments.append(current_segment)

    candidates: List[str] = []
    seen = set()

    def add_candidate(words: List[str]) -> None:
        phrase = " ".join(words).strip()
        normalized = normalize_text(phrase)
        normalized_words = normalized.split()

        if not normalized_words:
            return

        if normalized_words[0] in connectors:
            return

        if normalized_words[-1] in connectors:
            return

        meaningful_words = [
            word
            for word in normalized.split()
            if word not in connectors
            and word not in blacklist
            and len(word) >= 3
        ]

        if not normalized:
            return

        if not meaningful_words:
            return

        if normalized in seen:
            return

        seen.add(normalized)
        candidates.append(phrase)

    # Expressions métier : trois mots puis deux mots.
    for segment in segments:
        for size in (3, 2):
            if len(segment) < size:
                continue

            for index in range(len(segment) - size + 1):
                add_candidate(segment[index:index + size])

    # Termes isolés en dernier recours.
    for segment in segments:
        for term in segment:
            clean = normalize_text(term)

            if clean in connectors:
                continue

            if clean in blacklist:
                continue

            if len(clean) < 4:
                continue

            add_candidate([term])

    return candidates
def infer_rome_jobs_from_terms(
    cv_terms: List[str],
    max_terms: int = 5,
) -> List[Dict[str, str]]:
    """
    Recherche des métiers ROME à partir des termes détectés dans le CV
    puis les classe selon le nombre de termes du CV qui convergent vers eux.
    """

    rome_jobs: Dict[str, Dict] = {}

    for term in cv_terms[:max_terms]:

        query = str(term).strip()

        if not query:
            continue

        jobs = search_unique_rome_jobs(query)

        for job in jobs:

            code = job.get("metier_code")

            if not code:
                continue

            if code not in rome_jobs:

                rome_jobs[code] = {
                    **job,
                    "matched_terms": set(),
                    "term_score": 0,
                }

            rome_jobs[code]["matched_terms"].add(query)
            rome_jobs[code]["term_score"] = len(
                rome_jobs[code]["matched_terms"]
            )

    results = list(rome_jobs.values())

    results.sort(
        key=lambda j: (
            -j["term_score"],
            j["metier_libelle"],
        )
    )

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
                # ---------------------------------------------------------
    # Priorité métier : musique / violon / orchestre
    # Corrige le biais "formation générique" quand le CV est
    # clairement artistique avec une composante pédagogique.
    # ---------------------------------------------------------
    cv_terms_lower = {str(term).strip().lower() for term in cv_terms if str(term).strip()}

    music_markers = {
        "violon", "violoniste", "musique", "orchestre", "conservatoire",
        "chambre", "cpes", "musicolus", "acadomia"
    }

    music_hits = sum(1 for marker in music_markers if marker in cv_terms_lower)

    if music_hits >= 3:
        prioritized_music_jobs = [
            {"job": "professeur de violon", "domain": "culture", "family": "culture"},
            {"job": "violoniste", "domain": "culture", "family": "culture"},
            {"job": "musicien d'orchestre", "domain": "culture", "family": "culture"},
            {"job": "intervenant musique", "domain": "culture", "family": "culture"},
            {"job": "animation musicale", "domain": "culture", "family": "culture"},
        ]

        existing_keys = {
            (
                str(job.get("job", "")).strip().lower(),
                str(job.get("domain", "")).strip().lower()
            )
            for job in ranked_jobs
            if isinstance(job, dict)
        }

        music_jobs_to_add = []
        for job in prioritized_music_jobs:
            key = (
                str(job.get("job", "")).strip().lower(),
                str(job.get("domain", "")).strip().lower()
            )
            if key not in existing_keys:
                music_jobs_to_add.append(job)

        ranked_jobs = music_jobs_to_add + ranked_jobs

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

def compare_cv_to_rome_reference(
    cv_text: str,
    rome_reference: Dict
) -> Dict[str, List[Dict]]:
    """
    Compare le texte brut du CV aux compétences et savoirs ROME.

    Classe les éléments en deux groupes :
    - présents dans le CV ;
    - non repérés dans le CV.

    Cette première version repose sur une correspondance lexicale simple.
    """

    normalized_cv = normalize_text(cv_text or "")

    present = []
    missing = []

    reference_items = (
        rome_reference.get("competences", [])
        + rome_reference.get("savoirs", [])
    )

    for item in reference_items:
        libelle = item.get("libelle", "")
        normalized_label = normalize_text(libelle)

        if not normalized_label:
            continue

        label_terms = [
            word
            for word in normalized_label.split()
            if len(word) >= 4
        ]

        matched_terms = [
            word
            for word in label_terms
            if word in normalized_cv
        ]

        coverage = (
            len(matched_terms) / len(label_terms)
            if label_terms
            else 0
        )

        result_item = {
            **item,
            "matched_terms": matched_terms,
            "coverage": round(coverage, 2),
        }

        if coverage >= 0.5:
            present.append(result_item)
        else:
            missing.append(result_item)

    present.sort(
        key=lambda item: item.get("coverage", 0),
        reverse=True,
    )

    missing.sort(
        key=lambda item: item.get("coverage", 0),
        reverse=True,
    )

    return {
        "present": present,
        "missing": missing,
    }
if __name__ == "__main__":
    cv_text = """
    Gestion administrative de dossiers.
    Organisation de réunions.
    Rédaction de comptes rendus.
    Mise à jour de bases de données.
    Accueil et renseignement du public.
    Utilisation des outils bureautiques.
    """

    profile = get_rome_job_profile("M1607")
    reference = build_rome_job_reference(profile)

    comparison = compare_cv_to_rome_reference(
        cv_text=cv_text,
        rome_reference=reference,
    )

    print("Compétences présentes :", len(comparison["present"]))
    print("Compétences non repérées :", len(comparison["missing"]))

    print("\nPrésentes :")
    for item in comparison["present"][:10]:
        print(
            item["coverage"],
            "-",
            item["libelle"],
            "- termes trouvés :",
            item["matched_terms"],
        )

    print("\nNon repérées :")
    for item in comparison["missing"][:10]:
        print(
            item["coverage"],
            "-",
            item["libelle"],
            "- termes trouvés :",
            item["matched_terms"],
        )
