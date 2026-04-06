import re
import unicodedata
from collections import Counter
from typing import List

import streamlit as st

from cv_extract import extract_text_from_upload
from matching_simple import score_cv_offer, STOPWORDS,get_top_cv_families
from job_inference import (
    build_job_inference_summary,
    build_search_queries_from_job_summary,
    get_top_cv_families,
)
from offers_phase1 import fetch_offers_multi_queries
from location_helper import filter_communes, format_commune_label
from francetravail_api import search_communes, get_access_token


st.set_page_config(page_title="Hephaistos", layout="wide")
st.title("Hephaistos")
st.write("Agent IA emploi – prototype")


# =========================================================
# SESSION STATE
# =========================================================
if "offer_text" not in st.session_state:
    st.session_state["offer_text"] = ""

if "offers_scored" not in st.session_state:
    st.session_state["offers_scored"] = []

if "generated_queries" not in st.session_state:
    st.session_state["generated_queries"] = []

if "keywords_input" not in st.session_state:
    st.session_state["keywords_input"] = ""

if "last_analysis" not in st.session_state:
    st.session_state["last_analysis"] = None

if "suggested_keywords" not in st.session_state:
    st.session_state["suggested_keywords"] = ""


# =========================================================
# CONSTANTES
# =========================================================
VALID_PUBLIEE_DEPUIS = [1, 3, 7, 14, 30, 60, 90, 180, 365]

FAMILY_LABELS = {
    "production": "Production & Fabrication",
    "maintenance": "Maintenance & Réparation",
    "logistique": "Logistique & Transport",
    "batiment": "Construction & Bâtiment",
    "technique_installation": "Technique & Installation",
    "administratif_gestion": "Administratif & Gestion",
    "analyse_pilotage": "Analyse & Pilotage",
    "vente_commerce": "Vente & Commerce",
    "relation_client_accueil": "Relation Client & Accueil",
    "communication_marketing": "Communication & Marketing",
    "pedagogie_formation": "Pédagogie & Formation",
    "sante_soin": "Santé & Soin",
    "social_accompagnement": "Social & Accompagnement",
    "securite_protection": "Sécurité & Protection",
    "creation_artistique": "Création & Artistique",
    "hotellerie_restauration": "Hôtellerie & Restauration",
}

GENERIC_TOPIC_TERMS = {
    "professionnel",
    "professionnelle",
    "communication",
    "organisation",
    "gestion",
    "suivi",
    "accompagnement",
    "service",
    "services",
    "mission",
    "missions",
    "projet",
    "projets",
    "experience",
    "experiences",
    "activite",
    "activites",
    "competence",
    "competences",
    "poste",
    "profil",
    "travail",
    "structure",
    "entreprise",
    "societe",
    "domaine",
    "public",
    "annee",
}


# =========================================================
# UTILS
# =========================================================
FAMILY_LABELS = {
    "administratif_gestion": "Administratif & Gestion",
    "relation_client_accueil": "Relation Client & Accueil",
    "communication_marketing": "Communication & Marketing",
    "informatique_tech": "Informatique & Technique",
    "production_logistique": "Production & Logistique",
    "sante_soin": "Santé & Soin",
    "education_formation": "Éducation & Formation",
    "commerce_vente": "Commerce & Vente",
    "batiment_travaux": "Bâtiment & Travaux",
    "securite": "Sécurité",
}

def to_text(x) -> str:
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    if isinstance(x, (list, tuple)):
        return " ".join(str(i) for i in x if i is not None)
    return str(x)


def format_family_labels(families: List[str]) -> List[str]:
    if not families:
        return []
    return [FAMILY_LABELS.get(f, f) for f in families]


def _strip_accents_local(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s or "")
        if not unicodedata.combining(c)
    )


def _normalize_local(text: str) -> str:
    text = (text or "").lower()
    text = _strip_accents_local(text)
    text = re.sub(r"[/|\\,_;:()\[\]{}]+", " ", text)
    text = re.sub(r"[-'’]+", " ", text)
    text = re.sub(r"[^a-z0-9\s]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def remove_redundant_terms(terms: list[str]) -> list[str]:
    """
    Supprime les termes inclus dans des termes plus longs.
    """
    terms_sorted = sorted(terms, key=lambda x: len(x), reverse=True)
    result = []

    for term in terms_sorted:
        if not any(term in longer for longer in result):
            result.append(term)

    return result


def is_clean_term(term: str) -> bool:
    words = term.split()

    if len(words) > 4:
        return False

    if any(w in STOPWORDS for w in words):
        return False

    generic_words = {
        "agent", "profil", "poste", "travail", "mission", "metier",
        "qualites", "qualite", "organisation", "adaptation", "agenda",
        "experience", "competence", "formation", "service"
    }
    if any(w in generic_words for w in words):
        return False

    if any(len(w) < 3 for w in words):
        return False

    return True


def prepare_display_terms(terms: list[str], max_items: int = 8) -> list[str]:
    """
    Prépare une liste de termes pour affichage utilisateur.
    """
    cleaned = [t for t in terms if is_clean_term(t)]
    reduced = remove_redundant_terms(cleaned)
    return reduced[:max_items]


def interpret_score(score: int) -> str:
    """
    Donne une interprétation simple du score.
    """
    if score < 40:
        return "Correspondance faible"
    elif score < 60:
        return "Correspondance partielle"
    elif score < 80:
        return "Bonne correspondance"
    else:
        return "Très bonne correspondance"


def build_cv_suggestions_from_competencies(missing_competencies: list[dict]) -> list[str]:
    """
    Génère des suggestions CV à partir des compétences manquantes interprétées.
    """
    suggestions = []

    for comp in missing_competencies:
        concept = comp.get("concept")
        advice = comp.get("advice", "")

        if concept == "specifique_metier":
            continue

        if concept == "organisation_coordination":
            suggestions.append(
                "Ajoute ou reformule une expérience montrant la planification, la coordination ou le suivi d'activités."
            )

        elif concept == "suivi_analyse_donnees":
            suggestions.append(
                "Mets en avant l’utilisation d’outils comme Excel, reporting ou tableaux de bord avec des exemples concrets."
            )

        elif concept == "management":
            suggestions.append(
                "Si tu as encadré ou coordonné des personnes, mentionne-le explicitement avec des résultats ou responsabilités."
            )

        elif concept == "relation_client":
            suggestions.append(
                "Ajoute des exemples concrets de relation client : accueil, conseil, suivi ou gestion de demandes."
            )

        elif concept == "communication":
            suggestions.append(
                "Décris précisément tes actions de communication : contenus créés, réseaux utilisés, objectifs atteints."
            )

        elif concept == "outils_bureautiques":
            suggestions.append(
                "Précise les outils bureautiques maîtrisés (Word, Excel, PowerPoint) et leur usage concret."
            )

        elif concept == "outils_techniques":
            suggestions.append(
                "Indique clairement les outils ou technologies utilisés ainsi que ton niveau de maîtrise."
            )

        elif concept == "logistique_stock":
            suggestions.append(
                "Ajoute des expériences liées à la gestion de stock, réception, inventaire ou flux logistiques."
            )

        elif concept == "qualite_conformite":
            suggestions.append(
                "Mentionne les procédures, contrôles qualité ou normes que tu as appliqués."
            )

        elif concept == "soft_skills":
            suggestions.append(
                "Ajoute un exemple concret illustrant ta rigueur, ton autonomie ou ton travail en équipe."
            )

        else:
            if advice:
                suggestions.append(advice)

    return list(dict.fromkeys(suggestions))


def dedupe_keep_order(values: List[str]) -> List[str]:
    result = []
    seen = set()

    for value in values:
        cleaned = " ".join(str(value).strip().split())
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)

    return result


def is_generic_topic_term(term: str) -> bool:
    term_norm = _normalize_local(term)

    if not term_norm:
        return True

    words = term_norm.split()

    if term_norm in GENERIC_TOPIC_TERMS:
        return True

    if words and all(word in GENERIC_TOPIC_TERMS for word in words):
        return True

    return False


def detect_cv_topics(cv_text: str, top_n: int = 8) -> List[str]:
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

    normalized_phrases = [_normalize_local(p) for p in preferred_phrases]

    found_phrases = []
    for phrase in normalized_phrases:
        if phrase in text:
            found_phrases.append(phrase)

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

    useful_single_words = []
    for word, count in word_counts.items():
        score = count

        if word in {
            "accueil", "administratif", "administrative", "bureautique",
            "archivage", "secretariat", "documents", "planning",
            "stocks", "stock", "saisie", "client", "communication",
            "logistique", "vente", "support", "web", "numerique"
        }:
            score += 2

        useful_single_words.append((word, score))

    useful_single_words.sort(key=lambda x: (-x[1], x[0]))

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


def topics_to_skills(topics: List[str]) -> List[str]:
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
            skill = topic.capitalize()

        skills.append(skill)

    unique_skills = []
    seen = set()

    for s in skills:
        key = s.lower()
        if key not in seen:
            seen.add(key)
            unique_skills.append(s)

    return unique_skills[:8]

def infer_sub_family(topics, main_family):
    topics_joined = " ".join(topics).lower()

    # ADMINISTRATIF
    if main_family == "administratif_gestion":
        if any(word in topics_joined for word in ["saisie", "donnee", "excel"]):
            return "Traitement de données"
        if any(word in topics_joined for word in ["accueil", "telephone"]):
            return "Accueil & secrétariat"
        if any(word in topics_joined for word in ["compta", "facturation"]):
            return "Gestion comptable"
        return "Support administratif"

    # COMMUNICATION
    if main_family == "communication_marketing":
        if "reseaux sociaux" in topics_joined:
            return "Communication digitale"
        if "contenu" in topics_joined:
            return "Création de contenu"
        return "Communication générale"

    # LOGISTIQUE
    if main_family == "production_logistique":
        if "stock" in topics_joined:
            return "Gestion de stock"
        return "Opérations logistiques"

    return "Généraliste"

def display_family_label(family):
    if not family:
        return "Inconnu"

    return FAMILY_LABELS.get(
        family,
        family.replace("_", " ").capitalize()
    )


# =========================================================
# 1) IMPORTER LE CV
# =========================================================
st.subheader("1) Importer votre CV")

uploaded = st.file_uploader(
    "Dépose ton CV (PDF, DOCX ou TXT)",
    type=["pdf", "docx", "txt"],
    key="cv_uploader_main"
)

cv_text = ""
topics: List[str] = []
skills: List[str] = []
cv_families: List[str] = []
job_summary = {}
search_queries: List[str] = []
cv_terms_for_inference: List[str] = []
main_job_label = "inconnu"
domain_label = "inconnu"
related_jobs = []
selected_family = st.session_state.get("selected_family")

cv_families = get_top_cv_families(cv_text, top_n=3)
main_family = cv_families[0] if cv_families else "inconnu"

selected_family = st.session_state.get("selected_family")

if selected_family == main_family:
    st.session_state["selected_family"] = None
    selected_family = None
has_user_override = selected_family is not None
direction_family = selected_family if has_user_override else main_family    

if uploaded:
    uploaded.seek(0)
    file_bytes = uploaded.read()

    if not file_bytes:
        st.error("Fichier vide ou illisible. Recharge le CV.")
        st.stop()

    cv_text = to_text(extract_text_from_upload(uploaded.name, file_bytes))

    # ------------------------
    # Reset seulement si nouveau fichier
    # ------------------------
    if (
        "last_uploaded_name" not in st.session_state
        or st.session_state["last_uploaded_name"] != uploaded.name
    ):
        st.session_state["selected_family"] = None
        st.session_state["last_uploaded_name"] = uploaded.name

    # ------------------------
    # Base familles / direction
    # ------------------------
    cv_families = get_top_cv_families(cv_text, top_n=3)
    main_family = cv_families[0] if cv_families else "inconnu"
    secondary_families = cv_families[1:] if len(cv_families) > 1 else []
    detected_families = get_top_cv_families(cv_text, top_n=5)

    selected_family = st.session_state.get("selected_family")

    if selected_family == main_family:
        st.session_state["selected_family"] = None
        selected_family = None

    has_user_override = selected_family is not None
    direction_family = selected_family if has_user_override else main_family

    # ------------------------
    # Extraction thèmes / compétences
    # ------------------------
    cv_terms_for_inference = cv_text.split()

    topics_raw = detect_cv_topics(cv_text)
    topics = [t for t in topics_raw if not is_generic_topic_term(t)]

    if len(topics) < 3:
        topics = topics_raw[:5]

    if len(topics) < 3:
        for t in topics_raw:
            if t not in topics:
                topics.append(t)
            if len(topics) >= 5:
                break

    topics = dedupe_keep_order(topics)
    skills = topics_to_skills(topics)
    sub_family = infer_sub_family(topics, direction_family)

    # ------------------------
    # Résumé métier
    # ------------------------
    job_summary = build_job_inference_summary(
        detected_families=cv_families,
        cv_terms=cv_terms_for_inference,
        top_n=3
    )

    main_job_data = job_summary.get("main_job", {})
    related_jobs = job_summary.get("related_jobs", [])

    if isinstance(main_job_data, dict):
        main_job_label = main_job_data.get("job", "inconnu")
        domain_label = main_job_data.get("domain", "inconnu")
    else:
        main_job_label = main_job_data or "inconnu"
        domain_label = job_summary.get("domain", "inconnu")

    # ------------------------
    # Mots-clés suggérés
    # ------------------------
    keyword_candidates = []

    if sub_family and sub_family != "Généraliste":
        keyword_candidates.append(sub_family)

    if main_job_label and main_job_label != "inconnu" and main_job_label not in keyword_candidates:
        keyword_candidates.append(main_job_label)

    if domain_label and domain_label != "inconnu" and domain_label != main_job_label and domain_label not in keyword_candidates:
        keyword_candidates.append(domain_label)

    if related_jobs:
        first_related = related_jobs[0]
        if isinstance(first_related, dict):
            first_related_label = first_related.get("job", "")
        else:
            first_related_label = str(first_related)

        if first_related_label and first_related_label not in keyword_candidates:
            keyword_candidates.append(first_related_label)

    if not keyword_candidates:
        keyword_candidates = topics[:2]

    new_keywords_value = ", ".join(keyword_candidates[:3])
    st.session_state["suggested_keywords"] = new_keywords_value
    st.session_state["keywords_input"] = new_keywords_value

    search_queries = build_search_queries_from_job_summary(
        job_summary=job_summary,
        topics=topics,
        max_queries=5
    )
    st.session_state["generated_queries"] = search_queries

    # ------------------------
    # Étape 2B.11A — enrichir les requêtes avec la sous-famille
    # ------------------------
    if sub_family and sub_family != "Généraliste":
        enriched_queries = []

        for q in search_queries:
            enriched_queries.append(q)

            q_lower = q.lower()
            sub_lower = sub_family.lower()

            if sub_lower not in q_lower:
                enriched_queries.append(f"{q} {sub_family}")

        search_queries = dedupe_keep_order(enriched_queries)[:5]
        st.session_state["generated_queries"] = search_queries

    # ------------------------
    # AFFICHAGE UI — ordre logique unique
    # ------------------------
    st.success(f"CV importé — {len(cv_text)} caractères")

    with st.expander("Voir le texte extrait"):
        st.write(cv_text)

    st.markdown("### Thèmes dominants détectés dans votre CV")
    if topics:
        cols = st.columns(4)
        for i, t in enumerate(topics[:8]):
            cols[i % 4].info(t)
    else:
        st.write("Aucun thème dominant détecté.")

    if skills:
        st.markdown("### Compétences dominantes estimées")
        for skill in skills:
            st.write(f"• {skill}")

    secondary_labels = [display_family_label(f) for f in secondary_families]
    if secondary_labels:
        st.write("Ton CV montre aussi des éléments en :")
        for label in secondary_labels:
            st.write(f"- {label}")

    st.write(
        "Cette lecture signifie surtout que ton CV présente un axe principal, "
        "mais aussi plusieurs compétences secondaires utiles selon le poste visé."
    )

    if cv_families:
        st.markdown("### Familles métier dominantes détectées")
        for fam_label in format_family_labels(cv_families):
            st.success(fam_label)

    st.markdown("### Lecture de ton profil")
    st.write(
        f"Dominante détectée automatiquement : "
        f"**{display_family_label(main_family)}**"
    )

    if has_user_override:
        st.write(
            f"Réorientation choisie : "
            f"**{display_family_label(selected_family)}**"
        )
    else:
        st.write("Aucune réorientation choisie pour l’instant.")

    if detected_families:
        st.markdown("### Si cette dominante ne te convient pas, choisis une autre direction")
        st.caption(
            "Hephaistos te propose une direction principale, "
            "mais tu peux l’ajuster selon ton objectif."
        )

        family_cols = st.columns(len(detected_families))
        for i, family in enumerate(detected_families):
            with family_cols[i]:
                if st.button(
                    display_family_label(family),
                    key=f"family_btn_{family}_{i}"
                ):
                    st.session_state["selected_family"] = family

    # recalcul après clic possible
    selected_family = st.session_state.get("selected_family")
    if selected_family == main_family:
        st.session_state["selected_family"] = None
        selected_family = None

    has_user_override = selected_family is not None
    direction_family = selected_family if has_user_override else main_family
    sub_family = infer_sub_family(topics, direction_family)

    if has_user_override:
        st.write(
            f"Direction retenue pour l’analyse : "
            f"**{display_family_label(direction_family)}**"
        )
    else:
        st.write(
            f"Analyse actuellement basée sur la dominante détectée : "
            f"**{display_family_label(main_family)}**"
        )

    st.markdown("### Analyse métier du CV")
    st.write(f"Métier principal estimé : {main_job_label}")
    st.write(f"Domaine : {domain_label}")
    st.write(f"Sous-famille détectée : **{sub_family}**")

    secondary_family = cv_families[1] if len(cv_families) > 1 else None
    if secondary_family:
        st.write(
            "Profil secondaire détecté : "
            f"{display_family_label(secondary_family)}"
        )

    if related_jobs:
        st.write("Métiers proches :")
        for job in related_jobs:
            if isinstance(job, dict):
                st.write(f"• {job.get('job', 'inconnu')}")
            else:
                st.write(f"• {job}")
 

# =========================================================
# 2) PHASE 1 — TROUVER DES OFFRES
# =========================================================
st.subheader("2) Phase 1 — Trouver des offres (France Travail)")
st.markdown("### Localisation")

location_query = st.text_input(
    "Code postal, début de code postal, département ou ville",
    value="",
    placeholder="Ex : Paris, 75011, Toulouse...",
    help="Exemples : 75, 75011, Paris, Toulouse"
)

rayon_km = st.slider("Rayon autour du lieu (km)", 0, 100, 10)

selected_commune = None
generated_queries = st.session_state.get("generated_queries", [])

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

if generated_queries:
    st.markdown("### Requêtes suggérées à partir du CV")
    for q in generated_queries:
        st.write(f"• {q}")

keywords = st.text_input(
    "Mots-clés (séparés par virgules)",
    key="keywords_input"
)

days = st.select_slider(
    "Publié depuis",
    VALID_PUBLIEE_DEPUIS,
    value=7
)

max_results = st.selectbox(
    "Nombre d'offres à récupérer (max 150)",
    [50, 100, 150],
    index=0,
)

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
            manual_keywords = [k.strip() for k in keywords.split(",") if k.strip()]
            queries.extend(manual_keywords)

        for q in st.session_state.get("generated_queries", []):
            if q not in queries:
                queries.append(q)

        queries = dedupe_keep_order(queries)

        if not queries:
            st.warning("Aucune requête de recherche disponible.")
        else:
            offers_raw = fetch_offers_multi_queries(
                queries=queries,
                base_params=base_params,
                max_results_per_query=max_results
            )

            st.write(f"Offres récupérées : {len(offers_raw)}")

            scored = []

            for o in offers_raw:
                description = to_text(o.get("text", ""))

                if len(description.strip()) < 50:
                    continue

                result = score_cv_offer(
                    to_text(cv_text),
                    description
                )

                offer_families = get_top_cv_families(description)
                o["offer_families"] = offer_families

                cv_main_family = cv_families[0] if cv_families else None
                offer_main_family = offer_families[0] if offer_families else None

                adjusted_score = result["score"]

                title_text = to_text(o.get("title", "")).lower()
                description_lower = description.lower()

                if cv_main_family and offer_main_family and cv_main_family == offer_main_family:
                    adjusted_score += 12
                elif offer_main_family and offer_main_family in cv_families[:2]:
                    adjusted_score += 6
                elif cv_main_family and offer_main_family and offer_main_family not in cv_families:
                    adjusted_score -= 10

                family_overlap = len(set(cv_families[:3]) & set(offer_families[:3]))
                adjusted_score += family_overlap * 4

                main_job_label_lower = main_job_label.lower()

                if main_job_label_lower and main_job_label_lower in title_text:
                    adjusted_score += 18
                elif main_job_label_lower and main_job_label_lower in description_lower:
                    adjusted_score += 12

                for job in related_jobs:
                    if isinstance(job, dict):
                        related_label = job.get("job", "").lower()
                    else:
                        related_label = str(job).lower()

                    if not related_label:
                        continue

                    if related_label in title_text:
                        adjusted_score += 10
                    elif related_label in description_lower:
                        adjusted_score += 6

                keyword_values = [
                    k.strip().lower()
                    for k in st.session_state.get("keywords_input", "").split(",")
                    if k.strip()
                ]

                for kw in keyword_values:
                    if kw in title_text:
                        adjusted_score += 6
                    elif kw in description_lower:
                        adjusted_score += 3
                                 # Bonus sous-famille
                sub_family_lower = sub_family.lower() if sub_family else ""

                if sub_family_lower and sub_family_lower != "généraliste":
                    if sub_family_lower in title_text:
                        adjusted_score += 8
                    elif sub_family_lower in description_lower:
                        adjusted_score += 5
                    else:
                        sub_family_signals = {
                            "traitement de données": ["saisie", "excel", "données", "data", "base de données", "immatriculation"],
                            "accueil & secrétariat": ["accueil", "standard", "téléphone", "secrétariat", "courrier"],
                            "gestion comptable": ["compta", "comptable", "facturation", "paiement", "écriture"],
                            "support administratif": ["administratif", "classement", "dossier", "gestion"],
                            "communication digitale": ["réseaux sociaux", "social media", "community", "digital"],
                            "création de contenu": ["contenu", "rédaction", "éditorial", "newsletter"],
                            "opérations logistiques": ["logistique", "flux", "préparation", "expédition"],
                            "gestion de stock": ["stock", "inventaire", "magasin", "réception"],
                        }

                        signals = sub_family_signals.get(sub_family_lower, [])
                        signal_hits = sum(
                            1 for signal in signals
                            if signal in title_text or signal in description_lower
                        )

                        if signal_hits >= 2:
                            adjusted_score += 5
                        elif signal_hits == 1:
                            adjusted_score += 2       

                title_has_signal = False

                if main_job_label_lower and main_job_label_lower in title_text:
                    title_has_signal = True
                else:
                    for job in related_jobs:
                        if isinstance(job, dict):
                            related_label = job.get("job", "").lower()
                        else:
                            related_label = str(job).lower()

                        if related_label and related_label in title_text:
                            title_has_signal = True
                            break

                if not title_has_signal and offer_main_family and offer_main_family not in cv_families[:2]:
                    adjusted_score -= 6

                adjusted_score = max(0, min(100, adjusted_score))

                o["score"] = adjusted_score
                o["base_score"] = result["score"]
                o["matched_terms"] = result.get("matched_terms", [])
                o["missing_terms"] = result.get("missing_terms", [])

                scored.append(o)

            scored.sort(key=lambda x: x.get("score", 0), reverse=True)
            scored = scored[:30]

            st.session_state["offers_scored"] = scored

    except Exception as e:
        st.error(f"Erreur lors de la recherche d'offres : {e}")


# =========================================================
# 2b) TOP 30
# =========================================================
offers_scored = st.session_state.get("offers_scored", [])

if offers_scored:
    st.subheader("Top 30 (triées par compatibilité)")

    for i, o in enumerate(offers_scored[:30]):
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


# =========================================================
# 3) COLLER UNE OFFRE
# =========================================================
st.subheader("3) Coller une offre d'emploi (optionnel)")

st.text_area(
    "Texte de l'offre",
    height=180,
    key="offer_text"
)


# =========================================================
# 4) ANALYSER CV vs OFFRE
# =========================================================
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
    score = analysis.get("score", 0)
    interpretation = interpret_score(score)

    coverage = analysis.get("coverage_score", 0)
    bonus = analysis.get("bonus", 0)
    family_bonus = analysis.get("family_bonus", 0)

    st.markdown("### Score de compatibilité")
    st.markdown(f"## {score}/100 — {interpretation}")

    st.caption(
        f"Score basé sur : "
        f"{coverage}% de correspondance des termes, "
        f"+{bonus} bonus expressions, "
        f"+{family_bonus} bonus cohérence métier"
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Forces principales")

        matched_terms = analysis.get("matched_terms", [])
        display_matched_terms = prepare_display_terms(matched_terms, max_items=8)

        if display_matched_terms:
            for term in display_matched_terms:
                st.write(f"- {term}")
        else:
            st.write("Aucune force principale détectée.")

    with col2:
        st.markdown("### Compétences manquantes identifiées")

        missing_competencies = analysis.get("missing_competencies", [])

        visible_missing_competencies = [
            comp for comp in missing_competencies
            if comp.get("concept") != "specifique_metier"
        ]

        if visible_missing_competencies:
            for comp in visible_missing_competencies:
                label = comp.get("label", "Compétence")
                advice = comp.get("advice", "")
                source_terms = comp.get("source_terms", [])

                st.markdown(f"**{label}**")

                if source_terms:
                    st.caption("Termes repérés : " + ", ".join(source_terms[:5]))

                if advice:
                    st.write(advice)

                st.write("")
        else:
            st.write("Aucune compétence manquante interprétée.")

    with st.expander("Voir le détail technique (debug)"):
        st.markdown("#### Détail du score")
        st.write(f"Coverage : {coverage}%")
        st.write(f"Bonus expressions : +{bonus}")
        st.write(f"Bonus familles : +{family_bonus}")

        st.markdown("#### Mots trouvés (brut)")
        raw_matched_terms = analysis.get("matched_terms", [])

        if raw_matched_terms:
            for term in raw_matched_terms:
                st.write(f"- {term}")
        else:
            st.write("Aucun mot trouvé.")

        st.markdown("#### Mots absents (brut)")
        raw_missing_terms = analysis.get("missing_terms", [])

        if raw_missing_terms:
            for term in raw_missing_terms:
                st.write(f"- {term}")
        else:
            st.write("Aucun mot absent.")

    st.markdown("### Mots forts")
    strong_terms = prepare_display_terms(analysis.get("matched_terms", []), max_items=8)

    if strong_terms:
        st.write(", ".join(strong_terms))
    else:
        st.write("Aucun mot fort détecté.")

    st.markdown("### Suggestions pour améliorer le CV")

    missing_competencies = analysis.get("missing_competencies", [])
    suggestions = build_cv_suggestions_from_competencies(missing_competencies)

    if suggestions:
        for suggestion in suggestions:
            st.write(f"- {suggestion}")
    else:
        st.write("Aucune suggestion générée.")