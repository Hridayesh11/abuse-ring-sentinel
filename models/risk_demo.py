from __future__ import annotations

from models.inference import (
    assess_account_by_id,
    load_dataset,
    train_inference_model,
)


def main() -> None:
    dataset = load_dataset()
    model = train_inference_model()

    account_ids = [
        "ACC_00001",
        "ACC_00007",
        "ACC_00013",
        "ACC_00015",
        "ACC_00048",
        "ACC_00042",
    ]

    print()
    print("Abuse Ring Sentinel — Risk Assessment")
    print("=" * 60)

    for account_id in account_ids:
        try:
            assessment = assess_account_by_id(
                model,
                dataset,
                account_id,
            )
        except ValueError:
            continue

        print()
        print(
            f"Account           : "
            f"{assessment.account_id}"
        )
        print(
            f"Abuse probability : "
            f"{assessment.abuse_probability:.4f}"
        )
        print(
            f"Risk score        : "
            f"{assessment.risk_score}/100"
        )
        print(
            f"Risk level        : "
            f"{assessment.risk_level}"
        )
        print(
            f"Decision          : "
            f"{assessment.decision}"
        )

        print("Reasons:")

        for reason in assessment.reasons:
            print(f"  - {reason}")


if __name__ == "__main__":
    main()