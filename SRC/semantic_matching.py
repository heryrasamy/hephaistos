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

def evaluate_competence_match(
    competence_text: str,
    cv_text: str,
) -> dict:
    """
    Évalue la visibilité d'une compétence dans un CV.

    La fonction analyse uniquement ce qui est écrit dans le document.
    Elle ne juge pas les compétences réelles du candidat.
    """
    match_result = compute_token_match(
        reference=competence_text,
        candidate=cv_text,
    )

    visibility = match_result.get("score", 0.0)
    matched_tokens = match_result.get("matched_tokens", [])
    missing_tokens = match_result.get("missing_tokens", [])
    matches = match_result.get("matches", [])

    evidence = [
        {
            "reference": match.get("reference", ""),
            "cv_term": match.get("candidate", ""),
            "similarity": match.get("similarity", 0.0),
        }
        for match in matches
    ]

    if visibility >= 0.85 and not missing_tokens:
        status = "CLEARLY_VISIBLE"

        candidate_message = (
            "Cette compétence est clairement mise en avant dans ton CV."
        )

        recruiter_view = (
            "Un recruteur devrait pouvoir identifier rapidement "
            "cette compétence à la lecture de ton CV."
        )

        candidate_action = (
            "Vérifie simplement qu'elle apparaît dans une expérience "
            "pertinente pour le poste visé."
        )

    elif (
        visibility >= 0.35
        or (
            visibility >= 0.20
            and len(matched_tokens) >= 2
        )
    ):
        status = "PARTIALLY_VISIBLE"

        candidate_message = (
            "Ton CV présente plusieurs éléments liés à cette compétence, "
            "mais elle n'est pas encore totalement visible."
        )

        recruiter_view = (
            "Un recruteur pourrait repérer des éléments proches, "
            "sans forcément identifier immédiatement cette compétence."
        )

        candidate_action = (
            "Relis tes expériences et tes réalisations pour vérifier "
            "si tu peux décrire plus précisément ce que tu as réellement fait."
        )

    else:
        status = "NOT_INDICATED"

        candidate_message = (
            "Cette compétence n'est pas clairement indiquée dans ton CV."
        )

        recruiter_view = (
            "Un recruteur ne pourra probablement pas identifier "
            "cette compétence à partir des informations actuelles."
        )

        candidate_action = (
            "Si tu as réellement utilisé cette compétence, cherche dans "
            "ton parcours une expérience concrète qui permettrait de la présenter. "
            "Sinon, ne l'ajoute pas."
        )

    return {
        "competence": competence_text,
        "status": status,
        "visibility": visibility,
        "evidence": evidence,
        "matched_tokens": matched_tokens,
        "missing_tokens": missing_tokens,
        "candidate_message": candidate_message,
        "recruiter_view": recruiter_view,
        "candidate_action": candidate_action,
    }


def evaluate_rome_reference(
    cv_text: str,
    rome_reference: dict,
) -> dict:
    """
    Évalue la visibilité dans le CV de toutes les compétences
    et de tous les savoirs d'une référence métier ROME.
    """

    results = []

    reference_items = (
        rome_reference.get("competences", [])
        + rome_reference.get("savoirs", [])
    )

    for item in reference_items:
        libelle = str(item.get("libelle", "")).strip()

        if not libelle:
            continue

        evaluation = evaluate_competence_match(
            competence_text=libelle,
            cv_text=cv_text,
        )

        evaluation["rome_code"] = item.get("code", "")
        evaluation["rome_type"] = item.get("type", "")
        evaluation["enjeu"] = item.get("enjeu", "")
        evaluation["categorie"] = item.get("categorie", "")

        results.append(evaluation)

    clearly_visible = [
        item for item in results
        if item["status"] == "CLEARLY_VISIBLE"
    ]

    partially_visible = [
        item for item in results
        if item["status"] == "PARTIALLY_VISIBLE"
    ]

    not_indicated = [
        item for item in results
        if item["status"] == "NOT_INDICATED"
    ]

    return {
        "rome_code": rome_reference.get("code", ""),
        "rome_job": rome_reference.get("libelle", ""),
        "total": len(results),
        "clearly_visible": clearly_visible,
        "partially_visible": partially_visible,
        "not_indicated": not_indicated,
    }