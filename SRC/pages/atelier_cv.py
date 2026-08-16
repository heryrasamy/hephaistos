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

if st.button(
    "Retour à Héphaïstos",
    key="backhephaistos",
):
    st.switch_page("main.py")