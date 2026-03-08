from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, List, Set


# Réglages
MIN_LEN = 3
MAX_TERMS_PER_LIST = 20
MAX_STRONG = 15


BASE_STOPWORDS_FR = [
    "le", "la", "les", "de", "des", "du", "un", "une", "et", "ou", "avec", "sans", "pour", "par",
    "sur", "sous", "dans", "en", "au", "aux", "ce", "cet", "cette", "ces", "qui", "que", "quoi",
    "dont", "plus", "moins", "tres", "très", "afin", "etre", "être", "avoir", "faire", "sera",
    "sont", "nous", "vous", "ils", "elles", "leur", "leurs", "vos", "notre", "votre",
    "poste", "profil", "mission", "missions", "entreprise", "societe", "société",
    "experience", "expérience", "an", "annee", "année", "mois", "jour", "jours",
    "temps", "heures", "heure", "semaine", "semaines"
]


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    )


def normalize(text: Any) -> str:
    """
    Normalise le texte pour le matching :
    - cast vers str
    - minuscule
    - suppression des accents
    - remplacement de la ponctuation par des espaces
    - compactage des espaces
    """
    if text is None:
        text = ""
    elif not isinstance(text, str):
        if isinstance(text, (list, tuple)):
            text = " ".join(str(x) for x in text if x is not None)
        else:
            text = str(text)

    text = _strip_accents(text.lower())

    # Remplace certains séparateurs fréquents par des espaces
    text = re.sub(r"[/|\\,_;:()\[\]{}]+", " ", text)

    # Remplace les tirets et apostrophes par des espaces
    text = re.sub(r"[-'’]+", " ", text)

    # Supprime tout caractère non alphanumérique restant, sauf espace
    text = re.sub(r"[^a-z0-9\s]+", " ", text)

    # Compacte les espaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


def _has_digit(token: str) -> bool:
    return any(ch.isdigit() for ch in token)


def build_syn_map(profile: Dict[str, Any]) -> Dict[str, str]:
    """
    Construit une map {variant_normalise: canonical_normalise}
    """
    syn = profile.get("synonyms", {}) or {}
    mapping: Dict[str, str] = {}

    for canonical, variants in syn.items():
        c = normalize(canonical)
        if not c:
            continue

        mapping[c] = c

        for v in variants or []:
            v2 = normalize(v)
            if v2:
                mapping[v2] = c

    return mapping


def _profile_stopwords(profile: Dict[str, Any]) -> Set[str]:
    """
    Retourne les stopwords normalisés.
    Version simple et robuste.
    """
    combined = " ".join(BASE_STOPWORDS_FR)
    norm = normalize(combined)
    return set(norm.split()) if norm else set()


def _tokenize(text: str) -> List[str]:
    """
    Découpe le texte normalisé en tokens simples.
    """
    if not text:
        return []
    return [tok for tok in text.split() if tok]


def extract_terms(text: str, profile: Dict[str, Any]) -> Set[str]:
    """
    Extrait des termes utiles (mots + bigrams) avec nettoyage :
    - supprime stopwords
    - supprime tokens courts
    - supprime tokens contenant des chiffres
    - applique synonymes
    """
    stop = _profile_stopwords(profile)
    synmap = build_syn_map(profile)

    t = normalize(text)
    if not t:
        return set()

    raw_tokens = _tokenize(t)

    tokens = [
        tok for tok in raw_tokens
        if len(tok) >= MIN_LEN
        and tok not in stop
        and not tok.isdigit()
        and not _has_digit(tok)
    ]

    words = set(tokens)
    bigrams = {f"{tokens[i]} {tokens[i + 1]}" for i in range(len(tokens) - 1)}

    all_terms = words | bigrams

    return {synmap.get(term, term) for term in all_terms}


def _rank_terms(terms: Set[str]) -> List[str]:
    """
    Trie :
    - expressions d'abord
    - puis longueur décroissante
    - puis ordre alpha
    """
    return sorted(terms, key=lambda s: (-s.count(" "), -len(s), s))


@dataclass(frozen=True)
class MatchResult:
    score: int
    matched: List[str]
    missing: List[str]
    strong_hits: List[str]


def score_cv_offer(cv_text: str, offer_text: str, profile: Dict[str, Any]) -> MatchResult:
    profile = dict(profile or {})  # copie défensive

    cv_terms = extract_terms(cv_text, profile)
    offer_terms = extract_terms(offer_text, profile)

    matched_set = cv_terms & offer_terms
    missing_set = offer_terms - cv_terms

    matched = _rank_terms(matched_set)[:MAX_TERMS_PER_LIST]
    missing = _rank_terms(missing_set)[:MAX_TERMS_PER_LIST]

    # Mots-clés forts (bonus)
    strong = [normalize(s) for s in (profile.get("strong_keywords", []) or [])]
    strong_hits = sorted(
        [s for s in strong if s and s in cv_terms and s in offer_terms]
    )[:MAX_STRONG]

    # Score de base = couverture des termes de l'offre
    denom = max(len(offer_terms), 1)
    base = int(round((len(matched_set) / denom) * 100))

    # Bonus léger pour mots forts
    bonus = min(len(strong_hits) * 3, 15)

    score = max(0, min(100, base + bonus))

    return MatchResult(
        score=score,
        matched=matched,
        missing=missing,
        strong_hits=strong_hits
    )