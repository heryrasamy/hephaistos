import streamlit as st


st.set_page_config(
    page_title="Atelier CV | Héphaïstos",
    layout="wide",
)


st.markdown("## Adapter mon CV à cette offre")

cv_original_text = st.session_state.get(
    "cv_original_text",
    "",
)

if cv_original_text:
    st.success("Le CV a bien été transmis à l’Atelier.")
    st.caption(
        f"{len(cv_original_text)} caractères récupérés."
    )
else:
    st.warning(
        "Aucun CV n’est disponible. "
        "Importe d’abord un CV dans Héphaïstos."
    )

offer_text = st.session_state.get(
    "cv_adaptation_offer_text",
    "",
)

if offer_text:
    st.success("L’offre a bien été transmise à l’Atelier.")
    st.caption(
        f"{len(offer_text)} caractères récupérés pour l’offre."
    )
else:
    st.warning(
        "Aucune offre n’a été transmise à l’Atelier."
    )

adaptation_direction = st.session_state.get(
    "cv_adaptation_direction"
)

if adaptation_direction:
    direction_label = adaptation_direction.replace(
        "_",
        " ",
    ).capitalize()

    st.info(
        f"Direction professionnelle transmise : {direction_label}"
    )
else:
    st.warning(
        "Aucune direction professionnelle n’a été transmise."
    )
adaptation_analysis = st.session_state.get(
    "cv_adaptation_analysis"
)

if isinstance(adaptation_analysis, dict):
    compatibility_score = adaptation_analysis.get(
        "score",
        0,
    )

    st.info(
        f"Analyse transmise — compatibilité : "
        f"{compatibility_score} %"
    )
else:
    st.warning(
        "Aucune analyse CV–offre n’a été transmise."
    )

if st.button("Retour à Héphaïstos"):
    st.switch_page("main.py")