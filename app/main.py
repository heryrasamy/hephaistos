import io
import re
from collections import Counter

import streamlit as st
from pypdf import PdfReader
from docx import Document

st.set_page_config(page_title="Hephaistos", page_icon="🔥", layout="wide")
st.title("Hephaistos 🔥")
st.caption("Forge intelligente pour candidatures. Version 0.3 (score local)")

# ---- Extraction texte ----
def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts).strip()

def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs).strip()

# ---- Nettoyage / tokenisation ----
def normalize_text(txt: str) -> str:
    txt = txt.lower()
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()

def tokenize(txt: str) -> list[str]:
    # Mots simples (lettres + chiffres + + # -) ex: c#, c++, seo, wordpress
    return re.findall(r"[a-z0-9\+\#\-]{2,}", txt.lower())

# Petite base de compétences (v0) que nous enrichirons
SKILLS = [
    "wordpress", "seo", "sem", "google", "analytics", "tag", "manager", "gtm",
    "html", "css", "javascript", "react", "php", "mysql", "python",
    "shopify", "prestashop", "wix", "webflow",
    "figma", "photoshop", "illustrator", "canva",
    "git", "github", "linux", "windows",
    "support", "helpdesk", "ticket", "saisie", "excel"
]

# Mots "métier" (v0)
JOB_HINTS = {
    "webmaster": ["webmaster", "site", "cms", "wordpress", "wix", "seo", "html", "css"],
    "support informatique": ["support", "helpdesk", "ticket", "incident", "utilisateurs", "glpi"],
    "développeur web": ["javascript", "react", "python", "php", "api", "github", "git"],
    "assistant administratif": ["saisie", "excel", "planning", "reporting", "facturation"],
}

def extract_skills(cv_text: str) -> list[str]:
    txt = normalize_text(cv_text)
    found = []
    for s in SKILLS:
        if re.search(rf"\b{re.escape(s)}\b", txt):
            found.append(s)
    return sorted(set(found))

def guess_job(cv_text: str) -> tuple[str, int]:
    txt = normalize_text(cv_text)
    best_job = "inconnu"
    best_score = 0
    for job, hints in JOB_HINTS.items():
        score = sum(1 for h in hints if re.search(rf"\b{re.escape(h)}\b", txt))
        if score > best_score:
            best_score = score
            best_job = job
    return best_job, best_score

def match_score(cv_text: str, target_job: str) -> int:
    """
    Score 0-100 très simple:
    - bonus si mots du métier cible présents
    - bonus si compétences détectées
    """
    txt = normalize_text(cv_text)
    tokens = set(tokenize(txt))

    target = target_job.lower().strip()
    target_words = [w for w in re.findall(r"[a-z0-9\+\#\-]{2,}", target) if w]

    # Mots clés du métier (si on a une base)
    hints = JOB_HINTS.get(target, [])
    keywords = set(target_words + hints)

    keyword_hits = sum(1 for k in keywords if k in tokens)
    skills_hits = len(extract_skills(cv_text))

    # Pondération v0 (ajustable)
    raw = keyword_hits * 12 + skills_hits * 6
    return max(0, min(100, raw))

# ---- UI ----
with st.sidebar:
    st.header("Profil")
    metier = st.text_input("Métier cible", "Webmaster")
    ville = st.text_input("Ville", "Paris")
    remote = st.checkbox("Télétravail", value=True)

st.subheader("1) Importer ton CV")
cv_file = st.file_uploader("Choisis un CV (PDF ou DOCX)", type=["pdf", "docx"])

cv_text = ""
if cv_file is not None:
    data = cv_file.getvalue()
    try:
        if cv_file.name.lower().endswith(".pdf"):
            cv_text = extract_text_from_pdf(data)
        else:
            cv_text = extract_text_from_docx(data)
    except Exception as e:
        st.error(f"Erreur lecture CV: {e}")

st.subheader("2) Aperçu texte extrait")
if cv_file is None:
    st.info("Importe un CV pour afficher le texte extrait.")
else:
    if cv_text.strip():
        st.text_area("Texte extrait (lecture seule)", cv_text, height=250)
    else:
        st.warning("Texte vide. Si ton PDF est scanné, il faudra un OCR (plus tard).")

st.subheader("3) Analyse locale (sans IA)")
if cv_text.strip():
    skills = extract_skills(cv_text)
    guessed_job, guessed_score = guess_job(cv_text)
    score = match_score(cv_text, metier)

    col1, col2, col3 = st.columns(3)
    col1.metric("Score compatibilité", f"{score}/100")
    col2.metric("Métier détecté (approx.)", guessed_job)
    col3.metric("Indice détection", str(guessed_score))

    st.write("Compétences détectées:")
    if skills:
        st.write(", ".join(skills))
    else:
        st.write("Aucune compétence v0 trouvée (on enrichira la liste).")

    st.caption("Prochaine étape: brancher l’IA pour reformuler CV/LM et améliorer le scoring.")
else:
    st.info("Importe un CV pour lancer l’analyse.")

st.subheader("4) Radar (bientôt)")
st.write("Métier:", metier)
st.write("Ville:", ville)
st.write("Télétravail:", "Oui" if remote else "Non")