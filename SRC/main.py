import re
import unicodedata
from collections import Counter
import streamlit as st
from cv_extract import extract_text_from_upload
from matching_simple import score_cv_offer, extract_terms, get_top_cv_families
from offers_phase1 import fetch_offers_francetravail, add_location_params, fetch_offers_multi_queries
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
if "generated_queries" not in st.session_state:
    st.session_state["generated_queries"] = []

generated_queries = st.session_state.get("generated_queries", [])


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
def _strip_accents_local(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s)
        if not unicodedata.combining(c)
    )


def _normalize_local(text: str) -> str:
    """
    Normalise le texte pour la détection de thèmes.
    """
    text = (text or "").lower()
    text = _strip_accents_local(text)

    text = re.sub(r"[/|\\,_;:()\[\]{}]+", " ", text)
    text = re.sub(r"[-'’]+", " ", text)
    text = re.sub(r"[^a-z0-9\s]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text
    
def detect_cv_topics(cv_text, top_n=8):
    """
    Détecte des thèmes dominants plus utiles à partir du CV.
    Approche généraliste, sans dépendance NLP externe.
    Donne la priorité aux expressions métier fréquentes,
    même si elles n'apparaissent qu'une seule fois.
    """
    if not cv_text:
        return []

    text = _normalize_local(cv_text)

    function_words = {
        "le", "la", "les", "de", "des", "du", "un", "une",
        "et", "ou", "mais", "donc", "or", "ni", "car",
        "dans", "avec", "pour", "par", "sur", "sous", "en", "au", "aux",
        "ce", "cet", "cette", "ces", "qui", "que", "quoi", "dont",
        "comme", "ainsi", "tres", "plus", "moins", "bien",
        "depuis", "vers", "chez", "entre", "afin"
    }

    generic_verbs = {
        "etre", "avoir", "faire", "mettre", "prendre", "donner",
        "realiser", "participer", "effectuer", "travailler", "rejoindre",
        "developper", "creer", "suivre", "animer", "gerer", "coordonner",
        "rediger", "produire", "assurer", "accompagner", "contribuer"
    }

    generic_adjectives = {
        "bon", "bonne", "fort", "forte", "grand", "grande",
        "nouveau", "nouvelle", "determine", "determinee",
        "proactif", "proactive", "ingenieux", "ingenieuse",
        "polyvalent", "polyvalente", "autonome", "rigoureux",
        "rigoureuse", "curieux", "curieuse", "motive", "motivee",
        "dynamique", "adaptable"
    }

    months = {
        "janvier", "fevrier", "mars", "avril", "mai", "juin",
        "juillet", "aout", "septembre", "octobre", "novembre", "decembre"
    }

    location_words = {
        "paris", "france", "toulouse", "marseille", "lyon", "lille",
        "bordeaux", "nantes", "rennes", "tananarive"
    }

    weak_words = {
        "poste", "profil", "mission", "missions", "projet", "projets",
        "experience", "experiences", "activite", "activites",
        "realisation", "realisations", "participation", "domaine",
        "structure", "entreprise", "societe", "service", "equipe",
        "equipes", "mise", "jour", "role", "direction",
        "candidature", "diplome", "diplomes", "reference", "references",
        "outil", "outils", "travail", "secteur", "cadre",
        "competence", "competences", "formation"
    }

    # Expressions métier génériques, réutilisables sur plusieurs profils
    preferred_phrases = [
        "agent d accueil",
        "charge d accueil",
        "assistant administratif",
        "assistante administrative",
        "agent administratif",
        "accueil telephonique",
        "accueil physique",
        "relation client",
        "service client",
        "saisie de documents",
        "gestion des stocks",
        "gestion de stock",
        "prise de rendez vous",
        "suivi des plannings",
        "gestion planning",
        "travaux de secretariat",
        "gestion administrative",
        "classement archivage",
        "support technique",
        "support client",
        "communication numerique",
        "reseaux sociaux",
        "creation de contenu",
        "mediation culturelle",
        "gestion de projet",
        "chef de projet",
        "developpement web",
        "site internet",
    ]

    # Normalisation des expressions pour comparaison
    normalized_phrases = [_normalize_local(p) for p in preferred_phrases]

    # 1) Détection prioritaire d'expressions métier présentes dans le texte
    found_phrases = []
    for phrase in normalized_phrases:
        if phrase in text:
            found_phrases.append(phrase)

    # 2) Nettoyage des tokens simples
    tokens = [
        tok for tok in text.split()
        if len(tok) >= 4
        and not any(ch.isdigit() for ch in tok)
        and tok not in function_words
        and tok not in generic_verbs
        and tok not in generic_adjectives
        and tok not in months
        and tok not in location_words
        and tok not in weak_words
    ]

    if not tokens and not found_phrases:
        return []

    word_counts = Counter(tokens)

    # 3) Mots simples utiles, même avec fréquence 1
    useful_single_words = []
    for word, count in word_counts.items():
        score = count

        # petit bonus pour certains mots métier fréquents
        if word in {
            "accueil", "administratif", "administrative", "bureautique",
            "archivage", "secretariat", "documents", "planning",
            "stocks", "stock", "saisie", "client", "communication",
            "logistique", "vente", "support", "web", "numerique"
        }:
            score += 2

        useful_single_words.append((word, score))

    useful_single_words.sort(key=lambda x: (-x[1], x[0]))

    # 4) Fusion finale en évitant les doublons redondants
    topics = []
    covered_words = set()

    for phrase in found_phrases:
        topics.append(phrase)
        for w in phrase.split():
            covered_words.add(w)
        if len(topics) >= top_n:
            return topics[:top_n]

    for word, _score in useful_single_words:
        if word in covered_words:
            continue
        topics.append(word)
        covered_words.add(word)
        if len(topics) >= top_n:
            break

    return topics[:top_n]

def topics_to_skills(topics):
    """
    Transforme des thèmes détectés en compétences dominantes
    de manière généraliste, sans dépendre d'un CV particulier.
    """
    if not topics:
        return []

    skills = []

    software_terms = {
        "excel", "word", "powerpoint", "outlook", "sap", "salesforce",
        "wordpress", "canva", "photoshop", "illustrator", "indesign",
        "premiere", "google analytics", "sql", "python", "java",
        "html", "css", "javascript", "typescript", "php", "react",
        "angular", "vue", "docker", "jira", "trello", "figma",
        "autocad", "power bi", "tableau", "qlik", "drupal"
    }

    language_terms = {
        "anglais", "espagnol", "allemand", "italien", "portugais",
        "arabe", "chinois", "japonais", "russe"
    }

    management_terms = {
        "gestion", "coordination", "pilotage", "organisation",
        "suivi", "planification", "encadrement", "budget"
    }

    analysis_terms = {
        "analyse", "donnees", "data", "reporting",
        "tableau de bord", "indicateur", "analytics", "kpi"
    }

    communication_terms = {
        "communication", "contenu", "contenus", "redaction",
        "newsletter", "reseaux sociaux", "site internet",
        "community management", "marketing"
    }

    client_terms = {
        "client", "relation client", "vente", "accueil",
        "support", "conseil", "service client"
    }

    production_terms = {
        "podcast", "video", "montage", "audio", "photo",
        "wireframe", "storyboard", "creation"
    }

    for topic in topics:
        t = (topic or "").lower().strip()

        skill = None

        if t in software_terms:
            skill = f"Utilisation de {topic}"

        elif t in language_terms:
            skill = f"Maîtrise de {topic}"

        elif any(term in t for term in management_terms):
            skill = f"{topic.capitalize()} d'activités ou de projets"

        elif any(term in t for term in analysis_terms):
            skill = f"{topic.capitalize()}"

        elif any(term in t for term in communication_terms):
            skill = f"{topic.capitalize()}"

        elif any(term in t for term in client_terms):
            skill = f"{topic.capitalize()}"

        elif any(term in t for term in production_terms):
            skill = f"Production / gestion de {topic}"

        else:
            # fallback généraliste
            skill = topic.capitalize()

        skills.append(skill)

    # Supprimer les doublons en gardant l'ordre
    unique_skills = []
    seen = set()

    for s in skills:
        key = s.lower()
        if key not in seen:
            seen.add(key)
            unique_skills.append(s)

    return unique_skills[:8]  

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
    Classe un terme manquant dans une catégorie assez générique
    pour produire une suggestion CV réutilisable sur des profils variés.
    """
    t = (term or "").lower().strip()

    # Sécurité minimale
    if not t:
        return "generic"

    # 1) Langues
    language_markers = {
        "anglais", "espagnol", "allemand", "italien", "portugais",
        "arabe", "chinois", "japonais", "russe", "bilingue",
        "toeic", "toefl", "ielts"
    }
    if any(k in t for k in language_markers):
        return "language"

    # 2) Diplômes / formations / certifications
    diploma_markers = {
        "bac", "bachelor", "master", "licence", "bts", "dut", "but",
        "formation", "certification", "certifie", "certifiée",
        "diplome", "diplôm", "titre professionnel", "rncp"
    }
    if any(k in t for k in diploma_markers):
        return "diploma"

    # 3) Soft skills / savoir-être
    soft_skill_markers = {
        "autonomie", "rigueur", "organisation", "adaptabilite",
        "adaptation", "relationnel", "communication", "ecoute",
        "esprit analyse", "analyse", "proactivite", "initiative",
        "travail equipe", "travail en equipe", "polyvalence",
        "motivation", "dynamisme", "curiosite", "leadership"
    }
    if any(k in t for k in soft_skill_markers):
        return "soft_skill"

    # 4) Management / coordination / pilotage
    management_markers = {
        "gestion", "coordination", "pilotage", "organisation",
        "suivi", "planification", "planning", "encadrement",
        "management", "manager", "responsable", "supervision",
        "budget", "budgets", "reporting", "chef de projet"
    }
    if any(k in t for k in management_markers):
        return "management"

    # 5) Relation client / commerce / service
    client_markers = {
        "client", "clients", "vente", "ventes", "accueil",
        "service", "support", "conseil", "commercial",
        "prospection", "negociation", "fidélisation", "fidelisation",
        "relation client", "satisfaction", "sav"
    }
    if any(k in t for k in client_markers):
        return "client"

    # 6) Analyse / données / indicateurs
    analysis_markers = {
        "analyse", "donnees", "données", "data", "reporting",
        "tableau de bord", "indicateur", "indicateurs",
        "statistique", "statistiques", "analytics", "kpi"
    }
    if any(k in t for k in analysis_markers):
        return "analysis"

    # 7) Outils / logiciels / technologies
    # Ici on devient plus souple : on combine une petite base + motifs génériques
    software_markers = {
        "logiciel", "logiciels", "outil", "outils", "application",
        "applications", "plateforme", "plateformes", "erp", "crm",
        "cms", "saas", "api", "base de donnees", "base de données",
        "bureautique", "informatique", "digital", "numerique", "numérique"
    }

    software_examples = {
        "excel", "word", "powerpoint", "outlook", "sap", "salesforce",
        "wordpress", "canva", "photoshop", "illustrator", "indesign",
        "premiere", "google analytics", "sql", "python", "java",
        "html", "css", "javascript", "typescript", "php", "c++",
        "c#", "react", "angular", "vue", "docker", "kubernetes",
        "jira", "trello", "notion", "figma", "autocad", "matlab",
        "solidworks", "power bi", "tableau", "qlik"
    }

    # motifs typiques de techno / logiciel / sigle
    has_tech_shape = (
        "/" in t
        or "+" in t
        or "#" in t
        or any(x in t for x in ["sql", "api", "crm", "erp", "cms", "bi"])
    )

    if (
        any(k in t for k in software_markers)
        or any(k in t for k in software_examples)
        or has_tech_shape
    ):
        return "software"

    return "generic"

def build_search_queries_from_topics(topics, max_queries=5):
    """
    Génère des requêtes emploi à partir des thèmes détectés dans le CV.

    Stratégie :
    1. identifier des familles métiers probables
    2. produire d'abord des requêtes ciblées
    3. compléter avec quelques requêtes élargies
    """
    if not topics:
        return []

    cleaned = [t.strip().lower() for t in topics if t and t.strip()]
    cleaned = list(dict.fromkeys(cleaned))  # dédoublonnage

    TOPIC_TO_ROLES = {
        "musee": ["médiation culturelle", "chargé de projet culturel"],
        "musée": ["médiation culturelle", "chargé de projet culturel"],
        "musees": ["médiation culturelle", "chargé de projet culturel"],
        "musées": ["médiation culturelle", "chargé de projet culturel"],
        "patrimoine": ["médiation culturelle", "chargé de projet culturel"],
        "culture": ["médiation culturelle", "chargé de projet culturel"],

        "numerique": ["communication numérique", "web"],
        "numérique": ["communication numérique", "web"],
        "digital": ["communication numérique", "chargé de communication digitale"],
        "web": ["web", "chargé de communication digitale"],
        "site internet": ["web", "chargé de communication digitale"],
        "developpement": ["web", "chargé de communication digitale"],
        "développement": ["web", "chargé de communication digitale"],

        "reseaux sociaux": ["community manager", "chargé de communication"],
        "réseaux sociaux": ["community manager", "chargé de communication"],
        "communication": ["chargé de communication", "communication numérique"],
        "contenu": ["création de contenu", "chargé de communication"],
        "redaction": ["rédacteur web", "création de contenu"],
        "rédaction": ["rédacteur web", "création de contenu"],

        "animation": ["animation culturelle", "création de contenu"],
        "animation chaine": ["création de contenu", "community manager"],
        "animation chaîne": ["création de contenu", "community manager"],

        "gestion": ["assistant de gestion", "chargé de projet"],
        "coordination": ["chargé de projet", "assistant de coordination"],
        "organisation": ["assistant administratif", "chargé de projet"],

        "accueil": ["agent d'accueil", "chargé d'accueil"],
        "vente": ["conseiller de vente", "commercial"],
        "administratif": ["assistant administratif", "agent administratif"],
        "administration": ["assistant administratif", "agent administratif"],
        "logistique": ["agent logistique", "assistant logistique"],
        "support": ["support client", "conseiller client"],
        "service client": ["conseiller client", "support client"],
    }

    targeted_queries = []
    expanded_queries = []

    for topic in cleaned:
        roles = TOPIC_TO_ROLES.get(topic, [])
        for i, role in enumerate(roles):
            if i == 0:
                targeted_queries.append(role)
            else:
                expanded_queries.append(role)

    # secours minimal si aucun mapping exact
    if not targeted_queries:
        targeted_queries = cleaned[:2]
        expanded_queries = cleaned[2:4]

    targeted_queries = list(dict.fromkeys(targeted_queries))
    expanded_queries = list(dict.fromkeys(expanded_queries))

    final_queries = []

    # 1) on privilégie d'abord les requêtes ciblées
    for q in targeted_queries[:3]:
        final_queries.append(q)

    # 2) puis quelques requêtes élargies
    for q in expanded_queries[:2]:
        if q not in final_queries:
            final_queries.append(q)

    return final_queries[:max_queries]
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

cv_families = get_top_cv_families(cv_text)

st.markdown("### Familles métier dominantes détectées")
st.write(cv_families)
with st.expander("Voir le texte extrait"):
        st.write(cv_text)

        topics = detect_cv_topics(cv_text)
        skills = topics_to_skills(topics)

        st.session_state["suggested_keywords"] = " ".join(topics[:2])
        st.session_state["keywords_input"] = st.session_state["suggested_keywords"]

        search_queries = build_search_queries_from_topics(topics)
st.session_state["generated_queries"] = search_queries

st.markdown("### Thèmes dominants détectés dans votre CV")
if topics:
        cols = st.columns(4)
        for i, t in enumerate(topics):
            cols[i % 4].info(t)
        else:
            for fam in cv_families:
                st.success(fam)

        cv_families = get_top_cv_families(cv_text)

st.markdown("### Familles métier dominantes détectées")
st.write(cv_families)

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
generated_queries = st.session_state.get("generated_queries", [])

if generated_queries:
    st.markdown("### Requêtes suggérées à partir du CV")
    for q in generated_queries:
        st.write("•", q)

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
    key="keywords_input"
)

days = st.slider("Publié depuis (jours)", 1, 30, 7)

max_results = st.selectbox(
    "Nombre d'offres à récupérer (max 150)",
    [50, 100, 150],
    index=0,
)

# Bouton principal
st.write("Requêtes actuellement utilisées :", st.session_state.get("generated_queries", []))
st.write("Champ mots-clés actuel :", keywords)

if st.button("Rechercher et classer"):
    try:
        base_params = {
            "publieeDepuis": days,
        }

        if selected_commune:
            base_params["commune"] = selected_commune["code"]
            base_params["distance"] = rayon_km

        queries = []

        if keywords.strip():
            queries.append(keywords.strip())

        for q in st.session_state.get("generated_queries", []):
            if q not in queries:
                queries.append(q)

        offers_raw = fetch_offers_multi_queries(
            queries=queries,
            base_params=base_params,
            max_results_per_query=max_results
        )

        st.write(f"Offres récupérées : {len(offers_raw)}")

        scored = []

        for o in offers_raw:
            description = to_text(o.get("text", ""))

            # ignorer les annonces trop pauvres
            if len(description.strip()) < 50:
                continue

            result = score_cv_offer(
                to_text(cv_text),
                description
            )

            # enrichir l'offre avec le score
            o["score"] = result["score"]
            o["matched_terms"] = result["matched_terms"]
            o["missing_terms"] = result["missing_terms"]

            scored.append(o)

        # tri des offres par score
        scored.sort(key=lambda x: x.get("score", 0), reverse=True)

        # garder seulement le top 30
        scored = scored[:30]

        # stocker pour l'interface
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

st.subheader("3) Coller une offre d'emploi (optionnel)")

if "offer_text" not in st.session_state:
    st.session_state["offer_text"] = ""

st.text_area(
    "Texte de l'offre",
    height=180,
    key="offer_text"
)

# ================================
# 4) Analyser CV vs Offre
# ================================
st.subheader("4) Analyser CV vs Offre")

offer_text = st.session_state.get("offer_text", "")

if st.button("Analyser CV vs Offre"):
    if not cv_text:
        st.warning("Importer un CV d'abord.")
    elif not offer_text.strip():
        st.warning("Aucune offre fournie.")
    else:
        result = score_cv_offer(
            to_text(cv_text),
            to_text(offer_text)
        )

        st.session_state["last_analysis"] = result

analysis = st.session_state.get("last_analysis")

if analysis:
    st.markdown("### Score de compatibilité")
    st.markdown(f"## {analysis.get('score', 0)}/100")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Forces (mots trouvés)")
        matched_terms = analysis.get("matched_terms", [])
        if matched_terms:
            for term in matched_terms[:12]:
                st.write(f"- {term}")
        else:
            st.write("Aucune correspondance détectée.")

    with col2:
        st.markdown("### Manques (mots absents)")
        missing_terms = analysis.get("missing_terms", [])
        if missing_terms:
            for term in missing_terms[:12]:
                st.write(f"- {term}")
        else:
            st.write("Aucun manque détecté.")

    st.markdown("### Mots forts")
    strong_terms = analysis.get("matched_terms", [])[:8]
    if strong_terms:
        st.write(", ".join(strong_terms))
    else:
        st.write("Aucun mot fort détecté.")

    st.markdown("### Suggestions pour améliorer le CV")
    suggestions = analysis.get("missing_terms", [])[:8]

    if suggestions:
        for term in suggestions:
            st.write(f"- Ajouter ou reformuler une expérience liée à : {term}")
    else:
        st.write("Aucune suggestion générée.")