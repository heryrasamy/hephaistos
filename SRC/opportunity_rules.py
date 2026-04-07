from __future__ import annotations

from typing import Any, Dict, List, Set


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def _to_set(value: Any) -> Set[str]:
    """
    Convertit une valeur en set de chaînes normalisées simples.
    """
    if value is None:
        return set()

    if isinstance(value, str):
        value = [value]

    if not isinstance(value, (list, tuple, set)):
        return set()

    cleaned = set()
    for item in value:
        if item is None:
            continue
        text = str(item).strip().lower()
        if text:
            cleaned.add(text)
    return cleaned


def _contains_any(text: str, keywords: List[str]) -> bool:
    """
    Vérifie si au moins un mot-clé est présent dans le texte.
    """
    if not text:
        return False

    text = text.lower()
    return any(keyword.lower() in text for keyword in keywords)


# ---------------------------------------------------------
# Règles génériques
# ---------------------------------------------------------
DRIVING_KEYWORDS = [
    "permis b",
    "permis",
    "conduite",
    "véhicule",
    "vehicule",
    "livraison",
    "déplacement",
    "deplacement",
    "tournée",
    "tournee",
]

EXPERIENCE_KEYWORDS = [
    "expérience exigée",
    "experience exigee",
    "confirmé",
    "confirme",
    "senior",
    "autonome immédiatement",
    "autonomie immédiate",
    "autonomie immediate",
]

TRAINING_KEYWORDS = [
    "formation interne",
    "débutant accepté",
    "debutant accepte",
    "junior accepté",
    "junior accepte",
    "accompagnement",
    "tutorat",
]

ACCESSIBILITY_KEYWORDS = [
    "sans expérience",
    "sans experience",
    "débutant",
    "debutant",
    "alternance",
    "stage",
]


# ---------------------------------------------------------
# Extraction des signaux
# ---------------------------------------------------------
def extract_candidate_signals(cv_text: str, cv_terms: List[str] | Set[str] | None = None) -> Dict[str, Any]:
    """
    Extrait quelques signaux simples et généralistes à partir du CV.
    """
    cv_text = (cv_text or "").lower()
    cv_terms_set = _to_set(cv_terms)

    has_driving_license = (
        _contains_any(cv_text, ["permis b", "permis", "conduite"])
        or any(term in cv_terms_set for term in {"permis b", "permis", "conduite"})
    )

    return {
        "has_driving_license": has_driving_license,
        "cv_terms": cv_terms_set,
    }


def extract_offer_signals(
    offer_title: str,
    offer_text: str,
    offer_terms: List[str] | Set[str] | None = None,
) -> Dict[str, Any]:
    """
    Extrait quelques signaux simples et généralistes à partir d'une offre.
    """
    title = (offer_title or "").lower()
    text = (offer_text or "").lower()
    full_text = f"{title}\n{text}".strip()

    offer_terms_set = _to_set(offer_terms)

    requires_driving = (
        _contains_any(full_text, DRIVING_KEYWORDS)
        or any(term in offer_terms_set for term in {"livraison", "conduite", "véhicule", "vehicule"})
    )

    seems_accessible = _contains_any(full_text, ACCESSIBILITY_KEYWORDS) or _contains_any(full_text, TRAINING_KEYWORDS)

    requires_experience = _contains_any(full_text, EXPERIENCE_KEYWORDS)

    return {
        "requires_driving": requires_driving,
        "seems_accessible": seems_accessible,
        "requires_experience": requires_experience,
        "offer_terms": offer_terms_set,
    }


# ---------------------------------------------------------
# Règles d'opportunité réaliste
# ---------------------------------------------------------
def evaluate_realistic_opportunity(
    score: int | float,
    candidate_signals: Dict[str, Any],
    offer_signals: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Évalue si une offre semble réaliste, accessible ou plutôt ambitieuse,
    à partir du score et de quelques signaux concrets.

    Retourne un dict stable, simple à brancher dans l'UI plus tard.
    """
    score = int(score or 0)

    has_driving_license = bool(candidate_signals.get("has_driving_license", False))
    requires_driving = bool(offer_signals.get("requires_driving", False))
    seems_accessible = bool(offer_signals.get("seems_accessible", False))
    requires_experience = bool(offer_signals.get("requires_experience", False))

    blockers: List[str] = []
    strengths: List[str] = []
    verdict = "à étudier"

    # -------------------------
    # Blocages concrets
    # -------------------------
    if requires_driving and not has_driving_license:
        blockers.append("mobilité_permis")

    if requires_driving and has_driving_license:
        strengths.append("mobilité_compatible")

    # -------------------------
    # Logique générale
    # -------------------------
    if blockers:
        if score >= 55:
            verdict = "possible avec réserve"
        else:
            verdict = "peu réaliste"
    else:
        if score >= 70:
            verdict = "très réaliste"
        elif score >= 55:
            verdict = "réaliste"
        elif score >= 40:
            verdict = "accessible"
        else:
            verdict = "exploratoire"

    # -------------------------
    # Ajustements doux
    # -------------------------
    if seems_accessible and verdict in {"exploratoire", "accessible"}:
        strengths.append("offre_ouverte_aux_profils_en_transition")

    if requires_experience and score < 55:
        if verdict == "accessible":
            verdict = "accessible mais ambitieux"
        elif verdict == "exploratoire":
            verdict = "ambitieux"

    explanation_parts: List[str] = []

    if "mobilité_compatible" in strengths:
        explanation_parts.append("la mobilité semble compatible avec l’offre")

    if "offre_ouverte_aux_profils_en_transition" in strengths:
        explanation_parts.append("l’offre paraît ouverte à des profils en progression ou en transition")

    if "mobilité_permis" in blockers:
        explanation_parts.append("l’offre semble demander de la mobilité ou de la conduite sans signal équivalent dans le CV")

    if requires_experience:
        explanation_parts.append("l’offre paraît viser un niveau d’autonomie ou d’expérience déjà solide")

    if not explanation_parts:
        explanation_parts.append("le verdict repose surtout sur la compatibilité générale entre le CV et l’offre")

    return {
        "verdict": verdict,
        "blockers": blockers,
        "strengths": strengths,
        "explanation": " ; ".join(explanation_parts),
    }


# ---------------------------------------------------------
# Fonction principale prête à brancher
# ---------------------------------------------------------
def build_realistic_opportunity_summary(
    score: int | float,
    cv_text: str,
    offer_title: str,
    offer_text: str,
    cv_terms: List[str] | Set[str] | None = None,
    offer_terms: List[str] | Set[str] | None = None,
) -> Dict[str, Any]:
    """
    Fonction d'entrée simple :
    - extrait les signaux du candidat
    - extrait les signaux de l'offre
    - retourne un résumé exploitable par l'UI
    """
    candidate_signals = extract_candidate_signals(cv_text=cv_text, cv_terms=cv_terms)
    offer_signals = extract_offer_signals(
        offer_title=offer_title,
        offer_text=offer_text,
        offer_terms=offer_terms,
    )

    result = evaluate_realistic_opportunity(
        score=score,
        candidate_signals=candidate_signals,
        offer_signals=offer_signals,
    )

    return {
        "score": int(score or 0),
        "candidate_signals": candidate_signals,
        "offer_signals": offer_signals,
        **result,
    }