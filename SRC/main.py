import re
import unicodedata
from collections import Counter
from typing import List
import streamlit as st
from cv_extract import extract_text_from_upload
from matching_simple import score_cv_offer, STOPWORDS
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


def classify_term(term: str) -> str:
    t = (term or "").lower().strip()

    if not t:
        return "generic"

    language_markers = {
        "anglais", "espagnol", "allemand", "italien", "portugais",
        "arabe", "chinois", "japonais", "russe", "bilingue",
        "toeic", "toefl", "ielts"
    }
    if any(k in t for k in language_markers):
        return "language"

    diploma_markers = {
        "bac", "bachelor", "master", "licence", "bts", "dut", "but",
        "formation", "certification", "certifie", "certifiée",
        "diplome", "diplôm", "titre professionnel", "rncp"
    }
    if any(k in t for k in diploma_markers):
        return "diploma"

    soft_skill_markers = {
        "autonomie", "rigueur", "organisation", "adaptabilite",
        "adaptation", "relationnel", "communication", "ecoute",
        "esprit analyse", "analyse", "proactivite", "initiative",
        "travail equipe", "travail en equipe", "polyvalence",
        "motivation", "dynamisme", "curiosite", "leadership"
    }
    if any(k in t for k in soft_skill_markers):
        return "soft_skill"

    management_markers = {
        "gestion", "coordination", "pilotage", "organisation",
        "suivi", "planification", "planning", "encadrement",
        "management", "manager", "responsable", "supervision",
        "budget", "budgets", "reporting", "chef de projet"
    }
    if any(k in t for k in management_markers):
        return "management"

    client_markers = {
        "client", "clients", "vente", "ventes", "accueil",
        "service", "support", "conseil", "commercial",
        "prospection", "negociation", "fidélisation", "fidelisation",
        "relation client", "satisfaction", "sav"
    }
    if any(k in t for k in client_markers):
        return "client"

    analysis_markers = {
        "analyse", "donnees", "données", "data", "reporting",
        "tableau de bord", "indicateur", "indicateurs",
        "statistique", "statistiques", "analytics", "kpi"
    }
    if any(k in t for k in analysis_markers):
        return "analysis"

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


def suggest_for_term(term: str, category: str) -> str:
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


def build_cv_suggestions(missing_terms: List[str], max_suggestions: int = 6) -> List[str]:
    suggestions = []

    for term in missing_terms[:12]:
        category = classify_term(term)
        suggestion = suggest_for_term(term, category)
        suggestions.append(suggestion)

    unique = []
    seen = set()

    for s in suggestions:
        if s not in seen:
            seen.add(s)
            unique.append(s)

    return unique[:max_suggestions]


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


# =========================================================
# 1) IMPORTER LE CV
# =========================================================
st.subheader("1) Importer votre CV")

uploaded = st.file_uploader(
    "Dépose ton CV (PDF, DOCX ou TXT)",
    type=["pdf", "docx", "txt"],
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

if uploaded:
    file_bytes = uploaded.read()
    cv_text = to_text(extract_text_from_upload(uploaded.name, file_bytes))

    st.success(f"CV importé — {len(cv_text)} caractères")

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

    cv_families = get_top_cv_families(cv_text)
    skills = topics_to_skills(topics)

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

    keyword_candidates = []

    if main_job_label and main_job_label != "inconnu":
        keyword_candidates.append(main_job_label)

    if domain_label and domain_label != "inconnu" and domain_label != main_job_label:
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

with st.expander("Voir le texte extrait"):
    st.write(cv_text)

st.markdown("### Thèmes dominants détectés dans votre CV")
if topics:
    cols = st.columns(4)
    for i, t in enumerate(topics[:8]):
        cols[i % 4].info(t)
else:
    st.write("Aucun thème dominant détecté.")

if cv_families:
    st.markdown("### Familles métier dominantes détectées")
    for fam_label in format_family_labels(cv_families):
        st.success(fam_label)

if skills:
    st.markdown("### Compétences dominantes estimées")
    for skill in skills:
        st.write(f"• {skill}")

if uploaded:
    st.markdown("### Analyse métier du CV")
    st.write(f"Métier principal estimé : {main_job_label}")
    st.write(f"Domaine : {domain_label}")

    secondary_family = cv_families[1] if len(cv_families) > 1 else None
    if secondary_family:
        st.write(
            "Profil secondaire détecté : "
            f"{FAMILY_LABELS.get(secondary_family, secondary_family.replace('_', ' ').title())}"
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

                # 1) Cohérence des familles
                if cv_main_family and offer_main_family and cv_main_family == offer_main_family:
                    adjusted_score += 12
                elif offer_main_family and offer_main_family in cv_families[:2]:
                    adjusted_score += 6
                elif cv_main_family and offer_main_family and offer_main_family not in cv_families:
                    adjusted_score -= 10

                family_overlap = len(set(cv_families[:3]) & set(offer_families[:3]))
                adjusted_score += family_overlap * 4

                # 2) Bonus métier principal
                main_job_label_lower = main_job_label.lower()

                if main_job_label_lower and main_job_label_lower in title_text:
                    adjusted_score += 18
                elif main_job_label_lower and main_job_label_lower in description_lower:
                    adjusted_score += 12

                # 3) Bonus métiers proches
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

                # 4) Bonus mots-clés suggérés
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

                # 5) Léger malus si le titre est éloigné
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
        missing_terms = [
            t for t in analysis.get("missing_terms", [])
            if is_clean_term(t)
        ]

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
    suggestions = build_cv_suggestions(
        missing_terms=analysis.get("missing_terms", [])
    )

    if suggestions:
        for suggestion in suggestions:
            st.write(f"- {suggestion}")
    else:
        st.write("Aucune suggestion générée.")