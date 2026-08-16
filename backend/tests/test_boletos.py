from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


def _boleto_payload(**overrides: object) -> dict:
    payload = {
        "beneficiario": "Empresa XYZ Ltda",
        "pagador": "Fulano de Tal",
        "valor": "150.75",
        "linha_digitavel": "34191790010104351004791020150008291070026000",
        "data_vencimento": "2026-09-10",
        "observacoes": "Boleto de teste",
    }
    payload.update(overrides)
    return payload


async def test_create_boleto(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    response = await client.post("/boletos", json=_boleto_payload(), headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["beneficiario"] == "Empresa XYZ Ltda"
    assert body["status"] == "pendente"
    assert body["origem"] == "manual"


async def test_create_boleto_duplicate_linha_digitavel(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    await client.post("/boletos", json=_boleto_payload(), headers=auth_headers)
    response = await client.post("/boletos", json=_boleto_payload(), headers=auth_headers)
    assert response.status_code == 409


async def test_list_boletos(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    await client.post("/boletos", json=_boleto_payload(linha_digitavel="11111111111111111111111111111111111111111111"), headers=auth_headers)
    await client.post(
        "/boletos",
        json=_boleto_payload(
            linha_digitavel="22222222222222222222222222222222222222222222",
            data_vencimento="2026-12-01",
        ),
        headers=auth_headers,
    )

    response = await client.get("/boletos", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2


async def test_list_boletos_filter_by_status(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    create_response = await client.post("/boletos", json=_boleto_payload(), headers=auth_headers)
    boleto_id = create_response.json()["id"]
    await client.patch(f"/boletos/{boleto_id}", json={"status": "pago"}, headers=auth_headers)

    response = await client.get("/boletos", params={"status": "pago"}, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["status"] == "pago"
    assert body["items"][0]["data_pagamento"] is not None


async def test_get_boleto_detail(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    create_response = await client.post("/boletos", json=_boleto_payload(), headers=auth_headers)
    boleto_id = create_response.json()["id"]

    response = await client.get(f"/boletos/{boleto_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == boleto_id


async def test_update_boleto(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    create_response = await client.post("/boletos", json=_boleto_payload(), headers=auth_headers)
    boleto_id = create_response.json()["id"]

    response = await client.patch(
        f"/boletos/{boleto_id}", json={"observacoes": "Atualizado"}, headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["observacoes"] == "Atualizado"


async def test_delete_boleto(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    create_response = await client.post("/boletos", json=_boleto_payload(), headers=auth_headers)
    boleto_id = create_response.json()["id"]

    response = await client.delete(f"/boletos/{boleto_id}", headers=auth_headers)
    assert response.status_code == 204

    response = await client.get(f"/boletos/{boleto_id}", headers=auth_headers)
    assert response.status_code == 404


async def test_user_cannot_access_other_users_boleto(
    client: AsyncClient, auth_headers: dict[str, str], other_auth_headers: dict[str, str]
) -> None:
    create_response = await client.post("/boletos", json=_boleto_payload(), headers=auth_headers)
    boleto_id = create_response.json()["id"]

    response = await client.get(f"/boletos/{boleto_id}", headers=other_auth_headers)
    assert response.status_code == 404

    response = await client.get("/boletos", headers=other_auth_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 0
