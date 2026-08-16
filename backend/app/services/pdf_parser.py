from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import pdfplumber
from pdfminer.pdfdocument import PDFPasswordIncorrect

from app.utils.boleto_regex import (
    extract_beneficiario,
    extract_linha_digitavel,
    extract_valor,
    extract_vencimento,
)

MIN_TEXT_LENGTH = 50


class PdfPasswordProtectedError(Exception):
    """PDF está protegido por senha e não pôde ser aberto com a senha informada (ou nenhuma)."""


@dataclass
class BoletoData:
    valor: Decimal | None
    vencimento: date | None
    linha_digitavel: str | None
    beneficiario: str | None

    def is_usable(self) -> bool:
        return self.valor is not None and self.vencimento is not None


def _extract_text_pdfplumber(pdf_bytes: bytes, password: str | None = None) -> str:
    text_parts: list[str] = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes), password=password or "") as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_parts.append(page_text)
    except PDFPasswordIncorrect as exc:
        raise PdfPasswordProtectedError from exc
    return "\n".join(text_parts)


def _extract_text_ocr(pdf_bytes: bytes) -> str:
    try:
        import pytesseract
        from pdf2image import convert_from_bytes
    except ImportError:
        return ""

    try:
        images = convert_from_bytes(pdf_bytes)
    except Exception:  # noqa: BLE001 - poppler pode não estar instalado no ambiente
        return ""

    text_parts = [pytesseract.image_to_string(image, lang="por+eng") for image in images]
    return "\n".join(text_parts)


def extract_text(pdf_bytes: bytes, password: str | None = None) -> str:
    text = _extract_text_pdfplumber(pdf_bytes, password=password)
    if len(text.strip()) < MIN_TEXT_LENGTH:
        ocr_text = _extract_text_ocr(pdf_bytes)
        if len(ocr_text.strip()) > len(text.strip()):
            text = ocr_text
    return text


def parse_boleto_pdf(pdf_bytes: bytes, password: str | None = None) -> BoletoData | None:
    text = extract_text(pdf_bytes, password=password)
    if not text.strip():
        return None

    data = BoletoData(
        valor=extract_valor(text),
        vencimento=extract_vencimento(text),
        linha_digitavel=extract_linha_digitavel(text),
        beneficiario=extract_beneficiario(text),
    )

    if not data.is_usable():
        return None

    return data
