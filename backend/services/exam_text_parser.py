from __future__ import annotations

import re
from typing import Any


_QUESTION_START_RE = re.compile(r"^(\d{1,3})\s+(.+)$")
# Also match "Q1 ...", "Question 1 ..." style
_QUESTION_START_ALT_RE = re.compile(r"^Q(?:uestion)?\s*(\d{1,3})[.):\s]+(.+)$", re.IGNORECASE)
_PAGE_NUM_ISOLATED_RE = re.compile(r"^\s*\d{1,3}\s*$")
_PAGE_NUM_OF_RE = re.compile(r"^\s*\d+\s+of\s+\d+\s*$", re.IGNORECASE)
_PAGE_NUM_LABEL_RE = re.compile(r"^\s*page\s+\d+(\s+of\s+\d+)?\s*$", re.IGNORECASE)
_PAGE_NUM_DASHED_RE = re.compile(r"^\s*[-–—]?\s*\d{1,3}\s*[-–—]?\s*$")
_FOOTER_RE = re.compile(
    r"^(turn over|blank page|©|copyright\b|\[turn over\]|ucles\b|zimsec\b)",
    re.IGNORECASE,
)
_INSTRUCTION_HEADING_RE = re.compile(r"^(instructions?|information|read these)\b", re.IGNORECASE)
_REFERENCE_HEADING_RE = re.compile(
    r"^(qualitative analysis|periodic table|data sheet|appendix|formulae|formulas)\b",
    re.IGNORECASE,
)
_ALPHA_SUB_RE = re.compile(r"^\(([a-z])\)\s*(.*)$")
_ROMAN_SUB_RE = re.compile(r"^\(((?:i|ii|iii|iv|v|vi|vii|viii|ix|x))\)\s*(.*)$", re.IGNORECASE)
_OPTION_RE = re.compile(r"^([A-D])[\).:\-]?\s+(.+)$")
_FIGURE_REF_RE = re.compile(r"\b(?:Fig(?:ure)?\.?)\s*\d+(?:\.\d+)?\b", re.IGNORECASE)
_TABLE_REF_RE = re.compile(r"\bTable\s+\d+(?:\.\d+)?\b", re.IGNORECASE)
_TOTAL_MARK_RE = re.compile(r"\[\s*Total\s*:\s*(\d+)\s*\]", re.IGNORECASE)
_MARK_RE = re.compile(r"(?:\[\s*(\d+)(?:\s*marks?)?\s*\]|\(\s*(\d+)\s*marks?\s*\))", re.IGNORECASE)
_PRACTICAL_SIGNAL_RE = re.compile(
    r"\b(experiment|apparatus|procedure|investigation|practical)\b",
    re.IGNORECASE,
)


def parse_exam_text(raw_text: str) -> dict[str, Any]:
    lines = _prepare_lines(raw_text)
    question_chunks = _collect_question_chunks(lines)
    questions = [_parse_question(number, chunk_lines) for number, chunk_lines in question_chunks]
    return {
        "paper_type": _detect_paper_type(questions),
        "questions": questions,
    }


def _prepare_lines(raw_text: str) -> list[str]:
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n").replace("\f", "\n")
    prepared: list[str] = []
    for raw_line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        if not line:
            continue
        if _PAGE_NUM_ISOLATED_RE.match(line):
            continue
        if _PAGE_NUM_OF_RE.match(line):
            continue
        if _PAGE_NUM_LABEL_RE.match(line):
            continue
        if _PAGE_NUM_DASHED_RE.match(line):
            continue
        if _FOOTER_RE.match(line):
            continue
        prepared.append(line)
    return prepared


def _collect_question_chunks(lines: list[str]) -> list[tuple[int, list[str]]]:
    chunks: list[tuple[int, list[str]]] = []
    current_number: int | None = None
    current_lines: list[str] = []

    for index, line in enumerate(lines):
        question_match = _QUESTION_START_RE.match(line) or _QUESTION_START_ALT_RE.match(line)
        if question_match:
            if current_number is not None:
                chunks.append((current_number, current_lines))
            current_number = int(question_match.group(1))
            current_lines = [question_match.group(2).strip()]
            continue

        if current_number is None:
            continue

        if _REFERENCE_HEADING_RE.match(line) and not any(
            _QUESTION_START_RE.match(future) or _QUESTION_START_ALT_RE.match(future)
            for future in lines[index + 1 :]
        ):
            break

        if _INSTRUCTION_HEADING_RE.match(line) and not any(
            _QUESTION_START_RE.match(future) or _QUESTION_START_ALT_RE.match(future)
            for future in lines[index + 1 :]
        ):
            break

        current_lines.append(line)

    if current_number is not None:
        chunks.append((current_number, current_lines))

    return chunks


def _parse_question(question_number: int, chunk_lines: list[str]) -> dict[str, Any]:
    normalized_lines = _split_inline_markers(chunk_lines)

    parent_lines: list[str] = []
    sub_questions: list[dict[str, Any]] = []
    current_alpha: dict[str, Any] | None = None
    current_roman: dict[str, Any] | None = None

    for line in normalized_lines:
        roman_match = _ROMAN_SUB_RE.match(line)
        if roman_match and current_alpha is not None:
            if current_roman is not None:
                current_alpha["sub_questions"].append(_finalize_node(current_roman))
            current_roman = _new_sub_question(roman_match.group(1).lower(), roman_match.group(2))
            continue

        alpha_match = _ALPHA_SUB_RE.match(line)
        if alpha_match:
            if current_roman is not None and current_alpha is not None:
                current_alpha["sub_questions"].append(_finalize_node(current_roman))
                current_roman = None
            if current_alpha is not None:
                sub_questions.append(_finalize_node(current_alpha))
            current_alpha = _new_sub_question(alpha_match.group(1), alpha_match.group(2))
            continue

        if current_roman is not None:
            current_roman["lines"].append(line)
        elif current_alpha is not None:
            current_alpha["lines"].append(line)
        else:
            parent_lines.append(line)

    if current_roman is not None and current_alpha is not None:
        current_alpha["sub_questions"].append(_finalize_node(current_roman))
    if current_alpha is not None:
        sub_questions.append(_finalize_node(current_alpha))

    parent_text = _join_lines(parent_lines)
    parent_text, marks = _strip_marks(parent_text)
    parent_text, options = _extract_options(parent_text)
    figure_refs = _extract_refs(parent_text, _FIGURE_REF_RE)
    table_refs = _extract_refs(parent_text, _TABLE_REF_RE)

    return {
        "question_number": question_number,
        "text": parent_text,
        "marks": marks,
        "options": options,
        "sub_questions": sub_questions,
        "has_diagram": bool(figure_refs),
        "has_table": bool(table_refs),
        "figure_refs": figure_refs,
        "table_refs": table_refs,
    }


def _split_inline_markers(lines: list[str]) -> list[str]:
    split_lines: list[str] = []
    for line in lines:
        line = re.sub(r"\s+(?=\([a-z]\)\s)", "\n", line)
        line = re.sub(r"\s+(?=\((?:i|ii|iii|iv|v|vi|vii|viii|ix|x)\)\s)", "\n", line, flags=re.IGNORECASE)
        for part in line.split("\n"):
            cleaned = part.strip()
            if cleaned:
                split_lines.append(cleaned)
    return split_lines


def _new_sub_question(identifier: str, initial_text: str) -> dict[str, Any]:
    node: dict[str, Any] = {
        "id": identifier,
        "lines": [],
        "sub_questions": [],
    }
    if initial_text.strip():
        node["lines"].append(initial_text.strip())
    return node


def _finalize_node(node: dict[str, Any]) -> dict[str, Any]:
    text = _join_lines(node["lines"])
    text, marks = _strip_marks(text)
    text, options = _extract_options(text)
    figure_refs = _extract_refs(text, _FIGURE_REF_RE)
    table_refs = _extract_refs(text, _TABLE_REF_RE)
    return {
        "id": node["id"],
        "text": text,
        "marks": marks,
        "options": options,
        "sub_questions": node["sub_questions"],
        "has_diagram": bool(figure_refs),
        "has_table": bool(table_refs),
        "figure_refs": figure_refs,
        "table_refs": table_refs,
    }


def _join_lines(lines: list[str]) -> str:
    return "\n".join(re.sub(r"[ \t]+", " ", line).strip() for line in lines if line.strip()).strip()


def _strip_marks(text: str) -> tuple[str, int]:
    marks = 0

    total_match = _TOTAL_MARK_RE.search(text)
    if total_match:
        marks = int(total_match.group(1))
        text = _TOTAL_MARK_RE.sub("", text)
    else:
        mark_matches = _MARK_RE.findall(text)
        if len(mark_matches) == 1:
            # findall returns tuples with two groups; pick the non-empty one
            group1, group2 = mark_matches[0]
            marks = int(group1 or group2)
        text = _MARK_RE.sub("", text)

    text = re.sub(r" +\n", "\n", text)
    text = re.sub(r"\n +", "\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip(), marks


def _extract_options(text: str) -> tuple[str, dict[str, str]]:
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    stem_lines: list[str] = []
    options: dict[str, str] = {}
    current_option: str | None = None

    for line in lines:
        option_match = _OPTION_RE.match(line)
        if option_match:
            current_option = option_match.group(1)
            options[current_option] = option_match.group(2).strip()
            continue

        if current_option is not None and options:
            options[current_option] = f"{options[current_option]} {line}".strip()
        else:
            stem_lines.append(line)

    if set(options) >= {"A", "B", "C", "D"}:
        return _join_lines(stem_lines), {key: options[key] for key in ("A", "B", "C", "D")}

    return text.strip(), {}


def _extract_refs(text: str, pattern: re.Pattern[str]) -> list[str]:
    seen: list[str] = []
    for match in pattern.finditer(text):
        ref = re.sub(r"\s+", " ", match.group(0)).strip()
        if ref not in seen:
            seen.append(ref)
    return seen


def _detect_paper_type(questions: list[dict[str, Any]]) -> str:
    if any(_question_has_mcq(q) for q in questions):
        return "mcq"
    if any(_question_has_practical_signals(q) for q in questions):
        return "practical"
    return "theory"


def _question_has_mcq(question: dict[str, Any]) -> bool:
    if set((question.get("options") or {}).keys()) >= {"A", "B", "C", "D"}:
        return True
    return any(_question_has_mcq(sub) for sub in question.get("sub_questions") or [])


def _question_has_practical_signals(question: dict[str, Any]) -> bool:
    has_visual = bool(question.get("has_diagram")) or bool(question.get("has_table"))
    if _PRACTICAL_SIGNAL_RE.search(question.get("text", "")) and has_visual:
        return True
    if question.get("has_diagram") and question.get("has_table"):
        return True
    return any(_question_has_practical_signals(sub) for sub in question.get("sub_questions") or [])
