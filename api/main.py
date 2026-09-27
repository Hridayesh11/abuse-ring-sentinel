from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from audit.audit_log import record_case_action
from investigation.brief import build_investigator_brief
from investigation.investigator import build_investigation_context
from investigation.timeline import (
    build_account_timeline,
    timeline_to_dict,
)

from audit.audit_log import (
    get_account_audit_events,
    record_case_action,
)
from models.inference import (
    assess_all_accounts,
    load_dataset,
    train_inference_model,
)


DATASET_PATH = Path("datasets/abuse_ring_dataset.csv")
TRANSACTIONS_PATH = Path("datasets/transactions.csv")
ENTITIES_PATH = Path("datasets/shared_entities.json")
CASES_PATH = Path("datasets/investigation_cases.json")

CASE_ACTIONS = {
    "reviewed",
    "dismissed",
    "escalated",
    "restricted",
    "note_added",
    "open",
}


app = FastAPI(
    title="Abuse Ring Sentinel",
    description="Graph and entity-based abuse risk detection API",
    version="1.0.0",
)


# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Load ML data once on startup
# ---------------------------------------------------------------------------

dataset = load_dataset(DATASET_PATH)
model = train_inference_model(DATASET_PATH)


# ---------------------------------------------------------------------------
# Load additional relational data
# ---------------------------------------------------------------------------

transactions = []

with open(
    TRANSACTIONS_PATH,
    encoding="utf-8",
) as file:
    reader = csv.DictReader(file)

    for row in reader:
        transactions.append(row)


with open(
    ENTITIES_PATH,
    encoding="utf-8",
) as file:
    shared_entities = json.load(file)


# ---------------------------------------------------------------------------
# Pre-compute assessments for all accounts
# ---------------------------------------------------------------------------

all_assessments = assess_all_accounts(
    model,
    dataset,
)

assessment_by_id = {
    assessment.account_id: assessment
    for assessment in all_assessments
}


# ---------------------------------------------------------------------------
# Investigation case persistence
# ---------------------------------------------------------------------------

def _load_investigation_cases() -> dict[str, dict]:
    if not CASES_PATH.exists():
        return {}

    try:
        payload = json.loads(
            CASES_PATH.read_text(
                encoding="utf-8",
            )
        )
    except (OSError, json.JSONDecodeError):
        return {}

    if not isinstance(payload, dict):
        return {}

    return payload


def _save_investigation_cases() -> None:
    CASES_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    CASES_PATH.write_text(
        json.dumps(
            investigation_cases,
            indent=2,
        ),
        encoding="utf-8",
    )


investigation_cases: dict[str, dict] = (
    _load_investigation_cases()
)


def _case_payload(account_id: str) -> dict:
    record = investigation_cases.get(account_id)

    if not record:
        return {
            "account_id": account_id,
            "status": None,
            "updated_at": None,
            "notes": None,
            "investigator": None,
        }

    return {
        "account_id": account_id,
        "status": record.get("status"),
        "updated_at": record.get("updated_at"),
        "notes": record.get("notes"),
        "investigator": record.get("investigator"),
    }


# ---------------------------------------------------------------------------
# Primary signal
# ---------------------------------------------------------------------------

def _primary_signal(reasons: list[str]) -> str:
    """
    Convert the strongest existing risk reason into a concise
    investigator-facing primary signal.

    This does not create new risk logic. It only summarizes
    the existing assessment reason already produced by the
    risk engine.
    """
    if not reasons:
        return "No dominant signal"

    reason = reasons[0].strip()

    signal_mappings = (
        ("shared device", "Shared device"),
        ("shared ip", "Shared IP"),
        ("shared address", "Shared address"),
        ("shared payment", "Shared payment instrument"),
        ("multi-signal", "Multi-signal account links"),
        ("internal transaction", "High internal connectivity"),
        ("transaction", "Transaction behavior"),
        ("temporal", "Temporal behavior"),
    )

    normalized_reason = reason.lower()

    for keyword, label in signal_mappings:
        if keyword in normalized_reason:
            return label

    return reason


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class RiskResponse(BaseModel):
    account_id: str
    abuse_probability: float
    risk_score: int
    risk_level: str
    decision: str
    reasons: list[str]


class CaseActionRequest(BaseModel):
    action: str
    notes: str | None = None
    investigator: str | None = None


class CaseResponse(BaseModel):
    account_id: str
    status: str | None
    updated_at: str | None
    notes: str | None = None
    investigator: str | None = None


# ---------------------------------------------------------------------------
# Abuse Ring Discovery & Analytics
# ---------------------------------------------------------------------------

def _discover_abuse_rings() -> list[dict]:
    ring_members: dict[str, list[str]] = {}
    for entity in shared_entities:
        dev = str(entity.get("device_id", ""))
        if "RING_RING_" in dev:
            parts = dev.split("_")
            if len(parts) >= 3:
                r_id = f"RING_{parts[2]}"
                ring_members.setdefault(r_id, []).append(entity["account_id"])

    if not ring_members:
        dev_map: dict[str, list[str]] = {}
        for entity in shared_entities:
            dev = str(entity.get("device_id", ""))
            if dev:
                dev_map.setdefault(dev, []).append(entity["account_id"])
        idx = 1
        for dev, aids in dev_map.items():
            if len(aids) >= 3:
                ring_members[f"RING_{idx:03d}"] = aids
                idx += 1

    rings = []
    for ring_id, members in sorted(ring_members.items()):
        member_set = set(members)
        internal_txs = [
            t for t in transactions
            if t["sender_id"] in member_set and t["receiver_id"] in member_set
        ]
        internal_volume = sum(float(t["amount"]) for t in internal_txs)

        member_assessments = [
            assessment_by_id[aid] for aid in members if aid in assessment_by_id
        ]
        avg_score = (
            sum(a.risk_score for a in member_assessments) / len(member_assessments)
            if member_assessments else 0.0
        )
        max_score = (
            max(a.risk_score for a in member_assessments)
            if member_assessments else 0
        )
        critical_count = sum(1 for a in member_assessments if a.risk_level == "CRITICAL")
        high_count = sum(1 for a in member_assessments if a.risk_level == "HIGH")

        threat_level = "CRITICAL" if (avg_score >= 80 or critical_count >= 2) else "HIGH"

        primary_account = (
            max(member_assessments, key=lambda a: a.risk_score).account_id
            if member_assessments else members[0]
        )

        indicators = [
            f"Shared device & network entities across {len(members)} coordinated accounts",
            f"{len(internal_txs)} rapid circular transactions within ring",
            f"Concentrated internal volume (${internal_volume:,.2f})",
            f"{critical_count} critical & {high_count} high-risk members",
        ]

        rings.append({
            "ring_id": ring_id,
            "name": f"Syndicate {ring_id.replace('_', ' ')}",
            "threat_level": threat_level,
            "risk_score": int(round(max_score)),
            "avg_risk_score": round(avg_score, 1),
            "accounts_count": len(members),
            "primary_account": primary_account,
            "member_accounts": members,
            "internal_transactions": len(internal_txs),
            "internal_volume": round(internal_volume, 2),
            "critical_members_count": critical_count,
            "high_risk_members_count": high_count,
            "primary_pattern": "Hardware device fingerprint sharing & circular velocity funnel",
            "suspicious_indicators": indicators,
        })

    rings.sort(key=lambda r: (-r["risk_score"], -r["internal_volume"]))
    return rings


detected_abuse_rings = _discover_abuse_rings()


# ---------------------------------------------------------------------------
# Root / health
# ---------------------------------------------------------------------------

@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "Abuse Ring Sentinel",
        "status": "online",
        "version": "1.0.0",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "healthy",
    }


# ---------------------------------------------------------------------------
# Abuse rings list
# ---------------------------------------------------------------------------

@app.get("/rings")
def get_abuse_rings() -> list[dict]:
    """Return all detected abuse rings and suspicious clusters."""
    return detected_abuse_rings


# ---------------------------------------------------------------------------
# System statistics
# ---------------------------------------------------------------------------

@app.get("/stats")
def get_stats() -> dict:
    total_accounts = len(dataset)

    abuse_accounts = int(
        dataset["label"].sum()
    )

    normal_accounts = (
        total_accounts - abuse_accounts
    )

    critical_accounts = sum(
        1
        for assessment in assessment_by_id.values()
        if assessment.risk_level == "CRITICAL"
    )

    high_risk_accounts = sum(
        1
        for assessment in assessment_by_id.values()
        if assessment.risk_level == "HIGH"
    )

    review_count = sum(
        1
        for assessment in assessment_by_id.values()
        if assessment.decision == "REVIEW"
    )

    monitor_count = sum(
        1
        for assessment in assessment_by_id.values()
        if assessment.decision == "MONITOR"
    )

    allow_count = sum(
        1
        for assessment in assessment_by_id.values()
        if assessment.decision == "ALLOW"
    )

    total_flagged_volume = sum(
        float(t["amount"])
        for t in transactions
        if assessment_by_id.get(t["sender_id"], None)
        and assessment_by_id[t["sender_id"]].risk_level in ("HIGH", "CRITICAL")
    )

    return {
        "total_accounts": total_accounts,
        "abuse_accounts": abuse_accounts,
        "normal_accounts": normal_accounts,
        "critical_accounts": critical_accounts,
        "high_risk_accounts": high_risk_accounts,
        "medium_risk_accounts": sum(
            1
            for assessment in assessment_by_id.values()
            if assessment.risk_level == "MEDIUM"
        ),
        "low_risk_accounts": sum(
            1
            for assessment in assessment_by_id.values()
            if assessment.risk_level == "LOW"
        ),
        "review_count": review_count,
        "monitor_count": monitor_count,
        "allow_count": allow_count,
        "total_transactions": len(transactions),
        "detected_rings_count": len(detected_abuse_rings),
        "total_flagged_volume": round(total_flagged_volume, 2),
    }


# ---------------------------------------------------------------------------
# Account list
# ---------------------------------------------------------------------------

@app.get("/accounts")
def list_accounts() -> list[dict]:
    """
    Return accounts with their risk assessment for
    the frontend investigation queue.
    """
    result = []

    label_by_id = dict(
        zip(
            dataset["account_id"],
            dataset["label"],
            strict=False,
        )
    )

    for account_id, assessment in assessment_by_id.items():
        reasons = list(assessment.reasons)

        result.append(
            {
                "account_id": account_id,
                "label": int(
                    label_by_id.get(
                        account_id,
                        0,
                    )
                ),
                "abuse_probability": (
                    assessment.abuse_probability
                ),
                "risk_score": assessment.risk_score,
                "risk_level": assessment.risk_level,
                "decision": assessment.decision,
                "primary_signal": _primary_signal(
                    reasons
                ),
                "case_status": investigation_cases.get(
                    account_id,
                    {},
                ).get("status"),
            }
        )

    return result


# ---------------------------------------------------------------------------
# Account risk
# ---------------------------------------------------------------------------

@app.get(
    "/accounts/{account_id}",
    response_model=RiskResponse,
)
def get_account_risk(
    account_id: str,
) -> RiskResponse:
    if account_id not in assessment_by_id:
        raise HTTPException(
            status_code=404,
            detail=f"Account not found: {account_id}",
        )

    assessment = assessment_by_id[account_id]

    return RiskResponse(
        account_id=assessment.account_id,
        abuse_probability=(
            assessment.abuse_probability
        ),
        risk_score=assessment.risk_score,
        risk_level=assessment.risk_level,
        decision=assessment.decision,
        reasons=list(assessment.reasons),
    )


# ---------------------------------------------------------------------------
# Account case
# ---------------------------------------------------------------------------

@app.get(
    "/accounts/{account_id}/case",
    response_model=CaseResponse,
)
def get_account_case(
    account_id: str,
) -> CaseResponse:
    if account_id not in assessment_by_id:
        raise HTTPException(
            status_code=404,
            detail=f"Account not found: {account_id}",
        )

    return CaseResponse(
        **_case_payload(account_id)
    )


@app.post(
    "/accounts/{account_id}/case",
    response_model=CaseResponse,
)
def update_account_case(
    account_id: str,
    request: CaseActionRequest,
) -> CaseResponse:
    if account_id not in assessment_by_id:
        raise HTTPException(
            status_code=404,
            detail=f"Account not found: {account_id}",
        )

    action = request.action.strip().lower()

    if action not in CASE_ACTIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid action. Expected one of: "
                + ", ".join(sorted(CASE_ACTIONS))
            ),
        )

    previous_status = investigation_cases.get(
        account_id,
        {},
    ).get("status")

    if action == "open":
        investigation_cases.pop(
            account_id,
            None,
        )

        new_status = None

    elif action == "note_added":
        record = investigation_cases.get(account_id, {})
        new_status = record.get("status")
        investigation_cases[account_id] = {
            "status": new_status,
            "updated_at": datetime.now(UTC).isoformat(),
            "notes": request.notes or record.get("notes"),
            "investigator": request.investigator or record.get("investigator") or "Lead Risk Analyst",
        }

    else:
        investigation_cases[account_id] = {
            "status": action,
            "updated_at": datetime.now(
                UTC
            ).isoformat(),
            "notes": request.notes,
            "investigator": request.investigator or "Lead Risk Analyst",
        }

        new_status = action

    _save_investigation_cases()

    # Record the state transition after the case
    # persistence succeeds.
    record_case_action(
        account_id=account_id,
        action=action,
        previous_status=previous_status,
        new_status=new_status,
        notes=request.notes,
        investigator=request.investigator or "Lead Risk Analyst",
    )

    return CaseResponse(
        **_case_payload(account_id)
    )


# ---------------------------------------------------------------------------
# Account transactions
# ---------------------------------------------------------------------------

@app.get(
    "/accounts/{account_id}/transactions"
)
def get_account_transactions(
    account_id: str,
) -> list[dict]:
    if account_id not in assessment_by_id:
        raise HTTPException(
            status_code=404,
            detail=f"Account not found: {account_id}",
        )

    account_transactions = []

    for transaction in transactions:
        if (
            transaction["sender_id"] == account_id
            or transaction["receiver_id"] == account_id
        ):
            direction = (
                "outgoing"
                if transaction["sender_id"] == account_id
                else "incoming"
            )

            counterparty = (
                transaction["receiver_id"]
                if direction == "outgoing"
                else transaction["sender_id"]
            )

            counterparty_assessment = assessment_by_id.get(counterparty)

            is_suspicious = (
                counterparty_assessment is not None
                and counterparty_assessment.risk_level in ("HIGH", "CRITICAL")
            )

            suspicious_reason = (
                f"Counterparty {counterparty} is flagged as {counterparty_assessment.risk_level} risk (Score: {counterparty_assessment.risk_score})"
                if is_suspicious and counterparty_assessment
                else None
            )

            account_transactions.append(
                {
                    **transaction,
                    "direction": direction,
                    "counterparty": counterparty,
                    "counterparty_risk_level": (
                        counterparty_assessment.risk_level
                        if counterparty_assessment
                        else "NORMAL"
                    ),
                    "counterparty_risk_score": (
                        counterparty_assessment.risk_score
                        if counterparty_assessment
                        else 0
                    ),
                    "is_suspicious": is_suspicious,
                    "suspicious_reason": suspicious_reason,
                }
            )

    account_transactions.sort(
        key=lambda item: item["timestamp"],
        reverse=True,
    )

    return account_transactions


# ---------------------------------------------------------------------------
# Account network
# ---------------------------------------------------------------------------

@app.get(
    "/accounts/{account_id}/network"
)
def get_account_network(
    account_id: str,
) -> dict:
    if account_id not in assessment_by_id:
        raise HTTPException(
            status_code=404,
            detail=f"Account not found: {account_id}",
        )

    nodes = {}
    edges = []

    def add_account_node(aid: str) -> None:
        if aid not in nodes:
            assessment = assessment_by_id.get(aid)

            if assessment:
                nodes[aid] = {
                    "id": aid,
                    "type": "account",
                    "risk_score": assessment.risk_score,
                    "risk_level": assessment.risk_level,
                    "abuse_probability": (
                        assessment.abuse_probability
                    ),
                    "decision": assessment.decision,
                }

            else:
                nodes[aid] = {
                    "id": aid,
                    "type": "account",
                }

    # 1. Add requested account
    add_account_node(account_id)

    # 2. Add transaction relationships
    account_transactions = [
        transaction
        for transaction in transactions
        if (
            transaction["sender_id"] == account_id
            or transaction["receiver_id"] == account_id
        )
    ]

    for transaction in account_transactions:
        other_id = (
            transaction["receiver_id"]
            if transaction["sender_id"] == account_id
            else transaction["sender_id"]
        )

        add_account_node(other_id)

        edges.append(
            {
                "source": transaction["sender_id"],
                "target": transaction["receiver_id"],
                "type": "transaction",
                "amount": float(
                    transaction["amount"]
                ),
                "timestamp": transaction["timestamp"],
            }
        )

    # 3. Add shared entity relationships
    account_entities = None

    for entity in shared_entities:
        if entity["account_id"] == account_id:
            account_entities = entity
            break

    if account_entities:
        for other in shared_entities:
            shared_types = []

            if (
                other["device_id"]
                == account_entities["device_id"]
            ):
                shared_types.append(
                    (
                        "device",
                        other["device_id"],
                    )
                )

            if (
                other["ip_id"]
                == account_entities["ip_id"]
            ):
                shared_types.append(
                    (
                        "ip",
                        other["ip_id"],
                    )
                )

            if (
                other["address_id"]
                == account_entities["address_id"]
            ):
                shared_types.append(
                    (
                        "address",
                        other["address_id"],
                    )
                )

            if (
                other["payment_instrument_id"]
                == account_entities[
                    "payment_instrument_id"
                ]
            ):
                shared_types.append(
                    (
                        "payment",
                        other[
                            "payment_instrument_id"
                        ],
                    )
                )

            if (
                shared_types
                and other["account_id"] != account_id
            ):
                other_id = other["account_id"]

                add_account_node(other_id)

                for entity_type, entity_id in shared_types:
                    node_id = (
                        f"{entity_type}_{entity_id}"
                    )

                    if node_id not in nodes:
                        nodes[node_id] = {
                            "id": node_id,
                            "type": "entity",
                            "entity_type": entity_type,
                        }

                    edges.append(
                        {
                            "source": account_id,
                            "target": node_id,
                            "type": (
                                f"shared_{entity_type}"
                            ),
                        }
                    )

                    edges.append(
                        {
                            "source": other_id,
                            "target": node_id,
                            "type": (
                                f"shared_{entity_type}"
                            ),
                        }
                    )

    # Deduplicate edges
    unique_edges = []
    seen = set()

    for edge in edges:
        if edge["type"].startswith("shared_"):
            edge_key = (
                tuple(
                    sorted(
                        [
                            edge["source"],
                            edge["target"],
                        ]
                    )
                )
                + (edge["type"],)
            )
        else:
            edge_key = (
                edge["source"],
                edge["target"],
                edge["type"],
                edge.get("timestamp"),
            )

        if edge_key not in seen:
            seen.add(edge_key)
            unique_edges.append(edge)

    return {
        "nodes": list(nodes.values()),
        "edges": unique_edges,
    }


# ---------------------------------------------------------------------------
# Complete investigation workspace
# ---------------------------------------------------------------------------

@app.get(
    "/accounts/{account_id}/investigation"
)
def get_account_investigation(
    account_id: str,
) -> dict:
    """
    Return the complete investigation workspace
    context.
    """
    if account_id not in assessment_by_id:
        raise HTTPException(
            status_code=404,
            detail=f"Account not found: {account_id}",
        )

    account_rows = dataset[
        dataset["account_id"] == account_id
    ]

    if account_rows.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Account data not found: {account_id}",
        )

    account_row = account_rows.iloc[0]
    assessment = assessment_by_id[account_id]
    case = _case_payload(account_id)

    context = build_investigation_context(
        account_id=account_id,
        account_row=account_row,
        risk_assessment=assessment,
        transactions=transactions,
        shared_entities=shared_entities,
        case=case,
    )

    response = context.to_dict()

    investigator_brief = build_investigator_brief(
        risk=assessment,
        evidence=list(context.evidence),
    )

    response["investigator_brief"] = (
        investigator_brief.to_dict()
    )

    audit_history = get_account_audit_events(
        account_id
    )

    evidence_payload = [
        item.to_dict()
        for item in context.evidence
    ]

    timeline = build_account_timeline(
        account_id=account_id,
        transactions=transactions,
        evidence=evidence_payload,
        audit_events=audit_history,
    )

    response["timeline"] = timeline_to_dict(
        timeline
    )

    response["audit_history"] = audit_history

    return response