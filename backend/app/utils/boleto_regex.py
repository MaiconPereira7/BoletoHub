from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

# Linha digitável: boletos bancários (47 dígitos, 5 blocos) ou de convênio (48 dígitos, contínuo)
LINHA_DIGITAVEL_BANCARIA_RE = re.compile(
    r"\b\d{5}[.\s]?\d{5}\s+\d{5}[.\s]?\d{6}\s+\d{5}[.\s]?\d{6}\s+\d\s+\d{14}\b"
)
LINHA_DIGITAVEL_CONVENIO_RE = re.compile(r"\b\d{11}[-\s]?\d\s+\d{11}[-\s]?\d\s+\d{11}[-\s]?\d\s+\d{11}[-\s]?\d\b")
LINHA_DIGITAVEL_CONTINUA_RE = re.compile(r"\b\d{47,48}\b")

DATA_RE = re.compile(r"\b(\d{2})/(\d{2})/(\d{4})\b")

VALOR_KEYWORDS_RE = re.compile(
    r"(?:valor(?:\s+do)?\s+documento|valor\s+cobrado|\(=\)\s*valor|total\s+a\s+pagar|valor)\s*[:\-]?\s*R?\$?\s*"
    r"(\d{1,3}(?:\.\d{3})*,\d{2})",
    re.IGNORECASE,
)
VALOR_GENERIC_RE = re.compile(r"R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})")

VENCIMENTO_KEYWORDS_RE = re.compile(
    r"vencimento\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})",
    re.IGNORECASE,
)

BENEFICIARIO_RE = re.compile(
    r"(?:benefici[aá]rio|cedente|raz[aã]o\s+social)\s*[:\-]?\s*([^\n]{3,120})",
    re.IGNORECASE,
)


def normalize_linha_digitavel(raw: str) -> str:
    return re.sub(r"[.\s-]", "", raw)


def extract_linha_digitavel(text: str) -> str | None:
    for pattern in (LINHA_DIGITAVEL_BANCARIA_RE, LINHA_DIGITAVEL_CONVENIO_RE, LINHA_DIGITAVEL_CONTINUA_RE):
        match = pattern.search(text)
        if match:
            digits = normalize_linha_digitavel(match.group(0))
            if len(digits) in (47, 48):
                return digits
    return None


def _parse_valor_str(raw: str) -> Decimal | None:
    try:
        return Decimal(raw.replace(".", "").replace(",", "."))
    except InvalidOperation:
        return None


def extract_valor(text: str) -> Decimal | None:
    match = VALOR_KEYWORDS_RE.search(text)
    if match:
        valor = _parse_valor_str(match.group(1))
        if valor is not None:
            return valor

    match = VALOR_GENERIC_RE.search(text)
    if match:
        return _parse_valor_str(match.group(1))

    return None


def _parse_data_str(raw: str) -> date | None:
    try:
        return datetime.strptime(raw, "%d/%m/%Y").date()
    except ValueError:
        return None


def extract_vencimento(text: str) -> date | None:
    match = VENCIMENTO_KEYWORDS_RE.search(text)
    if match:
        parsed = _parse_data_str(match.group(1))
        if parsed is not None:
            return parsed

    match = DATA_RE.search(text)
    if match:
        return _parse_data_str(match.group(0))

    return None


def extract_beneficiario(text: str) -> str | None:
    match = BENEFICIARIO_RE.search(text)
    if not match:
        return None
    beneficiario = match.group(1).strip()
    beneficiario = re.split(r"\s{2,}|\t", beneficiario)[0].strip()
    return beneficiario or None
