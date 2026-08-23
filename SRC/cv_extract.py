from __future__ import annotations
from io import BytesIO
from typing import Tuple



def extract_text_from_upload(filename: str, file_bytes: bytes) -> Tuple[str, str]:
    name = (filename or "").lower().strip()

    if name.endswith(".pdf"):
        return _extract_pdf(file_bytes), "pdf"

    if name.endswith(".docx"):
        return _extract_docx(file_bytes), "docx"

    if name.endswith(".txt"):
        return file_bytes.decode("utf-8", errors="ignore"), "txt"

    # fallback
    try:
        return file_bytes.decode("utf-8", errors="ignore"), "unknown"
    except Exception:
        return "", "unknown"


def _extract_docx(file_bytes: bytes) -> str:
    from docx import Document
    doc = Document(BytesIO(file_bytes))
    parts = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    return "\n".join(parts).strip()


def _extract_pdf(file_bytes: bytes) -> str:
    import re

    from pypdf import PdfReader

    def clean_fragment(fragment: str) -> str:
        cleaned_groups = []

        for group in re.split(
            r" {2,}",
            fragment.strip(),
        ):
            group_words = group.split()

            is_spaced_heading = (
                len(group_words) >= 3
                and all(
                    len(word) == 1
                    and word.isalpha()
                    for word in group_words
                )
            )

            if is_spaced_heading:
                cleaned_groups.append(
                    "".join(group_words)
                )
            else:
                cleaned_groups.append(
                    " ".join(group_words)
                )

        return " ".join(
            group
            for group in cleaned_groups
            if group
        )

    def reorder_layout_page(
        layout_text: str,
    ) -> str:
        layout_lines = [
            line.rstrip()
            for line in layout_text.splitlines()
        ]

        gap_records = []
        gaps_by_line = {}

        for line_index, layout_line in enumerate(
            layout_lines
        ):
            line_gaps = []

            for gap_match in re.finditer(
                r" {8,}",
                layout_line,
            ):
                left_text = layout_line[
                    :gap_match.start()
                ].strip()

                right_text = layout_line[
                    gap_match.end():
                ].strip()

                if left_text and right_text:
                    gap_record = (
                        gap_match.start(),
                        gap_match.end(),
                    )

                    line_gaps.append(
                        gap_record
                    )

                    gap_records.append(
                        (
                            line_index,
                            gap_match.start(),
                            gap_match.end(),
                        )
                    )

            gaps_by_line[line_index] = line_gaps

        detected_gap_lines = {
            line_index
            for line_index, _, _
            in gap_records
        }

        if len(detected_gap_lines) < 6:
            return "\n".join(
                clean_fragment(line)
                for line in layout_lines
                if line.strip()
            )

        right_positions = sorted(
            gap_end
            for _, _, gap_end
            in gap_records
        )

        median_position = right_positions[
            len(right_positions) // 2
        ]

        stable_records = [
            record
            for record in gap_records
            if abs(
                record[2] - median_position
            ) <= 12
        ]

        stable_line_indices = {
            line_index
            for line_index, _, _
            in stable_records
        }

        if len(stable_line_indices) < 6:
            return "\n".join(
                clean_fragment(line)
                for line in layout_lines
                if line.strip()
            )

        stable_positions = sorted(
            gap_end
            for _, _, gap_end
            in stable_records
        )

        column_start = stable_positions[
            len(stable_positions) // 2
        ]

        body_start = min(
            stable_line_indices
        )

        header_lines = []
        left_column_lines = []
        right_column_lines = []

        for layout_line in layout_lines[
            :body_start
        ]:
            cleaned_line = clean_fragment(
                layout_line
            )

            if cleaned_line:
                header_lines.append(
                    cleaned_line
                )

        for line_index in range(
            body_start,
            len(layout_lines),
        ):
            layout_line = layout_lines[
                line_index
            ]

            if not layout_line.strip():
                continue

            matching_gaps = [
                gap
                for gap in gaps_by_line.get(
                    line_index,
                    [],
                )
                if abs(
                    gap[1] - column_start
                ) <= 12
            ]

            if matching_gaps:
                split_gap = min(
                    matching_gaps,
                    key=lambda gap: abs(
                        gap[1] - column_start
                    ),
                )

                left_fragment = clean_fragment(
                    layout_line[
                        :split_gap[0]
                    ]
                )

                right_fragment = clean_fragment(
                    layout_line[
                        split_gap[1]:
                    ]
                )

                if left_fragment:
                    left_column_lines.append(
                        left_fragment
                    )

                if right_fragment:
                    right_column_lines.append(
                        right_fragment
                    )

                continue

            first_character_position = (
                len(layout_line)
                - len(layout_line.lstrip())
            )

            cleaned_line = clean_fragment(
                layout_line
            )

            if not cleaned_line:
                continue

            if (
                first_character_position
                >= column_start - 12
            ):
                right_column_lines.append(
                    cleaned_line
                )
            else:
                left_column_lines.append(
                    cleaned_line
                )

        reordered_lines = (
            header_lines
            + left_column_lines
            + right_column_lines
        )

        return "\n".join(
            reordered_lines
        )

    def normalize_duplicate_line(line: str) -> str:
        return re.sub(r"\s+", " ", str(line)).strip().casefold()

    def remove_repeated_blocks(
        page_lines: list[str],
        previous_lines: list[str],
    ) -> list[str]:
        minimum_block_size = 5

        if (
            len(page_lines) < minimum_block_size
            or len(previous_lines)
            < minimum_block_size
        ):
            return page_lines

        normalized_page_lines = [
            normalize_duplicate_line(line)
            for line in page_lines
        ]

        normalized_previous_lines = [
            normalize_duplicate_line(line)
            for line in previous_lines
        ]

        unique_lines = []
        page_index = 0

        while page_index < len(page_lines):
            longest_repeated_block = 0

            for previous_index in range(
                len(previous_lines)
            ):
                repeated_line_count = 0

                while (
                    page_index
                    + repeated_line_count
                    < len(page_lines)
                    and previous_index
                    + repeated_line_count
                    < len(previous_lines)
                    and normalized_page_lines[
                        page_index
                        + repeated_line_count
                    ]
                    == normalized_previous_lines[
                        previous_index
                        + repeated_line_count
                    ]
                ):
                    repeated_line_count += 1

                longest_repeated_block = max(
                    longest_repeated_block,
                    repeated_line_count,
                )

            if (
                longest_repeated_block
                >= minimum_block_size
            ):
                page_index += (
                    longest_repeated_block
                )
                continue

            unique_lines.append(
                page_lines[page_index]
            )

            page_index += 1

        return unique_lines

    reader = PdfReader(
        BytesIO(file_bytes)
    )

    texts = []
    extracted_lines = []

    for page in reader.pages:
        try:
            layout_text = page.extract_text(
                extraction_mode="layout",
                layout_mode_space_vertically=False,
            ) or ""

            page_text = reorder_layout_page(
                layout_text
            )

        except (TypeError, ValueError):
            page_text = (
                page.extract_text()
                or ""
            )

        page_lines = [
            line.strip()
            for line in page_text.splitlines()
            if line.strip()
        ]

        unique_page_lines = remove_repeated_blocks(
            page_lines,
            extracted_lines,
        )

        if not unique_page_lines:
            continue

        texts.append(
            "\n".join(
                unique_page_lines
            )
        )

        extracted_lines.extend(
            unique_page_lines
        )

    return "\n".join(texts).strip()