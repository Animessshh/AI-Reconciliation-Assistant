import pandas as pd

from src.reconciliation_engine import ReconciliationEngine
from src.ai_investigator import (
    AIInvestigator,
    InvestigationCaseBuilder
)


INPUT_PATH = "data/raw/reconciliation_data.csv"


EXPECTED_DECISIONS = {
    "explainable_settlement_mismatch": "RESOLVED",
    "unexplainable_settlement_mismatch": "HUMAN_REVIEW",
    "conflicting_settlement_evidence": "HUMAN_REVIEW"
}


def main():

    # ----------------------------------------------
    # Run reconciliation
    # ----------------------------------------------

    engine = ReconciliationEngine(
        input_path=INPUT_PATH
    )

    results = engine.run()

    source = engine.df

    # ----------------------------------------------
    # Select representative cases
    # ----------------------------------------------

    scenarios = list(
        EXPECTED_DECISIONS.keys()
    )

    selected_cases = []

    for scenario in scenarios:

        scenario_rows = source[
            source["scenario"] == scenario
        ].head(3)

        selected_cases.extend(
            scenario_rows["order_id"].tolist()
        )

    print("\n" + "=" * 70)
    print("AI INVESTIGATOR EVALUATION")
    print("=" * 70)

    print(
        f"Testing {len(selected_cases)} representative cases"
    )

    # ----------------------------------------------
    # Investigate cases sequentially
    # ----------------------------------------------

    investigator = AIInvestigator()

    passed = 0
    failed = 0

    evaluation_results = []

    for order_id in selected_cases:

        source_row = source[
            source["order_id"] == order_id
        ].iloc[0]

        result_row = results[
            results["order_id"] == order_id
        ].iloc[0]

        scenario = source_row["scenario"]

        expected_decision = (
            EXPECTED_DECISIONS[scenario]
        )

        case = InvestigationCaseBuilder.build(
            source_row,
            result_row
        )

        print("\n" + "-" * 70)
        print(f"Order ID : {order_id}")
        print(f"Scenario : {scenario}")
        print(
            f"Expected : {expected_decision}"
        )

        try:

            investigation = investigator.investigate(
                case
            )

            actual_decision = (
                investigation.decision
            )

            passed_case = (
                actual_decision
                == expected_decision
            )

            if passed_case:
                passed += 1
                status = "PASS"
            else:
                failed += 1
                status = "FAIL"

            print(
                f"AI Decision : {actual_decision}"
            )

            print(
                f"Confidence  : "
                f"{investigation.confidence:.0%}"
            )

            print(
                f"Status      : {status}"
            )

            print(
                f"Reason      : "
                f"{investigation.reason}"
            )

            evaluation_results.append({
                "order_id": order_id,
                "scenario": scenario,
                "expected_decision": expected_decision,
                "actual_decision": actual_decision,
                "confidence": investigation.confidence,
                "status": status
            })

        except Exception as e:

            failed += 1

            print(
                f"Status      : ERROR"
            )

            print(
                f"Error       : {e}"
            )

            evaluation_results.append({
                "order_id": order_id,
                "scenario": scenario,
                "expected_decision": expected_decision,
                "actual_decision": None,
                "confidence": None,
                "status": "ERROR"
            })

    # ----------------------------------------------
    # Evaluation summary
    # ----------------------------------------------

    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)

    print(
        f"Total cases : {len(selected_cases)}"
    )

    print(
        f"Passed      : {passed}"
    )

    print(
        f"Failed      : {failed}"
    )

    accuracy = (
        passed / len(selected_cases)
        if selected_cases
        else 0
    )

    print(
        f"Decision accuracy : {accuracy:.0%}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()