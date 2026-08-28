from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_root() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "service": "Abuse Ring Sentinel",
        "status": "online",
        "version": "1.0.0",
    }


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
    }


def test_list_accounts() -> None:
    response = client.get("/accounts")

    assert response.status_code == 200

    accounts = response.json()

    assert isinstance(accounts, list)
    assert len(accounts) == 100

    first_account = accounts[0]

    assert "account_id" in first_account
    assert "label" in first_account


def test_get_high_risk_account() -> None:
    response = client.get("/accounts/ACC_00001")

    assert response.status_code == 200

    data = response.json()

    assert data["account_id"] == "ACC_00001"
    assert 0.0 <= data["abuse_probability"] <= 1.0
    assert 0 <= data["risk_score"] <= 100
    assert data["risk_level"] in {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    }
    assert data["decision"] in {
        "ALLOW",
        "MONITOR",
        "REVIEW",
    }
    assert isinstance(data["reasons"], list)
    assert len(data["reasons"]) > 0


def test_get_unknown_account() -> None:
    response = client.get("/accounts/ACC_99999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Account not found: ACC_99999",
    }


def test_risk_response_schema() -> None:
    response = client.get("/accounts/ACC_00001")

    assert response.status_code == 200

    data = response.json()

    expected_fields = {
        "account_id",
        "abuse_probability",
        "risk_score",
        "risk_level",
        "decision",
        "reasons",
    }

    assert set(data) == expected_fields


def test_openapi_available() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()

    assert schema["info"]["title"] == "Abuse Ring Sentinel"
    assert "/health" in schema["paths"]
    assert "/accounts" in schema["paths"]
    assert "/accounts/{account_id}" in schema["paths"]