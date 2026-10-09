"""Render the fictional sample documents to PDF.

Pages are laid out with PyMuPDF's HTML engine. Each content page gets a running
header and a page number (which the ingestion pipeline must learn to ignore),
and pages marked `scanned` are rasterised so they carry no text layer at all.
"""

from __future__ import annotations

from pathlib import Path

import pymupdf

from veridion.samples.content import COMPANIES, FICTION_NOTICE, SampleDocument

CSS = """
body { font-family: serif; font-size: 10.5pt; line-height: 1.45; color: #1c1c1c; }
h1 { font-family: sans-serif; font-size: 19pt; font-weight: bold; margin: 0 0 10pt 0; color: #111; }
h2 { font-family: sans-serif; font-size: 12.5pt; font-weight: bold; margin: 14pt 0 5pt 0; color: #222; }
h3 { font-family: sans-serif; font-size: 10.5pt; font-weight: bold; margin: 12pt 0 5pt 0; color: #333; }
p { margin: 0 0 8pt 0; text-align: left; }
table { border-collapse: collapse; width: 100%; margin: 4pt 0 10pt 0; font-family: sans-serif; font-size: 9.5pt; }
th, td { border: 0.6pt solid #8a8a8a; padding: 3pt 5pt; text-align: left; }
th { background-color: #ece9e1; font-weight: bold; }
.cover { margin-top: 210pt; }
.kicker { font-family: sans-serif; font-size: 11pt; letter-spacing: 1pt; color: #555; }
.cover-title { font-size: 30pt; margin: 6pt 0 10pt 0; }
.cover-sub { font-family: sans-serif; font-size: 12pt; color: #333; }
.notice { margin-top: 160pt; font-family: sans-serif; font-size: 8.5pt; color: #7a4a3a; }
"""

PAGE = pymupdf.paper_rect("a4")
BODY = PAGE + (62, 78, -62, -70)  # noqa: RUF005 - pymupdf.Rect arithmetic (inset margins)


def _render_html_page(writer: pymupdf.DocumentWriter, html: str) -> int:
    story = pymupdf.Story(html=html, user_css=CSS)
    pages = 0
    more = 1
    while more:
        device = writer.begin_page(PAGE)
        more, _ = story.place(BODY)
        story.draw(device)
        writer.end_page()
        pages += 1
    return pages


def render_document(doc: SampleDocument) -> bytes:
    """Return the PDF bytes for a sample document."""
    buffer = pymupdf.open()
    scanned_pages: set[int] = set()
    for page in doc.pages:
        writer_buf = _layout_to_pdf(page.html)
        part = pymupdf.open("pdf", writer_buf)
        start = len(buffer)
        buffer.insert_pdf(part)
        if page.scanned:
            scanned_pages.update(range(start, len(buffer)))
        part.close()

    total = len(buffer)
    for index in range(1, total):  # running header and folio on every page except the cover
        page = buffer[index]
        page.insert_text((62, 46), doc.header, fontname="helv", fontsize=7.5, color=(0.45, 0.45, 0.45))
        page.draw_line((62, 52), (PAGE.width - 62, 52), color=(0.75, 0.75, 0.75), width=0.4)
        page.insert_text((PAGE.width - 80, PAGE.height - 36), f"{index + 1}", fontname="helv", fontsize=8,
                         color=(0.45, 0.45, 0.45))

    for index in sorted(scanned_pages):
        _rasterise(buffer, index)

    buffer.set_metadata({
        "title": doc.title,
        "author": "Veridion sample generator",
        "subject": FICTION_NOTICE,
        "creator": "Veridion",
    })
    buffer.subset_fonts()
    data = buffer.tobytes(garbage=4, deflate=True)
    buffer.close()
    return data


def _layout_to_pdf(html: str) -> bytes:
    import io

    out = io.BytesIO()
    writer = pymupdf.DocumentWriter(out)
    _render_html_page(writer, html)
    writer.close()
    return out.getvalue()


def _rasterise(doc: pymupdf.Document, index: int) -> None:
    """Replace a page with an image of itself, as a scanner would produce."""
    page = doc[index]
    pix = page.get_pixmap(dpi=200, colorspace=pymupdf.csGRAY)
    rect = page.rect
    doc.delete_page(index)
    new_page = doc.new_page(index, width=rect.width, height=rect.height)
    new_page.insert_image(rect, pixmap=pix)


def write_samples(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    from veridion.samples.content import ALDERMERE_AR_V2

    for company in COMPANIES:
        for document in company.documents:
            path = out_dir / f"{document.slug}.pdf"
            path.write_bytes(render_document(document))
            written.append(path)
    path = out_dir / f"{ALDERMERE_AR_V2.slug}.pdf"
    path.write_bytes(render_document(ALDERMERE_AR_V2))
    written.append(path)
    return written
