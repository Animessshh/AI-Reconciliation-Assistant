import sys
from pathlib import Path

import pandas as pd

from src.exception import CustomException
from src.logger import logging


INPUT_PATH = Path(
    "data/raw/reconciliation_data.csv"
)

OUTPUT_PATH = Path(
    "data/processed/reconciliation_results.csv"
)


class ReconciliationEngine:

    def __init__(self, input_path=INPUT_PATH):

        self.input_path = Path(input_path)

        self.df = None

        logging.info(
            "Reconciliation engine initialized."
        )


    # ========================================================
    # Load Data
    # ========================================================

    def load_data(self):

        try:

            logging.info(
                f"Loading reconciliation data from "
                f"{self.input_path}"
            )

            self.df = pd.read_csv(
                self.input_path
            )

            logging.info(
                f"Loaded {len(self.df)} records."
            )

            return self.df

        except Exception as error:

            logging.error(
                "Failed to load reconciliation data."
            )

            raise CustomException(
                error,
                sys
            )


    # ========================================================
    # Validate Required Columns
    # ========================================================

    def validate_columns(self):

        required_columns = [

            "order_id",
            "order_amount",

            "payment_id",
            "payment_amount",
            "payment_status",
            "payment_count",

            "settlement_id",
            "settlement_amount",
            "fee",
            "adjustment",
            "settlement_status",
            "settlement_count",

        ]

        missing_columns = [

            column
            for column in required_columns
            if column not in self.df.columns

        ]

        if missing_columns:

            raise ValueError(
                f"Missing required columns: "
                f"{missing_columns}"
            )

        logging.info(
            "All required columns are present."
        )


    # ========================================================
    # Rule 1 + Rule 2 + Rule 3 + Rule 4 + Rule 5 + Rule 6
    # ========================================================

    def reconcile_record(self, row):

        try:

            # ------------------------------------------------
            # Default result
            # ------------------------------------------------

            result = {

                "order_id": row["order_id"],

                "reconciliation_status": "RECONCILED",

                "exception_type": None,

                "exception_description": None,

                "expected_settlement": None,

                "actual_settlement": None,

                "difference": None,

                "warning": None,

                "ai_required": False,

            }


            # =================================================
            # RULE 1
            # Payment must be successful
            # =================================================

            if row["payment_status"] != "Success":

                result["reconciliation_status"] = "EXCEPTION"

                result["exception_type"] = (
                    "PAYMENT_NOT_SUCCESSFUL"
                )

                result["exception_description"] = (
                    "Payment was not successful."
                )

                result["ai_required"] = False

                return result


            # =================================================
            # RULE 2
            # Order amount must match payment amount
            # =================================================

            order_amount = float(
                row["order_amount"]
            )

            payment_amount = float(
                row["payment_amount"]
            )

            if abs(
                order_amount - payment_amount
            ) > 0.01:

                result["reconciliation_status"] = (
                    "EXCEPTION"
                )

                result["exception_type"] = (
                    "PAYMENT_AMOUNT_MISMATCH"
                )

                result["exception_description"] = (
                    f"Order amount is "
                    f"{order_amount:.2f}, but payment "
                    f"amount is "
                    f"{payment_amount:.2f}."
                )

                result["ai_required"] = True

                return result


            # =================================================
            # RULE 3
            # Successful payment should be exactly one
            # =================================================

            payment_count = int(
                row["payment_count"]
            )

            if payment_count == 0:

                result["reconciliation_status"] = (
                    "EXCEPTION"
                )

                result["exception_type"] = (
                    "PAYMENT_MISSING"
                )

                result["exception_description"] = (
                    "No successful payment exists "
                    "for this order."
                )

                result["ai_required"] = False

                return result


            if payment_count > 1:

                result["reconciliation_status"] = (
                    "EXCEPTION"
                )

                result["exception_type"] = (
                    "DUPLICATE_PAYMENT"
                )

                result["exception_description"] = (
                    f"{payment_count} successful "
                    f"payments found for this order."
                )

                result["ai_required"] = True

                return result


            # =================================================
            # RULE 4
            # Settlement must exist
            # =================================================

            if pd.isna(
                row["settlement_id"]
            ):

                result["reconciliation_status"] = (
                    "EXCEPTION"
                )

                result["exception_type"] = (
                    "SETTLEMENT_MISSING"
                )

                result["exception_description"] = (
                    "Successful payment exists, "
                    "but no settlement record exists."
                )

                result["ai_required"] = True

                return result


            # =================================================
            # RULE 5
            # Calculate expected settlement
            # =================================================

            fee = float(
                row["fee"]
            )

            adjustment = float(
                row["adjustment"]
            )

            expected_settlement = round(
                payment_amount
                - fee
                + adjustment,
                2
            )

            actual_settlement = round(
                float(row["settlement_amount"]),
                2
            )

            difference = round(
                expected_settlement
                - actual_settlement,
                2
            )

            result["expected_settlement"] = (
                expected_settlement
            )

            result["actual_settlement"] = (
                actual_settlement
            )

            result["difference"] = (
                difference
            )


            # =================================================
            # RULE 6
            # Expected settlement must match actual
            # settlement
            # =================================================

            if abs(difference) > 0.01:

                result["reconciliation_status"] = (
                    "EXCEPTION"
                )

                result["exception_type"] = (
                    "SETTLEMENT_AMOUNT_MISMATCH"
                )

                result["exception_description"] = (
                    f"Expected settlement is "
                    f"{expected_settlement:.2f}, "
                    f"but actual settlement is "
                    f"{actual_settlement:.2f}. "
                    f"Difference is "
                    f"{abs(difference):.2f}."
                )

                result["ai_required"] = True

                return result


            # =================================================
            # RULE 7
            # Duplicate settlement
            # =================================================

            settlement_count = int(
                row["settlement_count"]
            )

            if settlement_count > 1:

                result["reconciliation_status"] = (
                    "EXCEPTION"
                )

                result["exception_type"] = (
                    "DUPLICATE_SETTLEMENT"
                )

                result["exception_description"] = (
                    f"{settlement_count} settlement "
                    f"records found for this payment."
                )

                result["ai_required"] = True

                return result


            # =================================================
            # RULE 8
            # Settlement timing
            # =================================================

            payment_date = pd.to_datetime(
                row["payment_date"]
            )

            settlement_date = pd.to_datetime(
                row["settlement_date"]
            )

            settlement_delay = (
                settlement_date - payment_date
            ).days

            if settlement_delay > 2:

                result["warning"] = (
                    f"Settlement occurred "
                    f"{settlement_delay} days after "
                    f"payment."
                )


            return result


        except Exception as error:

            logging.error(
                f"Error reconciling order "
                f"{row.get('order_id')}: {error}"
            )

            raise CustomException(
                error,
                sys
            )


    # ========================================================
    # Run Reconciliation
    # ========================================================

    def run(self):

        try:

            logging.info(
                "Starting reconciliation process."
            )

            self.load_data()

            self.validate_columns()


            results = []

            for _, row in self.df.iterrows():

                result = self.reconcile_record(
                    row
                )

                results.append(result)


            results_df = pd.DataFrame(
                results
            )


            logging.info(
                "Reconciliation completed successfully."
            )

            logging.info(
                f"Total records processed: "
                f"{len(results_df)}"
            )

            logging.info(
                f"Reconciled records: "
                f"{(results_df['reconciliation_status'] == 'RECONCILED').sum()}"
            )

            logging.info(
                f"Exception records: "
                f"{(results_df['reconciliation_status'] == 'EXCEPTION').sum()}"
            )


            return results_df
        
        except Exception as e:
            raise CustomException(e,sys)


    # ========================================================
    # Save Results
    # ========================================================

    def save_results(self, results_df):

        try:

            OUTPUT_PATH.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            results_df.to_csv(
                OUTPUT_PATH,
                index=False
            )

            logging.info(
                f"Reconciliation results saved to "
                f"{OUTPUT_PATH}"
            )

        except Exception as error:

            logging.error(
                "Failed to save reconciliation results."
            )

            raise CustomException(
                error,
                sys
            )


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    try:

        engine = ReconciliationEngine()

        results = engine.run()

        engine.save_results(
            results
        )

        print(
            "\nReconciliation completed successfully."
        )

        print(
            f"Total records: {len(results)}"
        )

        print(
            "\nStatus:"
        )

        print(
            results[
                "reconciliation_status"
            ].value_counts()
        )

        print(
            "\nExceptions:"
        )

        print(
            results[
                "exception_type"
            ].value_counts(dropna=True)
        )


    except Exception as error:

        print(
            f"Reconciliation failed: {error}"
        )