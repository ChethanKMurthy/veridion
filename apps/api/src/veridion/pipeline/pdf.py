"""PDF ingestion: text, tables and page-level provenance.

Output is a flat list of passages (paragraphs, headings, list items, tables and
table rows). Each passage carries its page number and bounding box in PDF points,
so the interface can open the exact location of every piece of evidence.

Digital pages use PyMuPDF's text and ruled-table extraction. Pages without a
text layer (scans) are passed to Tesseract; table rows on scanned pages are
reconstructed from text lines. Running headers, footers and page numbers are
detected across pages and dropped.
"""

from __future__ import annotations

import csv
import io
import logging
import re
import shutil
import subprocess
import tempfile
import time
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

from veridion.extraction.numbers import parse_number
from veridion.extraction.periods import Period, find_periods, parse_period_label

pymupdf.no_recommend_layout()
log = logging.getLogger("veridion.pipeline")

BULLET_RE = re.compile(r"^\s*(?:[•▪◦●\-–]|\(?\d{1,2}[.)]|\(?[a-z][.)])\s+")
SOFT_HYPHEN = "­"
MAX_PASSAGE_CHARS = 900


class PdfError(Exception):
    """The file cannot be processed (corrupt, encrypted, not a PDF)."""


@dataclass
class Line:
    text: str
    bbox: tuple[float, float, float, float]
    size: float = 10.0
    bold: bool = False
    words: list[tuple[float, float, float, float, str]] = field(default_factory=list)
    confidence: float = 1.0
    block: int = 0


@dataclass
class ParsedPassage:
    page: int
    kind: str
    text: str
    bbox: tuple[float, float, float, float]
    section: str | None = None
    method: str = "text"
    confidence: float = 1.0
    table_ref: str | None = None
    cells: dict | None = None


@dataclass
class ParsedDocument:
    page_count: int
    page_sizes: list[tuple[float, float]]
    passages: list[ParsedPassage]
    ocr_pages: list[int]
    warnings: list[str]
    detected_period: Period | None
    title: str | None
    stats: dict


# ---------------------------------------------------------------------------
# Page readers
# ---------------------------------------------------------------------------

def _union(boxes: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def _round_box(box) -> tuple[float, float, float, float]:
    return tuple(round(float(v), 1) for v in box)  # type: ignore[return-value]


def _digital_lines(page: pymupdf.Page) -> list[Line]:
    flags = pymupdf.TEXTFLAGS_DICT & ~pymupdf.TEXT_PRESERVE_IMAGES & ~pymupdf.TEXT_PRESERVE_LIGATURES
    data = page.get_text("dict", flags=flags, sort=True)
    lines: list[Line] = []
    for bno, block in enumerate(data["blocks"]):
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            spans = [s for s in line["spans"] if s["text"].strip()]
            if not spans:
                continue
            text = normalize_text("".join(s["text"] for s in line["spans"]))
            size = max(s["size"] for s in spans)
            bold = all((s["flags"] & 16) or "bold" in s["font"].lower() for s in spans)
            lines.append(Line(text=text.strip(), bbox=tuple(line["bbox"]), size=round(size, 1), bold=bold, block=bno))
    return lines


def tesseract_available() -> bool:
    return shutil.which("tesseract") is not None


def _ocr_lines(page: pymupdf.Page, dpi: int = 300) -> list[Line]:
    """OCR a page with the Tesseract CLI and return lines with boxes in PDF points."""
    pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
    scale = page.rect.width / pix.width
    with tempfile.TemporaryDirectory() as tmp:
        image = Path(tmp) / "page.png"
        pix.save(image)
        proc = subprocess.run(
            ["tesseract", str(image), "-", "--psm", "3", "tsv"],
            capture_output=True, text=True, timeout=120, check=False,
        )
    if proc.returncode != 0:
        raise PdfError(f"OCR failed on page {page.number + 1}: {proc.stderr.strip()[:200]}")
    grouped: dict[tuple[int, int, int], list[dict]] = {}
    for row in csv.DictReader(io.StringIO(proc.stdout), delimiter="\t", quoting=csv.QUOTE_NONE):
        if row.get("level") != "5" or not (row.get("text") or "").strip():
            continue
        key = (int(row["block_num"]), int(row["par_num"]), int(row["line_num"]))
        grouped.setdefault(key, []).append(row)
    lines: list[Line] = []
    for (block, _par, _ln), words in sorted(grouped.items()):
        boxes = []
        for w in words:
            x0, y0 = float(w["left"]) * scale, float(w["top"]) * scale
            x1, y1 = x0 + float(w["width"]) * scale, y0 + float(w["height"]) * scale
            boxes.append((x0, y0, x1, y1, w["text"]))
        confs = [float(w["conf"]) for w in words if float(w["conf"]) >= 0]
        height = sum(b[3] - b[1] for b in boxes) / len(boxes)
        lines.append(Line(
            text=normalize_text(" ".join(b[4] for b in boxes)), bbox=_union([b[:4] for b in boxes]),
            size=round(height * 1.25, 1),
            words=boxes, confidence=(sum(confs) / len(confs) / 100) if confs else 0.5, block=block,
        ))
    return lines


def _needs_ocr(page: pymupdf.Page) -> bool:
    return len(page.get_text("text").strip()) < 25 and bool(page.get_images(full=False))


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

def _clean_cell(value: str | None) -> str:
    return " ".join((value or "").replace(SOFT_HYPHEN, "").split())


def _is_header_row(row: list[str]) -> bool:
    cells = [c for c in row[1:] if c]
    if not cells:
        return False
    periodish = sum(1 for c in cells if parse_period_label(c) is not None)
    numeric = sum(1 for c in cells if parse_number(c) is not None and parse_period_label(c) is None)
    return periodish >= max(1, len(cells) // 2) or numeric == 0


@dataclass
class TableRow:
    label: str
    values: list[str]
    bbox: tuple[float, float, float, float]


@dataclass
class TableData:
    bbox: tuple[float, float, float, float]
    headers: list[str]
    rows: list[TableRow]
    method: str = "table"
    confidence: float = 1.0


def _ruled_tables(page: pymupdf.Page) -> list[TableData]:
    try:
        finder = page.find_tables()
    except Exception as exc:
        log.warning("Table detection failed on page %s: %s", page.number + 1, exc)
        return []
    out: list[TableData] = []
    for table in finder.tables:
        raw = [[_clean_cell(c) for c in row] for row in table.extract()]
        raw = [r for r in raw if any(r)]
        if len(raw) < 2 or max(len(r) for r in raw) < 2:
            continue
        headers: list[str] = []
        start = 0
        if _is_header_row(raw[0]):
            headers, start = raw[0][1:], 1
        rows = []
        for index in range(start, len(raw)):
            cells = raw[index]
            row_obj = table.rows[index] if index < len(table.rows) else None
            boxes = [c for c in (row_obj.cells if row_obj else []) if c]
            bbox = _union(boxes) if boxes else tuple(table.bbox)
            if cells[0]:
                rows.append(TableRow(label=cells[0], values=cells[1:], bbox=bbox))
        if rows:
            out.append(TableData(bbox=tuple(table.bbox), headers=headers, rows=rows))
    return out


_NUM_TOKEN = re.compile(r"^[-−(]?[\d.,]+%?\)?$|^[—–-]$|^n/?a$", re.IGNORECASE)


def _split_numeric_tail(line: Line) -> tuple[str, list[str], list] | None:
    tokens = [w for w in line.words if w[4] not in {"|", "¦", "I|"}] if line.words else []
    if not tokens:
        return None
    tail: list = []
    for w in reversed(tokens):
        if _NUM_TOKEN.match(w[4].strip("|")):
            tail.append(w)
        else:
            break
    if not tail or len(tail) == len(tokens):
        return None
    tail.reverse()
    label = " ".join(w[4] for w in tokens[: len(tokens) - len(tail)])
    return label, [w[4].strip("|") for w in tail], tail


def _text_tables(lines: list[Line]) -> tuple[list[TableData], set[int]]:
    """Reconstruct tables from OCR lines: a header of periods followed by label + numbers rows."""
    tables: list[TableData] = []
    used: set[int] = set()
    i = 0
    while i < len(lines):
        header_tokens = [w[4] for w in lines[i].words] if lines[i].words else lines[i].text.split()
        periods = [t for t in header_tokens if parse_period_label(t) is not None]
        if len(periods) >= 2:
            rows: list[TableRow] = []
            j = i + 1
            while j < len(lines):
                split = _split_numeric_tail(lines[j])
                if split is None:
                    break
                label, values, _tail = split
                if len(values) > len(periods):
                    break
                # Right-align values under the period headers.
                padded = [""] * (len(periods) - len(values)) + values
                rows.append(TableRow(label=label, values=padded, bbox=_round_box(lines[j].bbox)))
                j += 1
            if len(rows) >= 2:
                conf = min(lines[k].confidence for k in range(i, j))
                tables.append(TableData(
                    bbox=_round_box(_union([lines[k].bbox for k in range(i, j)])), headers=periods, rows=rows,
                    method="ocr", confidence=round(conf, 2),
                ))
                used.update(range(i, j))
                i = j
                continue
        i += 1
    return tables, used


# ---------------------------------------------------------------------------
# Document assembly
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """NFKC folds ligatures (ﬁ → fi), subscripts (CO₂ → CO2) and odd spaces; soft hyphens are dropped."""
    return unicodedata.normalize("NFKC", text.replace(SOFT_HYPHEN, ""))


def _norm_running(text: str) -> str:
    folded = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return re.sub(r"\d+", "#", " ".join(folded.split()))


def _overlap_ratio(inner, outer) -> float:
    x0, y0 = max(inner[0], outer[0]), max(inner[1], outer[1])
    x1, y1 = min(inner[2], outer[2]), min(inner[3], outer[3])
    if x1 <= x0 or y1 <= y0:
        return 0.0
    area = (inner[2] - inner[0]) * (inner[3] - inner[1]) or 1.0
    return (x1 - x0) * (y1 - y0) / area


def _join_lines(texts: list[str]) -> str:
    out = ""
    for text in texts:
        if not out:
            out = text
        elif out.endswith("-") and text[:1].islower():
            out += text  # keep compound hyphens: "location-" + "based"
        else:
            out += " " + text
    return out.strip()


def parse_pdf(data: bytes, *, fiscal_year_end: str | None = "12-31", period_hint: str | None = None,
              ocr_enabled: bool = True) -> ParsedDocument:
    started = time.perf_counter()
    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise PdfError(f"Not a readable PDF: {exc}") from exc
    if doc.needs_pass:
        raise PdfError("The PDF is password protected.")
    if doc.page_count == 0:
        raise PdfError("The PDF has no pages.")

    warnings: list[str] = []
    ocr_pages: list[int] = []
    page_sizes: list[tuple[float, float]] = []
    page_lines: list[list[Line]] = []
    page_tables: list[list[TableData]] = []
    page_methods: list[str] = []
    can_ocr = ocr_enabled and tesseract_available()

    for page in doc:
        page_sizes.append((round(page.rect.width, 1), round(page.rect.height, 1)))
        if _needs_ocr(page):
            if not can_ocr:
                warnings.append(f"Page {page.number + 1} has no text layer and OCR is unavailable; it was skipped.")
                page_lines.append([])
                page_tables.append([])
                page_methods.append("skipped")
                continue
            lines = _ocr_lines(page)
            ocr_pages.append(page.number + 1)
            tables, used = _text_tables(lines)
            page_lines.append([ln for k, ln in enumerate(lines) if k not in used])
            page_tables.append(tables)
            page_methods.append("ocr")
        else:
            page_lines.append(_digital_lines(page))
            page_tables.append(_ruled_tables(page))
            page_methods.append("text")

    # Running headers/footers: short lines in the top or bottom margin repeated on many pages.
    margin_counts: Counter[str] = Counter()
    for lines, (_, height) in zip(page_lines, page_sizes, strict=True):
        seen = set()
        for ln in lines:
            if ln.bbox[3] < height * 0.09 or ln.bbox[1] > height * 0.91:
                seen.add(_norm_running(ln.text))
        margin_counts.update(seen)
    threshold = max(2, int(0.5 * len(page_lines)))
    running = {t for t, n in margin_counts.items() if n >= threshold}

    # Typography: body size = size covering the most characters.
    size_chars: Counter[float] = Counter()
    for lines in page_lines:
        for ln in lines:
            size_chars[ln.size] += len(ln.text)
    body_size = size_chars.most_common(1)[0][0] if size_chars else 10.0
    heading_sizes = sorted({ln.size for lines in page_lines for ln in lines if ln.size >= body_size * 1.15},
                           reverse=True)
    # A size used only on the cover page is the document title, not a section heading.
    cover_only = {
        s for s in heading_sizes
        if all(ln.size != s for lines in page_lines[1:] for ln in lines)
    } if len(page_lines) > 1 else set()

    passages: list[ParsedPassage] = []
    section_stack: list[tuple[int, str]] = []
    title: str | None = None

    def section() -> str | None:
        return " › ".join(text for _, text in section_stack) or None

    for page_index, (lines, tables, method) in enumerate(zip(page_lines, page_tables, page_methods, strict=True)):
        page_no = page_index + 1
        height = page_sizes[page_index][1]
        content = [
            ln for ln in lines
            if not ((ln.bbox[3] < height * 0.09 or ln.bbox[1] > height * 0.91)
                    and (_norm_running(ln.text) in running or re.fullmatch(r"\d{1,4}", ln.text.strip())))
        ]
        if tables:
            content = [ln for ln in content if all(_overlap_ratio(ln.bbox, t.bbox) < 0.5 for t in tables)]

        # Group lines into blocks (same source block, close vertically).
        blocks: list[list[Line]] = []
        for ln in content:
            if blocks:
                prev = blocks[-1][-1]
                same_block = ln.block == prev.block
                gap = ln.bbox[1] - prev.bbox[3]
                if same_block and gap < prev.size * 0.9 and abs(ln.size - prev.size) < 0.6:
                    blocks[-1].append(ln)
                    continue
            blocks.append([ln])

        events: list[tuple[float, str, object]] = [(b[0].bbox[1], "block", b) for b in blocks]
        events += [(t.bbox[1], "table", t) for t in tables]
        events.sort(key=lambda e: e[0])
        table_no = 0
        last_short_text: str | None = None

        for _, kind, obj in events:
            if kind == "table":
                table_no += 1
                table: TableData = obj  # type: ignore[assignment]
                ref = f"p{page_no}-t{table_no}"
                caption = last_short_text or ""
                header_line = " | ".join(["", *table.headers]) if table.headers else ""
                body = "\n".join(f"{r.label} | " + " | ".join(r.values) for r in table.rows)
                passages.append(ParsedPassage(
                    page=page_no, kind="table", text=f"{caption}\n{header_line}\n{body}".strip(),
                    bbox=_round_box(table.bbox), section=section(), method=table.method,
                    confidence=table.confidence, table_ref=ref,
                    cells={"caption": caption, "headers": table.headers,
                           "rows": [[r.label, *r.values] for r in table.rows]},
                ))
                for row in table.rows:
                    pairs = "; ".join(
                        f"{h}: {v}" for h, v in zip(table.headers or [""] * len(row.values), row.values, strict=False) if v
                    )
                    prefix = f"{caption} — " if caption else ""
                    passages.append(ParsedPassage(
                        page=page_no, kind="table_row", text=f"{prefix}{row.label}: {pairs}",
                        bbox=_round_box(row.bbox), section=section(), method=table.method,
                        confidence=table.confidence, table_ref=ref,
                        cells={"label": row.label, "values": row.values, "headers": table.headers, "caption": caption},
                    ))
                continue

            block: list[Line] = obj  # type: ignore[assignment]
            text = _join_lines([ln.text for ln in block])
            if not text:
                continue
            size = max(ln.size for ln in block)
            is_heading = (
                (size >= body_size * 1.15 or (all(ln.bold for ln in block) and len(text) < 90))
                and len(text) < 160 and not text.endswith((".", ":"))
            )
            confidence = round(min(ln.confidence for ln in block), 2)
            bbox = _round_box(_union([ln.bbox for ln in block]))
            if is_heading:
                if size in cover_only:
                    title = title or text
                    last_short_text = text
                    continue
                level = heading_sizes.index(size) if size in heading_sizes else len(heading_sizes)
                while section_stack and section_stack[-1][0] >= level:
                    section_stack.pop()
                section_stack.append((level, text))
                passages.append(ParsedPassage(page=page_no, kind="heading", text=text, bbox=bbox,
                                              section=section(), method=method, confidence=confidence))
                last_short_text = text
                continue

            kind_name = "list_item" if BULLET_RE.match(text) else "paragraph"
            # Split long blocks at line boundaries so each passage stays citeable.
            chunk: list[Line] = []
            chunk_len = 0
            for ln in block:
                chunk.append(ln)
                chunk_len += len(ln.text) + 1
                if chunk_len >= MAX_PASSAGE_CHARS and ln.text.rstrip().endswith((".", ";")):
                    passages.append(ParsedPassage(
                        page=page_no, kind=kind_name, text=_join_lines([c.text for c in chunk]),
                        bbox=_round_box(_union([c.bbox for c in chunk])), section=section(), method=method,
                        confidence=round(min(c.confidence for c in chunk), 2),
                    ))
                    chunk, chunk_len = [], 0
            if chunk:
                passages.append(ParsedPassage(
                    page=page_no, kind=kind_name, text=_join_lines([c.text for c in chunk]),
                    bbox=_round_box(_union([c.bbox for c in chunk])), section=section(), method=method,
                    confidence=round(min(c.confidence for c in chunk), 2),
                ))
            last_short_text = text if len(text) < 120 else None

    if not title:
        meta_title = (doc.metadata or {}).get("title") or ""
        title = meta_title.strip() or None

    detected = None
    if period_hint:
        detected = parse_period_label(period_hint, fiscal_year_end)
    if detected is None:
        detected = _detect_period(passages, fiscal_year_end)

    doc.close()
    return ParsedDocument(
        page_count=len(page_sizes), page_sizes=page_sizes, passages=passages, ocr_pages=ocr_pages,
        warnings=warnings, detected_period=detected, title=title,
        stats={
            "parse_ms": round((time.perf_counter() - started) * 1000, 1),
            "passages": len(passages),
            "tables": sum(1 for p in passages if p.kind == "table"),
            "ocr_pages": len(ocr_pages),
            "body_font_size": body_size,
        },
    )


def _detect_period(passages: list[ParsedPassage], fiscal_year_end: str | None) -> Period | None:
    """Most frequent explicitly-dated period in the first pages (e.g. 'year ended 31 December 2025')."""
    counts: Counter[tuple] = Counter()
    by_key: dict[tuple, Period] = {}
    for p in passages:
        if p.page > 3:
            break
        for period, _, _ in find_periods(p.text, fiscal_year_end):
            key = (period.start, period.end)
            counts[key] += 3 if period.explicit else 1
            by_key[key] = period
    if not counts:
        return None
    return by_key[counts.most_common(1)[0][0]]


def render_page_png(data: bytes, page_number: int, scale: float = 1.5) -> bytes:
    with pymupdf.open(stream=data, filetype="pdf") as doc:
        if not 1 <= page_number <= doc.page_count:
            raise PdfError("Page out of range")
        page = doc[page_number - 1]
        pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
        return pix.tobytes("png")
