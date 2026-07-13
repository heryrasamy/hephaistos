from __future__ import annotations

import re
import unicodedata
from typing import List
from difflib import SequenceMatcher


GENERIC_STOPWORDS = {
    "a", "au", "aux", "avec", "ce", "ces", "dans", "de", "des",
    "du", "elle", "en", "et", "eux", "il", "ils", "je", "la",
    "le", "les", "leur", "leurs", "lui", "ma", "mais", "me",
    "mes", "mon", "ne", "nos", "notre", "nous", "on", "ou",
    "par", "pas", "pour", "qu", "que", "qui", "sa", "se", "ses",
    "son", "sur", "ta", "te", "tes", "toi", "ton", "tu", "un",
    "une", "vos", "votre", "vous",
}


def normalize_skill_tokens(text: str) -> List[str]:
    """
    Transforme un texte professionnel en termes comparables.

    Cette fonction est indépendante du métier :
    elle peut traiter une compétence administrative, industrielle,
    informatique, commerciale, culturelle ou technique.
    """
    if not text:
        return []

    normalized = unicodedata.normalize("NFKD", str(text))
    normalized = "".join(
        char
        for char in normalized
        if not unicodedata.combining(char)
    )

    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)

    tokens = []

    for token in normalized.split():
        if token in GENERIC_STOPWORDS:
            continue

        if len(token) < 3:
            continue

        tokens.append(stem_token(token))

    return tokens


def stem_token(token: str) -> str:
    """
    Réduit approximativement un mot français à une racine comparable.

    Cette version reste volontairement simple et généraliste.
    """
    suffixes = (
        "issements",
        "issement",
        "atrices",
        "ateurs",
        "ations",
        "atrice",
        "ateur",
        "ements",
        "ement",
        "iques",
        "ique",
        "ances",
        "ence",
        "ances",
        "ités",
        "ité",
        "ments",
        "ment",
        "ions",
        "ion",
        "ées",
        "ée",
        "er",
        "ir",
        "re",
        "es",
        "s",
    )

    for suffix in suffixes:
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            return token[:-len(suffix)]

    return token
def token_similarity(token_a: str, token_b: str) -> float:
    """
    Mesure la ressemblance entre deux formes lexicales.

    Cette fonction est indépendante du domaine métier.
    """
    if not token_a or not token_b:
        return 0.0

    if token_a == token_b:
        return 1.0

    return SequenceMatcher(
        None,
        token_a,
        token_b,
    ).ratio()


def compute_token_match(
    reference: str,
    candidate: str,
    similarity_threshold: float = 0.72,
) -> dict:
    """
    Compare deux descriptions professionnelles de manière lexicale
    et morphologique.

    Un token candidat ne peut servir qu'une seule fois.
    Les ressemblances inférieures au seuil ne comptent pas.
    """
    reference_tokens = normalize_skill_tokens(reference)
    candidate_tokens = normalize_skill_tokens(candidate)

    if not reference_tokens:
        return {
            "score": 0.0,
            "matched_tokens": [],
            "missing_tokens": [],
            "matches": [],
        }

    available_candidates = list(candidate_tokens)

    matched_tokens = []
    missing_tokens = []
    matches = []

    for reference_token in reference_tokens:
        best_index = None
        best_candidate = None
        best_similarity = 0.0

        for index, candidate_token in enumerate(available_candidates):
            similarity = token_similarity(
                reference_token,
                candidate_token,
            )

            if similarity > best_similarity:
                best_similarity = similarity
                best_candidate = candidate_token
                best_index = index

        if (
            best_candidate is not None
            and best_similarity >= similarity_threshold
        ):
            matched_tokens.append(reference_token)

            matches.append({
                "reference": reference_token,
                "candidate": best_candidate,
                "similarity": round(best_similarity, 2),
            })

            available_candidates.pop(best_index)
        else:
            missing_tokens.append(reference_token)

    score = len(matched_tokens) / len(reference_tokens)

    return {
        "score": round(score, 2),
        "matched_tokens": matched_tokens,
        "missing_tokens": missing_tokens,
        "matches": matches,
    }


if __name__ == "__main__":
    tests = [
        (
            "Organiser des réunions et rédiger les comptes rendus",
            "Organisation de réunions et rédaction de comptes rendus",
        ),
        (
            "Régler et contrôler une machine de production",
            "Réglage des machines et contrôle de la production",
        ),
        (
            "Analyser des données avec Python et SQL",
            "Analyse de données sous Python",
        ),
        (
            "Concevoir une stratégie de communication digitale",
            "Création de contenus pour les réseaux sociaux",
        ),
    ]

    for reference, candidate in tests:
        print("Référence :", reference)
        print("Candidat :", candidate)
        print(compute_token_match(reference, candidate))
        print()
        result = compute_token_match(reference, candidate)

print(result)