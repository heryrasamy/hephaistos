import base64
import html
import io
import unicodedata

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Frame,
    KeepInFrame,
    Paragraph,
    Spacer,
)


HORIZON_DARK = HexColor("#090d67")
HORIZON_PURPLE = HexColor("#4e30cd")
HORIZON_BLUE = HexColor("#3926ff")
HORIZON_TURQUOISE = HexColor("#22bfc4")
HORIZON_SIDEBAR = HexColor("#eefafa")
HORIZON_LIGHT = HexColor("#f7f8ff")


def _normalize_heading(value):
    normalized_value = unicodedata.normalize(
        "NFKD",
        str(value).casefold(),
    )

    normalized_value = "".join(
        character
        for character in normalized_value
        if not unicodedata.combining(character)
    )

    normalized_value = (
        normalized_value
        .replace("’", "'")
        .replace("œ", "oe")
    )

    return " ".join(
        normalized_value.split()
    ).strip(" :.-")


def _is_letter_spaced_identity(value):
    identity_words = [
        word.strip(" .,:;|-/")
        for word in value.split()
        if word.strip(" .,:;|-/")
    ]

    single_letter_words = [
        word
        for word in identity_words
        if len(word) == 1
        and word.isalpha()
    ]

    return (
        len(identity_words) >= 6
        and len(single_letter_words)
        >= int(len(identity_words) * 0.70)
    )


def _parse_horizon_text(cv_text):
    heading_map = {
        _normalize_heading("PROFIL"): "profile",
        _normalize_heading("À PROPOS"): "profile",
        _normalize_heading(
            "RÉSUMÉ PROFESSIONNEL"
        ): "profile",

        _normalize_heading(
            "EXPÉRIENCE PROFESSIONNELLE"
        ): "experience",
        _normalize_heading(
            "EXPÉRIENCES PROFESSIONNELLES"
        ): "experience",
        _normalize_heading(
            "PARCOURS PROFESSIONNEL"
        ): "experience",
        _normalize_heading(
            "PARCOURS PROFESSIONNELS"
        ): "experience",

        _normalize_heading(
            "RÉALISATIONS WEB"
        ): "projects",
        _normalize_heading(
            "PROJET TECHNIQUE"
        ): "projects",
        _normalize_heading(
            "PROJET PERTINENT"
        ): "projects",
        _normalize_heading(
            "PROJETS PERTINENTS"
        ): "projects",
        _normalize_heading("PROJETS"): "projects",

        _normalize_heading("COMPÉTENCES"): "skills",
        _normalize_heading(
            "MES COMPÉTENCES"
        ): "skills",
        _normalize_heading(
            "COMPÉTENCES CIBLÉES"
        ): "skills",
        _normalize_heading(
            "COMPÉTENCES PROFESSIONNELLES"
        ): "skills",

        _normalize_heading("OUTILS"): "tools",
        _normalize_heading(
            "OUTILS INFORMATIQUES"
        ): "tools",

        _normalize_heading("FORMATION"): "training",
        _normalize_heading("FORMATIONS"): "training",
        _normalize_heading("DIPLÔMES"): "training",

        _normalize_heading("LANGUES"): "languages",
        _normalize_heading(
            "LANGUES ET FORMATION"
        ): "languages_training",

        _normalize_heading(
            "CENTRES D'INTÉRÊT"
        ): "interests",
    }

    sections = {
        "header": [],
        "profile": [],
        "experience": [],
        "projects": [],
        "skills": [],
        "tools": [],
        "training": [],
        "languages": [],
        "languages_training": [],
        "interests": [],
    }

    current_section = "header"
    contact_lines = []

    for source_line in str(cv_text).splitlines():
        clean_line = source_line.strip()

        if not clean_line:
            continue

        normalized_heading = _normalize_heading(
            clean_line.rstrip(":")
        )
        if (
            "candidature" in normalized_heading
            and "mobilite" in normalized_heading
        ):
            continue

        heading_signature = "".join(
            character
            for character in normalized_heading
            if character.isalnum()
        )

        if heading_signature.startswith(
            ("centredint", "centresdint")
        ):
            detected_section = "interests"
        else:
            detected_section = next(
                (
                    section_name
                    for heading_name, section_name
                    in heading_map.items()
                    if "".join(
                        character
                        for character in heading_name
                        if character.isalnum()
                    )
                    == heading_signature
                ),
                None,
            )

        if (
            detected_section
            and len(normalized_heading.split()) == 1
            and clean_line[0].islower()
        ):
            detected_section = None

        if detected_section:
            current_section = detected_section
            continue

        normalized_contact = _normalize_heading(
            clean_line
        )

        contact_prefixes = (
            "mail",
            "email",
            "courriel",
            "telephone",
            "tel",
            "numero",
        )

        line_is_contact = (
            "@" in clean_line
            or any(
                normalized_contact == prefix
                or normalized_contact.startswith(
                    prefix + " "
                )
                for prefix in contact_prefixes
            )
        )

        if line_is_contact:
            contact_lines.append(clean_line)
            continue

        sections[current_section].append(clean_line)
        if sections["profile"]:
            profile_text = " ".join(
                sections["profile"]
            )

            profile_text = profile_text.replace(
                "J’ai notamment",
                "J’ai\u00a0notamment",
            )

            sections["profile"] = [
                profile_text
            ]
        continuation_sections = (
            "experience",
            "projects",
            "skills",
            "tools",
            "training",
            "languages",
            "languages_training",
            "interests",
        )

    for section_name in continuation_sections:
        merged_lines = []

        for section_line in sections[section_name]:
            line_is_continuation = (
                bool(merged_lines)
                and (
                    section_line[0].islower()
                    or section_line[0] in ";,:"
                )
            )

            if line_is_continuation:
                merged_lines[-1] = (
                    f"{merged_lines[-1].rstrip()} "
                    f"{section_line.lstrip()}"
                )
            else:
                merged_lines.append(section_line)

        sections[section_name] = merged_lines

    identity_candidates = []

    for header_line in sections["header"]:
        normalized_line = _normalize_heading(
            header_line
        )

        if "candidature" in normalized_line:
            continue

        identity_candidates.append(header_line)

    name = "Prenom Nom"
    selected_name_line = ""

    for identity_line in identity_candidates:
        if _is_letter_spaced_identity(
            identity_line
        ):
            continue

        word_count = len(identity_line.split())

        if 2 <= word_count <= 6:
            if identity_line == identity_line.upper():
                name = identity_line.title()
            else:
                name = identity_line

            selected_name_line = identity_line
            break

    title_lines = [
        line
        for line in identity_candidates
        if line != selected_name_line
    ]

    title = " ".join(title_lines)
    contact = " | ".join(
        dict.fromkeys(contact_lines)
    )

    return {
        "name": name,
        "title": title,
        "contact": contact,
        "sections": sections,
    }


def _paragraph(text, style):
    return Paragraph(
        html.escape(str(text)),
        style,
    )


def _build_column_story(
    sections,
    section_definitions,
    heading_style,
    line_style,
):
    story = []

    for title, section_key in section_definitions:
        section_lines = sections.get(
            section_key,
            [],
        )

        if not section_lines:
            continue

        story.append(
            _paragraph(
                title.upper(),
                heading_style,
            )
        )

        story.append(Spacer(1, 2.5 * mm))

        for section_line in section_lines:
            story.append(
                _paragraph(
                    section_line,
                    line_style,
                )
            )

            story.append(Spacer(1, 0.4 * mm))

        story.append(Spacer(1, 3 * mm))

    return story


def _draw_photo(
    pdf_canvas,
    photo_data_uri,
    x,
    y,
    diameter,
):
    if not photo_data_uri:
        return False

    try:
        encoded_photo = photo_data_uri.split(
            ",",
            1,
        )[1]

        photo_bytes = base64.b64decode(
            encoded_photo
        )

        photo_reader = ImageReader(
            io.BytesIO(photo_bytes)
        )

        image_width, image_height = (
            photo_reader.getSize()
        )

        scale = max(
            diameter / image_width,
            diameter / image_height,
        )

        drawn_width = image_width * scale
        drawn_height = image_height * scale

        drawn_x = (
            x
            + (diameter - drawn_width) / 2
        )

        drawn_y = (
            y
            + (diameter - drawn_height) / 2
        )

        pdf_canvas.saveState()

        clipping_path = pdf_canvas.beginPath()
        clipping_path.circle(
            x + diameter / 2,
            y + diameter / 2,
            diameter / 2,
        )

        pdf_canvas.clipPath(
            clipping_path,
            stroke=0,
            fill=0,
        )

        pdf_canvas.drawImage(
            photo_reader,
            drawn_x,
            drawn_y,
            width=drawn_width,
            height=drawn_height,
            mask="auto",
        )

        pdf_canvas.restoreState()

        pdf_canvas.setStrokeColor(
            HORIZON_PURPLE
        )

        pdf_canvas.setLineWidth(1.5)

        pdf_canvas.circle(
            x + diameter / 2,
            y + diameter / 2,
            diameter / 2,
            stroke=1,
            fill=0,
        )

        return True

    except (
        ValueError,
        IndexError,
        TypeError,
        base64.binascii.Error,
    ):
        return False


def build_horizon_pdf(
    cv_text,
    photo_data_uri="",
):
    parsed_cv = _parse_horizon_text(
        cv_text
    )

    output_buffer = io.BytesIO()

    pdf_canvas = canvas.Canvas(
        output_buffer,
        pagesize=A4,
    )

    page_width, page_height = A4

    pdf_canvas.setTitle(
        f"CV - {parsed_cv['name']}"
    )

    pdf_canvas.setFillColor(
        HORIZON_LIGHT
    )

    pdf_canvas.rect(
        0,
        0,
        page_width,
        page_height,
        stroke=0,
        fill=1,
    )

    pdf_canvas.setFillColor(
        HexColor("#ffffff")
    )

    pdf_canvas.roundRect(
        10 * mm,
        10 * mm,
        page_width - 20 * mm,
        page_height - 20 * mm,
        4 * mm,
        stroke=0,
        fill=1,
    )

    pdf_canvas.saveState()

    try:
        pdf_canvas.setFillAlpha(0.18)
    except AttributeError:
        pass

    pdf_canvas.setFillColor(
        HORIZON_PURPLE
    )

    pdf_canvas.circle(
        page_width - 20 * mm,
        page_height + 17 * mm,
        50 * mm,
        stroke=0,
        fill=1,
    )

    pdf_canvas.restoreState()

    curve_path = pdf_canvas.beginPath()

    curve_path.moveTo(
        8 * mm,
        page_height - 57 * mm,
    )

    curve_path.curveTo(
        page_width * 0.30,
        page_height - 68 * mm,
        page_width * 0.70,
        page_height - 68 * mm,
        page_width - 8 * mm,
        page_height - 57 * mm,
    )

    pdf_canvas.setStrokeColor(
        HORIZON_TURQUOISE
    )

    pdf_canvas.setLineWidth(1.5)
    pdf_canvas.drawPath(curve_path)

    photo_diameter = 31 * mm
    photo_x = 20 * mm
    photo_y = page_height - 50 * mm

    photo_drawn = _draw_photo(
        pdf_canvas,
        photo_data_uri,
        photo_x,
        photo_y,
        photo_diameter,
    )

    if photo_drawn:
        identity_x = 60 * mm
        identity_width = 125 * mm
    else:
        identity_x = 20 * mm
        identity_width = 165 * mm

    name_style = ParagraphStyle(
        "HorizonName",
        fontName="Helvetica-Bold",
        fontSize=21,
        leading=24,
        textColor=HORIZON_DARK,
        alignment=TA_LEFT,
        spaceAfter=0,
    )

    title_style = ParagraphStyle(
        "HorizonTitle",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=HORIZON_PURPLE,
        alignment=TA_LEFT,
        spaceAfter=0,
    )

    contact_style = ParagraphStyle(
        "HorizonContact",
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=HORIZON_DARK,
        alignment=TA_LEFT,
        spaceAfter=0,
    )

    header_story = [
        _paragraph(
            parsed_cv["name"],
            name_style,
        ),
    ]

    if parsed_cv["title"]:
        header_story.extend(
            [
                Spacer(1, 2 * mm),
                _paragraph(
                    parsed_cv["title"],
                    title_style,
                ),
            ]
        )

    if parsed_cv["contact"]:
        header_story.extend(
            [
                Spacer(1, 2.5 * mm),
                _paragraph(
                    parsed_cv["contact"],
                    contact_style,
                ),
            ]
        )

    header_frame = Frame(
        identity_x,
        page_height - 53 * mm,
        identity_width,
        37 * mm,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        showBoundary=0,
    )

    header_frame.addFromList(
        [
            KeepInFrame(
                identity_width,
                37 * mm,
                header_story,
                mode="shrink",
            )
        ],
        pdf_canvas,
    )

    body_bottom = 18 * mm
    body_top = page_height - 66 * mm
    body_height = body_top - body_bottom

    main_x = 18 * mm
    main_width = 114 * mm

    sidebar_x = 139 * mm
    sidebar_width = 52 * mm

    pdf_canvas.setFillColor(
        HORIZON_SIDEBAR
    )

    pdf_canvas.roundRect(
        sidebar_x - 4 * mm,
        body_bottom - 3 * mm,
        sidebar_width + 8 * mm,
        body_height + 6 * mm,
        4 * mm,
        stroke=0,
        fill=1,
    )

    main_heading_style = ParagraphStyle(
        "HorizonMainHeading",
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13,
        textColor=HORIZON_PURPLE,
        alignment=TA_LEFT,
        spaceAfter=0,
    )

    sidebar_heading_style = ParagraphStyle(
        "HorizonSidebarHeading",
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12,
        textColor=HORIZON_TURQUOISE,
        alignment=TA_LEFT,
        spaceAfter=0,
    )

    main_line_style = ParagraphStyle(
        "HorizonMainLine",
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=HORIZON_DARK,
        alignment=TA_LEFT,
        spaceAfter=0,
    )

    sidebar_line_style = ParagraphStyle(
        "HorizonSidebarLine",
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=HORIZON_DARK,
        alignment=TA_LEFT,
        spaceAfter=0,
    )

    main_story = _build_column_story(
        parsed_cv["sections"],
        (
            ("Profil", "profile"),
            (
                "Expérience professionnelle",
                "experience",
            ),
            ("Projets", "projects"),
        ),
        main_heading_style,
        main_line_style,
    )

    sidebar_story = _build_column_story(
        parsed_cv["sections"],
        (
            ("Compétences", "skills"),
            ("Outils", "tools"),
            ("Formation", "training"),
            ("Langues", "languages"),
            (
                "Langues et formation",
                "languages_training",
            ),
            (
                "Centres d'intérêt",
                "interests",
            ),
        ),
        sidebar_heading_style,
        sidebar_line_style,
    )

    main_frame = Frame(
        main_x,
        body_bottom,
        main_width,
        body_height,
        leftPadding=0,
        rightPadding=4 * mm,
        topPadding=0,
        bottomPadding=0,
        showBoundary=0,
    )

    sidebar_frame = Frame(
        sidebar_x,
        body_bottom,
        sidebar_width,
        body_height,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        showBoundary=0,
    )

    main_frame.addFromList(
        [
            KeepInFrame(
                main_width - 4 * mm,
                body_height,
                main_story,
                mode="shrink",
            )
        ],
        pdf_canvas,
    )

    sidebar_frame.addFromList(
        [
            KeepInFrame(
                sidebar_width,
                body_height,
                sidebar_story,
                mode="shrink",
            )
        ],
        pdf_canvas,
    )

    pdf_canvas.showPage()
    pdf_canvas.save()

    return output_buffer.getvalue()


def build_cv_pdf(
    template_name,
    cv_text,
    photo_data_uri="",
):
    normalized_template = (
        str(template_name)
        .strip()
        .casefold()
    )

    if normalized_template != "horizon":
        raise ValueError(
            "Le PDF natif est actuellement disponible "
            "uniquement pour le modèle Horizon."
        )

    return build_horizon_pdf(
        cv_text=cv_text,
        photo_data_uri=photo_data_uri,
    )