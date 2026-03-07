import streamlit as st
import requests

from cv_extract import extract_text_from_upload
from matching_simple import score_cv_offer
from offers_phase1 import fetch_offers_francetravail, add_location_params

st.set_page_config(page_title="Hephaistos", layout="wide")

st.title("Hephaistos")
st.write("Agent IA emploi – prototype")

# ------------------------
# Session state
# ------------------------
if "offer_text" not in st.session_state:
    st.session_state["offer_text"] = ""
if "offers_scored" not in st.session_state:
    st.session_state["offers_scored"] = []  # cache du dernier Top calculé


# ------------------------
# Utils
# ------------------------
def to_text(x) -> str:
    """Convertit x en texte utilisable par le scoring (évite tuple/list/None)."""
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    if isinstance(x, (list, tuple)):
        return " ".join(str(i) for i in x if i is not None)
    return str(x)
def to_score(x) -> int:
    """Force un score entier (0..100). Si x est bizarre (MatchResult, tuple, etc.), retourne 0."""
    if x is None:
        return 0
    if isinstance(x, bool):
        return int(x)
    if isinstance(x, (int, float)):
        return int(x)
    if isinstance(x, (list, tuple)) and x:
        return to_score(x[0])
    # MatchResult ou autre objet: tentative de conversion
    try:
        return int(float(x))
    except Exception:
        return 0


def resolve_commune_code(code_postal: str, ville: str) -> str | None:
    """Résout un code INSEE de commune via geo.api.gouv.fr."""
    code_postal = (code_postal or "").strip()
    ville = (ville or "").strip()

    try:
        if code_postal:
            r = requests.get(
                "https://geo.api.gouv.fr/communes",
                params={"codePostal": code_postal, "fields": "code,nom", "format": "json"},
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
            if data:
                return data[0].get("code")

        if ville:
            r = requests.get(
                "https://geo.api.gouv.fr/communes",
                params={"nom": ville, "boost": "population", "fields": "code,nom", "format": "json"},
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
            if data:
                return data[0].get("code")

    except Exception:
        return None

    return None


# ================================
# 1) IMPORT CV
# ================================
st.subheader("1) Importer votre CV")

uploaded = st.file_uploader(
    "Dépose ton CV (PDF, DOCX ou TXT)",
    type=["pdf", "docx", "txt"],
)

cv_text = ""

if uploaded:
    file_bytes = uploaded.read()
    cv_text = to_text(extract_text_from_upload(uploaded.name, file_bytes))

    st.success(f"CV importé — {len(cv_text)} caractères")

    with st.expander("Voir le texte extrait"):
        st.write(cv_text)


# ================================
# 2) PHASE 1 — RECHERCHE OFFRES
# ================================
st.subheader("2) Phase 1 — Trouver des offres (France Travail)")

col1, col2, col3 = st.columns(3)
with col1:
    code_postal = st.text_input("Code postal (recommandé)", value="")
with col2:
    ville = st.text_input("Ville (optionnel)", value="")
with col3:
    rayon_km = st.slider("Rayon autour du lieu (km)", 0, 100, 10)

keywords = st.text_input(
    "Mots-clés (séparés par virgules)",
    value="assistant administratif,excel",
)

days = st.slider("Publié depuis (jours)", 1, 30, 7)

max_results = st.selectbox(
    "Nombre d'offres à récupérer (max 150)",
    [50, 100, 150],
    index=0,
)

# Bouton principal
if st.button("Rechercher et classer"):

    commune_code = resolve_commune_code(code_postal, ville)

    params = {"motsCles": keywords}
    params = add_location_params(params, commune_code, rayon_km)

    offers_raw, content_range = fetch_offers_francetravail(
        params=params,
        max_results=max_results,
    )

    st.success(f"Offres récupérées : {len(offers_raw)}")

    scored = []
    for o in offers_raw:
        description = to_text(o.get("description", ""))
        profile = to_text(o.get("profile", ""))

        result = score_cv_offer(to_text(cv_text), description, profile)

        oo = dict(o)
        oo["score"] = int(getattr(result, "score", 0))
        oo["match_result"] = result
        scored.append(oo)

    scored.sort(key=lambda x: x.get("score", 0), reverse=True)
    st.session_state["offers_scored"] = scored

# ================================
# 2b) TOP 30
# ================================
offers_scored = st.session_state.get("offers_scored", [])
if offers_scored:
    top = offers_scored[:30]
    st.subheader("Top 30 (triées par compatibilité)")

    for i, o in enumerate(top):
        title = o.get("title", "Sans titre")
        company = o.get("company", "")
        location = o.get("location", "")
        url = o.get("url", "")
        score = o.get("score", 0)

        st.write(f"**{score}/100 — {title}**")
        st.write(f"{company} — {location}")
        if url:
            st.write(url)

        if st.button("Utiliser cette offre", key=f"use_offer_{i}"):
            st.session_state["offer_text"] = to_text(o.get("description", ""))

        with st.expander("Voir description", expanded=False):
            st.write(to_text(o.get("description", "Description non disponible")))


# ================================
# 3) COLLER OFFRE
# ================================
st.subheader("3) Coller une offre d'emploi (optionnel)")

offer_text = st.text_area(
    "Texte de l'offre",
    value=st.session_state["offer_text"],
    height=220,
)

# ================================
# 4) ANALYSE
# ================================
st.subheader("4) Analyser CV vs Offre")

if st.button("Analyser CV vs Offre"):
    if not cv_text:
        st.warning("Importer un CV d'abord.")
    elif not offer_text.strip():
        st.warning("Aucune offre fournie.")
    else:
        result = score_cv_offer(to_text(cv_text), to_text(offer_text), "")

        st.metric("Score de compatibilité", f"{int(getattr(result, 'score', 0))}/100")

        matched = getattr(result, "matched", [])
        missing = getattr(result, "missing", [])
        strong_hits = getattr(result, "strong_hits", [])

        st.write("Forces (mots trouvés):", matched[:30])
        st.write("Manques (mots absents):", missing[:30])
        st.write("Mots forts:", strong_hits[:30])