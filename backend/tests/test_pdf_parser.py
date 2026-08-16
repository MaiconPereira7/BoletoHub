from __future__ import annotations

import io

from reportlab.pdfgen import canvas

from app.services.pdf_parser import extract_text, parse_boleto_pdf


def _build_boleto_pdf(lines: list[str]) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(595, 842))
    pdf.setFont("Helvetica", 10)

    y = 800
    for line in lines:
        pdf.drawString(40, y, line)
        y -= 20

    pdf.save()
    return buffer.getvalue()


def _blank_pdf() -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(595, 842))
    pdf.save()
    return buffer.getvalue()


def test_parse_boleto_pdf_extracts_all_fields() -> None:
    pdf_bytes = _build_boleto_pdf(
        [
            "Beneficiario: Empresa XYZ Ltda",
            "Vencimento: 15/09/2026",
            "Valor do documento: R$ 1.234,56",
            "34191.79001 01043.510047 91020.150008 2 91070026000000",
        ]
    )

    data = parse_boleto_pdf(pdf_bytes)

    assert data is not None
    assert data.beneficiario == "Empresa XYZ Ltda"
    assert str(data.vencimento) == "2026-09-15"
    assert str(data.valor) == "1234.56"
    assert data.linha_digitavel is not None
    assert len(data.linha_digitavel) in (47, 48)


def test_parse_boleto_pdf_returns_none_for_non_boleto() -> None:
    pdf_bytes = _build_boleto_pdf(["Relatório mensal de vendas", "Nenhum dado financeiro relevante aqui"])

    data = parse_boleto_pdf(pdf_bytes)

    assert data is None


def test_parse_boleto_pdf_falls_back_to_ocr_gracefully_on_blank_pdf() -> None:
    pdf_bytes = _blank_pdf()

    text = extract_text(pdf_bytes)
    assert text.strip() == "" or len(text.strip()) < 5

    data = parse_boleto_pdf(pdf_bytes)
    assert data is None
