import base64
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from cv_pdf import build_cv_pdf


st.set_page_config(
    page_title="Validation du CV",
    layout="wide",
)
project_root = Path(
    __file__
).resolve().parents[2]

validation_logo_path = (
    project_root
    / "Assets"
    / "Logo boussole sf.png"
)

validation_logo_html = ""

if validation_logo_path.exists():
    validation_logo_base64 = (
        base64.b64encode(
            validation_logo_path.read_bytes()
        ).decode("ascii")
    )

    validation_logo_html = (
        '<img class="validation-page-logo" '
        'src="data:image/png;base64,'
        f'{validation_logo_base64}" '
        'alt="La Boussole de l’emploi">'
    )

validation_sailboat_path = (
    project_root
    / "Assets"
    / "Logo_Voilier SF.png"
)

validation_sailboat_html = ""

if validation_sailboat_path.exists():
    validation_sailboat_base64 = (
        base64.b64encode(
            validation_sailboat_path.read_bytes()
        ).decode("ascii")
    )

    validation_sailboat_html = (
        '<img '
        'class="validation-flow-sailboat" '
        'src="data:image/png;base64,'
        f'{validation_sailboat_base64}" '
        'alt="">'
    )

st.html(
    """
    <style>
            html,
        body,
        [data-testid="stAppViewContainer"] {
            background: #f7f8ff !important;
        }

        [data-testid="stHeader"] {
            background: #f7f8ff !important;
        }
        .stApp {
            background: #f7f8ff;
            font-family: Arial, sans-serif;
        }

        .stApp .block-container {
            max-width: 1720px;
            padding-top: 28px;
            padding-bottom: 48px;
        }

        .stApp h1,
        .stApp h2,
        .stApp h3 {
            color: #090d67;
        }

        .validation-page-hero {
            position: relative;
            overflow: hidden;

            margin-bottom: 24px;
            padding: 28px 34px;

            border: 1px solid #d9d5ff;
            border-radius: 18px;

            background: #ffffff;
            box-shadow:
                0 14px 35px
                rgba(57, 38, 255, 0.08);
        }

        .validation-page-hero::before {
            content: "";

            position: absolute;
            top: 0;
            left: 0;

            width: 100%;
            height: 6px;

            background: linear-gradient(
                90deg,
                #4e30cd,
                #3926ff
            );
        }

        .validation-page-brand {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 24px;

            margin-bottom: 20px;
        }

        .validation-page-logo {
            display: block;
            width: 250px;
            max-width: 45%;
            height: auto;
        }
        .validation-page-kicker {
            margin: 0;
            padding: 10px 18px;

            border-radius: 999px;

            background: #f0eeff;
            color: #3926ff;

            font-size: 18px;
            font-weight: 800;
            letter-spacing: 0.04em;
        }

        .validation-page-title {
            margin: 0 0 8px;

            color: #090d67;
            font-size: clamp(
                32px,
                4vw,
                48px
            );
            font-weight: 800;
            line-height: 1.12;
        }

        .validation-page-subtitle {
            margin: 0;

            color: #555b8f;
            font-size: 17px;
            line-height: 1.5;
        }
                .validation-flow {
            display: grid;
            grid-template-columns:
                auto minmax(100px, 260px) auto;
            align-items: center;
            gap: 18px;

            max-width: 760px;
            margin: 0 auto 30px;
            padding: 13px 20px;

            border: 1px solid #d9d5ff;
            border-radius: 999px;

            background: #ffffff;
            box-shadow:
                0 8px 24px
                rgba(57, 38, 255, 0.06);
        }

        .validation-flow-label {
            color: #090d67;
            font-size: 15px;
            font-weight: 700;
            white-space: nowrap;
        }

        .validation-flow-destination {
            padding: 7px 14px;

            border-radius: 999px;

            background: linear-gradient(
                110deg,
                #4e30cd,
                #3926ff
            );

            color: #ffffff;
            font-size: 15px;
            font-weight: 700;
            white-space: nowrap;
        }


        .validation-flow-sailboat {
            position: absolute;
            z-index: 2;
            top: 50%;
            left: 100%;

            width: 52px;
            height: auto;

            transform: translate(-72%, -58%);
            filter: drop-shadow(
                0 5px 8px rgba(31, 25, 122, 0.20)
            );
    }

    .validation-flow--animated
    .validation-flow-sailboat {
        animation:
            validation-sailboat-crossing
            1.15s
            ease-out
            both;
    }

@keyframes validation-sailboat-crossing {
    from {
        left: 0;
        opacity: 0;
        transform: translate(-20%, -58%);
    }

    30% {
        opacity: 1;
    }

    to {
        left: 100%;
        opacity: 1;
        transform: translate(-72%, -58%);
    }
    }.validation-flow-track {
        position: relative;
        display: block;

        min-width: 100px;
        height: 52px;
        overflow: hidden;
    }

    .validation-flow-sailboat {
        position: absolute;
        z-index: 2;
        top: 50%;
        left: 84%;

        width: 52px;
        height: auto;

        transform: translate(-50%, -58%);

        filter: drop-shadow(
            0 5px 8px rgba(31, 25, 122, 0.20)
        );
    }

    .validation-flow--animated
    .validation-flow-sailboat {
        animation:
            validation-sailboat-crossing
            2.8s
            ease-in-out
            both;
    }


@keyframes validation-sailboat-crossing {
    from {
        left: 0;
        opacity: 0;
        transform: translate(-20%, -58%);
    }

    30% {
        opacity: 1;
    }

    to {
        left: 100%;
        opacity: 1;
        transform: translate(-72%, -58%);
    }
}

        @keyframes validation-flow-progress {
            from {
                opacity: 0.15;
                transform: scaleX(0);
            }

            to {
                opacity: 1;
                transform: scaleX(1);
            }
        }
    </style>

    <section class="validation-page-hero">

        <div class="validation-page-brand">
            VALIDATION_LOGO_HTML

            <div class="validation-page-kicker">
                L’Atelier CV
            </div>
        </div>
        <h1 class="validation-page-title">
            Comparer et valider mon CV
        </h1>

        <p class="validation-page-subtitle">
            Compare ton document original avec la version adaptée,
            puis confirme les informations avant de poursuivre.
        </p>
    </section>
        """.replace(
        "VALIDATION_LOGO_HTML",
        validation_logo_html,
    )
)

validation_payload = st.session_state.get(
    "cv_validation_payload",
    {},
)


if not validation_payload:
    st.warning(
        "Aucun CV adapté n’a été transmis "
        "à cette page."
    )

    if st.button("Retourner à l’Atelier"):
        st.switch_page(
            "pages/atelier_cv.py"
        )

    st.stop()


original_file_name = validation_payload.get(
    "original_file_name",
    "CV original",
)
original_file_bytes = validation_payload.get(
    "original_file_bytes",
    b"",
)

original_file_type = validation_payload.get(
    "original_file_type",
    "",
)

original_file_is_available = (
    isinstance(
        original_file_bytes,
        (bytes, bytearray),
    )
    and bool(original_file_bytes)
)
original_file_is_pdf = (
    original_file_type == "application/pdf"
    or original_file_name.lower().endswith(".pdf")
)

selected_template = validation_payload.get(
    "template",
    "",
)
adapted_cv_html = validation_payload.get(
    "final_html",
    "",
)
cv_photo_data_uri = str(
    validation_payload.get(
        "photo_data_uri",
        "",
    )
    or ""
)

adapted_cv_is_available = (
    isinstance(adapted_cv_html, str)
    and bool(adapted_cv_html.strip())
)
offer_signature = str(
    validation_payload.get(
        "offer_signature",
        "",
    )
)

adapted_cv_text = str(
    validation_payload.get(
        "adapted_text",
        "",
    )
)

if selected_template.strip().casefold() == "horizon":
    native_pdf_bytes = build_cv_pdf(
        template_name=selected_template,
        cv_text=adapted_cv_text,
        photo_data_uri=cv_photo_data_uri,
    )

validated_reformulations = (
    validation_payload.get(
        "reformulations",
        {},
    )
)

if not isinstance(
    validated_reformulations,
    dict,
):
    validated_reformulations = {}

if not original_file_is_available:
    st.warning(
        "Le fichier original n’est plus disponible. "
        "Réimporte le CV depuis Héphaïstos."
    )


transition_state_key = (
    f"cv_validation_sailboat_seen_"
    f"{offer_signature}_"
    f"{selected_template.lower()}"
)

transition_should_animate = not (
    st.session_state.get(
        transition_state_key,
        False,
    )
)

st.session_state[
    transition_state_key
] = True

transition_css_class = ""

if transition_should_animate:
    transition_css_class = (
        " validation-flow--animated"
    )


st.html(
    f"""
    <div class="validation-flow{transition_css_class}">
        <span class="validation-flow-label">
            Document source
        </span>

        <span class="validation-flow-track">
    {validation_sailboat_html}
</span>

        <span class="validation-flow-destination">
            Version {selected_template}
        </span>
    </div>
    """
)

original_column, adapted_column = st.columns(
    2,
    gap="large",
)


with original_column:
    st.subheader("CV original")

    if (
        original_file_is_available
        and original_file_is_pdf
    ):
        st.pdf(
            original_file_bytes,
            height=1100,
            key="original_cv_pdf",
        )

    else:
        st.warning(
            "Le CV original ne peut pas être "
            "affiché dans son format visuel."
        )


with adapted_column:
    st.subheader(
        f"CV adapté — modèle {selected_template}"
    )

    if adapted_cv_is_available:
        st.html(adapted_cv_html)

    else:
        st.warning(
            "Le rendu du CV adapté "
            "n’est pas disponible."
        )

st.divider()


validation_id = (
    f"{offer_signature}_"
    f"{selected_template.lower()}"
)

validation_results = (
    st.session_state.setdefault(
        "cv_validation_results",
        {},
    )
)

current_validation = validation_results.get(
    validation_id,
    {},
)

current_cv_is_validated = (
    current_validation.get("validated") is True
    and current_validation.get("final_html")
    == adapted_cv_html
)

st.html(
    """
    <style>
        div[data-testid="stCheckbox"] label,
        div[data-testid="stCheckbox"] label p {
            color: #090d67 !important;
        }

        div[data-testid="stCheckbox"]
        label[data-baseweb="checkbox"]
        > span:first-child {
            border: 1px solid #4e30cd !important;
            background-color: #ffffff !important;
        }

        div[data-testid="stCheckbox"]
        label[data-baseweb="checkbox"]:has(input:checked)
        > span:first-child {
            border-color: #3926ff !important;
            background-color: #3926ff !important;
        }

        button[kind="secondary"],
        [data-testid="stBaseButton-secondary"] {
            border: 1px solid #d9d5ff !important;
            border-radius: 9px !important;

            color: #090d67 !important;
            font-weight: 700 !important;

            background: #efedff !important;
            box-shadow: none !important;
        }

        button[kind="secondary"] p,
        [data-testid="stBaseButton-secondary"] p {
            color: #090d67 !important;
        }

        button[kind="primary"],
        [data-testid="stBaseButton-primary"] {
            border: 1px solid #3926ff !important;
            border-radius: 9px !important;

            color: #ffffff !important;
            font-weight: 700 !important;

            background: linear-gradient(
                110deg,
                #4e30cd 0%,
                #3926ff 100%
            ) !important;
        }

        button[kind="primary"] p,
        [data-testid="stBaseButton-primary"] p {
            color: #ffffff !important;
        }

        button[kind="primary"]:disabled,
        [data-testid="stBaseButton-primary"]:disabled {
            border-color: #d9d5ff !important;

            color: #77739b !important;

            background: #e9e7f7 !important;
            opacity: 1 !important;
        }

        button[kind="primary"]:disabled p,
        [data-testid="stBaseButton-primary"]:disabled p {
            color: #77739b !important;
        }
    </style>
    """
)
if not current_cv_is_validated:
    confirmation_key = (
        f"confirm_cv_validation_"
        f"{offer_signature}_"
        f"{selected_template.lower()}"
    )

    information_is_confirmed = st.checkbox(
        "J’ai vérifié les informations "
        "et les reformulations",
        key=confirmation_key,
    )

    back_column, validate_column = st.columns(2)

    with back_column:
        if st.button(
            "Retourner à l’Atelier",
            key="back_to_cv_workshop",
            type="secondary",
            use_container_width=True,
        ):
            st.switch_page(
                "pages/atelier_cv.py"
            )

    with validate_column:
        validate_cv = st.button(
            "Valider ce CV",
            key="validate_adapted_cv",
            type="primary",
            disabled=not information_is_confirmed,
            use_container_width=True,
        )

    if validate_cv:
        validation_results[validation_id] = {
            "validated": True,
            "template": selected_template,
            "offer_signature": offer_signature,
            "adapted_text": adapted_cv_text,
            "final_html": adapted_cv_html,
            "reformulations": (
                validated_reformulations
            ),
        }

        st.rerun()

if current_cv_is_validated:
    st.html(
        """
            <style>
        button[kind="secondary"],
        [data-testid="stBaseButton-secondary"] {
            border: 1px solid #d9d5ff !important;
            border-radius: 9px !important;

            color: #090d67 !important;
            font-weight: 700 !important;

            background: #efedff !important;
            box-shadow: none !important;
        }

        button[kind="secondary"] p,
        [data-testid="stBaseButton-secondary"] p {
            color: #090d67 !important;
        }

        button[kind="secondary"]:hover,
        [data-testid="stBaseButton-secondary"]:hover {
            border-color: #4e30cd !important;

            color: #090d67 !important;
            background: #e5e1ff !important;
        }

        .cv-ready-message {
            position: relative;

            padding: 20px 24px 17px;
            overflow: hidden;

            border: 1px solid #d9d5ff;
            border-radius: 10px;

            background: #efedff;
            color: #090d67;

            text-align: center;
        }

        .cv-ready-message::before {
            content: "";

            position: absolute;
            top: 0;
            right: 0;
            left: 0;

            height: 4px;

            background: linear-gradient(
                90deg,
                #4e30cd 0%,
                #3926ff 100%
            );
        }

        .cv-ready-title {
            margin-bottom: 5px;

            font-size: 18px;
            font-weight: 700;
        }

        .cv-ready-text {
            color: #4f5685;
            font-size: 14px;
        }
    </style>

    <div class="cv-ready-message">
        <div class="cv-ready-title">
            Ton CV est prêt.
        </div>

        <div class="cv-ready-text">
            La version validée peut maintenant
            être imprimée ou enregistrée au
            format PDF.
        </div>
    </div>
    """
    )

    pdf_download_action_html = """
    <button
        class="
            print-action
            print-action--primary
        "
        type="button"
        onclick="window.print()"
    >
        Enregistrer en PDF
    </button>
    """

    if (
        selected_template.strip().casefold() == "horizon"
        and native_pdf_bytes
    ):
        native_pdf_base64 = base64.b64encode(
            native_pdf_bytes
        ).decode("ascii")

        pdf_download_action_html = f"""
            <a
                class="
                    print-action
                    print-action--primary
                "
                href="data:application/pdf;base64,{native_pdf_base64}"
                download="CV_Horizon.pdf"
                style="
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-sizing: border-box;
                    text-decoration: none;
                "
            >
                Enregistrer en PDF
            </a>
        """

    printable_cv_html = str(
        validation_payload.get(
            "final_html",
            "",
        )
    )

    print_component_document = (
        """
        <!DOCTYPE html>

        <html lang="fr">
        <head>
            <meta charset="utf-8">

            <style>
                html,
                body {
                    margin: 0;
                    padding: 0;

                    font-family:
                        Arial,
                        sans-serif;

                    background: transparent;
                }

                .print-actions {
                    display: grid;
                    grid-template-columns:
                        repeat(2, minmax(0, 1fr));
                    gap: 14px;
                }

                .print-action {
                    min-height: 48px;
                    padding: 10px 18px;

                    border: 1px solid #3926ff;
                    border-radius: 9px;

                    color: #090d67;
                    font-size: 16px;
                    font-weight: 700;

                    background: #ffffff;
                    cursor: pointer;
                }

                .print-action--primary {
                    color: #ffffff;

                    background: linear-gradient(
                        110deg,
                        #4e30cd 0%,
                        #3926ff 100%
                    );
                }

                .print-help {
                    margin: 10px 0 0;

                    color: #4f5685;
                    font-size: 13px;
                    text-align: center;
                }

                .printable-cv {
                    display: none;
                }

                @media print {
                    @page {
                        size: A4;
                        margin: 0;
                    }

                    html,
                    body {
                        background: #ffffff;
                    }

                    .print-actions,
                    .print-help {
                        display: none;
                    }

                    .printable-cv {
                        display: block;
                    }
                    .printable-cv,
                    .printable-cv *,
                    .printable-cv *::before,
                    .printable-cv *::after {
                        -webkit-print-color-adjust:
                            exact !important;

                        print-color-adjust:
                            exact !important;
                    }
                    .cv-cap-page,
                    .cv-horizon-page {
                        width: 100% !important;
                        max-width: none !important;
                        margin: 0 !important;

                        border: none !important;
                        border-radius: 0 !important;
                        box-shadow: none !important;
                    }
                    .cv-cap-header,
                    .cv-horizon-header {
                        break-after: avoid-page !important;
                        page-break-after: avoid !important;
                    }

                    .cv-cap-grid,
                    .cv-horizon-grid {
                        break-before: avoid-page !important;
                        page-break-before: avoid !important;

                        break-inside: auto !important;
                        page-break-inside: auto !important;
                    }

                    .cv-cap-header:not(
                    .cv-cap-header--without-photo
                    ),
                    .cv-horizon-header:not(
                        .cv-horizon-header--without-photo
                    ) {
                        display: grid !important;
                        grid-template-columns:
                            145px minmax(0, 1fr) !important;
                        align-items: center !important;
                    }

                    .cv-cap-header--without-photo,
                    .cv-horizon-header--without-photo {
                        grid-template-columns:
                            minmax(0, 1fr) !important;
                    }

                    .cv-cap-frame,
                    .cv-horizon-frame {
                        display: block !important;
                    }

                    .cv-cap-header--without-photo
                    .cv-cap-frame,
                    .cv-horizon-header--without-photo
                    .cv-horizon-frame {
                        display: none !important;
                    }

                    .cv-cap-grid {
                        display: grid !important;
                        grid-template-columns:
                            minmax(0, 1.75fr)
                            minmax(210px, 0.85fr) !important;

                        break-inside: auto !important;
                        page-break-inside: auto !important;
                    }

                    .cv-horizon-grid {
                        display: grid !important;
                        grid-template-columns:
                            minmax(0, 1.7fr)
                            minmax(210px, 0.85fr) !important;

                        break-inside: auto !important;
                        page-break-inside: auto !important;
                    }

                    .cv-cap-main,
                    .cv-cap-sidebar,
                    .cv-horizon-main,
                    .cv-horizon-sidebar {
                        min-height: 0 !important;
                        overflow: visible !important;

                        break-inside: auto !important;
                        page-break-inside: auto !important;
                    }

                    .cv-cap-page,
                    .cv-horizon-page {
                        position: relative !important;
                        overflow: visible !important;
                    }

                    .cv-cap-header,
                    .cv-horizon-header {
                        position: absolute !important;
                        z-index: 2;

                        top: 0 !important;
                        right: 0 !important;
                        left: 0 !important;

                        width: 100% !important;
                        box-sizing: border-box !important;
                    }

                    .cv-cap-grid {
                        margin-top: 0 !important;
                        padding-top: 265px !important;
                    }

                    .cv-horizon-grid {
                        margin-top: 0 !important;
                        padding-top: 280px !important;
                    }
                    .cv-cap-section h3,
                    .cv-horizon-section h3 {
                        break-after: avoid-page !important;
                        page-break-after: avoid !important;
                    }

                    .cv-cap-section h3 + *,
                    .cv-horizon-section h3 + * {
                        break-before: avoid-page !important;
                        page-break-before: avoid !important;
                    }

                    .cv-cap-sidebar .cv-cap-section,
                    .cv-horizon-sidebar .cv-horizon-section {
                        break-inside: avoid-page !important;
                        page-break-inside: avoid !important;
                    }

                    .cv-cap-line,
                    .cv-horizon-line {
                        break-inside: avoid-page !important;
                        page-break-inside: avoid !important;
                    }

                    .cv-cap-sidebar,
                    .cv-horizon-sidebar {
                        -webkit-box-decoration-break:
                            clone !important;

                        box-decoration-break:
                            clone !important;
                    }

                }
            </style>
        </head>

        <body>
            <div class="print-actions">
                <button
                    class="print-action"
                    type="button"
                    onclick="window.print()"
                >
                    Imprimer le CV
                </button>

                                __PDF_DOWNLOAD_ACTION__
            </div>

            <p class="print-help">
                Dans la fenêtre d’impression,
                choisis ton imprimante ou
                « Enregistrer au format PDF ».
            </p>

            <div class="printable-cv">
                __PRINTABLE_CV__
            </div>
        </body>
        </html>
        """
        .replace(
            "__PRINTABLE_CV__",
            printable_cv_html,
        )
        .replace(
            "__PDF_DOWNLOAD_ACTION__",
            pdf_download_action_html,
        )
    )

    components.html(
        print_component_document,
        height=100,
        scrolling=False,
    )
    if st.button(
        "Retourner à l’Atelier",
        key="back_after_cv_validation",
        type="secondary",
        use_container_width=True,
    ):
        st.switch_page(
            "pages/atelier_cv.py"
        )