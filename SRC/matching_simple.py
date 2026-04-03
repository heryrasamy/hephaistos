from __future__ import annotations
import re
import unicodedata
from collections import defaultdict
from typing import Dict, List, Set, Tuple


# =========================================================
# Stopwords simples
# =========================================================
STOPWORDS = {
    "de", "des", "du", "la", "le", "les", "un", "une", "et", "ou", "en", "au", "aux",
    "pour", "par", "avec", "sans", "sur", "sous", "dans", "chez", "vers", "entre",
    "a", "à", "d", "l", "the", "and", "of", "to", "in", "on",
    "est", "sont", "etre", "être", "avoir", "faire", "plus", "moins",
    "ce", "cet", "cette", "ces", "son", "sa", "ses", "leur", "leurs",
    "vos", "notre", "nos", "votre", "mes", "tes", "je", "tu", "il", "elle", "nous", "vous",

}

# =========================================================
# Compétences manquantes - nettoyage / regroupement / abstraction
# =========================================================

GENERIC_MISSING_TERMS = {
    "poste", "postes",
    "mission", "missions",
    "profil", "profils",
    "candidat", "candidats", "candidature", "candidatures",
    "entreprise", "societe", "structure",
    "recrutement", "recruter",
    "recherche", "rechercher",
    "demande", "demandes", "demandee", "demandees",
    "souhaite", "souhaites", "souhaitee", "souhaitees",
    "experience", "experiences",
    "competence", "competences",
    "capable", "capacite", "capacites",
    "bonne", "bon", "bonnes", "bons",
    "sens", "niveau", "poste a pourvoir",
}
GENERIC_MISSING_WORDS = {
    "poste", "postes",
    "mission", "missions",
    "profil", "profils",
    "candidat", "candidats", "candidature", "candidatures",
    "entreprise", "societe", "structure",
    "recrutement", "recruter",
    "recherche", "rechercher", "recherchant",
    "demande", "demandes", "demandee", "demandees",
    "souhaite", "souhaites", "souhaitee", "souhaitees",
    "experience", "experiences",
    "competence", "competences",
    "capable", "capacite", "capacites",
    "bonne", "bon", "bonnes", "bons",
    "sens", "niveau",
}

SHORT_MEANINGFUL_TERMS = {
    "rh", "paie", "sap", "sql", "crm", "erp", "seo", "sea",
    "php", "css", "html", "xml", "api", "bi", "qa", "ux", "ui",
    "aws", "gcp", "seo", "c++", "c#", "r"
}

TERM_TO_CONCEPT = {
    # Analyse / gestion / données
    "excel": "suivi_analyse_donnees",
    "reporting": "suivi_analyse_donnees",
    "tableau de bord": "suivi_analyse_donnees",
    "tableaux de bord": "suivi_analyse_donnees",
    "indicateur": "suivi_analyse_donnees",
    "indicateurs": "suivi_analyse_donnees",
    "kpi": "suivi_analyse_donnees",
    "suivi": "suivi_analyse_donnees",
    "analyse": "suivi_analyse_donnees",
    "analyse de donnees": "suivi_analyse_donnees",

    # Organisation / coordination
    "coordination": "organisation_coordination",
    "coordonner": "organisation_coordination",
    "coordonne": "organisation_coordination",
    "planification": "organisation_coordination",
    "planning": "organisation_coordination",
    "organisation": "organisation_coordination",
    "organiser": "organisation_coordination",
    "organisation d activites": "organisation_coordination",
    "gestion de planning": "organisation_coordination",

    # Management
    "management": "management",
    "manager": "management",
    "encadrement": "management",
    "encadrer": "management",
    "supervision": "management",
    "superviser": "management",
    "animation d equipe": "management",
    "chef d equipe": "management",
    "pilotage": "management",

    # Relation client / accueil
    "relation client": "relation_client",
    "relations clients": "relation_client",
    "client": "relation_client",
    "clients": "relation_client",
    "accueil": "relation_client",
    "service client": "relation_client",
    "conseil client": "relation_client",
    "satisfaction client": "relation_client",
    "relation usager": "relation_client",
    "relation usagers": "relation_client",

    # Communication
    "communication": "communication",
    "communication digitale": "communication",
    "reseaux sociaux": "communication",
    "community management": "communication",
    "redaction": "communication",
    "contenu": "communication",
    "media": "communication",
    "diffusion": "communication",

    # Outils bureautiques
    "word": "outils_bureautiques",
    "powerpoint": "outils_bureautiques",
    "pack office": "outils_bureautiques",
    "bureautique": "outils_bureautiques",
    "office": "outils_bureautiques",

    # Outils techniques / informatique
    "python": "outils_techniques",
    "sql": "outils_techniques",
    "java": "outils_techniques",
    "html": "outils_techniques",
    "css": "outils_techniques",
    "javascript": "outils_techniques",
    "php": "outils_techniques",
    "git": "outils_techniques",
    "linux": "outils_techniques",
    "api": "outils_techniques",
    "aws": "outils_techniques",
    "crm": "outils_techniques",
    "erp": "outils_techniques",
    "sap": "outils_techniques",

    # Logistique / stock
    "stock": "logistique_stock",
    "gestion de stock": "logistique_stock",
    "gestion stock": "logistique_stock",
    "inventaire": "logistique_stock",
    "approvisionnement": "logistique_stock",
    "logistique": "logistique_stock",
    "reception": "logistique_stock",
    "expedition": "logistique_stock",

    # Qualité / conformité
    "qualite": "qualite_conformite",
    "controle": "qualite_conformite",
    "normes": "qualite_conformite",
    "procedure": "qualite_conformite",
    "procedures": "qualite_conformite",
    "amelioration continue": "qualite_conformite",
    "conformite": "qualite_conformite",

    # Soft skills
    "rigueur": "soft_skills",
    "autonomie": "soft_skills",
    "polyvalence": "soft_skills",
    "adaptabilite": "soft_skills",
    "esprit d equipe": "soft_skills",
    "travail en equipe": "soft_skills",
}

CONCEPT_METADATA = {
    "suivi_analyse_donnees": {
        "label": "Suivi et analyse de données",
        "category": "analyse_gestion",
        "advice": "Mettre en avant les outils de suivi, reporting, Excel ou tableaux de bord déjà utilisés."
    },
    "organisation_coordination": {
        "label": "Organisation et coordination",
        "category": "organisation",
        "advice": "Mentionner les expériences de planification, coordination, organisation ou suivi d'activités."
    },
    "management": {
        "label": "Encadrement et management",
        "category": "management",
        "advice": "Valoriser les expériences de supervision, pilotage, animation ou encadrement d'équipe."
    },
    "relation_client": {
        "label": "Relation client / usager",
        "category": "relation_client",
        "advice": "Ajouter les expériences liées à l'accueil, au conseil, au suivi client ou à la relation usager."
    },
    "communication": {
        "label": "Communication",
        "category": "communication",
        "advice": "Mettre en avant les actions de rédaction, diffusion, contenus, communication digitale ou réseaux sociaux."
    },
    "outils_bureautiques": {
        "label": "Outils bureautiques",
        "category": "outil_bureautique",
        "advice": "Préciser les logiciels bureautiques maîtrisés comme Word, PowerPoint ou le Pack Office."
    },
    "outils_techniques": {
        "label": "Outils techniques",
        "category": "outil_technique",
        "advice": "Indiquer les outils, langages, logiciels ou environnements techniques déjà utilisés."
    },
    "logistique_stock": {
        "label": "Logistique et gestion de stock",
        "category": "logistique",
        "advice": "Mentionner les tâches de réception, inventaire, approvisionnement, expédition ou suivi de stock."
    },
    "qualite_conformite": {
        "label": "Qualité et conformité",
        "category": "qualite_conformite",
        "advice": "Mettre en avant les contrôles, procédures, normes ou actions d'amélioration continue."
    },
    "soft_skills": {
        "label": "Savoir-être professionnels",
        "category": "soft_skill",
        "advice": "Illustrer concrètement la rigueur, l'autonomie, l'adaptabilité ou le travail en équipe par des exemples."
    },
    "specifique_metier": {
        "label": "Compétence métier spécifique",
        "category": "specifique_metier",
        "advice": "Ajouter si possible cette compétence métier avec un exemple concret, un outil, une mission ou un contexte d'utilisation."
    },
}


def normalize_missing_term(term: str) -> str:
    """
    Normalise un terme manquant pour le rendre comparable :
    - minuscules
    - suppression accents
    - ponctuation simplifiée
    - espaces nettoyés
    """
    if not term:
        return ""

    term = term.strip().lower()

    term = unicodedata.normalize("NFKD", term)
    term = "".join(c for c in term if not unicodedata.combining(c))

    term = re.sub(r"[’']", " ", term)
    term = re.sub(r"[^a-z0-9+# ]+", " ", term)
    term = re.sub(r"\s+", " ", term).strip()

    return term


def clean_missing_terms(missing_terms: list[str]) -> list[str]:
    """
    Nettoie une liste de missing_terms sans interprétation métier lourde.
    Objectif :
    - retirer le bruit lexical
    - conserver les termes utiles
    - dédupliquer proprement
    """
    cleaned = []
    seen = set()

    for raw_term in missing_terms:
        term = normalize_missing_term(raw_term)

        if not term:
            continue

        if term in GENERIC_MISSING_TERMS:
            continue

        if len(term) < 3 and term not in SHORT_MEANINGFUL_TERMS:
            continue

        if len(term.split()) == 1 and len(term) < 4 and term not in SHORT_MEANINGFUL_TERMS:
            continue

        if term not in seen:
            cleaned.append(term)
            seen.add(term)

    return cleaned
def filter_missing_terms_for_diagnosis(missing_terms: list[str]) -> list[str]:
    """
    Filtre les missing_terms bruts issus du matching pour ne garder
    que les termes exploitables dans le diagnostic métier.

    Règles :
    - garder en priorité les termes connus dans TERM_TO_CONCEPT
    - éliminer les groupes contenant des mots RH parasites
    - éliminer la plupart des n-grammes trop longs non reconnus
    - conserver au maximum les termes de 1 à 2 mots interprétables
    """
    filtered = []
    seen = set()

    for raw_term in missing_terms:
        term = normalize_missing_term(raw_term)

        if not term:
            continue

        # 1) si connu du mapping métier, on garde directement
        if term in TERM_TO_CONCEPT:
            if term not in seen:
                filtered.append(term)
                seen.add(term)
            continue

        words = term.split()

        # 2) rejeter les termes composés uniquement de bruit RH
        if words and all(w in GENERIC_MISSING_WORDS for w in words):
            continue

        # 3) rejeter les termes contenant au moins un mot RH parasite
        # quand ce sont des groupes multi-mots
        if len(words) >= 2 and any(w in GENERIC_MISSING_WORDS for w in words):
            continue

        # 4) pour les groupes multi-mots non reconnus :
        # - plus de 2 mots -> rejet
        # - exactement 2 mots mais non reconnus -> rejet
        if len(words) > 2:
            continue

        if len(words) == 2 and term not in TERM_TO_CONCEPT:
            continue

        # 5) rejeter les mots unitaires trop faibles
        if len(words) == 1:
            w = words[0]

            if len(w) < 4 and w not in SHORT_MEANINGFUL_TERMS:
                continue

            if w in {"bord", "tableaux", "tableau"}:
                continue

        if term not in seen:
            filtered.append(term)
            seen.add(term)

    return filtered


def group_terms_by_concept(clean_terms: list[str]) -> dict[str, list[str]]:
    """
    Regroupe les termes nettoyés par concept métier.
    Les termes inconnus tombent dans 'specifique_metier'.
    """
    grouped = {}

    for term in clean_terms:
        concept = TERM_TO_CONCEPT.get(term, "specifique_metier")

        if concept not in grouped:
            grouped[concept] = []

        grouped[concept].append(term)

    return grouped


def build_missing_competencies(missing_terms: list[str]) -> list[dict]:
    """
    Transforme une liste brute de missing_terms en compétences manquantes structurées.

    Format de sortie :
    [
        {
            "source_terms": [...],
            "concept": "...",
            "label": "...",
            "category": "...",
            "advice": "..."
        }
    ]
    """
    clean_terms = clean_missing_terms(missing_terms)
    concept_groups = group_terms_by_concept(clean_terms)

    results = []

    for concept, source_terms in concept_groups.items():
        meta = CONCEPT_METADATA.get(concept, CONCEPT_METADATA["specifique_metier"])

        results.append(
            {
                "source_terms": source_terms,
                "concept": concept,
                "label": meta["label"],
                "category": meta["category"],
                "advice": meta["advice"],
            }
        )

    return results
# =========================================================
# Familles métier
# La clé = noyau canonique
# La valeur = ensemble de formulations proches
# =========================================================
JOB_FAMILIES: Dict[str, Set[str]] = {
    "administratif": {
        "administratif",
        "assistante administrative",
        "assistant administratif",
        "agent administratif",
        "secretaire administrative",
        "secretaire administratif",
        "gestion administrative",
        "taches administratives",
        "travaux administratifs",
        "suivi administratif",
        "dossier administratif",
        "gestion de dossiers",
        "saisie de documents",
        "saisie administrative",
    },

    "accueil": {
        "accueil",
        "agent d accueil",
        "charge d accueil",
        "hote d accueil",
        "hotesse d accueil",
        "accueil physique",
        "accueil telephonique",
        "standard",
        "standard telephonique",
        "orientation du public",
        "relation usager",
        "relation client",
        "service client",
        "contact client",
        "conseil client",
    },

    "planning": {
        "planning",
        "prise de rendez vous",
        "gestion des rendez vous",
        "gestion de rendez vous",
        "suivi des plannings",
        "gestion de planning",
        "gestion des plannings",
        "organisation planning",
        "organisation",
        "agenda",
        "gestion d agenda",
        "coordination",
    },

    "stock": {
        "stock",
        "gestion des stocks",
        "gestion de stock",
        "suivi des stocks",
        "stockage",
        "inventaire",
        "approvisionnement",
        "magasinage",
        "gestion magasin",
    },

    "bureautique": {
        "bureautique",
        "word",
        "excel",
        "powerpoint",
        "outlook",
        "pack office",
        "microsoft office",
    },

    "vente": {
        "vente",
        "vente en magasin",
        "vente conseil",
        "conseil de vente",
        "commercial",
        "relation commerciale",
    },

    "caisse": {
        "caisse",
        "encaissement",
        "tenue de caisse",
        "gestion de caisse",
    },

    "support": {
        "support",
        "assistance",
        "support client",
        "support utilisateur",
        "assistance utilisateur",
        "service support",
        "helpdesk",
    },

    "informatique": {
        "informatique",
        "support informatique",
        "maintenance informatique",
        "technicien informatique",
        "outils informatiques",
        "logiciel",
        "application",
    },

    "logistique": {
        "logistique",
        "preparation de commandes",
        "expedition",
        "reception",
        "manutention",
        "gestion logistique",
        "flux",
    },

    "communication": {
        "communication",
        "redaction",
        "contenu",
        "animation",
        "reseaux sociaux",
        "creation de contenu",
        "communication digitale",
    },

    "rigueur": {
        "rigueur",
    },

    "autonomie": {
        "autonomie",
    },

    "polyvalence": {
        "polyvalence",
    },
}


# =========================================================
# Génération automatique des synonymes
# variante -> noyau canonique
# =========================================================
SYNONYM_MAP: Dict[str, str] = {}

for canonical, variants in JOB_FAMILIES.items():
    for variant in variants:
        SYNONYM_MAP[variant] = canonical


# =========================================================
# Reverse map : noyau canonique -> variantes
# =========================================================
CANONICAL_TO_VARIANTS: Dict[str, Set[str]] = defaultdict(set)

for canonical, variants in JOB_FAMILIES.items():
    CANONICAL_TO_VARIANTS[canonical].add(canonical)
    for variant in variants:
        CANONICAL_TO_VARIANTS[canonical].add(variant)

# =========================================================
# Outils de normalisation
# =========================================================
def strip_accents(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")


def normalize(text: str) -> str:
    """
    Normalisation unique du fichier :
    - minuscules
    - suppression accents
    - apostrophes et tirets simplifiés
    - caractères non alphanumériques remplacés par espace
    - espaces multiples réduits
    """
    if not text:
        return ""

    text = text.lower().strip()
    text = strip_accents(text)

    text = text.replace("’", "'")
    text = text.replace("-", " ")
    text = text.replace("/", " ")

    # ex: d'accueil -> d accueil
    text = re.sub(r"[']", " ", text)

    # garde lettres/chiffres/espaces
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # compacte les espaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_with_synonyms(term: str) -> str:
    """
    Normalise un terme puis applique la forme canonique si connue.
    """
    term_n = normalize(term)
    return SYNONYM_MAP.get(term_n, term_n)


# =========================================================
# Extraction de termes
# =========================================================
def tokenize(text: str) -> List[str]:
    text = normalize(text)
    if not text:
        return []
    return [tok for tok in text.split() if tok and tok not in STOPWORDS and len(tok) >= 2]


def build_ngrams(tokens: List[str], min_n: int = 1, max_n: int = 4) -> Set[str]:
    """
    Génère des n-grammes simples jusqu'à 4 mots.
    """
    grams: Set[str] = set()
    n_tokens = len(tokens)

    for n in range(min_n, max_n + 1):
        for i in range(n_tokens - n + 1):
            gram = " ".join(tokens[i:i + n]).strip()
            if gram:
                grams.add(gram)

    return grams


def extract_terms(text: str) -> Set[str]:
    """
    Extrait un ensemble de termes utiles à comparer :
    - mots significatifs
    - groupes de mots (1 à 4 mots)
    - variantes reconnues dans SYNONYM_MAP

    Le but n'est pas d'être 'parfait', mais stable et robuste.
    """
    if not text:
        return set()

    tokens = tokenize(text)
    if not tokens:
        return set()

    candidates = build_ngrams(tokens, min_n=1, max_n=4)

    # On filtre un peu les n-grammes très peu informatifs
    cleaned: Set[str] = set()
    for term in candidates:
        if len(term) < 2:
            continue

        words = term.split()

        # on évite les groupes composés uniquement de mini-mots
        if all((w in STOPWORDS or len(w) < 2) for w in words):
            continue

        cleaned.add(term)

    return cleaned


# =========================================================
# Enrichissement des termes par équivalences métier
# =========================================================
def expand_terms_with_equivalents(terms: Set[str]) -> Set[str]:
    """
    Pour chaque terme :
    - ajoute sa version normalisée
    - ajoute sa forme canonique
    - ajoute les variantes du même groupe canonique

    Exemple :
    'assistante administrative'
      -> 'assistante administrative'
      -> 'assistant administratif'
      -> autres variantes du même groupe
    """
    expanded: Set[str] = set()

    for term in terms:
        term_n = normalize(term)
        if not term_n:
            continue

        expanded.add(term_n)

        canonical = normalize_with_synonyms(term_n)
        expanded.add(canonical)

        if canonical in CANONICAL_TO_VARIANTS:
            expanded.update(CANONICAL_TO_VARIANTS[canonical])

    return expanded

def detect_cv_job_families(cv_text: str) -> Dict[str, int]:
    """
    Détecte les familles métier dominantes dans un CV.
    Retourne un dictionnaire :
    {famille_metier: nombre_d_occurrences}
    """

    terms = extract_terms(cv_text)
    terms = expand_terms_with_equivalents(terms)

    families_count: Dict[str, int] = {}

    for t in terms:
        family = SYNONYM_MAP.get(t)
        if family:
            families_count[family] = families_count.get(family, 0) + 1

    return families_count
def get_top_cv_families(cv_text: str, top_n: int = 3) -> List[str]:
    """
    Retourne les familles métier les plus présentes dans le CV.
    """

    families_count = detect_cv_job_families(cv_text)

    sorted_families = sorted(
        families_count.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return [f[0] for f in sorted_families[:top_n]]
# =========================================================
# Scoring CV ↔ offre
# =========================================================
def score_cv_offer(cv_text: str, offer_text: str) -> Dict[str, object]:
    """
    Compare un CV et une offre avec :
    - extraction des termes
    - normalisation
    - synonymes / équivalences métier
    - calcul d'un score de compatibilité
    """

    cv_raw_terms = extract_terms(cv_text)
    offer_raw_terms = extract_terms(offer_text)

    cv_terms = expand_terms_with_equivalents(cv_raw_terms)
    offer_terms = expand_terms_with_equivalents(offer_raw_terms)

    # garder les termes pertinents
    def is_relevant(term: str) -> bool:
        return (" " in term) or (len(term) >= 4)

    cv_terms = {t for t in cv_terms if is_relevant(t)}
    offer_terms = {t for t in offer_terms if is_relevant(t)}

    matched = cv_terms & offer_terms
    missing = offer_terms - cv_terms

    missing_terms_for_diagnosis = filter_missing_terms_for_diagnosis(sorted(missing))
    missing_competencies = build_missing_competencies(missing_terms_for_diagnosis)

    # Score de couverture
    if offer_terms:
        coverage_score = round((len(matched) / len(offer_terms)) * 100)
    else:
        coverage_score = 0

    # Bonus expressions métier
    long_matches = {t for t in matched if " " in t}
    bonus = min(len(long_matches) * 5, 20)

    # Détection des familles métier
    cv_families = {SYNONYM_MAP.get(t, t) for t in cv_terms if t in SYNONYM_MAP}
    offer_families = {SYNONYM_MAP.get(t, t) for t in offer_terms if t in SYNONYM_MAP}

    common_families = cv_families & offer_families
    family_bonus = min(len(common_families) * 5, 15)

    final_score = min(coverage_score + bonus + family_bonus, 100)

    return {
        "score": final_score,
        "coverage_score": coverage_score,
        "bonus": bonus,
        "family_bonus": family_bonus,
        "common_families": sorted(common_families),
        "matched_terms": sorted(matched),
        "missing_terms": sorted(missing),
        "missing_competencies": missing_competencies,
        "cv_terms": sorted(cv_terms),
        "offer_terms": sorted(offer_terms),
    }


def get_top_cv_families(cv_text: str, top_n: int = 3) -> List[str]:
    """
    Retourne les familles métier les plus fréquentes dans le CV.
    """

    families_count = detect_cv_job_families(cv_text)

    sorted_families = sorted(
        families_count.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return [f[0] for f in sorted_families[:top_n]]
