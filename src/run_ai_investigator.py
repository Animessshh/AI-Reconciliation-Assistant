from src.reconciliation_engine import ReconciliationEngine
from src.ai_investigator import AIInvestigator, InvestigationCaseBuilder


INPUT_PATH = "data/raw/reconciliation_data.csv"


def main():

    # Run deterministic reconciliation
    engine = ReconciliationEngine(input_path=INPUT_PATH)

    results = engine.run()

    # Get original source data
    source = engine.df

    # Select one settlement mismatch for investigation
    settlement_mismatches = results[
        results["exception_type"] == "SETTLEMENT_AMOUNT_MISMATCH"
    ]

    result = settlement_mismatches.iloc[0]

    # Find corresponding original transaction
    order_id = result["order_id"]

    row = source[
        source["order_id"] == order_id
    ].iloc[0]

    # Build structured investigation case
    case = InvestigationCaseBuilder.build(
        row=row,
        reconciliation_result=result
    )

    # Create Gemini investigator
    investigator = AIInvestigator()

    # Investigate
    investigation = investigator.investigate(case)

    print("\n" + "=" * 60)
    print("AI INVESTIGATION RESULT")
    print("=" * 60)

    print(f"Order ID   : {order_id}")
    print(f"Decision   : {investigation.decision}")
    print(f"Reason     : {investigation.reason}")
    print(f"Evidence   : {investigation.evidence}")
    print(f"Confidence : {investigation.confidence}")

    print("=" * 60)


if __name__ == "__main__":
    main()