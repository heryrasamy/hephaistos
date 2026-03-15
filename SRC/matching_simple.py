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
        "cv_terms": sorted(cv_terms),
        "offer_terms": sorted(offer_terms),
    }
def detect_cv_job_families(cv_text: str) -> Dict[str, int]:
    """
    Détecte les familles métier présentes dans un CV
    et compte leur fréquence.
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
    Retourne les familles métier les plus fréquentes dans le CV.
    """

    families_count = detect_cv_job_families(cv_text)

    sorted_families = sorted(
        families_count.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return [f[0] for f in sorted_families[:top_n]]
