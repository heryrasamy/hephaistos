import re
import unicodedata
from collections import Counter
from typing import List

import streamlit as st

from cv_extract import extract_text_from_upload
from matching_simple import score_cv_offer, STOPWORDS, extract_terms
from job_inference import (
    build_job_inference_summary,
    build_search_queries_from_job_summary,
    get_top_cv_families,
)
from offers_phase1 import fetch_offers_multi_queries
from opportunity_rules import build_realistic_opportunity_summary
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

if "selected_family" not in st.session_state:
    st.session_state["selected_family"] = None

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
    "production": "Production & Fabrication",
    "maintenance": "Maintenance & Réparation",
    "logistique": "Logistique & Transport",
    "batiment": "Construction & Bâtiment",
    "technique_installation": "Technique & Installation",
    "analyse_pilotage": "Analyse & Pilotage",
    "pedagogie_formation": "Pédagogie & Formation",
    "social_accompagnement": "Social & Accompagnement",
    "securite_protection": "Sécurité & Protection",
    "creation_artistique": "Création & Artistique",
    "hotellerie_restauration": "Hôtellerie & Restauration",
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
        c
        for c in unicodedata.normalize("NFKD", s or "")
        if not unicodedata.combining(c)
    )


def _normalize_local(text: str) -> str:
    text = (text or "").lower()
    text = _strip_accents_local(text)
    text = re.sub(r"[/|\\,_;:()\[\]{}]+", "", text)
    text = re.sub(r"[-'']+", "", text)
    text = re.sub(r"[^a-z0-9\\s]+", " ", text)
    text = re.sub(r"\\s+", " ", text).strip()
    return text


def remove_redundant_terms(terms: list[str]) -> list[str]:
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
        "agent",
        "profil",
        "poste",
        "travail",
        "mission",
        "metier",
        "qualites",
        "qualite",
        "organisation",
        "adaptation",
        "agenda",
        "experience",
        "competence",
        "formation",
        "service",
    }
    if any(w in generic_words for w in words):
        return False

    if any(len(w) < 3 for w in words):
        return False

    return True


def prepare_display_terms(terms: list[str], max_items: int = 8) -> list[str]:
    cleaned = [t for t in terms if is_clean_term(t)]
    reduced = remove_redundant_terms(cleaned)
    return reduced[:max_items]


def interpret_score(score: int) -> str:
    if score < 40:
        return "Correspondance faible"
    if score < 60:
        return "Correspondance partielle"
    if score < 80:
        return "Bonne correspondance"
    return "Très bonne correspondance"


def build_cv_suggestions_from_competencies(
    missing_competencies: list[dict],
) -> list[str]:
    suggestions = []

    for comp in missing_competencies:
        concept = comp.get("concept")
        advice = comp.get("advice", "")

        if concept == "specifique_metier":
            continue

        if concept == "organisation_coordination":
            suggestions.append(
                "Ajoute ou reformule une expérience montrant la planification,"
                " la coordination ou le suivi d'activités."
            )
        elif concept == "suivi_analyse_donnees":
            suggestions.append(
                "Mets en avant l’utilisation d’outils comme Excel,"
                " reporting ou tableaux de bord avec des exemples concrets."
            )
        elif concept == "management":
            suggestions.append(
                "Si tu as encadré ou coordonné des personnes,"
                " mentionne-le explicitement avec des résultats ou responsabilités."
            )
        elif concept == "relation_client":
            suggestions.append(
                "Ajoute des exemples concrets de relation client :"
                " accueil, conseil, suivi ou gestion de demandes."
            )
        elif concept == "communication":
            suggestions.append(
                "Décris précisément tes actions de communication :"
                " contenus créés, réseaux utilisés, objectifs atteints."
            )
        elif concept == "outils_bureautiques":
            suggestions.append(
                "Précise les outils bureautiques maîtrisés (Word, Excel, PowerPoint)"
                " et leur usage concret."
            )
        elif concept == "outils_techniques":
            suggestions.append(
                "Indique clairement les outils ou technologies utilisés ainsi que ton niveau de maîtrise."
            )
        elif concept == "logistique_stock":
            suggestions.append(
                "Ajoute des expériences liées à la gestion de stock, réception,"
                " inventaire ou flux logistiques."
            )
        elif concept == "qualite_conformite":
            suggestions.append(
                "Mentionne les procédures, contrôles qualité ou normes que tu as appliqués."
            )
        elif concept == "soft_skills":
            suggestions.append(
                "Ajoute un exemple concret illustrant ta rigueur, ton autonomie"
                " ou ton travail en équipe."
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
        "le",
        "la",
        "les",
        "de",
        "des",
        "du",
        "un",
        "une",
        "et",
        "ou",
        "mais",
        "donc",
        "or",
        "ni",
        "car",
        "dans",
        "avec",
        "pour",
        "par",
        "sur",
        "sous",
        "en",
        "au",
        "aux",
        "ce",
        "cet",
        "cette",
        "ces",
        "qui",
        "que",
        "quoi",
        "dont",
        "comme",
        "ainsi",
        "tres",
        "plus",
        "moins",
        "bien",
        "depuis",
        "vers",
        "chez",
        "entre",
        "afin",
    }

    generic_verbs = {
        "etre",
        "avoir",
        "faire",
        "mettre",
        "prendre",
        "donner",
        "realiser",
        "participer",
        "effectuer",
        "travailler",
        "rejoindre",
        "developper",
        "creer",
        "suivre",
        "animer",
        "gerer",
        "coordonner",
        "rediger",
        "produire",
        "assurer",
        "accompagner",
        "contribuer",
    }

    generic_adjectives = {
        "bon",
        "bonne",
        "fort",
        "forte",
        "grand",
        "grande",
        "nouveau",
        "nouvelle",
        "determine",
        "determinee",
        "proactif",
        "proactive",
        "ingenieux",
        "ingenieuse",
        "polyvalent",
        "polyvalente",
        "autonome",
        "rigoureux",
        "rigoureuse",
        "curieux",
        "curieuse",
        "motive",
        "motivee",
        "dynamique",
        "adaptable",
    }

    months = {
        "janvier",
        "fevrier",
        "mars",
        "avril",
        "mai",
        "juin",
        "juillet",
        "aout",
        "septembre",
        "octobre",
        "novembre",
        "decembre",
    }

    location_words = {
        "paris",
        "france",
        "toulouse",
        "marseille",
        "lyon",
        "lille",
        "bordeaux",
        "nantes",
        "rennes",
        "tananarive",
    }

    weak_words = {
        "poste",
        "profil",
        "mission",
        "missions",
        "projet",
        "projets",
        "experience",
        "experiences",
        "activite",
        "activites",
        "realisation",
        "realisations",
        "participation",
        "domaine",
        "structure",
        "entreprise",
        "societe",
        "service",
        "equipe",
        "equipes",
        "mise",
        "jour",
        "role",
        "direction",
        "candidature",
        "diplome",
        "diplomes",
        "reference",
        "references",
        "outil",
        "outils",
        "travail",
        "secteur",
        "cadre",
        "competence",
        "competences",
        "formation",
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
        tok
        for tok in text.split()
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
            "accueil",
            "administratif",
            "administrative",
            "bureautique",
            "archivage",
            "secretariat",
            "documents",
            "planning",
            "stocks",
            "stock",
            "saisie",
            "client",
            "communication",
            "logistique",
            "vente",
            "support",
            "web",
            "numerique",
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
        "excel",
        "word",
        "powerpoint",
        "outlook",
        "sap",
        "salesforce",
        "wordpress",
        "canva",
        "photoshop",
        "illustrator",
        "indesign",
        "premiere",
        "google analytics",
        "sql",
        "python",
        "java",
        "html",
        "css",
        "javascript",
        "typescript",
        "php",
        "react",
        "angular",
        "vue",
        "docker",
        "jira",
        "trello",
        "figma",
        "autocad",
        "power bi",
        "tableau",
        "qlik",
        "drupal",
    }

    language_terms = {
        "anglais",
        "espagnol",
        "allemand",
        "italien",
        "portugais",
        "arabe",
        "chinois",
        "japonais",
        "russe",
    }

    management_terms = {
        "gestion",
        "coordination",
        "pilotage",
        "organisation",
        "suivi",
        "planification",
        "encadrement",
        "budget",
    }

    analysis_terms = {
        "analyse",
        "donnees",
        "data",
        "reporting",
        "tableau de bord",
        "indicateur",
        "analytics",
        "kpi",
    }

    communication_terms = {
        "communication",
        "contenu",
        "contenus",
        "redaction",
        "newsletter",
        "reseaux sociaux",
        "site internet",
        "community management",
        "marketing",
    }

    client_terms = {
        "client",
        "relation client",
        "vente",
        "accueil",
        "support",
        "conseil",
        "service client",
    }

    production_terms = {
        "podcast",
        "video",
        "montage",
        "audio",
        "photo",
        "wireframe",
        "storyboard",
        "creation",
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

    for skill in skills:
        key = skill.lower()
        if key not in seen:
            seen.add(key)
            unique_skills.append(skill)

    return unique_skills[:8]


def infer_sub_family(topics, main_family):
    topics_joined = " ".join(topics).lower()

    if main_family == "administratif_gestion":
        if any(word in topics_joined for word in ["saisie", "donnee", "excel"]):
            return "Traitement de données"
        if any(word in topics_joined for word in ["accueil", "telephone"]):
            return "Accueil & secrétariat"
        if any(word in topics_joined for word in ["compta", "facturation"]):
            return "Gestion comptable"
        return "Support administratif"

    if main_family == "communication_marketing":
        if "reseaux sociaux" in topics_joined:
            return "Communication digitale"
        if "contenu" in topics_joined:
            return "Création de contenu"
        return "Communication générale"

    if main_family in {"production_logistique", "logistique", "production"}:
        if "stock" in topics_joined:
            return "Gestion de stock"
        return "Opérations logistiques"

    return "Généraliste"


def display_family_label(family):
    if not family:
        return "Inconnu"
    return FAMILY_LABELS.get(family, family.replace("_", " ").capitalize())


# =========================================================
# 1) IMPORTER LE CV
# =========================================================
st.subheader("1) Importer votre CV")

uploaded = st.file_uploader(
    "Dépose ton CV (PDF, DOCX ou TXT)",
    type=["pdf", "docx", "txt"],
    key="cv_uploader_main",
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
final_family_direction = direction_family
secondary_families = []
detected_families = []
sub_family = "Généraliste"

if uploaded:
    uploaded.seek(0)
    file_bytes = uploaded.read()

    if not file_bytes:
        st.error("Fichier vide ou illisible. Recharge le CV.")
        st.stop()

    cv_text = to_text(extract_text_from_upload(uploaded.name, file_bytes))

    if (
        "last_uploaded_name" not in st.session_state
        or st.session_state["last_uploaded_name"] != uploaded.name
    ):
        st.session_state["selected_family"] = None
        st.session_state["last_uploaded_name"] = uploaded.name

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
    final_family_direction = direction_family

    cv_terms_for_inference = cv_text.split()

    topics_raw = detect_cv_topics(cv_text)
    topics = [topic for topic in topics_raw if not is_generic_topic_term(topic)]

    if len(topics) < 3:
        topics = topics_raw[:5]

    if len(topics) < 3:
        for topic in topics_raw:
            if topic not in topics:
                topics.append(topic)
            if len(topics) >= 5:
                break

    topics = dedupe_keep_order(topics)
    skills = topics_to_skills(topics)
    sub_family = infer_sub_family(topics, direction_family)

    job_summary = build_job_inference_summary(
        detected_families=cv_families,
        cv_terms=cv_terms_for_inference,
        top_n=3,
    )

    main_job_data = job_summary.get("main_job", {})
    related_jobs = job_summary.get("related_jobs", [])

    if isinstance(main_job_data, dict):
        main_job_label = main_job_data.get("job", "inconnu")
        domain_label = main_job_data.get("domain", "inconnu")
    else:
        main_job_label = main_job_data or "inconnu"
        domain_label = job_summary.get("domain", "inconnu")

    keyword_candidates = []

    if sub_family and sub_family != "Généraliste":
        keyword_candidates.append(sub_family)

    if (
        main_job_label
        and main_job_label != "inconnu"
        and main_job_label not in keyword_candidates
    ):
        keyword_candidates.append(main_job_label)

    if (
        domain_label
        and domain_label != "inconnu"
        and domain_label != main_job_label
        and domain_label not in keyword_candidates
    ):
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
        job_summary,
        topics,
        max_queries=5,
    )

    main_family = cv_families[0] if cv_families else None
    selected_family = st.session_state.get("selected_family")
    final_family_direction = selected_family if selected_family else main_family

    if final_family_direction:
        search_queries = [final_family_direction] + search_queries

    st.session_state["generated_queries"] = search_queries

    if sub_family and sub_family != "Généraliste":
        enriched_queries = []

        for query in search_queries:
            enriched_queries.append(query)

            query_lower = query.lower()
            sub_family_lower = sub_family.lower()

            if sub_family_lower not in query_lower:
                enriched_queries.append(f"{query} {sub_family}")

        search_queries = dedupe_keep_order(enriched_queries)[:5]
        st.session_state["generated_queries"] = search_queries

    st.success(f"CV importé — {len(cv_text)} caractères")

    with st.expander("Voir le texte extrait"):
        st.write(cv_text)

    st.markdown("### Thèmes dominants détectés dans votre CV")
    if topics:
        cols = st.columns(4)
        for i, topic in enumerate(topics[:8]):
            cols[i % 4].info(topic)
    else:
        st.write("Aucun thème dominant détecté.")

    if skills:
        st.markdown("### Compétences dominantes estimées")
        for skill in skills:
            st.write(f"• {skill}")

    if cv_families:
        st.markdown("### Choisir une direction métier")

    main_family = cv_families[0] if cv_families else None
    selected_family = st.session_state.get("selected_family")
    final_family_direction = selected_family if selected_family else main_family

    direction_options = dedupe_keep_order(cv_families + detected_families)

    if direction_options:
        if selected_family in direction_options:
            selected_index = direction_options.index(selected_family)
        else:
            selected_index = 0

        selected_family = st.selectbox(
            "Tu peux garder la direction proposée ou en choisir une autre :",
            options=direction_options,
            index=selected_index,
        )

        st.session_state["selected_family"] = selected_family

    current_family = st.session_state.get("selected_family") or main_family

    st.caption(f"Dominante détectée dans le CV : {display_family_label(main_family)}")

    st.caption(f"Direction actuellement choisie : {display_family_label(current_family)}")

    secondary_labels = [display_family_label(family) for family in secondary_families]
    if secondary_labels:
        st.write("Ton CV montre aussi des éléments en :")
        for label in secondary_labels:
            st.write(f"- {label}")

    st.write(
        "Cette lecture signifie surtout que"
        " ton CV présente un axe principal, "
        "mais aussi plusieurs compétences"
        " secondaires utiles selon le poste visé."
    )

    if cv_families:
        st.markdown("### Familles métier dominantes détectées")
        for fam_label in format_family_labels(cv_families):
            st.success(fam_label)

        st.markdown("### Lecture de ton profil")

    st.write(
        f"Dominante détectée automatiquement : **{display_family_label(main_family)}**"
    )

    selected_family = st.session_state.get("selected_family")
    has_user_override = selected_family is not None and selected_family != main_family

    if has_user_override:
        st.write(
            f"Réorientation choisie : **{display_family_label(selected_family)}**"
        )
        st.info(
            "Tu explores une nouvelle direction."
            " Les résultats sont orientés par ton objectif,"
            " tout en restant cohérents avec ton profil."
        )
    else:
        st.write("Aucune réorientation choisie pour l’instant.")

    if detected_families:
        st.markdown(
            "### Hephaistos détecte une direction principale,"
            " mais tu peux aussi explorer d’autres orientations réalistes"
        )
        st.caption(
            "La direction choisie guide la recherche. Ton CV sert ensuite de filtre de réalité."
        )

        family_cols = st.columns(len(detected_families))
        for i, family in enumerate(detected_families):
            with family_cols[i]:
                if st.button(
                    display_family_label(family),
                    key=f"family_btn_{family}_{i}",
                ):
                    st.session_state["selected_family"] = family

    selected_family = st.session_state.get("selected_family")
    if selected_family == main_family:
        st.session_state["selected_family"] = None
        selected_family = None

    has_user_override = selected_family is not None
    direction_family = selected_family if has_user_override else main_family
    final_family_direction = direction_family
    sub_family = infer_sub_family(topics, direction_family)

    if has_user_override:
        st.write(
            f"Direction retenue pour l’analyse : **{display_family_label(direction_family)}**"
        )
    else:
        st.write(
            f"Analyse actuellement basée sur la dominante détectée : **{display_family_label(main_family)}**"
        )

    st.markdown("### Analyse de trajectoire")
    st.write(f"Direction choisie : **{display_family_label(direction_family)}**")
    st.write(f"Ce que le CV apporte déjà : {main_job_label}")
    st.write(f"Domaine détecté : {domain_label}")
    st.write(f"Ce qui structure encore le profil : **{sub_family}**")

    secondary_family = cv_families[1] if len(cv_families) > 1 else None
    if secondary_family:
        st.write(
            f"Profil secondaire détecté : {display_family_label(secondary_family)}"
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
    help="Exemples : 75, 75011, Paris, Toulouse",
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
                options=[format_commune_label(c) for c in suggestions],
            )

            selected_commune = next(
                c for c in suggestions if format_commune_label(c) == selected_label
            )

            st.caption(
                f"Commune sélectionnée : {selected_commune['libelle']} | CP {selected_commune['codePostal']}"
            )
        else:
            st.warning("Aucune commune trouvée pour cette saisie.")

    except Exception as e:
        st.error(f"Erreur référentiel communes : {e}")

keywords = st.text_input("Mots-clés (séparés par virgules)", key="keywords_input")

days = st.select_slider("Publié depuis", VALID_PUBLIEE_DEPUIS, value=7)

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
        selected_family = st.session_state.get("selected_family")
        cv_main_family_for_mode = cv_families[0] if cv_families else None

        family_seed_queries = {
            "Production": [
                "agent de production",
                "responsable de production",
                "technicien de production",
            ],
            "Maintenance": [
                "technicien de maintenance",
                "agent de maintenance",
                "maintenance industrielle",
            ],
            "Administratif & Gestion": [
                "assistant administratif",
                "gestionnaire administratif",
                "assistant de gestion",
            ],
            "Communication & Marketing": [
                "chargé de communication",
                "assistant communication",
                "community manager",
            ],
            "Analyse pilotage": [
                "assistant contrôle de gestion",
                "chargé d'études",
                "analyste de données",
            ],
        }

        if selected_family:
            selected_family_queries = family_seed_queries.get(
                selected_family,
                [selected_family],
            )
            queries.extend(selected_family_queries)

        if keywords.strip():
            manual_keywords = [k.strip() for k in keywords.split(",") if k.strip()]
            queries.extend(manual_keywords)

        if not selected_family:
            for query in st.session_state.get("generated_queries", []):
                if query not in queries:
                    queries.append(query)

        queries = dedupe_keep_order(queries)
        st.session_state["last_search_queries"] = queries

        if not queries:
            st.warning("Aucune requête de recherche disponible.")
        else:
            offers_raw = fetch_offers_multi_queries(
                queries=queries,
                base_params=base_params,
                max_results_per_query=max_results,
            )

            st.write(f"Offres récupérées : {len(offers_raw)}")

            direction_offer_filters = {
                "Production": [
                    "production",
                    "ordonnancement",
                    "lancement",
                    "fabrication",
                    "industrie",
                    "industriel",
                ],
                "Maintenance": [
                    "maintenance",
                    "technicien de maintenance",
                    "maintenance industrielle",
                    "réparation",
                    "dépannage",
                ],
                "Administratif & Gestion": [
                    "assistant administratif",
                    "administratif",
                    "gestionnaire",
                    "assistant de direction",
                    "assistant de gestion",
                    "scolarité",
                    "gestion",
                ],
                "Communication & Marketing": [
                    "communication",
                    "marketing",
                    "community manager",
                    "réseaux sociaux",
                    "digital",
                    "contenu",
                    "événementiel",
                    "évènementiel",
                    "relation presse",
                ],
                "Analyse pilotage": [
                    "contrôle de gestion",
                    "controle de gestion",
                    "analyste",
                    "analyse",
                    "reporting",
                    "tableau de bord",
                    "données",
                    "donnees",
                    "pilotage",
                    "études",
                    "etudes",
                ],
            }

            selected_family = st.session_state.get("selected_family")
            family_filter_terms = direction_offer_filters.get(selected_family, [])

            if family_filter_terms:
                filtered_offers = []

                for offer in offers_raw:
                    offer_title_text = to_text(offer.get("title", "")).lower()
                    offer_description_text = to_text(offer.get("text", "")).lower()
                    offer_search_text = (
                        f"{offer_title_text} {offer_description_text}"
                    )

                    if any(term in offer_search_text for term in family_filter_terms):
                        filtered_offers.append(offer)

                if filtered_offers:
                    offers_raw = filtered_offers
                    st.write(
                        f"Offres après filtrage direction métier : {len(offers_raw)}"
                    )

        scored = []
        is_reorientation_mode = (
            st.session_state.get("selected_family") is not None
            and st.session_state.get("selected_family") != main_family
        )

        for offer in offers_raw:
            description = to_text(offer.get("text", ""))

            if len(description.strip()) < 50:
                continue

            cv_text_for_scoring = to_text(cv_text)

            if final_family_direction:
                direction_label = "Direction métier prioritaire :"
                cv_text_for_scoring = (
                    f"{cv_text_for_scoring}\n\n"
                    f"{direction_label} {final_family_direction}"
                )

            result = score_cv_offer(cv_text_for_scoring, description)

            cv_text_clean = to_text(cv_text)
            offer_title_clean = to_text(offer.get("title", ""))
            offer_text_clean = description

            score_value = int(result.get("score", 0) or 0)
            matched_terms = result.get("matched_terms", []) or []
            missing_terms = result.get("missing_terms", []) or []
            cv_terms = extract_terms(cv_text_clean)
            offer_terms = extract_terms(offer_text_clean)

            realistic_summary = build_realistic_opportunity_summary(
                score=score_value,
                cv_text=cv_text_clean,
                offer_title=offer_title_clean,
                offer_text=offer_text_clean,
                cv_terms=cv_terms,
                offer_terms=offer_terms,
            )

            offer_families: list[str] = get_top_cv_families(description)
            offer["offer_families"] = offer_families

            selected_family = st.session_state.get("selected-family")
            cv_main_family_for_scoring = (
                selected_family
                if selected_family
                else (cv_families[0] if cv_families else None)
            )

            cv_families_for_scoring = list(cv_families)
            if selected_family and selected_family not in cv_families_for_scoring:
                cv_families_for_scoring.insert(0, selected_family)

            offer_main_family = offer_families[0] if offer_families else None

            adjusted_score = score_value

            is_reorientation_mode = False
            if selected_family and cv_main_family_for_mode:
                if selected_family != cv_main_family_for_mode:
                    is_reorientation_mode = True

                if is_reorientation_mode:
                    adjusted_score = int(score_value * 0.7)
                if selected_family and offer_main_family:
                    if selected_family == offer_main_family:
                        adjusted_score += 20
                    elif offer_main_family in cv_families_for_scoring[:3]:
                        adjusted_score += 10

            title_text = offer_title_clean.lower()
            description_lower = offer_text_clean.lower()

            if (
                cv_main_family_for_scoring
                and offer_main_family
                and cv_main_family_for_scoring == offer_main_family
            ):
                adjusted_score += 12
            elif (
                offer_main_family
                and offer_main_family in cv_families_for_scoring[:2]
            ):
                adjusted_score += 6
            elif (
                cv_main_family_for_scoring
                and offer_main_family
                and offer_main_family not in cv_families_for_scoring
            ):
                adjusted_score -= 10

            family_overlap = len(
                set(cv_families_for_scoring[:3]) & set(offer_families[:3])
            )
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
                keyword.strip().lower()
                for keyword in st.session_state.get("keywords_input", "").split(",")
                if keyword.strip()
            ]

            for keyword in keyword_values:
                if keyword in title_text:
                    adjusted_score += 6
                elif keyword in description_lower:
                    adjusted_score += 3

            sub_family_lower = sub_family.lower() if sub_family else ""
            if sub_family_lower and sub_family_lower != "généraliste":
                if sub_family_lower in title_text:
                    adjusted_score += 8
                elif sub_family_lower in description_lower:
                    adjusted_score += 5
                else:
                    sub_family_signals = {
                        "traitement de données": [
                            "saisie",
                            "excel",
                            "données",
                            "data",
                            "base de données",
                            "immatriculation",
                        ],
                        "accueil & secrétariat": [
                            "accueil",
                            "standard",
                            "téléphone",
                            "secrétariat",
                            "courrier",
                        ],
                        "gestion comptable": [
                            "compta",
                            "comptable",
                            "facturation",
                            "paiement",
                            "écriture",
                        ],
                        "support administratif": [
                            "administratif",
                            "classement",
                            "dossier",
                            "gestion",
                        ],
                        "communication digitale": [
                            "réseaux sociaux",
                            "social media",
                            "community",
                            "digital",
                        ],
                        "création de contenu": [
                            "contenu",
                            "rédaction",
                            "éditorial",
                            "newsletter",
                        ],
                        "opérations logistiques": [
                            "logistique",
                            "flux",
                            "préparation",
                            "expédition",
                        ],
                        "gestion de stock": [
                            "stock",
                            "inventaire",
                            "magasin",
                            "réception",
                        ],
                    }

                    signals = sub_family_signals.get(sub_family_lower, [])
                    signal_hits = sum(
                        1
                        for signal in signals
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

            if (
                not title_has_signal
                and offer_main_family
                and offer_main_family not in cv_families_for_scoring[:2]
            ):
                adjusted_score -= 6

            adjusted_score = max(0, min(100, adjusted_score))

            offer["score"] = adjusted_score
            offer["base_score"] = score_value
            offer["matched_terms"] = matched_terms
            offer["missing_terms"] = missing_terms
            offer["realistic_opportunity"] = realistic_summary

            keep_offer = True
            if is_reorientation_mode:
                if selected_family and offer_main_family:
                    if selected_family != offer_main_family:
                        if offer_main_family not in cv_families_for_scoring[:2]:
                            keep_offer = False

                if keep_offer:
                    has_min_score = adjusted_score >= 35
                    has_common_terms = len(matched_terms) > 0
                    has_family_link = (
                        offer_main_family in cv_families_for_scoring
                        if offer_main_family
                        else False
                    )

                    if not (
                        has_min_score or has_common_terms or has_family_link
                    ):
                        keep_offer = False

            if keep_offer:
                scored.append(offer)

        scored.sort(key=lambda x: x.get("score", 0), reverse=True)
        scored = scored[:30]
        st.session_state["offers_scored"] = scored

    except Exception as e:
        st.error(f"erreur lors des recherche d'offres:{e}")


# =========================================================
# 2b) TOP 30
# =========================================================
offers_scored = st.session_state.get("offers_scored", [])

if offers_scored:
    st.subheader("Top 30 (triées par compatibilité)")

    for i, offer in enumerate(offers_scored[:30]):
        title = to_text(offer.get("title", "Sans titre"))
        company = to_text(offer.get("company", ""))
        location = to_text(offer.get("location", ""))
        url = to_text(offer.get("url", ""))
        score = offer.get("score", 0)

        realistic = offer.get("realistic_opportunity", {}) or {}
        realistic_verdict = realistic.get("verdict", "à étudier")
        realistic_explanation = realistic.get("explanation", "")

        st.write(f"**{score}/100 — {title}**")
        st.caption(f"Opportunité réaliste : {realistic_verdict}")

        if realistic_explanation:
            st.write(f"Pourquoi : {realistic_explanation}")

        if company:
            st.write(f"**Entreprise :** {company}")

        if location:
            st.write(f"**Lieu :** {location}")

        if url:
            st.markdown(f"**Lien pour postuler :** [Ouvrir l'annonce]({url})")

        if st.button("Utiliser cette offre", key=f"use_offer_{i}"):
            st.session_state["offer_text"] = to_text(offer.get("text", ""))
            st.session_state["selected_offer_meta"] = {
                "title": title,
                "company": company,
                "location": location,
                "url": url,
                "score": offer.get("score", 0),
                "base_score": offer.get("base_score", 0),
                "realistic_opportunity": realistic,
            }

        with st.expander("Voir description", expanded=False):
            st.write(to_text(offer.get("text", "Description non disponible")))


# =========================================================
# 3) COLLER UNE OFFRE
# =========================================================
st.subheader("3) Coller une offre d'emploi (optionnel)")
st.text_area("Texte de l'offre", height=180, key="offer_text")


# =========================================================
# 4) ANALYSER CV vs OFFRE
# =========================================================
st.subheader("4) Analyse de correspondance")

offer_text = st.session_state.get("offer_text", "")
selected_offer_meta = st.session_state.get("selected_offer_meta", {}) or {}

if st.button("Analyser CV vs Offre"):
    if not cv_text:
        st.warning("Importer un CV d'abord.")
    elif not offer_text.strip():
        st.warning("Aucune offre fournie.")
    else:
        result = score_cv_offer(to_text(cv_text), to_text(offer_text))
        st.session_state["last_analysis"] = result

analysis = st.session_state.get("last_analysis")

if analysis:
    score = analysis.get("score", 0)
    interpretation = interpret_score(score)

    coverage = analysis.get("coverage_score", 0)
    bonus = analysis.get("bonus", 0)
    family_bonus = analysis.get("family_bonus", 0)

    selected_offer_score = selected_offer_meta.get("score")
    selected_offer_base_score = selected_offer_meta.get("base_score")
    selected_realistic = selected_offer_meta.get("realistic_opportunity", {}) or {}
    selected_realistic_verdict = selected_realistic.get("verdict", "à étudier")
    selected_realistic_explanation = selected_realistic.get("explanation", "")

    cv_lower = to_text(cv_text).lower()

    experience_markers = [
        "ans",
        "année",
        "ans d'expérience",
        "expérience de",
        "responsable",
        "gestion",
        "pilotage",
        "encadrement",
    ]
    junior_markers = ["stage", "alternance", "débutant", "junior"]

    if any(word in cv_lower for word in junior_markers):
        profile_level = "junior"
    elif any(word in cv_lower for word in experience_markers):
        profile_level = "experienced"
    else:
        profile_level = "intermediate"

    st.markdown("### Ta position pour cette offre")

    if selected_offer_score is not None:
        st.markdown(
            f"**Cette offre semble globalement adaptée : {selected_offer_score}/100**"
        )

    st.markdown(
        f"**Ce que ton CV montre dans cette annonce : {score}/100 — {interpretation}**"
    )

    selected_family = st.session_state.get("selected_family")
    if selected_family:
        st.caption(
            "Cette lecture combine la direction choisie et les éléments réellement visibles dans ton CV."
        )
    elif selected_offer_score is not None:
        st.caption(
            "Cette offre remonte parce qu’elle semble cohérente avec ton profil."
            " Le score ci-dessous regarde plus strictement ce qui apparaît réellement"
            " dans ton CV par rapport à l’annonce."
        )

    if selected_offer_base_score is not None:
        st.caption(
            f"Score de départ avant ajustements métier : {selected_offer_base_score}/100"
        )

    if selected_realistic_verdict:
        st.write(f"Conseil de positionnement : {selected_realistic_verdict}")

    if selected_realistic_explanation:
        st.write(f"Pourquoi : {selected_realistic_explanation}")

    st.markdown("### Conseil rapide")

    positioning_advice = selected_realistic_verdict
    direction_text = (
        f"dans la direction \"{selected_family}\""
        if selected_family
        else "par rapport à ton profil"
    )

    if positioning_advice in ["très réaliste", "réaliste"]:
        st.success(f"Tu peux postuler : {direction_text}, cette offre est cohérente.")
    elif positioning_advice in ["accessible"]:
        st.info(
            f"Tu peux tenter ta chance : {direction_text}, ton profil reste crédible avec un CV ajusté."
        )
    elif positioning_advice in ["exploratoire"]:
        st.warning(
            f"Cette piste peut se tenter : {direction_text}, il manque encore des éléments visibles dans ton CV."
        )
    elif positioning_advice in ["possible avec réserve"]:
        st.warning(
            f"Cette offre peut se tenter : {direction_text}, mais un point concret peut freiner ta candidature."
        )
    else:
        st.error(
            f"{direction_text.capitalize()}, cette offre paraît encore trop éloignée."
        )

    st.markdown("#### Ce que ça veut dire concrètement")
    if positioning_advice in ["très réaliste", "réaliste"]:
        st.write(
            f"{direction_text.capitalize()}, ton profil correspond bien à ce type de poste."
            " Les recruteurs devraient comprendre rapidement ta candidature."
        )
    elif positioning_advice in ["accessible"]:
        st.write(
            f"{direction_text.capitalize()}, tu n’as pas tous les éléments, mais ton profil"
            " reste cohérent avec l’offre."
        )
    elif positioning_advice in ["exploratoire"]:
        st.write(
            f"{direction_text.capitalize()}, ton profil s’en rapproche, mais l’annonce attend"
            " des éléments peu visibles dans ton CV."
        )
    elif positioning_advice in ["possible avec réserve"]:
        st.write(
            f"{direction_text.capitalize()}, un point concret peut poser problème"
            " (mobilité, expérience, compétences spécifiques)."
        )
    else:
        st.write(
            f"{direction_text.capitalize()}, l’offre reste encore trop éloignée de ton profil actuel."
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
            comp
            for comp in missing_competencies
            if comp.get("concept") != "specifique_metier"
        ]

        if visible_missing_competencies:
            for comp in visible_missing_competencies:
                label = comp.get("label", "Compétence")
                advice = comp.get("advice", "")
                source_terms = comp.get("source_terms", [])

                st.markdown(f"**{label}**")

                if source_terms:
                    st.caption("Repéré dans l’annonce : " + ", ".join(source_terms[:5]))

                suggestion_text = ""
                label_lower = label.lower()

                if "relation" in label_lower:
                    if profile_level == "junior":
                        suggestion_text = (
                            "Accueil des clients lors de stages ou missions, gestion des demandes simples"
                        )
                    elif profile_level == "experienced":
                        suggestion_text = (
                            "Gestion de la relation client, suivi des demandes et amélioration de la satisfaction"
                        )
                    else:
                        suggestion_text = (
                            "Accueil des clients, traitement des demandes et suivi des dossiers"
                        )
                elif "bureautique" in label_lower:
                    if profile_level == "junior":
                        suggestion_text = (
                            "Utilisation basique de Word et Excel pour saisir et organiser des données"
                        )
                    elif profile_level == "experienced":
                        suggestion_text = (
                            "Maîtrise avancée des outils bureautiques (Excel, reporting, tableaux de suivi)"
                        )
                    else:
                        suggestion_text = (
                            "Utilisation de Word, Excel et outils bureautiques pour le suivi et la gestion des données"
                        )
                elif "analyse" in label_lower or "suivi" in label_lower:
                    if profile_level == "junior":
                        suggestion_text = (
                            "Participation au suivi d’activité et mise à jour de tableaux simples"
                        )
                    elif profile_level == "experienced":
                        suggestion_text = (
                            "Analyse de données, suivi de performance et reporting régulier"
                        )
                    else:
                        suggestion_text = (
                            "Suivi d’activité, mise à jour de tableaux Excel et reporting simple"
                        )
                elif "qualité" in label_lower or "conformité" in label_lower:
                    suggestion_text = (
                        "Contrôle de conformité, respect des procédures et suivi de la qualité"
                    )
                elif (
                    "organisation" in label_lower
                    or "coordination" in label_lower
                    or "planning" in label_lower
                ):
                    suggestion_text = (
                        "Organisation des tâches, coordination d’activités et suivi de planning"
                    )

                if suggestion_text:
                    st.success(f"À ajouter dans ton CV : {suggestion_text}")

                if advice:
                    st.write(f"Conseil : {advice}")

                st.write("")
        else:
            st.write("Aucune compétence manquante interprétée.")

    with st.expander("Voir le détail technique (debug)"):
        st.markdown("#### Détail du score")
        st.write(f"Coverage : {coverage}%")
        st.write(f"Bonus expressions : +{bonus}")
        st.write(f"Bonus familles : +{family_bonus}")

        if st.checkbox(
            "Afficher les détails techniques avancés",
            key="debug_terms_checkbox",
        ):
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

    raw_strong_terms = prepare_display_terms(
        analysis.get("matched_terms", []),
        max_items=40,
    )

    banned_terms = {
        "direction",
        "entreprise",
        "niveau",
        "mettre",
        "jour",
        "avant",
        "possible",
        "vendredi",
        "lundi",
        "heures",
        "travail",
        "action",
        "missions",
        "seront",
        "gestion",
        "suivi",
        "organisation",
        "communication",
    }

    strong_terms = []
    for term in raw_strong_terms:
        term_clean = term.strip().lower()

        if not term_clean:
            continue
        if term_clean in banned_terms:
            continue
        if len(term_clean) < 4:
            continue
        if any(char.isdigit() for char in term_clean):
            continue
        if len(term_clean.split()) > 3:
            continue

        strong_terms.append(term)

    strong_terms = strong_terms[:8]

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
