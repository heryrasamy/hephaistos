import re
import unicodedata
import base64
from pathlib import Path
from collections import Counter
from typing import List

import streamlit as st

from cv_extract import extract_text_from_upload
from matching_simple import score_cv_offer, STOPWORDS, extract_terms
from job_inference import (
    build_job_inference_summary,
    build_search_queries_from_job_summary,
    get_top_cv_families,
    infer_rome_jobs_from_terms,
    filter_rome_candidate_terms,
    normalize_text,
    rank_rome_jobs_against_cv,
    rank_rome_candidate_terms
)
from offers_phase1 import fetch_offers_multi_queries
from opportunity_rules import build_realistic_opportunity_summary
from location_helper import (
    filter_communes,
    format_commune_label,
    search_communes_geo_api,
)
from francetravail_api import get_access_token
from semantic_matching import evaluate_rome_reference

st.set_page_config(
    page_title="Héphaïstos | La Boussole de l'Emploi",
    layout="wide",
    initial_sidebar_state="collapsed",
)

project_root = Path(__file__).resolve().parents[1]

rower_path = (
    project_root
    / "Assets"
    / "Rameur.png"
)

rower_base64 = base64.b64encode(
    rower_path.read_bytes()
).decode("utf-8")

logo_path = (
    project_root
    / "Assets"
    / "Logo boussole sf.png"
)

logo_base64 = base64.b64encode(
    logo_path.read_bytes()
).decode("utf-8")

st.markdown(

    """
   <style>
    .stApp {
        background: #f7f8ff;
    }

    .block-container {
        max-width: none;
        padding: 0 28px 4rem;
    }


    /* ========================= */
    /* BARRE NATIVE STREAMLIT */
    /* ========================= */

    header[data-testid="stHeader"] {
        display: none;
    }

    [data-testid="stToolbar"] {
        display: none;
    }

    #MainMenu {
        visibility: hidden;
    }


    /* ========================= */
    /* NAVIGATION DU SITE */
    /* ========================= */

    .hephaistos-site-nav {
        width: 100%;
        min-height: 76px;
        margin-bottom: 0;

        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 32px;

        font-family: Arial, sans-serif;
    }


    /* Logo */

    .hephaistos-site-logo-link {
        display: flex;
        align-items: center;

        flex: 0 0 auto;

        text-decoration: none;
    }

    .hephaistos-site-logo {
        display: block;

        width: 220px;
        height: auto;
    }


    /* Liens */

    .hephaistos-site-links {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 46px;

        flex: 1 1 auto;
    }

    .hephaistos-site-links a {
        position: relative;

        display: inline-flex;
        align-items: center;

        min-height: 76px;

        color: #090d67;

        font-family: Arial, sans-serif;
        font-size: 16px;
        font-weight: 600;

        text-decoration: none;
        white-space: nowrap;
    }

    .hephaistos-site-links a:hover {
        color: #3926ff;
    }


    /* Soulignement au survol */

    .hephaistos-site-links a::after {
        content: "";

        position: absolute;
        right: 0;
        bottom: 2px;
        left: 0;

        height: 2px;

        background: #3926ff;

        transform: scaleX(0);
        transform-origin: center;

        transition: transform 0.2s ease;
    }

    .hephaistos-site-links a:hover::after {
        transform: scaleX(1);
    }


    /* ========================= */
    /* BANDEAU HÉPHAÏSTOS */
    /* ========================= */

    .hephaistos-header {
        width: calc(100% + 56px);
        min-height: 460px;
        margin: 0 -28px 48px;
        padding: 42px clamp(40px, 8vw, 140px);

        box-sizing: border-box;

        display: grid;
        grid-template-columns:
            minmax(520px, 1.1fr)
            minmax(360px, 0.9fr);

        align-items: center;
        gap: clamp(40px, 6vw, 100px);

        border-radius: 0;

        background:
            radial-gradient(
                circle at 18% 50%,
                rgba(123, 91, 249, 0.34) 0%,
                transparent 36%
            ),
            linear-gradient(
                115deg,
                #4e30cd 0%,
                #12328c 54%,
                #06286e 100%
            );

        box-shadow:
            0 18px 45px rgba(19, 26, 102, 0.14);

        overflow: hidden;
    }


    /* Partie texte */

    .hephaistos-header-content {
        flex: 1 1 62%;
        max-width: 720px;

        color: #ffffff;
    }

    .hephaistos-platform-name {
        display: inline-flex;

        margin: 0 0 22px;
        padding: 9px 16px;

        border: 1px solid rgba(255, 255, 255, 0.48);
        border-radius: 999px;

        background: rgba(255, 255, 255, 0.07);

        color: #ffffff;

        font-family: Arial, sans-serif;
        font-size: 16px;
        font-weight: 700;
        letter-spacing: 0;
        text-transform: none;
    }

    .hephaistos-header-title {
        margin: 0 0 24px;

        color: #ffffff;

        font-family: Arial, sans-serif;
        font-size: clamp(48px, 4.2vw, 64px);
        font-weight: 700;
        line-height: 1.06;
        letter-spacing: -1.5px;
    }

    .hephaistos-header-text {
        max-width: 620px;
        margin: 0;

        color: rgba(255, 255, 255, 0.94);

        font-family: Arial, sans-serif;
        font-size: 18px;
        line-height: 1.55;
    }


    /* Partie illustration */

    .hephaistos-header-visual {
        flex: 0 0 300px;

        display: flex;
        align-items: center;
        justify-content: center;
    }

    .hephaistos-header-visual-circle {
        width: 260px;
        height: 260px;

        display: flex;
        align-items: center;
        justify-content: center;

        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 50%;

        background: rgba(255, 255, 255, 0.1);
    }

    .hephaistos-header-visual-img {
        display: block;

        width: 100%;
        height: 100%;

        object-fit: contain;

        transform: scale(1.65);
        transform-origin: 50% 50%;
    }

    .hephaistos-header-visual-circle:hover
    .hephaistos-header-visual-img {
        animation: rower-forward 1.4s ease-in-out 1;
    }

    @keyframes rower-forward {
        0% {
            transform:
                translateY(0)
                scale(1.55);
        }

        50% {
            transform:
                translateY(-5px)
                scale(1.60);
        }

        100% {
            transform:
                translateY(0)
                scale(1.55);
        }
        /* ========================= */
/* BANDEAU HÉPHAÏSTOS — MOBILE */
/* ========================= */

@media (max-width: 768px) {

    .hephaistos-header {
        width: calc(100% + 32px);
        min-height: auto;
        margin: 0 -16px 36px;
        padding: 34px 24px 38px;

        grid-template-columns: minmax(0, 1fr);
        gap: 0;

        overflow: hidden;
    }

    .hephaistos-header-content {
        width: 100%;
        min-width: 0;
        max-width: 100%;

        text-align: center;
    }

    .hephaistos-platform-name {
        max-width: 100%;
        margin-bottom: 20px;
        padding: 8px 14px;

        justify-content: center;

        white-space: normal;
        text-align: center;

        font-size: 14px;
        line-height: 1.35;
    }

    .hephaistos-header-title {
        margin-bottom: 20px;

        font-size: clamp(40px, 13vw, 52px);
        line-height: 1.05;
        letter-spacing: -0.6px;

        overflow-wrap: anywhere;
    }

    .hephaistos-header-text {
        width: 100%;
        max-width: 100%;

        font-size: 16px;
        line-height: 1.5;

        overflow-wrap: anywhere;
    }

    .hephaistos-header-visual {
        display: none;
    }
}
    }


    /* ========================= */
    /* TEXTES DE L'APPLICATION */
    /* ========================= */

    [data-testid="stMarkdownContainer"]
    p:not(.hephaistos-platform-name):not(.hephaistos-header-text),
    [data-testid="stWidgetLabel"] p,
    label {
        color: #25285f !important;
    }


    /* ========================= */
    /* WIDGETS STREAMLIT */
    /* ========================= */

    /* Zone upload CV */

    [data-testid="stFileUploaderDropzone"] {
        background:
            linear-gradient(
                115deg,
                #243a9a 0%,
                #17348d 55%,
                #0c2b78 100%
            ) !important;

        border:
            1px solid
            rgba(255, 255, 255, 0.14) !important;

        border-radius: 16px !important;
    }

    [data-testid="stFileUploaderDropzone"] * {
        color: #ffffff !important;
    }

    [data-testid="stFileUploaderDropzone"] button {
        background:
            rgba(255, 255, 255, 0.08) !important;

        color: #ffffff !important;

        border:
            1px solid
            rgba(255, 255, 255, 0.18) !important;

        border-radius: 12px !important;
    }


    /* Champs texte */

    div[data-baseweb="input"] > div,
    div[data-baseweb="base-input"] > div,
    div[data-baseweb="textarea"] {
        background:
            linear-gradient(
                115deg,
                #243a9a 0%,
                #17348d 55%,
                #0c2b78 100%
            ) !important;

        border:
            1px solid
            rgba(255, 255, 255, 0.12) !important;

        border-radius: 14px !important;
    }

    div[data-baseweb="input"] input,
    div[data-baseweb="base-input"] input,
    div[data-baseweb="textarea"] textarea {
        color: #ffffff !important;
    }

    div[data-baseweb="input"] input::placeholder,
    div[data-baseweb="base-input"] input::placeholder,
    div[data-baseweb="textarea"] textarea::placeholder {
        color:
            rgba(255, 255, 255, 0.72) !important;
    }


    /* Selectbox */

    div[data-baseweb="select"] > div {
        background:
            linear-gradient(
                115deg,
                #243a9a 0%,
                #17348d 55%,
                #0c2b78 100%
            ) !important;

        border:
            1px solid
            rgba(255, 255, 255, 0.12) !important;

        border-radius: 14px !important;

        color: #ffffff !important;
    }

    div[data-baseweb="select"] * {
        color: #ffffff !important;
    }


    /* ========================= */
    /* BOUTONS STREAMLIT BLANCS */
    /* ========================= */

    [data-testid="stButton"] button {
        min-height: 46px;
        padding: 0 18px;

        border:
            1px solid #3926ff !important;

        border-radius: 12px;

        background: #ffffff !important;
        color: #2415d8 !important;

        font-weight: 700;
    }

    [data-testid="stButton"] button p,
    [data-testid="stButton"] button span {
        color: #2415d8 !important;

        -webkit-text-fill-color:
            #2415d8 !important;
    }

    [data-testid="stButton"] button:hover {
        border-color: #2818dd !important;

        background: #f4f2ff !important;
        color: #2818dd !important;
    }

    [data-testid="stButton"] button:hover p,
    [data-testid="stButton"] button:hover span {
        color: #2818dd !important;

        -webkit-text-fill-color:
            #2818dd !important;
    }


    /* ========================= */
    /* TEXTAREA : TEXTE DE L'OFFRE */
    /* ========================= */

    [data-testid="stTextArea"] {
        background: transparent !important;
    }

    [data-testid="stTextArea"]
    div[data-baseweb="textarea"],
    [data-testid="stTextArea"]
    div[data-baseweb="base-input"] {
        overflow: hidden;

        background: #17348d !important;
        background-color: #17348d !important;

        border: none !important;
        outline: none !important;
        box-shadow: none !important;

        border-radius: 16px !important;
    }

    [data-testid="stTextArea"] textarea {
        background: #17348d !important;
        background-color: #17348d !important;

        border: none !important;
        outline: none !important;
        box-shadow: none !important;

        border-radius: 16px !important;

        color: #ffffff !important;
        caret-color: #ffffff !important;

        -webkit-text-fill-color:
            #ffffff !important;
    }

    [data-testid="stTextArea"]
    div[data-baseweb="textarea"]:focus-within,
    [data-testid="stTextArea"]
    div[data-baseweb="base-input"]:focus-within,
    [data-testid="stTextArea"] textarea:focus {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }

    [data-testid="stTextArea"]
    textarea::placeholder {
        color:
            rgba(255, 255, 255, 0.72) !important;

        -webkit-text-fill-color:
            rgba(255, 255, 255, 0.72) !important;
    }


    /* ========================= */
    /* TITRES DE L'APPLICATION */
    /* ========================= */

    .stApp h1,
    .stApp h2,
    .stApp h3,
    .stApp h4,
    .stApp h5,
    .stApp h6 {
        color: #0a1468 !important;

        -webkit-text-fill-color:
            #0a1468 !important;

        opacity: 1 !important;
    }

    .hephaistos-section-title {
        margin: 34px 0 18px;

        color: #0a1468 !important;

        -webkit-text-fill-color:
            #0a1468 !important;

        font-family: Arial, sans-serif;
        font-size: 28px;
        font-weight: 700;
        line-height: 1.25;

        opacity: 1 !important;
    }


    /* Le bandeau conserve ses textes blancs */

    .stApp
    .hephaistos-header
    .hephaistos-header-title {
        color: #ffffff !important;

        -webkit-text-fill-color:
            #ffffff !important;
    }

    .stApp
    .hephaistos-header
    .hephaistos-platform-name {
        color: #ffffff !important;

        -webkit-text-fill-color:
            #ffffff !important;
    }

    .stApp
    .hephaistos-header
    .hephaistos-header-text {
        color:
            rgba(255, 255, 255, 0.94) !important;

        -webkit-text-fill-color:
            rgba(255, 255, 255, 0.94) !important;
    }
    /* ========================= */
    /* MODALE D’ANALYSE */
    /* ========================= */

    div[data-testid="stDialog"] div[role="dialog"] {
        background: #f7f8ff !important;
        color: #0a1468 !important;
        border: 1px solid #dfe3f5 !important;
        border-radius: 20px !important;
    }

    div[data-testid="stDialog"] h1,
    div[data-testid="stDialog"] h2,
    div[data-testid="stDialog"] h3,
    div[data-testid="stDialog"] h4 {
        color: #0a1468 !important;
    }

    div[data-testid="stDialog"]
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stDialog"]
    div[data-testid="stMarkdownContainer"] li {
        color: #17215f !important;
        opacity: 1 !important;
    }

    div[data-testid="stDialog"]
    div[data-testid="stCaptionContainer"],
    div[data-testid="stDialog"]
    div[data-testid="stCaptionContainer"] p {
        color: #5d6482 !important;
        opacity: 1 !important;
    }
    /* ========================= */
    /* BLOCS DÉPLIABLES */
    /* ========================= */

    div[data-testid="stExpander"] details {
        overflow: hidden;

        background: #ffffff !important;
        border: 1px solid #d9d4ff !important;
        border-radius: 14px !important;

        box-shadow:
            0 4px 12px
            rgba(18, 32, 99, 0.05);
    }

    div[data-testid="stExpander"] summary {
        background: #f0edff !important;
        color: #0a1468 !important;
    }

    div[data-testid="stExpander"] summary p {
        color: #0a1468 !important;
        font-weight: 600 !important;
    }

    div[data-testid="stExpander"] summary svg {
        color: #3926ff !important;
        fill: #3926ff !important;
    }
    /* ========================= */
    /* CARTES DES FORCES */
    /* ========================= */

    div[class*="st-key-strength-card-"] {
        min-height: 54px;
        margin-bottom: 14px;
        padding: 14px 16px;

        border: 1px solid transparent;
        border-radius: 14px;

        box-sizing: border-box;
        box-shadow:
            0 4px 12px
            rgba(18, 32, 99, 0.05);
    }

    div[class*="st-key-strength-card-"] p {
        margin: 0 !important;
        color: #0a1468 !important;
        font-weight: 600;
    }

    /* Communication : lavande */
    div[class*="st-key-strength-card-0"],
    div[class*="st-key-strength-card-7"] {
        background: #f0edff !important;
        border-color: #ddd6ff !important;
    }

    /* Accueil : bleu clair */
    div[class*="st-key-strength-card-1"],
    div[class*="st-key-strength-card-2"],
    div[class*="st-key-strength-card-3"] {
        background: #eaf5ff !important;
        border-color: #d2e9fa !important;
    }

    /* Outils numériques : jaune sable */
    div[class*="st-key-strength-card-4"] {
        background: #fff7df !important;
        border-color: #f2e6bd !important;
    }

    /* Relationnel : vert menthe */
    div[class*="st-key-strength-card-5"],
    div[class*="st-key-strength-card-6"] {
        background: #eaf8f1 !important;
        border-color: #d1ebde !important;
    }
        /* ========================= */
    /* CARTES DES OFFRES */
    /* ========================= */

    div[class*="st-key-offer-card-"] {
        margin-bottom: 18px;
        padding: 22px 24px;

        background: #ffffff !important;
        border: 1px solid #dfe3f5 !important;
        border-radius: 20px !important;

        box-shadow:
            0 8px 24px
            rgba(18, 32, 99, 0.08) !important;

        box-sizing: border-box;
    }
    /* ========================= */
    /* TEXTES SECONDAIRES */
    /* ========================= */

    div[data-testid="stCaptionContainer"],
    div[data-testid="stCaptionContainer"] p {
        color: #5d6482 !important;
        opacity: 1 !important;
    }
    /* ========================= */
    /* VERDIC D'OPPORTUNITE DANS LES CARTES */
    /* ========================= */

    div[class*="st-key-offer-card-"]
    [data-testid="stCaptionContainer"] {
        color: #4b507d !important;
    }

    div[class*="st-key-offer-card-"]
    [data-testid="stCaptionContainer"] p {
        color: #4b507d !important;

    -webkit-text-fill-color:
        #4b507d !important;

    opacity: 1 !important;
}
    /* ========================= */
    /* RESPONSIVE */
    /* ========================= */

    @media (max-width: 1050px) {
        .hephaistos-site-nav {
            flex-wrap: wrap;
            padding-bottom: 14px;
        }

        .hephaistos-site-links {
            order: 3;
            width: 100%;

            justify-content: flex-start;
            flex-wrap: wrap;

            gap: 8px 26px;
        }
    }

    @media (max-width: 760px) {
        .block-container {
            padding-top: 1rem;
        }

        .hephaistos-header {
            min-height: auto;
            padding: 42px 26px;

            flex-direction: column;
            gap: 34px;

            text-align: center;
        }

        .hephaistos-header-content {
            flex: none;
            max-width: 100%;
        }

        .hephaistos-platform-name {
            margin-bottom: 18px;
        }

        .hephaistos-header-title {
            font-size: 42px;
        }

        .hephaistos-header-text {
            font-size: 16px;
        }

        .hephaistos-header-visual {
            flex: none;
            width: 100%;
        }

        .hephaistos-header-visual-circle {
            width: 200px;
            height: 200px;
        }

        .hephaistos-section-title {
            margin: 28px 0 16px;
            font-size: 24px;
        }
        /* ========================= */
/* BANDEAU HÉPHAÏSTOS — MOBILE */
/* ========================= */

@media screen and (max-width: 900px) {

    .hephaistos-header {
        display: block !important;

        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        min-height: 0 !important;

        margin: 0 0 32px !important;
        padding: 30px 20px 34px !important;

        box-sizing: border-box !important;
        overflow: hidden !important;
    }

    .hephaistos-header-content {
        display: block !important;

        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;

        margin: 0 !important;

        box-sizing: border-box !important;
        text-align: center !important;
    }

    .hephaistos-platform-name {
        display: inline-block !important;

        width: auto !important;
        max-width: 100% !important;

        margin: 0 auto 18px !important;
        padding: 8px 12px !important;

        box-sizing: border-box !important;

        white-space: normal !important;
        overflow-wrap: anywhere !important;

        font-size: 13px !important;
        line-height: 1.35 !important;
        text-align: center !important;
    }

    .hephaistos-header-title {
        width: 100% !important;
        max-width: 100% !important;

        margin: 0 0 18px !important;

        font-size: clamp(38px, 12vw, 50px) !important;
        line-height: 1.05 !important;
        letter-spacing: -0.5px !important;

        overflow-wrap: anywhere !important;
        text-align: center !important;
    }

    .hephaistos-header-text {
        width: 100% !important;
        max-width: 100% !important;

        margin: 0 !important;

        font-size: 16px !important;
        line-height: 1.5 !important;

        overflow-wrap: anywhere !important;
        text-align: center !important;
    }

    .hephaistos-header-visual {
        display: none !important;
    }

    }
</style>
    """,
    unsafe_allow_html=True,
)

navigation_html = (
    '<nav class="hephaistos-site-nav">'

    '<a href="#" '
    'class="hephaistos-site-logo-link" '
    'aria-label="Accueil - La Boussole de l\'Emploi">'

    '<img '
    'class="hephaistos-site-logo" '
    f'src="data:image/png;base64,{logo_base64}" '
    'alt="La Boussole de l\'Emploi">'

    '</a>'

    '<div class="hephaistos-site-links">'
    '<a href="https://heryrasamy.github.io/la-boussole-de-l-Emploi/">Accueil</a>'
    '<a href="https://heryrasamy.github.io/la-boussole-de-l-Emploi/Utiliser-Hephaistos.html">Découvrir</a>'
    '</div>'

    '</nav>'
)

header_html = (
    f'<section class="hephaistos-header">'
    f'<div class="hephaistos-header-content">'
    f'<p class="hephaistos-platform-name">'
    f'Votre guide pour garder le cap'
    f'</p>'
    f'<h1 class="hephaistos-header-title">'
    f'Héphaïstos'
    f'</h1>'
    f'<p class="hephaistos-header-text">'
    f'Votre guide pour comprendre votre parcours, '
    f'choisir votre direction professionnelle '
    f'et identifier les opportunités adaptées à votre profil.'
    f'</p>'
    f'</div>'
    f'<div class="hephaistos-header-visual">'
    f'<div class="hephaistos-header-visual-circle">'
    f'<img class="hephaistos-header-visual-img" '
    f'src="data:image/png;base64,{rower_base64}" '
    f'alt="Rameur Héphaïstos">'
    f'</div>'
    f'</div>'
    f'</section>'
)

st.markdown(
    navigation_html + header_html,
    unsafe_allow_html=True,
)


# =========================================================
# SESSION STATE
# =========================================================
if "offer_text" not in st.session_state:
    st.session_state["offer_text"] = ""

if "cv_adaptation_direction" not in st.session_state:
    st.session_state["cv_adaptation_direction"] = None

if "cv_adaptation_analysis" not in st.session_state:
    st.session_state["cv_adaptation_analysis"] = None

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

if "cv_original_text" not in st.session_state:
    st.session_state["cv_original_text"] = ""

if "cv_adaptation_offer_text" not in st.session_state:
    st.session_state["cv_adaptation_offer_text"] = ""


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
        c
        for c in unicodedata.normalize("NFKD", s or "")
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


def normalize_text(text: str) -> str:
    return _normalize_local(text)


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


def build_cv_suggestions_from_competencies(
    missing_competencies: list[dict],
) -> list[str]:
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
                "Mets en avant l’utilisation d’outils comme Excel,"
                "reporting ou tableaux de bord"
                "avec des exemples concrets."
            )

        elif concept == "management":
            suggestions.append(
                "Si tu as encadré ou coordonné des personnes, "
                "mentionne-le explicitement avec des résultats ou responsabilités."
            )

        elif concept == "relation_client":
            suggestions.append(
                "Ajoute des exemples concrets de relation client : accueil, conseil, suivi ou gestion de demandes."
            )

        elif concept == "communication":
            suggestions.append(
                "Décris précisément tes actions de communication : "
                "contenus créés, réseaux utilisés, objectifs atteints."
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

    return FAMILY_LABELS.get(family, family.replace("_", " ").capitalize())


# =========================================================
# 1) IMPORTER LE CV
# =========================================================

st.markdown(
    """
    <h2 style="
        margin: 34px 0 18px;
        color: #0a1468 !important;
        -webkit-text-fill-color: #0a1468 !important;
        font-family: Arial, sans-serif;
        font-size: 28px;
        font-weight: 700;
        line-height: 1.25;
        opacity: 1;
    ">
        1) Importer votre CV
    </h2>
    """,
    unsafe_allow_html=True,
)


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

if uploaded:
    uploaded.seek(0)
    file_bytes = uploaded.read()

    if not file_bytes:
        st.error("Fichier vide ou illisible. Recharge le CV.")
        st.stop()

    cv_text = to_text(extract_text_from_upload(uploaded.name, file_bytes))
    st.session_state["cv_original_text"] = cv_text
 
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

    topics = filter_rome_candidate_terms(topics)

    skills = topics_to_skills(topics)

    sub_family = infer_sub_family(topics, direction_family)

    # ------------------------
    # Résumé métier
    # ------------------------
    job_summary = build_job_inference_summary(
    detected_families=cv_families,
    cv_terms=cv_terms_for_inference,
    top_n=3,
)
    
main_job_data = job_summary.get("main_job", {})
related_jobs = job_summary.get("related_jobs", [])

if isinstance(main_job_data, dict):
    main_job_label = main_job_data.get(
        "job",
        "inconnu",
    )
    domain_label = main_job_data.get(
        "domain",
        "inconnu",
    )
else:
    main_job_label = main_job_data or "inconnu"
    domain_label = job_summary.get(
        "domain",
        "inconnu",
    )

rome_candidate_terms = filter_rome_candidate_terms(
    cv_terms_for_inference
)

selected_rome_terms = rank_rome_candidate_terms(
    terms=rome_candidate_terms,
    max_terms=5,
)

rome_search_terms = []
normalized_main_job = ""

if main_job_label and main_job_label != "inconnu":
    normalized_main_job = normalize_text(
        main_job_label
    )

    normalized_cv = normalize_text(cv_text)

    main_job_words = [
        word
        for word in normalized_main_job.split()
        if len(word) >= 4
    ]

    matched_main_job_words = [
        word
        for word in main_job_words
        if word in normalized_cv
    ]

    main_job_coverage = (
        len(matched_main_job_words) / len(main_job_words)
        if main_job_words
        else 0.0
    )

    # Le métier principal historique n'est prioritaire
    # que s'il est suffisamment visible dans le CV.
    if main_job_coverage >= 0.6:
        rome_search_terms.append(main_job_label)

    for term in selected_rome_terms:
        normalized_term = normalize_text(term)

        if not normalized_term:
            continue

        already_present = any(
            normalize_text(existing) == normalized_term
            for existing in rome_search_terms
        )

        if not already_present:
            rome_search_terms.append(term)

    #with st.expander("Diagnostic ROME"):
        #st.write(
            #"Termes candidats — premiers :",
            #rome_candidate_terms[:40],
        #)

        #st.write(
            #"Termes sélectionnés :",
            #selected_rome_terms,
        #)

        #st.write(
            #"Requêtes ROME réellement envoyées :",
            #rome_search_terms,
        #)

    rome_jobs = infer_rome_jobs_from_terms(
        rome_search_terms,
        max_terms=6,
    )

    rome_jobs = rank_rome_jobs_against_cv(
        cv_text=cv_text,
        rome_jobs=rome_jobs,
        main_job_label=main_job_label,
        domain_label=domain_label,
        )

    rome_reference = st.session_state.get("rome_reference", {})
    cached_analysis = st.session_state.get("rome_visibility_analysis", {})
    cached_cv_text = st.session_state.get("rome_visibility_cv_text", "")

    if cached_cv_text != cv_text or not cached_analysis:
        rome_visibility_analysis = evaluate_rome_reference(
            cv_text=cv_text,
            rome_reference=rome_reference,
        )

        st.session_state[
            "rome_visibility_analysis"
        ] = rome_visibility_analysis

        st.session_state[
            "rome_visibility_cv_text"
        ] = cv_text

    else:
        rome_visibility_analysis = cached_analysis
    # ------------------------
    # Mots-clés suggérés
    # ------------------------
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
        job_summary=job_summary, topics=topics, max_queries=5
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
   # with st.expander("Voir le texte extrait"):
        #st.write(cv_text)

    #st.markdown("### Métier principal détecté dans votre CV")
    #st.success(main_job_label.capitalize())
    #if rome_jobs:
        #st.markdown("### Métiers ROME candidats détectés")
        #for job in rome_jobs[:5]:
            #st.info(
                #f"{job.get('metier_code', '')} — {job.get('metier_libelle', '')}"
            #)

    st.markdown("### Compétences et axes transférables détectés dans votre CV")

    if topics:
        cols = st.columns(4)
        for i, t in enumerate(topics[:8]):
            cols[i % 4].info(t)
    else:
        st.write("Aucun thème dominant détecté.")

    #if skills:
        #st.markdown("### Compétences dominantes estimées")
        #for skill in skills:
            #st.write(f"• {skill}")
    # =====================================================
# Choix de direction métier par l'utilisateur
# =====================================================

detected_family = cv_families[0] if cv_families else None

if cv_families:
    st.markdown("### Choisir une direction professionnelle")

    current_selected_family = st.session_state.get("selected_family")

    # Si l'ancienne sélection n'existe plus dans le nouveau CV,
    # on revient à la dominante détectée.
    if current_selected_family in cv_families:
        selected_index = cv_families.index(current_selected_family)
    else:
        selected_index = 0

    selected_family_ui = st.selectbox(
        "Tu peux garder la direction proposée ou en choisir une autre :",
        options=cv_families,
        index=selected_index,
        format_func=display_family_label,
    )

    # La dominante automatique n'est pas considérée
    # comme une réorientation choisie par l'utilisateur.
    if selected_family_ui == detected_family:
        st.session_state["selected_family"] = None
        selected_family = None
    else:
        st.session_state["selected_family"] = selected_family_ui
        selected_family = selected_family_ui

    st.caption(
        "Direction proposée à partir du CV : "
        f"{display_family_label(detected_family)}"
    )

    secondary_labels = [
        display_family_label(family)
        for family in cv_families[1:]
    ]

    if secondary_labels:
        st.write(
            "Ton CV présente également des éléments utiles dans les "
            "directions suivantes :"
        )

        for label in secondary_labels:
            st.write(f"• {label}")

else:
    selected_family = None

    if uploaded is not None:
        st.info(
            "Aucune direction professionnelle suffisamment claire "
            "n'a été détectée dans le CV."
        )

# =====================================================
# Direction utilisée par le moteur
# =====================================================

has_user_override = selected_family is not None

direction_family = (
    selected_family
    if has_user_override
    else main_family
)

sub_family = infer_sub_family(
    topics,
    direction_family,
)

if has_user_override:
    st.caption(
        "La recherche sera orientée vers : "
        f"{display_family_label(direction_family)}"
    )
    secondary_family = cv_families[1] if len(cv_families) > 1 else None
    if secondary_family:
        st.write(
            "Profil secondaire détecté : " f"{display_family_label(secondary_family)}"
        )

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
        all_communes = search_communes_geo_api(location_query)
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
                f"Commune sélectionnée : {selected_commune['libelle']} | "
                f"CP {selected_commune['codePostal']}"
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

        if selected_family:
            queries.append(selected_family)

        if keywords.strip():
            manual_keywords = [k.strip() for k in keywords.split(",") if k.strip()]
            queries.extend(manual_keywords)

        for q in st.session_state.get("generated_queries", []):
            if q not in queries:
                queries.append(q)

        queries = dedupe_keep_order(queries)
        st.session_state["last_search_queries"] = queries

        if not queries:
            st.warning("Aucune requête de recherche disponible.")
        else:
            with st.spinner("Héphaïstos recherche et classe les offres..."):
                offers_raw = fetch_offers_multi_queries(
                    queries=queries,
                    base_params=base_params,
                    max_results_per_query=max_results,
                    debug=False,
                )
            st.write(f"Offres récupérées : {len(offers_raw)}")

            scored = []

            for o in offers_raw:
                description = to_text(o.get("text", ""))

                if len(description.strip()) < 50:
                    continue

                result = score_cv_offer(to_text(cv_text), description)

                offer_title = to_text(o.get("title", ""))
                offer_description = description

                score_value = int(result.get("score", 0) or 0)
                matched_terms = result.get("matched_terms", []) or []
                missing_terms = result.get("missing_terms", []) or []

                realistic_summary = build_realistic_opportunity_summary(
                    score=score_value,
                    cv_text=to_text(cv_text),
                    offer_title=offer_title,
                    offer_text=offer_description,
                    cv_terms=extract_terms(to_text(cv_text)),
                    offer_terms=extract_terms(offer_description),
                )

                offer_families = get_top_cv_families(description)
                o["offer_families"] = offer_families

                selected_family = st.session_state.get("selected_family")
                cv_main_family = (
                    selected_family
                    if selected_family
                    else (cv_families[0] if cv_families else None)
                )
                offer_main_family = offer_families[0] if offer_families else None

                adjusted_score = score_value

                title_text = offer_title.lower()
                description_lower = description.lower()

                if (
                    cv_main_family
                    and offer_main_family
                    and cv_main_family == offer_main_family
                ):
                    adjusted_score += 12
                elif offer_main_family and offer_main_family in cv_families[:2]:
                    adjusted_score += 6
                elif (
                    cv_main_family
                    and offer_main_family
                    and offer_main_family not in cv_families
                ):
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
                    and offer_main_family not in cv_families[:2]
                ):
                    adjusted_score -= 6

                adjusted_score = max(0, min(100, adjusted_score))

                o["score"] = adjusted_score
                o["base_score"] = score_value
                o["matched_terms"] = matched_terms
                o["missing_terms"] = missing_terms
                o["realistic_opportunity"] = realistic_summary

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
        title = to_text(o.get("title", "Sans titre"))
        company = to_text(o.get("company", ""))
        location = to_text(o.get("location", ""))
        url = to_text(o.get("url", ""))
        score = o.get("score", 0)

        realistic = (
            o.get("realistic_opportunity", {}) or {}
        )

        realistic_verdict = realistic.get(
            "verdict",
            "à étudier",
        )

        realistic_explanation = realistic.get(
            "explanation",
            "",
        )

        with st.container(
                border=True,
                key=f"offer-card-{i}",
            ):
            st.write(f"**{score}/100 — {title}**")

            st.caption(
                f"Opportunité réaliste : "
                f"{realistic_verdict}"
            )

            if realistic_explanation:
                st.write(
                    f"Pourquoi : "
                    f"{realistic_explanation}"
                )

            if company:
                st.write(
                    f"**Entreprise :** {company}"
                )

            if location:
                st.write(
                    f"**Lieu :** {location}"
                )

            if url:
                st.markdown(
                    f"**Lien pour postuler :** "
                    f"[Ouvrir l'annonce]({url})"
                )

            if st.button(
                "Utiliser cette offre",
                key=f"use_offer_{i}",
            ):
                st.session_state["offer_text"] = (
                    to_text(o.get("text", ""))
                )

                st.session_state[
                    "selected_offer_meta"
                ] = {
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": url,
                    "score": o.get("score", 0),
                    "base_score": o.get(
                        "base_score",
                        0,
                    ),
                    "realistic_opportunity": (
                        o.get(
                            "realistic_opportunity",
                            {},
                        )
                        or {}
                    ),
                }

                selected_offer_text = (
                    st.session_state.get(
                        "offer_text",
                        "",
                    )
                )

                if (
                    cv_text
                    and selected_offer_text.strip()
                ):
                    result = score_cv_offer(
                        to_text(cv_text),
                        to_text(
                            selected_offer_text
                        ),
                    )

                    st.session_state[
                        "last_analysis"
                    ] = result

                    st.session_state[
                        "show_analysis_dialog"
                    ] = True
                else:
                    st.session_state[
                        "show_analysis_dialog"
                    ] = False

            with st.expander(
                "Voir description",
                expanded=False,
            ):
                st.write(
                    to_text(
                        o.get(
                            "text",
                            "Description non disponible",
                        )
                    )
                )


# =========================================================
# ANALYSER UNE OFFRE EXTERNE
# =========================================================
selected_offer_meta = (
    st.session_state.get(
        "selected_offer_meta",
        {},
    )
    or {}
)

with st.expander(
    "Vous avez trouvé une offre ailleurs ?",
    expanded=False,
):
    st.write(
        "Colle ici une annonce trouvée sur un autre "
        "site pour la comparer avec ton CV."
    )

    st.text_area(
        "Texte de l’offre",
        height=180,
        key="offer_text",
    )

    if st.button(
        "Analyser cette offre externe",
        key="analyze-external-offer",
    ):
        external_offer_text = (
            st.session_state.get(
                "offer_text",
                "",
            )
        )

        if not cv_text:
            st.warning(
                "Importe d’abord un CV."
            )

        elif not external_offer_text.strip():
            st.warning(
                "Colle d’abord le texte de l’offre."
            )

        else:
            result = score_cv_offer(
                to_text(cv_text),
                to_text(
                    external_offer_text
                ),
            )

            st.session_state[
                "last_analysis"
            ] = result

            # Une offre externe ne possède pas les
            # scores et métadonnées du Top 30.
            st.session_state[
                "selected_offer_meta"
            ] = {}

            selected_offer_meta = {}

            st.session_state[
                "show_analysis_dialog"
            ] = True

@st.dialog(
    "Analyse CV vs offre",
    width="large",
)
def show_analysis_dialog():
    analysis = st.session_state.get(
        "last_analysis"
    )

    if not analysis:
        st.warning(
            "Aucune analyse disponible."
        )
        return
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

    # Détection simple du niveau du profil
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

    st.markdown("### Comprendre cette offre")

    if selected_offer_score is not None:
        st.markdown(
            f"**Cette offre semble globalement adaptée : {selected_offer_score}/100**"
        )

    st.markdown(
        f"**Ce que ton CV montre dans cette annonce : {score}/100 — {interpretation}**"
    )

    if selected_offer_score is not None:
        st.write(
            "Cette offre remonte parce qu’elle semble cohérente avec ton profil et ta direction métier. "
            "Le score ci-dessous regarde plus strictement ce qui "
            "apparaît réellement dans ton CV par rapport à l’annonce."
        )

    if selected_offer_base_score is not None:
        st.write(
            f"Score de départ avant ajustements métier : {selected_offer_base_score}/100"
        )

    if selected_realistic_verdict:
        st.write(f"Conseil de positionnement : {selected_realistic_verdict}")

    if selected_realistic_explanation:
        st.write(f"Pourquoi : {selected_realistic_explanation}")

    st.markdown("### Conseil rapide")
    selected_family = st.session_state.get("selected_family")

    positioning_advice = selected_realistic_verdict

    direction_text = (
        f'dans la direction "{selected_family}"'
        if selected_family
        else "par rapport à ton profil"
    )

    if positioning_advice in ["très réaliste", "réaliste"]:
        st.success(f" Tu peux postuler : {direction_text}, cette offre est cohérente.")

    elif positioning_advice in ["accessible"]:
        st.info(
            f" Tu peux tenter ta chance : {direction_text}, ton profil reste crédible avec un CV ajusté."
        )

    elif positioning_advice in ["exploratoire"]:
        st.warning(
            f" Cette piste peut se tenter : {direction_text}, il manque encore des éléments visibles dans ton CV."
        )

    elif positioning_advice in ["possible avec réserve"]:
        st.warning(
            f" Cette offre peut se tenter : {direction_text}, mais un point concret peut freiner ta candidature."
        )

    else:
        st.error(
            f" {direction_text.capitalize()}, cette offre paraît encore trop éloignée."
        )

        st.markdown("#### Ce que ça veut dire concrètement")

    if positioning_advice in ["très réaliste", "réaliste"]:
        st.write(
            f"{direction_text.capitalize()}, ton profil correspond bien à ce type "
            f"de poste. Les recruteurs devraient comprendre rapidement ta candidature."
        )

    elif positioning_advice in ["accessible"]:
        st.write(
            f"{direction_text.capitalize()}, tu n’as pas tous les éléments,"
            "mais ton profil reste cohérent avec l’offre."
        )

    elif positioning_advice in ["exploratoire"]:
        st.write(
            f"{direction_text.capitalize()}, ton profil s’en rapproche, "
            "mais l’annonce attend des éléments peu visibles dans ton CV."
        )

    elif positioning_advice in ["possible avec réserve"]:
        st.write(
            f"{direction_text.capitalize()}, un point concret peut poser problème"
            "(mobilité, expérience, compétences spécifiques)."
        )
    else:
        st.write(
            f"{direction_text.capitalize()}, l’offre reste encore trop éloignée de ton profil actuel."
        )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Forces principales")

        matched_terms = analysis.get("matched_terms", [])
        display_matched_terms = prepare_display_terms(
            matched_terms,
            max_items=8,
        )

        def get_strength_category(term):
            normalized_term = str(term).lower()

            category_keywords = {
                "communication": (
                    "communication",
                    "réseau social",
                    "reseau social",
                    "réseaux sociaux",
                    "reseaux sociaux",
                    "digital",
                    "contenu",
                    "rédaction",
                    "redaction",
                ),
                "accueil": (
                    "accueil",
                    "standard",
                    "téléphonique",
                    "telephonique",
                    "réception",
                    "reception",
                ),
                "numerique": (
                    "office",
                    "excel",
                    "word",
                    "powerpoint",
                    "logiciel",
                    "informatique",
                    "numérique",
                    "numerique",
                    "tableau",
                ),
                "relationnel": (
                    "relation client",
                    "relation usager",
                    "service client",
                    "accompagnement",
                    "écoute",
                    "ecoute",
                ),
            }

            for category, keywords in category_keywords.items():
                if any(
                    keyword in normalized_term
                    for keyword in keywords
                ):
                    return category

            return "general"

        if display_matched_terms:
            strength_columns = st.columns(2)

            for index, term in enumerate(display_matched_terms):
                column = strength_columns[index % 2]

                with column:
                    with st.container(
                        key=f"strength-card-{index}",
                    ):
                        st.write(term)
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
                        suggestion_text = "Accueil des clients lors de stages ou missions, gestion des demandes simples"
                    elif profile_level == "experienced":
                        suggestion_text = (
                            "Gestion de la relation client, suivi des demandes"
                        )
                        "et amélioration de la satisfaction"
                    else:
                        suggestion_text = "Accueil des clients, traitement des demandes et suivi des dossiers"

                elif "bureautique" in label_lower:
                    if profile_level == "junior":
                        suggestion_text = "Utilisation basique de Word et Excel pour saisir et organiser des données"
                    elif profile_level == "experienced":
                        suggestion_text = "Maîtrise avancée des outils bureautiques"
                        "(Excel, reporting, tableaux de suivi)"
                    else:
                        suggestion_text = (
                            "Utilisation de Word, Excel et outils bureautiques"
                        )
                        "pour le suivi et la gestion des données"

                elif "analyse" in label_lower or "suivi" in label_lower:
                    if profile_level == "junior":
                        suggestion_text = "Participation au suivi d’activité et mise à jour de tableaux simples"
                    elif profile_level == "experienced":
                        suggestion_text = "Analyse de données, suivi de performance et reporting régulier"
                    else:
                        suggestion_text = "Suivi d’activité, mise à jour de tableaux Excel et reporting simple"

                elif "qualité" in label_lower or "conformité" in label_lower:
                    suggestion_text = "Contrôle de conformité, respect des procédures et suivi de la qualité"

                elif (
                    "organisation" in label_lower
                    or "coordination" in label_lower
                    or "planning" in label_lower
                ):
                    suggestion_text = "Organisation des tâches, coordination d’activités et suivi de planning"

                if suggestion_text:
                    st.success(f"À ajouter dans ton CV : {suggestion_text}")

                if advice:
                    st.write(f"Conseil : {advice}")

                st.write("")
        else:
            st.write("Aucune compétence manquante interprétée.")

    
            

    st.markdown("### Mots forts")

    raw_strong_terms = prepare_display_terms(
        analysis.get("matched_terms", []), max_items=40
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
    suggestions = build_cv_suggestions_from_competencies(
        missing_competencies
    )

    if suggestions:
        for suggestion in suggestions:
            st.write(f"• {suggestion}")
    else:
        st.write("Aucune suggestion générée.")

    if st.button(
        "Adapter mon CV à cette offre",
        key="open_cv_workshop",
        type="primary",
        use_container_width=True,
    ):
        st.session_state["cv_adaptation_offer_text"] = (
            st.session_state.get("offer_text", "")
        )

        st.session_state["cv_adaptation_direction"] = direction_family

        st.session_state["cv_adaptation_analysis"] = analysis

        st.switch_page("pages/atelier_cv.py")

    if st.button(
        "Fermer l’analyse",
        key="close-analysis-dialog",
        use_container_width=True,
    ):
        st.session_state["show_analysis_dialog"] = False
        st.rerun()


if st.session_state.get("show_analysis_dialog", False):
    show_analysis_dialog()
