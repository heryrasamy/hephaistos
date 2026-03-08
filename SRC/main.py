import streamlit as st
from cv_extract import extract_text_from_upload
from matching_simple import score_cv_offer
from offers_phase1 import fetch_offers_francetravail
from francetravail_api import get_access_token, search_communes
from location_helper import filter_communes, format_commune_label

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
# ================================
# 1) IMPORT CV
# ================================
def classify_term(term: str) -> str:
    """
    Classe un terme manquant dans une grande catégorie
    pour produire une suggestion générique et honnête.
    """
    t = (term or "").lower().strip()

    software_keywords = {
        "excel", "word", "powerpoint", "outlook", "sap", "salesforce",
        "wordpress", "canva", "photoshop", "illustrator", "indesign",
        "premiere", "premiere pro", "google analytics", "sql", "python",
        "java", "html", "css", "capcut", "drupal", "suite adobe"
    }

    soft_skills_keywords = {
        "autonomie", "rigueur", "organisation", "communication",
        "travail equipe", "travail en equipe", "adaptabilite",
        "adaptation", "relationnel", "esprit analyse", "analyse",
        "proactivite", "force proposition"
    }

    language_keywords = {
        "anglais", "espagnol", "allemand", "italien", "bilingue", "toeic", "toefl"
    }

    diploma_keywords = {
        "bac", "master", "licence", "bts", "dut", "formation",
        "certification", "diplome"
    }

    management_keywords = {
        "gestion", "coordination", "pilotage", "organisation", "suivi",
        "planification", "planning", "encadrement"
    }

    client_keywords = {
        "client", "vente", "accueil", "service", "support",
        "relation client", "conseil"
    }

    analysis_keywords = {
        "analyse", "donnees", "data", "reporting", "tableau de bord",
        "indicateur", "analytics"
    }

    if any(k in t for k in software_keywords):
        return "software"
    if any(k in t for k in language_keywords):
        return "language"
    if any(k in t for k in diploma_keywords):
        return "diploma"
    if any(k in t for k in soft_skills_keywords):
        return "soft_skill"
    if any(k in t for k in management_keywords):
        return "management"
    if any(k in t for k in client_keywords):
        return "client"
    if any(k in t for k in analysis_keywords):
        return "analysis"

    return "generic"


def suggest_for_term(term: str, category: str) -> str:
    """
    Génère une suggestion honnête à partir d'un terme manquant
    et de sa catégorie.
    """
    if category == "software":
        return (
            f"Si vous maîtrisez réellement « {term} », citez-le explicitement "
            f"dans une expérience ou dans la rubrique compétences."
        )

    if category == "language":
        return (
            f"Si « {term} » correspond à votre profil, indiquez-le avec un niveau précis sur le CV."
        )

    if category == "diploma":
        return (
            f"Vérifiez que « {term} » est visible rapidement dans la partie formation ou certifications."
        )

    if category == "soft_skill":
        return (
            f"Pour « {term} », privilégiez un exemple concret dans une expérience plutôt qu’une simple liste de qualités."
        )

    if category == "management":
        return (
            f"Si vous avez réellement exercé « {term} », reformulez une mission pour le faire apparaître plus clairement."
        )

    if category == "client":
        return (
            f"Si « {term} » fait partie de votre expérience, mettez-le en avant dans une mission ou un résultat concret."
        )

    if category == "analysis":
        return (
            f"Si vous avez déjà réalisé « {term} », précisez-le dans une expérience avec un exemple concret."
        )

    return (
        f"Vérifiez si « {term} » correspond à une compétence ou mission réelle déjà présente, "
        f"et reformulez-la plus explicitement si nécessaire."
    )


def build_cv_suggestions(matched, missing, max_suggestions: int = 6):
    """
    Construit une liste de suggestions génériques pour améliorer le CV
    sans inventer d'expérience ni de compétence.
    """
    suggestions = []

    for term in missing[:12]:
        category = classify_term(term)
        suggestion = suggest_for_term(term, category)
        suggestions.append(suggestion)

    # Supprime les doublons tout en gardant l'ordre
    unique = []
    seen = set()

    for s in suggestions:
        if s not in seen:
            seen.add(s)
            unique.append(s)

    return unique[:max_suggestions]
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
# ================================
# 2) PHASE 1 — RECHERCHE OFFRES
# ================================
st.subheader("2) Phase 1 — Trouver des offres (France Travail)")

st.write("Localisation")

location_query = st.text_input(
    "Code postal, début de code postal, département ou ville",
    value="75",
    help="Exemples : 75, 75011, Paris, Toulouse"
)

rayon_km = st.slider("Rayon autour du lieu (km)", 0, 100, 10)

selected_commune = None

if location_query.strip():
    try:
        token = get_access_token()
        all_communes = search_communes(token)
        suggestions = filter_communes(all_communes, location_query, limit=20)

        if suggestions:
            selected_label = st.selectbox(
                "Suggestions de communes",
                options=[format_commune_label(c) for c in suggestions]
            )

            selected_commune = next(
                c for c in suggestions
                if format_commune_label(c) == selected_label
            )

            st.caption(
                f"Commune sélectionnée : {selected_commune['libelle']} | "
                f"CP {selected_commune['codePostal']}"
            )
        else:
            st.warning("Aucune commune trouvée pour cette saisie.")

    except Exception as e:
        st.error(f"Erreur référentiel communes : {e}")

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
    params = {
        "motsCles": keywords,
        "publieeDepuis": days,
    }

    if selected_commune:
        params["commune"] = selected_commune["code"]
        params["distance"] = rayon_km

    try:
        offers_raw, content_range = fetch_offers_francetravail(
            params=params,
            max_results=max_results,
        )

        st.success(f"Offres récupérées : {len(offers_raw)}")

        scored = []

        for o in offers_raw:
            description = to_text(o.get("text", ""))

            result = score_cv_offer(
                to_text(cv_text),
                description,
                {}
            )

            oo = dict(o)
            oo["score"] = int(getattr(result, "score", 0))
            oo["match_result"] = result

            scored.append(oo)

        scored.sort(key=lambda x: x.get("score", 0), reverse=True)
        st.session_state["offers_scored"] = scored

    except Exception as e:
        st.error(f"Erreur lors de la recherche d'offres : {e}")
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
            st.session_state["offer_text"] = to_text(o.get("text", ""))

        with st.expander("Voir description", expanded=False):
            st.write(to_text(o.get("text", "Description non disponible")))


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

# récupérer la dernière analyse si elle existe
result = st.session_state.get("last_analysis", None)

if st.button("Analyser CV vs Offre"):

    if not cv_text:
        st.warning("Importer un CV d'abord.")

    elif not offer_text.strip():
        st.warning("Aucune offre fournie.")

    else:
        result = score_cv_offer(to_text(cv_text), to_text(offer_text), {})

        # mémoriser l'analyse
        st.session_state["last_analysis"] = result


# afficher l'analyse si elle existe
if result:

    st.metric("Score de compatibilité", f"{int(getattr(result, 'score', 0))}/100")

    matched = getattr(result, "matched", [])
    missing = getattr(result, "missing", [])
    strong_hits = getattr(result, "strong_hits", [])

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Forces (mots trouvés)")
        for m in matched[:30]:
            st.write("✔", m)

    with col2:
        st.markdown("### Manques (mots absents)")
        for m in missing[:30]:
            st.write("✖", m)

    st.markdown("### Mots forts")

    if strong_hits:
        for m in strong_hits[:30]:
            st.write("⭐", m)
    else:
        st.write("Aucun mot fort détecté.")

    suggestions = build_cv_suggestions(matched, missing)

    st.markdown("### Suggestions pour améliorer le CV")

    if suggestions:
        for s in suggestions:
            st.write("•", s)
            