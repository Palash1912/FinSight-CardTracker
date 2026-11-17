"""Statement parser registry, PDF text extractor, and detector."""

from __future__ import annotations

import io
from typing import Final

from pypdf import PdfReader

from app.parsers.base import BaseStatementParser, ParsedStatementData
from app.parsers.generic import GenericStatementParser
from app.parsers.hdfc import HDFCStatementParser
from app.parsers.hsbc import HSBCStatementParser
from app.parsers.icici import ICICIStatementParser

# Registered parsers in priority order
PARSERS: Final[list[BaseStatementParser]] = [
    ICICIStatementParser(),
    HDFCStatementParser(),
    HSBCStatementParser(),
    GenericStatementParser(),
]


def extract_text_from_pdf(pdf_bytes: bytes) -> tuple[str, list[str]]:
    """Extract raw text from PDF bytes.

    Returns:
        tuple of (full_text, list_of_page_texts)
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    page_texts: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        page_texts.append(page_text)

    full_text = "\n".join(page_texts)
    return full_text, page_texts


def detect_and_parse(pdf_bytes: bytes) -> tuple[ParsedStatementData, str]:
    """Extract text and parse using the best matching statement parser adapter.

    Returns:
        tuple of (ParsedStatementData, parser_name)
    """
    full_text, pages = extract_text_from_pdf(pdf_bytes)

    for parser in PARSERS:
        if parser.can_parse(full_text):
            result = parser.parse(full_text, pages)
            return result, parser.name

    # Fallback to generic
    generic = GenericStatementParser()
    return generic.parse(full_text, pages), generic.name
