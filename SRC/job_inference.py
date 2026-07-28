from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import Dict, Iterable, List, Sequence, Tuple

from francetravail_api import search_unique_rome_jobs


# =========================================================
# OUTILS DE BASE
# =========================================================

STOPWORDS = {
    "a", "à", "au", "aux", "avec", "ce", "ces", "cet", "cette",
    "chez", "d", "dans", "de", "des", "dont", "du", "elle", "en",
    "entre", "et", "eux", "il", "ils", "je", "la", "le", "les",
    "leur", "leurs", "l", "lui", "ma", "mais", "me", "mes", "mon",
    "ne", "nos", "notre", "nous", "on", "ou", "par", "pas", "plus",
    "pour", "qu", "que", "qui", "quoi", "sa", "sans", "se", "ses",
    "son", "sous", "sur", "ta", "te", "tes", "the", "to", "ton",
    "tu", "un", "une", "vers", "vos", "votre", "vous",
    "activite", "activites", "annee", "annees", "candidat", "candidature",
    "competence", "competences", "emploi", "entreprise", "equipe",
    "experience", "experiences", "faire", "formation", "mission", "missions",
    "poste", "profil", "projet", "projets", "service", "societe", "structure",
    "travail",
}

GENERIC_ROME_WORDS = {
    "actuellement", "annee", "annees", "candidature", "compatible",
    "curriculum", "emploi", "etude", "etudes", "etudiant", "etudiante",
    "experience", "experiences", "mention", "partiel", "poste", "profil",
    "recherche", "rechercher", "temps", "vitae",
}

CONNECTOR_WORDS = {
    "a", "au", "aux", "avec", "de", "des", "du", "en", "et", "je",
    "la", "le", "les", "ma", "mes", "mon", "pour", "sur", "un", "une",
}


def strip_accents(text: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", text or "")
        if not unicodedata.combining(char)
    )


def normalize_text(text: str) -> str:
    """Normalise un texte pour les comparaisons lexicales."""
    normalized = strip_accents(str(text or "")).lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return " ".join(normalized.split())


def _meaningful_words(text: str, min_len: int = 3) -> List[str]:
    return [
        word
        for word in normalize_text(text).split()
        if len(word) >= min_len and word not in STOPWORDS
    ]


def _dedupe_keep_order(values: Iterable[str]) -> List[str]:
    result: List[str] = []
    seen = set()

    for value in values:
        clean = " ".join(str(value or "").split())
        key = normalize_text(clean)
        if clean and key and key not in seen:
            seen.add(key)
            result.append(clean)

    return result


# =========================================================
# FAMILLES METIER
# =========================================================

# Référentiel interne volontairement généraliste. Il sert à produire une
# première hypothèse ; ROME et le contenu réel du CV doivent ensuite l'affiner.
FAMILY_KEYWORDS: Dict[str, set[str]] = {
    "Administratif & Gestion": {
        "administratif", "administration", "agenda", "archive", "assistant",
        "bureautique", "comptabilite", "courrier", "dossier", "facturation",
        "gestion", "planning", "secretariat", "tableur",
    },
    "Relation Client & Accueil": {
        "accueil", "client", "conseil", "contact", "caisse", "commercial",
        "information", "public", "reclamation", "relation", "renseigner",
        "vente", "visiteur",
    },
    "Production": {
        "assemblage", "conditionnement", "controle", "fabrication", "ligne",
        "machine", "operateur", "production", "qualite", "reglage",
    },
    "Maintenance": {
        "depannage", "diagnostic", "entretien", "installation", "maintenance",
        "mecanique", "preventif", "reparation", "technique",
    },
    "Logistique & Stock": {
        "approvisionnement", "commande", "expedition", "inventaire", "livraison",
        "logistique", "magasin", "preparation", "reception", "stock",
    },
    "Communication & Marketing": {
        "communication", "contenu", "digital", "editorial", "marketing",
        "media", "numerique", "reseaux", "seo", "social",
    },
    "Analyse & Pilotage": {
        "analyse", "data", "donnees", "indicateur", "pilotage", "reporting",
        "statistique", "tableau", "veille",
    },
    "Informatique & Numérique": {
        "application", "code", "developpement", "git", "html", "informatique",
        "javascript", "python", "sql", "streamlit", "web",
    },
    "Pédagogie & Formation": {
        "accompagnement", "animation", "apprenant", "cours", "enseignement",
        "formateur", "formation", "pedagogie", "tuteur",
    },
    "Culture & Création": {
        "art", "artistique", "concert", "culture", "musee", "musique",
        "orchestre", "patrimoine", "spectacle", "violon",
    },
}


JOB_FAMILY_TO_ROLES: Dict[str, List[Tuple[str, str]]] = {
    "Administratif & Gestion": [
        ("assistant administratif", "administratif"),
        ("assistant de gestion", "gestion"),
        ("secrétaire", "administratif"),
    ],
    "Relation Client & Accueil": [
        ("agent d'accueil", "relation client"),
        ("conseiller clientèle", "relation client"),
        ("employé commercial", "commerce"),
    ],
    "Production": [
        ("agent de production", "industrie"),
        ("opérateur de fabrication", "industrie"),
        ("agent de conditionnement", "industrie"),
    ],
    "Maintenance": [
        ("technicien de maintenance", "maintenance"),
        ("agent de maintenance", "maintenance"),
    ],
    "Logistique & Stock": [
        ("agent logistique", "logistique"),
        ("préparateur de commandes", "logistique"),
        ("gestionnaire de stock", "logistique"),
    ],
    "Communication & Marketing": [
        ("chargé de communication", "communication"),
        ("chargé de communication digitale", "communication digitale"),
        ("créateur de contenu", "communication"),
    ],
    "Analyse & Pilotage": [
        ("analyste de données", "analyse de données"),
        ("chargé de reporting", "pilotage"),
    ],
    "Informatique & Numérique": [
        ("développeur web", "informatique"),
        ("développeur Python", "informatique"),
        ("concepteur de solutions numériques", "numérique"),
    ],
    "Pédagogie & Formation": [
        ("formateur", "formation"),
        ("animateur pédagogique", "formation"),
    ],
    "Culture & Création": [
        ("musicien", "culture"),
        ("médiateur culturel", "culture"),
        ("chargé de projet culturel", "culture"),
    ],
}


def get_top_cv_families(
    cv_terms: Sequence[str] | str,
    top_n: int = 5,
) -> List[str]:
    """Détecte les familles dominantes à partir du texte ou des termes du CV."""
    if isinstance(cv_terms, str):
        source_text = cv_terms
    else:
        source_text = " ".join(str(term) for term in (cv_terms or []))

    words = _meaningful_words(source_text)
    counts = Counter(words)
    scored: List[Tuple[str, int]] = []

    for family, keywords in FAMILY_KEYWORDS.items():
        score = sum(counts.get(keyword, 0) for keyword in keywords)
        if score > 0:
            scored.append((family, score))

    scored.sort(key=lambda item: (-item[1], item[0]))
    return [family for family, _ in scored[:top_n]]


# =========================================================
# INFERENCE METIER INTERNE
# =========================================================


def build_job_inference_summary(
    detected_families: List[str],
    cv_terms: List[str],
    top_n: int = 3,
) -> Dict[str, object]:
    """Construit une première synthèse métier à partir des familles détectées."""
    families = (detected_families or [])[:top_n]
    ranked_jobs: List[Dict[str, str]] = []

    for family in families:
        for job_label, domain in JOB_FAMILY_TO_ROLES.get(family, []):
            ranked_jobs.append({
                "job": job_label,
                "domain": domain,
                "family": family,
            })

    main_job = (
        ranked_jobs[0]
        if ranked_jobs
        else {"job": "inconnu", "domain": "inconnu", "family": ""}
    )

    return {
        "main_job": main_job,
        "related_jobs": ranked_jobs[1:4],
        "families_used": families,
        "ranked_jobs": ranked_jobs,
        "domain": main_job.get("domain", "inconnu"),
    }


def build_search_queries_from_job_summary(
    job_summary: Dict[str, object],
    topics: List[str],
    max_queries: int = 5,
) -> List[str]:
    """Génère les requêtes d'offres à partir du résumé métier."""
    queries: List[str] = []

    main_job = job_summary.get("main_job", {})
    related_jobs = job_summary.get("related_jobs", [])

    if isinstance(main_job, dict):
        queries.extend([
            str(main_job.get("job", "")),
            str(main_job.get("domain", "")),
        ])

    for item in related_jobs:
        if isinstance(item, dict):
            queries.append(str(item.get("job", "")))

    queries.extend(str(topic) for topic in (topics or [])[:5])
    return _dedupe_keep_order(queries)[:max_queries]


# =========================================================
# TERMES CANDIDATS ROME
# =========================================================


def filter_rome_candidate_terms(terms: List[str]) -> List[str]:
    """
    Nettoie les expressions candidates avant leur classement ROME.

    La fonction reste volontairement généraliste : elle retire surtout les
    coordonnées, rubriques, phrases administratives et expressions sans signal.
    """
    blacklist = {
        "adresse", "candidature", "contact", "coordonnees", "curriculum",
        "email", "identite", "mail", "parcours", "poste", "profil",
        "professionnel", "professionnelle", "savoir faire", "telephone", "vitae",
    }

    candidates: List[str] = []

    for term in terms or []:
        original = " ".join(str(term or "").strip().split())
        normalized = normalize_text(original)

        if not normalized or normalized in blacklist:
            continue
        if "@" in original:
            continue
        if re.fullmatch(r"[\d\s()+.,/-]+", original):
            continue

        meaningful = [
            word
            for word in normalized.split()
            if len(word) >= 3
            and word not in CONNECTOR_WORDS
            and word not in GENERIC_ROME_WORDS
            and word not in STOPWORDS
        ]

        if meaningful:
            candidates.append(original)

    return _dedupe_keep_order(candidates)


def rank_rome_candidate_terms(
    terms: List[str],
    max_terms: int = 5,
) -> List[str]:
    """
    Classe les termes réellement extraits du CV avant interrogation de ROME.

    La fonction ne fabrique aucune expression nouvelle.
    Elle privilégie les termes professionnels visibles dans le CV
    et écarte les noms, coordonnées, rubriques et qualités trop générales.
    """

    noise_words = {
        # Présentation et recherche d'emploi
        "actuellement", "candidature", "compatible",
        "curriculum", "emploi", "poste", "profil",
        "recherche", "rechercher", "temps", "partiel", "vitae",

        # Études et rubriques génériques
        "annee", "annees", "baccalaureat", "certificat",
        "cursus", "cycle", "diplome", "diplomes",
        "equivalence", "etude", "etudes",
        "etudiant", "etudiante", "formation",
        "langue", "langues", "mention", "niveau",

        # Coordonnées et fichiers
        "adresse", "email", "mail", "telephone",
        "pdf", "doc", "docx",

        # Qualités personnelles générales
        "adaptable", "dynamique", "ecoute", "esprit",
        "organisation", "ponctualite",
        "reactif", "rigueur", "sens",

        # Termes narratifs
        "centre", "construire", "disposant",
        "durablement", "pratique", "souhaite",
        "tres", "bien", "aujourdhui",

        # Langues
        "francais", "anglais","lecoute",
    }

    connector_words = {
        "avec", "dans", "de", "des", "du",
        "elle", "en", "est", "et", "je",
        "la", "le", "les", "ma", "mes",
        "mon", "pour", "sur", "une", "un",
    }

    professional_suffixes = (
        "iste",
        "eur",
        "euse",
        "teur",
        "trice",
    )

    prepared = []
    frequencies: Dict[str, int] = {}

    # Première passe : normalisation et comptage
    for term in terms:
        original = str(term).strip()
        normalized = normalize_text(original)

        if not normalized:
            continue

        frequencies[normalized] = frequencies.get(normalized, 0) + 1

    # Deuxième passe : sélection et score
    for position, term in enumerate(terms):
        original = str(term).strip()
        normalized = normalize_text(original)

        if not normalized:
            continue

        if normalized in noise_words:
            continue

        if normalized in connector_words:
            continue

        if len(normalized) < 4:
            continue

        if any(char.isdigit() for char in normalized):
            continue

        if "@" in original:
            continue

        # Nom de famille probable en majuscules.
        # On conserve toutefois les intitulés professionnels,
        # par exemple VIOLONISTE.
        if (
            original.isupper()
            and not normalized.endswith(professional_suffixes)
            and frequencies.get(normalized, 0) == 1
        ):
            continue

        # Nom propre ou lieu probable :
        # mot isolé avec majuscule, non répété et sans signal métier.
        if (
            original[:1].isupper()
            and not original.isupper()
            and not normalized.endswith(professional_suffixes)
            and frequencies.get(normalized, 0) == 1
        ):
            continue

        score = 0.0

        # Répétition dans le CV
        score += frequencies.get(normalized, 0) * 8

        # Le début du CV reste prioritaire
        if position < 10:
            score += 20
        elif position < 25:
            score += 10
        elif position < 50:
            score += 5

        # Intitulé professionnel probable
        if normalized.endswith(professional_suffixes):
            score += 20

        # Les termes composés déjà présents dans le CV sont utiles
        if "-" in original:
            score += 12

        # Les mots longs sont généralement plus discriminants
        score += min(len(normalized), 14) / 2

        prepared.append({
            "term": original,
            "normalized": normalized,
            "score": score,
            "position": position,
        })

    prepared.sort(
        key=lambda item: (
            -item["score"],
            item["position"],
            item["normalized"],
        )
    )

    selected = []
    seen = set()

    for item in prepared:
        normalized = item["normalized"]

        if normalized in seen:
            continue

        seen.add(normalized)
        selected.append(item["term"])

        if len(selected) >= max_terms:
            break

    return selected

    def add_candidate(
        selected_items: List[Dict],
        position: int,
    ) -> None:
        words = []

        for item in selected_items:
            words.extend(item["words"])

        # Déduplication locale en conservant l'ordre.
        unique_words = list(dict.fromkeys(words))

        if not unique_words:
            return

        phrase = " ".join(unique_words)
        score = 0.0

        # Les expressions professionnelles sont préférées
        # aux mots isolés.
        if len(unique_words) == 3:
            score += 26
        elif len(unique_words) == 2:
            score += 22
        else:
            score += 4

        # Importance de la position dans le CV,
        # mais sans écraser la qualité de l'expression.
        if position < 10:
            score += 18
        elif position < 25:
            score += 10
        elif position < 50:
            score += 5

        # Répétition dans le CV.
        score += sum(
            word_frequency.get(word, 0) * 4
            for word in set(unique_words)
        )

        # Signal d'intitulé professionnel.
        if any(
            word.endswith(professional_suffixes)
            for word in unique_words
        ):
            score += 18

        # Un mot isolé n'est conservé que s'il dispose
        # d'un signal professionnel suffisant.
        if len(unique_words) == 1:
            word = unique_words[0]

            is_professional_word = (
                word.endswith(professional_suffixes)
                or word_frequency.get(word, 0) >= 2
                or "-" in selected_items[0]["original"]
                or (
                    selected_items[0]["original"].isupper()
                    and len(word) > 5
                )
            )

            if not is_professional_word:
                return

        candidates.append({
            "term": phrase,
            "normalized": phrase,
            "score": score,
            "position": position,
        })

    # Expressions contiguës de trois puis deux termes.
    for size in (3, 2):
        for index in range(len(cleaned_terms) - size + 1):
            window = cleaned_terms[index:index + size]

            # Évite de fusionner des éléments trop éloignés
            # dans le texte original.
            positions = [item["position"] for item in window]

            if max(positions) - min(positions) > size + 2:
                continue

            add_candidate(window, min(positions))

    # Mots isolés avec signal professionnel suffisant.
    for item in cleaned_terms:
        add_candidate([item], item["position"])

    candidates.sort(
        key=lambda item: (
            -item["score"],
            item["position"],
            -len(item["normalized"]),
            item["normalized"],
        )
    )

    selected = []
    seen = set()

    for item in candidates:
        normalized = item["normalized"]

        if normalized in seen:
            continue

        # Évite de sélectionner à la fois une expression complète
        # et plusieurs variantes quasiment identiques.
        if any(
            normalized in previous
            or previous in normalized
            for previous in seen
        ):
            continue

        seen.add(normalized)
        selected.append(item["term"])

        if len(selected) >= max_terms:
            break

    return selected


# =========================================================
# ROME : GENERATION ET CLASSEMENT
# =========================================================


def infer_rome_jobs_from_terms(
    cv_terms: List[str],
    max_terms: int = 5,
) -> List[Dict[str, object]]:
    """Recherche et déduplique les métiers ROME issus des meilleurs termes."""
    selected_terms = rank_rome_candidate_terms(cv_terms, max_terms=max_terms)
    rome_jobs: Dict[str, Dict[str, object]] = {}

    for term in selected_terms:
        query = str(term).strip()
        if not query:
            continue

        try:
            jobs = search_unique_rome_jobs(query)
        except Exception:
            # Une requête ROME isolée ne doit pas faire tomber tout le pipeline.
            continue

        for job in jobs or []:
            code = job.get("metier_code")
            if not code:
                continue

            if code not in rome_jobs:
                rome_jobs[code] = {
                    **job,
                    "matched_terms": [],
                    "term_score": 0,
                }

            matched_terms = rome_jobs[code]["matched_terms"]
            if query not in matched_terms:
                matched_terms.append(query)

            rome_jobs[code]["term_score"] = len(matched_terms)

    results = list(rome_jobs.values())
    results.sort(
        key=lambda job: (
            -int(job.get("term_score", 0)),
            str(job.get("metier_libelle", "")),
        )
    )
    return results


def rank_rome_jobs_against_cv(
    cv_text: str,
    rome_jobs: List[Dict],
    main_job_label: str = "",
    domain_label: str = "",
) -> List[Dict]:
    """Classe les métiers ROME candidats selon leur cohérence avec le CV."""
    normalized_cv = normalize_text(cv_text)
    cv_words = set(_meaningful_words(cv_text, min_len=4))
    main_words = set(_meaningful_words(main_job_label, min_len=4))
    domain_words = set(_meaningful_words(domain_label, min_len=4))

    ranked_jobs: List[Dict] = []

    for job in rome_jobs or []:
        job_copy = dict(job)
        job_label = str(job.get("metier_libelle", "")).strip()
        job_words = set(_meaningful_words(job_label, min_len=4))
        matched_terms = list(job.get("matched_terms", []) or [])
        term_score = int(job.get("term_score", 0) or 0)

        score = min(term_score * 12, 36)
        reasons: List[str] = []

        if term_score:
            reasons.append(f"{term_score} terme(s) du CV convergent vers ce métier")

        # Libellé ROME retrouvé directement dans le CV.
        common_cv_words = job_words & cv_words
        label_coverage = (
            len(common_cv_words) / len(job_words)
            if job_words else 0.0
        )
        score += round(label_coverage * 40)

        if common_cv_words:
            reasons.append(
                "libellé métier rapproché du CV : "
                + ", ".join(sorted(common_cv_words))
            )

        # Cohérence avec l'inférence interne déjà produite.
        common_main_words = job_words & main_words
        if common_main_words:
            score += 18
            reasons.append("cohérent avec le métier principal détecté")

        common_domain_words = job_words & domain_words
        if common_domain_words:
            score += 10
            reasons.append("cohérent avec le domaine principal du CV")

        # Bonus lorsque les termes déclencheurs eux-mêmes sont présents dans le CV.
        trigger_words = set()
        for term in matched_terms:
            trigger_words.update(_meaningful_words(str(term), min_len=4))

        trigger_overlap = trigger_words & cv_words
        trigger_bonus = min(len(trigger_overlap) * 3, 15)
        score += trigger_bonus

        if trigger_overlap:
            reasons.append(
                "termes déclencheurs retrouvés : "
                + ", ".join(sorted(trigger_overlap))
            )

        job_copy.update({
            "ranking_score": score,
            "ranking_reasons": reasons,
            "label_coverage": round(label_coverage, 2),
            "matched_terms": matched_terms,
        })
        ranked_jobs.append(job_copy)

    ranked_jobs.sort(
        key=lambda job: (
            -int(job.get("ranking_score", 0)),
            -int(job.get("term_score", 0)),
            str(job.get("metier_libelle", "")),
        )
    )
    return ranked_jobs