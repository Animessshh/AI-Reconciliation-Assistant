import pandas as pd

from src.reconciliation_engine import ReconciliationEngine
from src.ai_investigator import InvestigationCaseBuilder
from src.batch_investigator import BatchInvestigator


INPUT_PATH = "data/raw/reconciliation_data.csv"


def main():

    # -----------------------------
    # 1. Run reconciliation engine
    # -----------------------------

    engine = ReconciliationEngine(
        input_path=INPUT_PATH
    )

    results = engine.run()

    source = engine.df

    # ----------------------------------------
    # 2. Select cases requiring AI investigation
    # ----------------------------------------

    settlement_mismatches = results[
        results["exception_type"] == "SETTLEMENT_AMOUNT_MISMATCH"
    ]



    # Process all AI-required cases

    

    cases = []

    for _, result in settlement_mismatches.iterrows():

        order_id = result["order_id"]

        row = source[
            source["order_id"] == order_id
        ].iloc[0]

        case = InvestigationCaseBuilder.build(
            row,
            result
        )

        cases.append(case)

    print("\n" + "=" * 60)
    print("BATCH AI INVESTIGATION")
    print("=" * 60)

    print(f"Cases selected : {len(cases)}")
    print(f"Workers        : 5")
    print("=" * 60)

    # ----------------------------------------
    # 4. Run batch investigation
    # ----------------------------------------

    batch_investigator = BatchInvestigator(
        max_workers=5
    )

    investigation_results = (
        batch_investigator.investigate_cases(
            cases
        )
    )
    
    # ----------------------------------------
    # 5. Save results
    # ----------------------------------------

    output_path = "data/processed/ai_investigation_results.csv"

    ai_results_df = pd.DataFrame(
        investigation_results
    )

    ai_results_df.to_csv(
        output_path,
        index=False
    )

    print("\n" + "=" * 60)
    print("AI INVESTIGATION COMPLETE")
    print("=" * 60)

    print(
        f"Results saved to: {output_path}"
    )

    print(
        f"Total cases: {len(ai_results_df)}"
    )

    print(
        f"Successful: "
        f"{(ai_results_df['status'] == 'SUCCESS').sum()}"
    )

    print(
        f"Failed: "
        f"{(ai_results_df['status'] != 'SUCCESS').sum()}"
    )

    # ----------------------------------------
    # 6. Display results
    # ----------------------------------------
    '''
    print("\n" + "=" * 60)
    print("BATCH RESULTS")
    print("=" * 60)

    for result in investigation_results:

        print(
            f"\nOrder ID   : {result['order_id']}"
        )

        print(
            f"Decision   : {result['decision']}"
        )

        print(
            f"Confidence : {result['confidence']}"
        )

        print(
            f"Status     : {result['status']}"
        )

        print(
            f"Reason     : {result['reason']}"
        )

        print(
            f"Evidence   : {result['evidence']}"
        )
    '''


if __name__ == "__main__":
    main()