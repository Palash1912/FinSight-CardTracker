"""Statement parsing module."""

from app.parsers.base import BaseStatementParser, ParsedStatementData, RawTransaction
from app.parsers.detector import detect_and_parse, extract_text_from_pdf
from app.parsers.generic import GenericStatementParser
from app.parsers.hdfc import HDFCStatementParser
from app.parsers.hsbc import HSBCStatementParser
from app.parsers.icici import ICICIStatementParser

__all__ = [
    "BaseStatementParser",
    "ParsedStatementData",
    "RawTransaction",
    "ICICIStatementParser",
    "HDFCStatementParser",
    "HSBCStatementParser",
    "GenericStatementParser",
    "detect_and_parse",
    "extract_text_from_pdf",
]
