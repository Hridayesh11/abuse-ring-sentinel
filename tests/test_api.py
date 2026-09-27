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
    assert len(accounts) > 0

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


def test_get_stats() -> None:
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_accounts" in data
    assert "abuse_accounts" in data
    assert "normal_accounts" in data
    assert "critical_accounts" in data
    assert "high_risk_accounts" in data
    assert "review_count" in data
    assert "monitor_count" in data
    assert "allow_count" in data
    assert "total_transactions" in data
    assert data["total_accounts"] > 0


def test_get_account_network() -> None:
    response = client.get("/accounts/ACC_00001/network")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert isinstance(data["nodes"], list)
    assert isinstance(data["edges"], list)
    assert len(data["nodes"]) > 0

    account_ids = [node["id"] for node in data["nodes"]]
    assert "ACC_00001" in account_ids


def test_get_account_network_unknown() -> None:
    response = client.get("/accounts/ACC_99999/network")
    assert response.status_code == 404


def test_get_account_transactions() -> None:
    response = client.get("/accounts/ACC_00001/transactions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        first_txn = data[0]
        assert "transaction_id" in first_txn
        assert "amount" in first_txn
        assert "timestamp" in first_txn
        assert "direction" in first_txn


def test_get_account_transactions_unknown() -> None:
    response = client.get("/accounts/ACC_99999/transactions")
    assert response.status_code == 404


def test_get_account_case_defaults_to_open() -> None:
    from api import main as api_main

    original = dict(api_main.investigation_cases)
    api_main.investigation_cases.pop("ACC_00001", None)

    try:
        response = client.get("/accounts/ACC_00001/case")
        assert response.status_code == 200
        data = response.json()
        assert data["account_id"] == "ACC_00001"
        assert data["status"] is None
        assert data["updated_at"] is None
    finally:
        api_main.investigation_cases.clear()
        api_main.investigation_cases.update(original)
        api_main._save_investigation_cases()


def test_update_account_case_persists_status() -> None:
    from api import main as api_main

    original = dict(api_main.investigation_cases)

    try:
        response = client.post(
            "/accounts/ACC_00001/case",
            json={"action": "escalated"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["account_id"] == "ACC_00001"
        assert data["status"] == "escalated"
        assert data["updated_at"] is not None

        listed = client.get("/accounts").json()
        match = next(acc for acc in listed if acc["account_id"] == "ACC_00001")
        assert match["case_status"] == "escalated"

        reloaded = client.get("/accounts/ACC_00001/case").json()
        assert reloaded["status"] == "escalated"
    finally:
        api_main.investigation_cases.clear()
        api_main.investigation_cases.update(original)
        api_main._save_investigation_cases()


def test_update_account_case_can_reopen() -> None:
    from api import main as api_main

    original = dict(api_main.investigation_cases)

    try:
        client.post("/accounts/ACC_00001/case", json={"action": "reviewed"})
        response = client.post(
            "/accounts/ACC_00001/case",
            json={"action": "open"},
        )
        assert response.status_code == 200
        assert response.json()["status"] is None
    finally:
        api_main.investigation_cases.clear()
        api_main.investigation_cases.update(original)
        api_main._save_investigation_cases()


def test_update_account_case_unknown_account() -> None:
    response = client.post(
        "/accounts/ACC_99999/case",
        json={"action": "reviewed"},
    )
    assert response.status_code == 404


def test_update_account_case_invalid_action() -> None:
    response = client.post(
        "/accounts/ACC_00001/case",
        json={"action": "ignore"},
    )
    assert response.status_code == 400