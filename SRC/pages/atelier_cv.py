import base64
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Atelier CV | Héphaïstos",
    layout="wide",
)

project_root = Path(__file__).resolve().parents[2]

logo_path = (
    project_root
    / "Assets"
    / "Logo boussole sf.png"
)

sailboat_path = (
    project_root
    / "Assets"
    / "Logo_Voilier SF.png"
)

sailboat_base64 = base64.b64encode(
    sailboat_path.read_bytes()
).decode("utf-8")

sea_path = (
    project_root
    / "Assets"
    / "Mer_Vagues_Boussole.png"
)

sea_base64 = base64.b64encode(
    sea_path.read_bytes()
).decode("utf-8")


st.markdown(
    """
    <style>
        .stApp {
            background: #f7f8ff;
        }

        .block-container {
            max-width: none;
            padding: 22px 28px 4rem;
        }

        header[data-testid="stHeader"] {
            display: none;
        }

        [data-testid="stToolbar"] {
            display: none;
        }

        #MainMenu {
            visibility: hidden;
        }

        h1, h2, h3, p {
            color: #090d67;
            font-family: Arial, sans-serif;
        }

        [data-testid="stMarkdownContainer"] h2 {
            color: #090d67 !important;
            -webkit-text-fill-color: #090d67 !important;

            font-family: Arial, sans-serif !important;
            font-weight: 700 !important;

            opacity: 1 !important;
        }

                    opacity: 1 !important;
        }


        div[data-testid="stButton"] > button {
            min-height: 44px;
            padding: 0 22px !important;

            border: 1px solid #3926ff !important;
            border-radius: 10px !important;

            background: linear-gradient(
                90deg,
                #4e30cd 0%,
                #3926ff 100%
            ) !important;

            color: #ffffff !important;

            font-family: Arial, sans-serif !important;
            font-size: 15px !important;
            font-weight: 700 !important;
        }

        div[data-testid="stButton"] > button p {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }

        div[data-testid="stButton"] > button:hover {
            background: #4e30cd !important;
            transform: translateY(-1px);
        }

        div[class*="st-key-backhephaistos"] button {
    border: 1px solid #3926ff !important;
    border-radius: 10px !important;

    background: linear-gradient(
        90deg,
        #4e30cd 0%,
        #3926ff 100%
    ) !important;

    color: #ffffff !important;

    box-shadow:
        0 6px 16px rgba(57, 38, 255, 0.20);
}

div[class*="st-key-backhephaistos"] button p {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

div[class*="st-key-backhephaistos"] button:hover {
    background: linear-gradient(
        90deg,
        #3926ff 0%,
        #4e30cd 100%
    ) !important;

    transform: translateY(-1px);
}
        /* Titres de niveau 3 */
        [data-testid="stMarkdownContainer"] h3 {
            color: #090d67 !important;
            -webkit-text-fill-color: #090d67 !important;

            font-family: Arial, sans-serif !important;
            font-weight: 700 !important;

            opacity: 1 !important;
        }

    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
        /* Sélecteurs et listes multiples */
        div[data-baseweb="select"] > div {
            border: 1px solid #c9c3ff !important;
            border-radius: 10px !important;

            background: #ffffff !important;
            color: #090d67 !important;

            box-shadow:
                0 3px 10px rgba(9, 13, 103, 0.06);
        }

        div[data-baseweb="select"]:focus-within > div {
            border-color: #3926ff !important;

            box-shadow:
                0 0 0 2px rgba(57, 38, 255, 0.14) !important;
        }

        div[data-baseweb="select"] input {
            color: #090d67 !important;
            -webkit-text-fill-color: #090d67 !important;
        }

        div[data-baseweb="select"] svg {
            fill: #3926ff !important;
        }

        /* Étiquettes des éléments sélectionnés */
        span[data-baseweb="tag"] {
            border: 0 !important;
            border-radius: 7px !important;

            background: linear-gradient(
                90deg,
                #4e30cd 0%,
                #3926ff 100%
            ) !important;

            color: #ffffff !important;
        }

        span[data-baseweb="tag"] * {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }

        span[data-baseweb="tag"] svg {
            fill: #ffffff !important;
        }

        /* Menu déroulant */
        div[data-baseweb="popover"],
        div[data-baseweb="popover"] > div,
        ul[role="listbox"] {
            border-color: #d9d5ff !important;
            background: #ffffff !important;
        }

        li[role="option"] {
            background: #ffffff !important;
            color: #090d67 !important;
        }

        li[role="option"] * {
            color: #090d67 !important;
            -webkit-text-fill-color: #090d67 !important;
        }

        li[role="option"]:hover,
        li[role="option"][aria-selected="true"] {
            background: #f0eeff !important;
        }

        /* Zones de reformulation */
        div[data-testid="stTextArea"] textarea {
            border: 1px solid #c9c3ff !important;
            border-radius: 10px !important;

            background: #ffffff !important;
            color: #090d67 !important;
            -webkit-text-fill-color: #090d67 !important;

            box-shadow:
                0 3px 10px rgba(9, 13, 103, 0.06);
        }

        div[data-testid="stTextArea"] textarea:focus {
            border-color: #3926ff !important;

            box-shadow:
                0 0 0 2px rgba(57, 38, 255, 0.14) !important;
        }

        div[data-testid="stTextArea"] textarea::placeholder {
            color: #7377a3 !important;
            -webkit-text-fill-color: #7377a3 !important;
            opacity: 1 !important;
        }

        /* Boutons fonctionnels */
        div[data-testid="stButton"] button {
            border: 1px solid #3926ff !important;
            border-radius: 10px !important;

            background: linear-gradient(
                90deg,
                #4e30cd 0%,
                #3926ff 100%
            ) !important;

            color: #ffffff !important;

            box-shadow:
                0 6px 16px rgba(57, 38, 255, 0.20);
        }

        div[data-testid="stButton"] button p {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }

        div[data-testid="stButton"] button:hover {
            border-color: #4e30cd !important;

            background: linear-gradient(
                90deg,
                #3926ff 0%,
                #4e30cd 100%
            ) !important;

            transform: translateY(-1px);
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.image(
    str(logo_path),
    width=220,
)


st.markdown("## Adapter mon CV à cette offre")

cv_original_text = st.session_state.get(
    "cv_original_text",
    "",
)

st.html(
    """
    <style>
        .cv-construction-banner {
            position: relative;
            min-height: 115px;
            margin: 0 0 24px;
            padding: 22px 320px 22px 24px;
            overflow: hidden;

            border: 1px solid #c9c3ff;
            border-left: 5px solid #3926ff;
            border-radius: 14px;

            background: linear-gradient(
                100deg,
                #f0eeff 0%,
                #f7f8ff 72%
            );

            color: #090d67;
            font-family: Arial, sans-serif;
        }

        .cv-construction-title {
            margin-bottom: 7px;
            color: #090d67;
            font-size: 17px;
            font-weight: 700;
        }

        .cv-construction-text {
            max-width: 900px;
            color: #343a72;
            font-size: 14px;
            line-height: 1.55;
        }

        .cv-sailing-area {
            position: absolute;
            right: 20px;
            bottom: 0;

            width: 280px;
            height: 110px;
        }

        .cv-sea {
            position: absolute;
            right: 0;
            bottom: 0;
            left: 0;

            width: 100%;
            height: 100%;

            object-fit: contain;
            object-position: center bottom;
    }
        .cv-sailboat {
    position: absolute;
    bottom: 22px;
    left: 0;

    width: 70px;

    font-size: 58px;
    line-height: 1;

    filter: drop-shadow(
        0 5px 5px rgba(57, 38, 255, 0.18)
    );

        animation: cv-sailing 6s ease-in-out infinite;
    }

    @keyframes cv-sailing {
        0% {
            left: 0;
            opacity: 1;
            transform: translateY(0) rotate(-2deg);
        }

        45% {
            transform: translateY(-6px) rotate(2deg);
        }

        85% {
            left: 190px;
            opacity: 1;
            transform: translateY(0) rotate(-2deg);
        }

        100% {
            left: 220px;
            opacity: 0;
            transform: translateY(-2px) rotate(0deg);
        }
    }

        @media (max-width: 800px) {
            .cv-construction-banner {
                padding: 20px 20px 125px;
            }

            .cv-sailing-area {
                right: 50%;
                transform: translateX(50%);
            }
        }
    <    </style>

    <div class="cv-construction-banner">
        <div class="cv-construction-title">
            Atelier CV en construction
        </div>

        <div class="cv-construction-text">
             Le chantier avance : le CV, l’offre, la direction
             et l’analyse sont correctement transmis.
             Les fonctions d’adaptation et de prévisualisation
             sont en développement.
        </div>

                        <div class="cv-sailing-area" aria-hidden="true">
            <img
                class="cv-sea"
                src="data:image/png;base64,SEA_BASE64"
                alt=""
            >

            <img
                class="cv-sailboat"
                src="data:image/png;base64,SAILBOAT_BASE64"
                alt="Voilier de La Boussole de l’emploi"
            >
        </div>
    </div>
    """.replace(
        "SAILBOAT_BASE64",
        sailboat_base64,
    ).replace(
        "SEA_BASE64",
        sea_base64,
    )
)
    
offer_text = st.session_state.get(
    "cv_adaptation_offer_text",
    "",
)

adaptation_direction = st.session_state.get(
    "cv_adaptation_direction"
)

adaptation_analysis = st.session_state.get(
    "cv_adaptation_analysis"
)


cv_icon = "✓" if cv_original_text else "–"
cv_status = "Document transmis" if cv_original_text else "Non transmis"

offer_icon = "✓" if offer_text else "–"
offer_status = "Offre transmise" if offer_text else "Non transmise"

if adaptation_direction:
    direction_icon = "✓"
    direction_label = adaptation_direction.replace(
        "_",
        " ",
    ).capitalize()
else:
    direction_icon = "–"
    direction_label = "Non définie"

if isinstance(adaptation_analysis, dict):
    analysis_icon = "✓"
    compatibility_score = adaptation_analysis.get(
        "score",
        0,
    )
    analysis_label = f"{compatibility_score} % de compatibilité"
else:
    analysis_icon = "–"
    analysis_label = "Analyse indisponible"


st.html(
    f"""
    <div style="
        margin: 28px 0 24px;
        padding: 20px 22px;

        border: 1px solid #d9d5ff;
        border-radius: 14px;

        background: #ffffff;

        box-shadow:
            0 8px 24px rgba(9, 13, 103, 0.06);

        font-family: Arial, sans-serif;
    ">
        <div style="
            margin-bottom: 16px;
            color: #090d67;
            font-size: 18px;
            font-weight: 700;
        ">
            Données transmises à l’Atelier
        </div>

        <div style="
            display: grid;
            grid-template-columns:
                repeat(auto-fit, minmax(190px, 1fr));
            gap: 12px;
        ">
            <div style="
                padding: 14px;
                border: 1px solid #e0dcff;
                border-radius: 11px;
                background: #f5f3ff;
            ">
                <strong style="color: #3926ff;">
                    {cv_icon} CV
                </strong><br>
                <span style="color: #4b507d;">
                    {cv_status}
                </span>
            </div>

            <div style="
                padding: 14px;
                border: 1px solid #e0dcff;
                border-radius: 11px;
                background: #f5f3ff;
            ">
                <strong style="color: #3926ff;">
                    {offer_icon} Offre
                </strong><br>
                <span style="color: #4b507d;">
                    {offer_status}
                </span>
            </div>

            <div style="
                padding: 14px;
                border: 1px solid #e0dcff;
                border-radius: 11px;
                background: #f5f3ff;
            ">
                <strong style="color: #3926ff;">
                    {direction_icon} Direction
                </strong><br>
                <span style="color: #4b507d;">
                    {direction_label}
                </span>
            </div>

            <div style="
                padding: 14px;
                border: 1px solid #e0dcff;
                border-radius: 11px;
                background: #f5f3ff;
            ">
                <strong style="color: #3926ff;">
                    {analysis_icon} Analyse
                </strong><br>
                <span style="color: #4b507d;">
                    {analysis_label}
                </span>
            </div>
               </div>
    </div>
    """
)
heading_translation = str.maketrans(
    {
        "à": "a",
        "â": "a",
        "ä": "a",
        "ç": "c",
        "é": "e",
        "è": "e",
        "ê": "e",
        "ë": "e",
        "î": "i",
        "ï": "i",
        "ô": "o",
        "ö": "o",
        "ù": "u",
        "û": "u",
        "ü": "u",
        "ÿ": "y",
        "œ": "oe",
    }
)


def normalize_heading(text):
    normalized_text = (
        str(text)
        .casefold()
        .translate(heading_translation)
        .replace("’", "'")
    )

    return " ".join(
        normalized_text.split()
    ).strip(" :.-")


def is_employer_header(line):
    header_part = line

    for separator in (
        "—",
        " – ",
        " | ",
        " - ",
    ):
        if separator in header_part:
            header_part = header_part.split(
                separator,
                1,
            )[0].strip()
            break

    letters = [
        character
        for character in header_part
        if character.isalpha()
    ]

    if len(letters) < 3:
        return False

    uppercase_ratio = (
        sum(
            character.isupper()
            for character in letters
        )
        / len(letters)
    )

    return (
        uppercase_ratio >= 0.80
        and len(header_part) <= 90
    )


def extract_experience_blocks(cv_text):
    start_headings = {
        "experience professionnelle",
        "experiences professionnelles",
        "parcours professionnel",
    }

    stop_headings = {
        "projet",
        "projets",
        "projet technique",
        "competence",
        "competences",
        "formation",
        "formations",
        "diplome",
        "diplomes",
        "langue",
        "langues",
        "centre d'interet",
        "centres d'interet",
        "informations complementaires",
    }

    clean_lines = []

    for raw_line in cv_text.splitlines():
        clean_line = " ".join(
            raw_line.split()
        )

        if clean_line:
            clean_lines.append(clean_line)

    experience_blocks = []
    current_block = []
    inside_experience_section = False

    for line in clean_lines:
        normalized_line = normalize_heading(
            line
        )

        if not inside_experience_section:
            if normalized_line in start_headings:
                inside_experience_section = True

            continue

        if normalized_line in stop_headings:
            break

        if is_employer_header(line):
            if current_block:
                experience_blocks.append(
                    {
                        "header": current_block[0],
                        "content": current_block[1:],
                    }
                )

            current_block = [line]

        elif current_block:
            current_block.append(line)

    if current_block:
        experience_blocks.append(
            {
                "header": current_block[0],
                "content": current_block[1:],
            }
        )

    return experience_blocks


experience_blocks = extract_experience_blocks(
    cv_original_text
)


heading_translation = str.maketrans(
    {
        "à": "a",
        "â": "a",
        "ä": "a",
        "ç": "c",
        "é": "e",
        "è": "e",
        "ê": "e",
        "ë": "e",
        "î": "i",
        "ï": "i",
        "ô": "o",
        "ö": "o",
        "ù": "u",
        "û": "u",
        "ü": "u",
        "ÿ": "y",
        "œ": "oe",
    }
)


def normalize_heading(text):
    normalized_text = (
        str(text)
        .casefold()
        .translate(heading_translation)
        .replace("’", "'")
    )

    return " ".join(
        normalized_text.split()
    ).strip(" :.-")


def is_employer_header(line):
    header_part = line

    for separator in (
        "—",
        " – ",
        " | ",
        " - ",
    ):
        if separator in header_part:
            header_part = header_part.split(
                separator,
                1,
            )[0].strip()
            break

    letters = [
        character
        for character in header_part
        if character.isalpha()
    ]

    if len(letters) < 3:
        return False

    uppercase_ratio = (
        sum(
            character.isupper()
            for character in letters
        )
        / len(letters)
    )

    return (
        uppercase_ratio >= 0.80
        and len(header_part) <= 90
    )


def extract_experience_blocks(cv_text):
    start_headings = {
        "experience professionnelle",
        "experiences professionnelles",
        "parcours professionnel",
    }

    stop_headings = {
        "projet",
        "projets",
        "projet technique",
        "competence",
        "competences",
        "formation",
        "formations",
        "diplome",
        "diplomes",
        "langue",
        "langues",
        "centre d'interet",
        "centres d'interet",
        "informations complementaires",
    }

    clean_lines = []

    for raw_line in cv_text.splitlines():
        clean_line = " ".join(
            raw_line.split()
        )

        if clean_line:
            clean_lines.append(clean_line)

    experience_blocks = []
    current_block = []
    inside_experience_section = False

    for line in clean_lines:
        normalized_line = normalize_heading(
            line
        )

        if not inside_experience_section:
            if normalized_line in start_headings:
                inside_experience_section = True

            continue

        if normalized_line in stop_headings:
            break

        if is_employer_header(line):
            if current_block:
                experience_blocks.append(
                    {
                        "header": current_block[0],
                        "content": current_block[1:],
                    }
                )

            current_block = [line]

        elif current_block:
            current_block.append(line)

    if current_block:
        experience_blocks.append(
            {
                "header": current_block[0],
                "content": current_block[1:],
            }
        )

    return experience_blocks


experience_blocks = extract_experience_blocks(
    cv_original_text
)


missing_competencies = []

if isinstance(adaptation_analysis, dict):
    raw_missing_competencies = (
        adaptation_analysis.get(
            "missing_competencies",
            [],
        )
    )

    if isinstance(raw_missing_competencies, list):
        missing_competencies = [
            competency
            for competency in raw_missing_competencies
            if isinstance(competency, dict)
        ]


safe_suggestions = {
    "soft_skill": (
        "Repère dans ton CV une mission qui démontre "
        "réellement ce savoir-être. Si elle existe, "
        "reformule cette mission avec une action et "
        "un contexte précis, plutôt que d’ajouter "
        "une simple liste de qualités."
    ),
    "relation_client": (
        "Recherche dans tes expériences une mission "
        "réelle d’accueil, de conseil, d’orientation "
        "ou de suivi. Si elle existe, rends cette "
        "mission plus visible dans le CV."
    ),
    "specifique_metier": (
        "Compare les missions de l’offre avec les "
        "tâches et les outils réellement présents "
        "dans ton parcours. Ne conserve que les "
        "correspondances que tu peux justifier."
    ),
}


st.markdown("### Premières pistes d’adaptation")

st.caption(
    "Ces pistes signalent des besoins présents dans "
    "l’offre mais insuffisamment visibles dans le CV. "
    "Elles ne doivent jamais servir à inventer une expérience."
)

if not cv_original_text or not offer_text:
    st.warning(
        "Le CV et l’offre doivent être transmis "
        "pour produire des pistes d’adaptation."
    )

elif not missing_competencies:
    st.info(
        "Aucun axe structuré n’a été détecté "
        "dans l’analyse transmise."
    )

else:
    for index, competency in enumerate(
        missing_competencies,
        start=1,
    ):
        category = competency.get(
            "category",
            "",
        )

        label = competency.get(
            "label",
            "Point à vérifier",
        )

        suggestion = safe_suggestions.get(
            category,
            (
                "Vérifie si ce besoin correspond à une "
                "expérience ou à une compétence réellement "
                "présente dans ton parcours. Si ce n’est "
                "pas le cas, ne l’ajoute pas au CV."
            ),
        )

        with st.container(border=True):
            st.markdown(
                f"**{index}. {label}**"
            )

            st.write(suggestion)

            st.caption(
                "À intégrer uniquement si tu peux "
                "l’appuyer sur un fait réel."
            )

            confirmation_key = (
                f"confirm_"
                f"{abs(hash(offer_text))}_"
                f"{index}_"
                f"{category}"
            )

            competency_confirmed = st.checkbox(
                (
                    "Je confirme que ce point correspond "
                    "réellement à mon parcours."
                ),
                key=confirmation_key,
            )

            if competency_confirmed:
                evidence_terms_by_category = {
                    "soft_skill": [
                        "rigueur",
                        "autonom",
                        "adaptab",
                        "polyval",
                        "équipe",
                        "equipe",
                    ],
                    "relation_client": [
                        "accueil",
                        "client",
                        "usager",
                        "public",
                        "conseil",
                        "orient",
                        "téléphon",
                        "telephon",
                    ],
                    "organisation_coordination": [
                        "organis",
                        "coord",
                        "planif",
                        "priorit",
                        "suivi",
                        "gestion",
                    ],
                }

                source_terms = competency.get(
                    "source_terms",
                    [],
                )

                if not isinstance(source_terms, list):
                    source_terms = []

                ignored_terms = {
                    "travail",
                    "poste",
                    "mission",
                    "missions",
                    "attendue",
                    "attendues",
                    "partir",
                    "pourvoir",
                    "information",
                }

                raw_search_terms = (
                    evidence_terms_by_category.get(
                        category,
                        [],
                    )
                    + source_terms
                )

                search_terms = []

                for term in raw_search_terms:
                    if not isinstance(term, str):
                        continue

                    normalized_term = term.casefold().strip()

                    if (
                        len(normalized_term) >= 4
                        and normalized_term not in ignored_terms
                        and normalized_term not in search_terms
                    ):
                        search_terms.append(normalized_term)

                controlled_term_variants = {
                    "orient": (
                        "orientation",
                        "orienter",
                        "orienté le public",
                        "orienter le public",
                    ),
                    "équipe": (
                        "travail en équipe",
                        "travail d’équipe",
                        "travail d'équipe",
                        "au sein d’une équipe",
                        "au sein d'une équipe",
                        "avec l’équipe",
                        "avec l'équipe",
                        "équipe de ",
                        "gestion d’équipe",
                        "gestion d'équipe",
                        "management d’équipe",
                        "management d'équipe",
                        "animation d’équipe",
                        "animation d'équipe",
                    ),
                    "equipe": (
                        "travail en equipe",
                        "travail d'equipe",
                        "au sein d'une equipe",
                        "avec l'equipe",
                        "equipe de ",
                        "gestion d'equipe",
                        "management d'equipe",
                        "animation d'equipe",
                    ),
                }

                scored_experiences = []

                for experience_index, experience in enumerate(
                    experience_blocks
                ):
                    experience_text = " ".join(
                        [
                            experience.get(
                                "header",
                                "",
                            ),
                            *experience.get(
                                "content",
                                [],
                            ),
                        ]
                    )

                    normalized_experience = (
                        experience_text.casefold()
                    )

                    match_count = 0

                    for term in search_terms:
                        controlled_variants = (
                            controlled_term_variants.get(
                                term
                            )
                        )

                        if controlled_variants:
                            term_found = any(
                                variant in normalized_experience
                                for variant
                                in controlled_variants
                            )
                        else:
                            term_found = (
                                term in normalized_experience
                            )

                        if term_found:
                            match_count += 1

                    if match_count:
                        scored_experiences.append(
                            (
                                experience_index,
                                match_count,
                            )
                        )

                scored_experiences.sort(
                    key=lambda item: item[1],
                    reverse=True,
                )

                recommended_indices = [
                    experience_index
                    for experience_index, match_count
                    in scored_experiences
                ]

                all_experience_indices = list(
                    range(len(experience_blocks))
                )

                ordered_indices = (
                    recommended_indices
                    + [
                        experience_index
                        for experience_index
                        in all_experience_indices
                        if experience_index
                        not in recommended_indices
                    ]
                )

                evidence_key = (
                    f"evidence_"
                    f"{abs(hash(offer_text))}_"
                    f"{index}_"
                    f"{category}"
                )

                if not experience_blocks:
                    st.warning(
                        "Aucune expérience existante "
                        "n’est disponible dans le CV."
                    )

                else:
                    if recommended_indices:
                        recommended_labels = [
                            experience_blocks[
                                experience_index
                            ]["header"]
                            for experience_index
                            in recommended_indices
                        ]

                        st.caption(
                            "Expériences repérées automatiquement : "
                            + " ; ".join(recommended_labels)
                        )

                    else:
                        st.caption(
                            "Aucune expérience n’a été repérée "
                            "automatiquement pour ce point."
                        )

                    selected_experiences = st.multiselect(
                        (
                            "Sélectionne une ou plusieurs "
                            "expériences existantes"
                        ),
                        options=ordered_indices,
                        default=[],
                        format_func=lambda experience_index: (
                            (
                                "Repérée automatiquement — "
                                if experience_index
                                in recommended_indices
                                else ""
                            )
                            + experience_blocks[
                                experience_index
                            ]["header"]
                        ),
                        placeholder=(
                            "Choisir les expériences concernées"
                        ),
                        key=f"{evidence_key}_experiences",
                    )

                    current_offer_signature = str(
                        abs(
                            hash(
                                offer_text
                            )
                        )
                    )

                    all_validated_reformulations = (
                        st.session_state.setdefault(
                            "cv_validated_reformulations",
                            {},
                        )
                    )

                    current_offer_reformulations = (
                        all_validated_reformulations.setdefault(
                            current_offer_signature,
                            {},
                        )
                    )

                    current_category_prefix = (
                        f"{index}_{category}_"
                    )

                    active_reformulation_ids = {
                        (
                            f"{index}_"
                            f"{category}_"
                            f"{experience_index}"
                        )
                        for experience_index
                        in selected_experiences
                    }

                    for stored_id in list(
                        current_offer_reformulations.keys()
                    ):
                        if (
                            stored_id.startswith(
                                current_category_prefix
                            )
                            and stored_id
                            not in active_reformulation_ids
                        ):
                            current_offer_reformulations.pop(
                                stored_id,
                                None,
                            )

                    if selected_experiences:
                        selected_count = len(
                            selected_experiences
                        )

                        if selected_count == 1:
                            selection_message = (
                                "1 expérience choisie "
                                "pour vérification."
                            )
                        else:
                            selection_message = (
                                f"{selected_count} expériences "
                                "choisies pour vérification."
                            )

                        st.info(selection_message)

                        justification_by_category = {
                            "soft_skill": (
                                "Cette expérience peut servir à "
                                "illustrer un savoir-être professionnel, "
                                "à condition que l’action et le contexte "
                                "soient réellement précisés dans le CV."
                            ),
                            "relation_client": (
                                "Cette expérience peut étayer la relation "
                                "client ou usager, car elle contient un "
                                "élément lié à l’accueil, au conseil ou "
                                "à l’orientation."
                            ),
                            "specifique_metier": (
                                "Cette expérience contient un élément "
                                "correspondant à une compétence métier "
                                "présente dans l’offre."
                            ),
                            "organisation_coordination": (
                                "Cette expérience contient un élément "
                                "lié à l’organisation, à la coordination "
                                "ou au suivi d’une activité."
                            ),
                        }

                        for selected_index in selected_experiences:
                            selected_experience = (
                                experience_blocks[
                                    selected_index
                                ]
                            )

                            selected_header = (
                                selected_experience.get(
                                    "header",
                                    "Expérience sélectionnée",
                                )
                            )

                            selected_content = (
                                selected_experience.get(
                                    "content",
                                    [],
                                )
                            )

                            normalized_selected_text = (
                                " ".join(
                                    [
                                        selected_header,
                                        *selected_content,
                                    ]
                                ).casefold()
                            )

                            matched_experience_terms = []

                            for term in search_terms:
                                controlled_variants = (
                                    controlled_term_variants.get(
                                        term
                                    )
                                )

                                if controlled_variants:
                                    matching_variant = next(
                                        (
                                            variant
                                            for variant
                                            in controlled_variants
                                            if variant
                                            in normalized_selected_text
                                        ),
                                        None,
                                    )

                                    if matching_variant:
                                        matched_experience_terms.append(
                                            matching_variant
                                        )

                                elif term in normalized_selected_text:
                                    matched_experience_terms.append(
                                        term
                                    )

                            matched_experience_terms = list(
                                dict.fromkeys(
                                    matched_experience_terms
                                )
                            )[:6]

                            matching_details = []

                            for detail in selected_content:
                                normalized_detail = (
                                    detail.casefold()
                                )

                                if any(
                                    term in normalized_detail
                                    for term
                                    in matched_experience_terms
                                ):
                                    matching_details.append(
                                        detail
                                    )

                            with st.container(border=True):
                                st.markdown(
                                    f"**{selected_header}**"
                                )

                                st.markdown(
                                    "**Contenu actuel dans le CV**"
                                )

                                for detail in selected_content:
                                    st.write(
                                        f"• {detail}"
                                    )

                                st.markdown(
                                    "**Justification**"
                                )

                                if matched_experience_terms:
                                    justification_text = (
                                        justification_by_category.get(
                                            category,
                                            (
                                                "Cette expérience contient "
                                                "un élément lié au besoin "
                                                "détecté dans l’offre."
                                            ),
                                        )
                                    )

                                    st.write(
                                        justification_text
                                    )

                                    if matching_details:
                                        st.write(
                                            "Élément justificatif déjà "
                                            "présent dans le CV :"
                                        )

                                        for detail in matching_details:
                                            st.write(
                                                f"« {detail} »"
                                            )

                                    st.caption(
                                        "Rapprochement fondé sur : "
                                        + ", ".join(
                                            matched_experience_terms
                                        )
                                        + "."
                                    )

                                else:
                                    st.warning(
                                        "Aucun lien direct n’a été détecté "
                                        "dans le contenu actuel de cette "
                                        "expérience."
                                    )

                                    st.caption(
                                        "Elle ne pourra être utilisée que "
                                        "si tu confirmes ci-dessous un fait "
                                        "réel appartenant à cette expérience."
                                    )

                                guided_facts_by_category = {
                                    "soft_skill": [
                                        "Adaptabilité face aux situations",
                                        "Polyvalence dans les missions",
                                        "Autonomie",
                                        "Travail en équipe",
                                        "Rigueur",
                                    ],
                                    "relation_client": [
                                        "Accueil de clients ou d’usagers",
                                        "Conseil auprès des clients",
                                        (
                                            "Orientation vers une solution "
                                            "ou un service"
                                        ),
                                        "Suivi des demandes",
                                        "Assistance technique",
                                    ],
                                    "organisation_coordination": [
                                        "Organisation de l’activité",
                                        (
                                            "Coordination avec d’autres "
                                            "personnes"
                                        ),
                                        "Planification des tâches",
                                        "Gestion des priorités",
                                        "Suivi de l’activité",
                                    ],
                                }

                                guided_fact_options = (
                                    guided_facts_by_category.get(
                                        category,
                                        [],
                                    )
                                )

                                if guided_fact_options:
                                    st.markdown(
                                        "**Confirmation guidée**"
                                    )

                                    st.caption(
                                        "Sélectionne uniquement les faits "
                                        "que tu as réellement réalisés "
                                        "dans cette expérience."
                                    )

                                    confirmed_facts = st.multiselect(
                                        (
                                            "Quels faits peux-tu confirmer "
                                            "pour cette expérience ?"
                                        ),
                                        options=guided_fact_options,
                                        default=[],
                                        key=(
                                            f"{evidence_key}_"
                                            f"confirmed_facts_"
                                            f"{selected_index}"
                                        ),
                                        placeholder=(
                                            "Choisir uniquement "
                                            "les faits réels"
                                        ),
                                    )

                                    if confirmed_facts:
                                        confirmed_count = len(
                                            confirmed_facts
                                        )

                                        if confirmed_count == 1:
                                            confirmation_message = (
                                                "1 fait confirmé par "
                                                "l’utilisateur."
                                            )
                                        else:
                                            confirmation_message = (
                                                f"{confirmed_count} faits "
                                                "confirmés par l’utilisateur."
                                            )

                                        st.success(
                                            confirmation_message
                                        )

                                        for confirmed_fact in (
                                            confirmed_facts
                                        ):
                                            st.write(
                                                f"✓ {confirmed_fact}"
                                            )

                                        st.caption(
                                            "Ces faits pourront être "
                                            "utilisés dans la reformulation. "
                                            "Aucun autre élément ne sera ajouté."
                                        )

                                        if matching_details:
                                            base_candidate = (
                                                matching_details[0]
                                                .strip()
                                                .rstrip(" .;,:")
                                            )

                                        elif selected_content:
                                            base_candidate = (
                                                selected_content[0]
                                                .strip()
                                                .rstrip(" .;,:")
                                            )

                                        else:
                                            base_candidate = (
                                                selected_header
                                                .strip()
                                                .rstrip(" .;,:")
                                            )

                                        date_words = {
                                            "depuis",
                                            "debut",
                                            "début",
                                            "fin",
                                            "en",
                                            "cours",
                                            "present",
                                            "présent",
                                            "au",
                                            "a",
                                            "à",
                                            "de",
                                            "du",
                                            "janvier",
                                            "fevrier",
                                            "février",
                                            "mars",
                                            "avril",
                                            "mai",
                                            "juin",
                                            "juillet",
                                            "aout",
                                            "août",
                                            "septembre",
                                            "octobre",
                                            "novembre",
                                            "decembre",
                                            "décembre",
                                        }

                                        candidate_words = (
                                            base_candidate
                                            .casefold()
                                            .replace("—", " ")
                                            .replace("–", " ")
                                            .replace("-", " ")
                                            .replace("/", " ")
                                            .replace("|", " ")
                                            .split()
                                        )

                                        non_numeric_words = []

                                        for candidate_word in candidate_words:
                                            clean_candidate_word = (
                                                candidate_word.strip(
                                                    " .,:;()"
                                                )
                                            )

                                            if (
                                                clean_candidate_word
                                                and not any(
                                                    character.isdigit()
                                                    for character
                                                    in clean_candidate_word
                                                )
                                            ):
                                                non_numeric_words.append(
                                                    clean_candidate_word
                                                )

                                        candidate_contains_number = any(
                                            character.isdigit()
                                            for character in base_candidate
                                        )

                                        base_is_date_line = (
                                            candidate_contains_number
                                            and all(
                                                word in date_words
                                                for word
                                                in non_numeric_words
                                            )
                                        )

                                        if base_is_date_line:
                                            base_text = (
                                                selected_header
                                                .strip()
                                                .rstrip(" .;,:")
                                            )
                                        else:
                                            base_text = base_candidate

                                        soft_skill_wording = {
                                            (
                                                "Adaptabilité face "
                                                "aux situations"
                                            ): (
                                                "l’adaptabilité face "
                                                "aux situations"
                                            ),
                                            (
                                                "Polyvalence dans "
                                                "les missions"
                                            ): (
                                                "la polyvalence dans "
                                                "les missions"
                                            ),
                                            "Autonomie": "l’autonomie",
                                            (
                                                "Travail en équipe"
                                            ): (
                                                "le travail en équipe"
                                            ),
                                            "Rigueur": "la rigueur",
                                        }

                                        if category == "soft_skill":
                                            normalized_confirmed_facts = [
                                                soft_skill_wording.get(
                                                    fact,
                                                    (
                                                        fact[:1].lower()
                                                        + fact[1:]
                                                    ),
                                                )
                                                for fact in confirmed_facts
                                                if fact
                                            ]
                                        else:
                                            normalized_confirmed_facts = [
                                                (
                                                    fact[:1].lower()
                                                    + fact[1:]
                                                )
                                                for fact
                                                in confirmed_facts
                                                if fact
                                            ]

                                        if (
                                            len(
                                                normalized_confirmed_facts
                                            )
                                            == 1
                                        ):
                                            joined_facts = (
                                                normalized_confirmed_facts[0]
                                            )

                                        else:
                                            joined_facts = (
                                                ", ".join(
                                                    normalized_confirmed_facts[
                                                        :-1
                                                    ]
                                                )
                                                + " et "
                                                + normalized_confirmed_facts[
                                                    -1
                                                ]
                                            )

                                        if category == "soft_skill":
                                            proposed_reformulation = (
                                                f"{base_text} — mission "
                                                f"mobilisant {joined_facts}."
                                            )

                                        elif category == (
                                            "organisation_coordination"
                                        ):
                                            proposed_reformulation = (
                                                f"{base_text} — "
                                                "responsabilités incluant "
                                                f"{joined_facts}."
                                            )

                                        else:
                                            proposed_reformulation = (
                                                f"{base_text} — "
                                                f"{joined_facts}."
                                            )

                                        facts_signature = abs(
                                            hash(
                                                tuple(
                                                    confirmed_facts
                                                )
                                            )
                                        )

                                        st.markdown(
                                            "**Proposition de reformulation**"
                                        )

                                        edited_reformulation = st.text_area(
                                            (
                                                "Version proposée pour "
                                                "cette expérience"
                                            ),
                                            value=proposed_reformulation,
                                            key=(
                                                f"{evidence_key}_"
                                                f"reformulation_"
                                                f"{selected_index}_"
                                                f"{facts_signature}"
                                            ),
                                            height=110,
                                        )

                                        st.caption(
                                            "Cette proposition utilise "
                                            "uniquement le contenu actuel "
                                            "du CV et les faits que tu viens "
                                            "de confirmer."
                                        )

                                        offer_signature = str(
                                            abs(
                                                hash(
                                                    offer_text
                                                )
                                            )
                                        )

                                        validated_reformulations = (
                                            st.session_state.setdefault(
                                                "cv_validated_reformulations",
                                                {},
                                            )
                                        )

                                        offer_reformulations = (
                                            validated_reformulations.setdefault(
                                                offer_signature,
                                                {},
                                            )
                                        )

                                        reformulation_id = (
                                            f"{index}_"
                                            f"{category}_"
                                            f"{selected_index}"
                                        )

                                        if st.button(
                                            "Valider cette reformulation",
                                            key=(
                                                f"validate_"
                                                f"{reformulation_id}_"
                                                f"{facts_signature}"
                                            ),
                                        ):
                                            offer_reformulations[
                                                reformulation_id
                                            ] = {
                                                "category": category,
                                                "label": label,
                                                "experience_index": (
                                                    selected_index
                                                ),
                                                "experience_header": (
                                                    selected_header
                                                ),
                                                "original_text": base_text,
                                                "confirmed_facts": list(
                                                    confirmed_facts
                                                ),
                                                "validated_text": (
                                                    edited_reformulation
                                                    .strip()
                                                ),
                                            }

                                        stored_reformulation = (
                                            offer_reformulations.get(
                                                reformulation_id
                                            )
                                        )

                                        if stored_reformulation:
                                            stored_text = (
                                                stored_reformulation.get(
                                                    "validated_text",
                                                    "",
                                                )
                                            )

                                            stored_facts = (
                                                stored_reformulation.get(
                                                    "confirmed_facts",
                                                    [],
                                                )
                                            )

                                            current_text = (
                                                edited_reformulation.strip()
                                            )

                                            validation_is_current = (
                                                stored_text == current_text
                                                and stored_facts
                                                == list(confirmed_facts)
                                            )

                                            if validation_is_current:
                                                st.success(
                                                    "Reformulation validée "
                                                    "et conservée."
                                                )

                                            else:
                                                offer_reformulations.pop(
                                                    reformulation_id,
                                                    None,
                                                )

                                                st.warning(
                                                    "La proposition a été "
                                                    "modifiée. Sa précédente "
                                                    "validation a été annulée. "
                                                    "Valide-la de nouveau."
                                                )

                                        else:
                                            st.info(
                                                "Cette reformulation n’est "
                                                "pas encore validée."
                                            )

                                    else:
                                        st.info(
                                            "Aucun fait supplémentaire "
                                            "n’est encore confirmé."
                                        )

                                else:
                                    st.info(
                                        "La confirmation guidée pour cette "
                                        "catégorie sera ajoutée après le "
                                        "filtrage de ses termes spécifiques."
                                    )

                    else:
                        st.info(
                            "Aucune expérience ne sera utilisée "
                            "tant que tu n’en as pas sélectionné."
                        )

summary_offer_signature = str(
    abs(
        hash(
            offer_text
        )
    )
)

all_saved_reformulations = (
    st.session_state.get(
        "cv_validated_reformulations",
        {},
    )
)

saved_offer_reformulations = (
    all_saved_reformulations.get(
        summary_offer_signature,
        {},
    )
)

valid_summary_items = {
    reformulation_id: reformulation
    for reformulation_id, reformulation
    in saved_offer_reformulations.items()
    if (
        isinstance(reformulation, dict)
        and reformulation.get(
            "validated_text",
            "",
        ).strip()
    )
}


if valid_summary_items:
    st.markdown(
        "### Synthèse des reformulations validées"
    )

    validated_count = len(
        valid_summary_items
    )

    if validated_count == 1:
        summary_message = (
            "1 reformulation validée est prête "
            "pour le futur CV adapté."
        )
    else:
        summary_message = (
            f"{validated_count} reformulations validées "
            "sont prêtes pour le futur CV adapté."
        )

    st.success(
        summary_message
    )

    for reformulation in (
        valid_summary_items.values()
    ):
        experience_header = reformulation.get(
            "experience_header",
            "Expérience",
        )

        reformulation_label = reformulation.get(
            "label",
            "Axe d’adaptation",
        )

        original_text = reformulation.get(
            "original_text",
            "",
        )

        validated_text = reformulation.get(
            "validated_text",
            "",
        )

        confirmed_facts = reformulation.get(
            "confirmed_facts",
            [],
        )

        with st.container(border=True):
            st.markdown(
                f"**{experience_header}**"
            )

            st.caption(
                f"Axe travaillé : {reformulation_label}"
            )

            if original_text:
                st.markdown(
                    "**Texte utilisé comme base**"
                )

                st.write(
                    original_text
                )

            st.markdown(
                "**Version validée**"
            )

            st.write(
                validated_text
            )

            if confirmed_facts:
                st.markdown(
                    "**Faits confirmés**"
                )

                for confirmed_fact in confirmed_facts:
                    st.write(
                        f"✓ {confirmed_fact}"
                    )

preview_state_key = (
    f"show_cv_preview_"
    f"{summary_offer_signature}"
)


if valid_summary_items:
    preview_is_visible = st.session_state.get(
        preview_state_key,
        False,
    )

    if preview_is_visible:
        preview_button_label = (
            "Masquer la prévisualisation"
        )
    else:
        preview_button_label = (
            "Prévisualiser mon CV adapté"
        )

    if st.button(
        preview_button_label,
        key=f"toggle_cv_preview_{summary_offer_signature}",
    ):
        st.session_state[preview_state_key] = not preview_is_visible
        st.rerun()

    if preview_is_visible:
        clean_preview_lines = []
        first_preview_line = ""

        for raw_line in cv_original_text.splitlines():
            clean_preview_line = " ".join(
                raw_line.split()
            )
            pdf_bullet_detected = False

            while clean_preview_line and (
                0xF000 <= ord(clean_preview_line[0]) <= 0xF8FF
                or clean_preview_line[0]
                in {"▪", "▫", "●", "○", "■", "□"}
            ):
                clean_preview_line = clean_preview_line[1:].lstrip()
                pdf_bullet_detected = True

            if pdf_bullet_detected and clean_preview_line:
                clean_preview_line = f"• {clean_preview_line}"

            if clean_preview_line:
                if not first_preview_line:
                    first_preview_line = clean_preview_line
                elif clean_preview_line == first_preview_line:
                    continue

                clean_preview_lines.append(clean_preview_line)
        if (
            clean_preview_lines
            and clean_preview_lines[-1].endswith(" pdf")
        ):
            clean_preview_lines[-1] = (
                clean_preview_lines[-1][:-4].rstrip()
            )
        preview_cv_text = "\n".join(
            clean_preview_lines
        )

        reformulations_by_original = {}

        for reformulation in valid_summary_items.values():
            raw_original_text = str(
                reformulation.get(
                    "original_text",
                    "",
                )
            ).strip()

            if not raw_original_text:
                continue

            preview_original_text = raw_original_text
            preview_bullet_detected = False

            while preview_original_text and (
                0xF000
                <= ord(preview_original_text[0])
                <= 0xF8FF
                or preview_original_text[0]
                in {"▪", "▫", "●", "○", "■", "□"}
            ):
                preview_original_text = (
                    preview_original_text[1:].lstrip()
                )
                preview_bullet_detected = True

            if (
                preview_bullet_detected
                and preview_original_text
            ):
                preview_original_text = (
                    f"• {preview_original_text}"
                )

            preview_reformulation = dict(reformulation)

            validated_text = str(
                reformulation.get(
                    "validated_text",
                    "",
                )
            ).strip()

            if validated_text.startswith(raw_original_text):
                preview_reformulation["validated_text"] = (
                    preview_original_text
                    + validated_text[
                        len(raw_original_text):
                    ]
                )

            reformulations_by_original.setdefault(
                preview_original_text,
                [],
            ).append(preview_reformulation)

        preview_warnings = []

        for original_text, related_reformulations in (
            reformulations_by_original.items()
        ):
            if original_text not in preview_cv_text:
                preview_warnings.append(
                    "La reformulation concernant "
                    f"« {original_text} » n’a pas pu "
                    "être replacée automatiquement."
                )
                continue
            replacement_target = original_text

            original_position = (
                preview_cv_text.find(
                    original_text
                )
            )

            punctuation_position = (
                original_position
                + len(original_text)
            )

            if (
                original_position >= 0
                and punctuation_position
                < len(preview_cv_text)
                and preview_cv_text[
                    punctuation_position
                ]
                in ".;,:"
            ):
                replacement_target += (
                    preview_cv_text[
                        punctuation_position
                    ]
                )

            if len(related_reformulations) == 1:
                validated_text = str(
                    related_reformulations[0].get(
                        "validated_text",
                        "",
                    )
                ).strip()

                if validated_text:
                    preview_cv_text = preview_cv_text.replace(
                        replacement_target,
                        validated_text,
                        1,
                    )

                continue

            merged_confirmed_facts = []
            seen_confirmed_facts = set()

            for reformulation in related_reformulations:
                for confirmed_fact in reformulation.get(
                    "confirmed_facts",
                    [],
                ):
                    clean_confirmed_fact = str(
                        confirmed_fact
                    ).strip().rstrip(
                        " .;"
                    )

                    normalized_confirmed_fact = (
                        clean_confirmed_fact.casefold()
                    )

                    if (
                        clean_confirmed_fact
                        and normalized_confirmed_fact
                        not in seen_confirmed_facts
                    ):
                        seen_confirmed_facts.add(
                            normalized_confirmed_fact
                        )
                        merged_confirmed_facts.append(
                            clean_confirmed_fact
                        )

            base_text_for_merge = original_text.rstrip(
                " .;"
            )

            normalized_base_text = (
                base_text_for_merge.casefold()
            )

            facts_to_append = []

            for confirmed_fact in merged_confirmed_facts:
                normalized_confirmed_fact = (
                    confirmed_fact.casefold()
                )

                fact_is_already_visible = (
                    normalized_confirmed_fact
                    in normalized_base_text
                )

                if (
                    normalized_confirmed_fact
                    == "autonomie"
                    and "autonom" in normalized_base_text
                ):
                    fact_is_already_visible = True

                if (
                    normalized_confirmed_fact
                    == "respect des délais"
                    and "délai" in normalized_base_text
                ):
                    fact_is_already_visible = True

                if not fact_is_already_visible:
                    displayed_fact = (
                        confirmed_fact[0].lower()
                        + confirmed_fact[1:]
                    )

                    facts_to_append.append(
                        displayed_fact
                    )

            if facts_to_append:
                if len(facts_to_append) == 1:
                    joined_facts = facts_to_append[0]

                else:
                    joined_facts = (
                        ", ".join(facts_to_append[:-1])
                        + " et "
                        + facts_to_append[-1]
                    )

                merged_text = (
                    f"{base_text_for_merge} ; "
                    f"{joined_facts}."
                )

            else:
                merged_text = (
                    f"{base_text_for_merge}."
                )

            preview_cv_text = preview_cv_text.replace(
                replacement_target,
                merged_text,
                1,
            )

            # No additional replacement is attempted when multiple
            # reformulations must be merged; this is delegated to the
            # earlier fusion logic above.

        st.markdown(
            "### Prévisualisation textuelle du CV adapté"
        )

        st.caption(
            "Cette prévisualisation modifie uniquement "
            "une copie du texte extrait. Le CV original "
            "reste inchangé."
        )

        preview_signature = abs(
            hash(
                preview_cv_text
            )
        )

        st.text_area(
            "Contenu prévisualisé",
            value=preview_cv_text,
            height=620,
            disabled=True,
            key=(
                f"adapted_cv_preview_"
                f"{summary_offer_signature}_"
                f"{preview_signature}"
            ),
        )

        for preview_warning in preview_warnings:
            st.warning(
                preview_warning
            )

if st.button(
    "Retour à Héphaïstos",
    key="backhephaistos",
):
    st.switch_page("main.py")
