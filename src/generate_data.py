import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from src.exception import CustomException
from src.logger import logging


# ============================================================
# Configuration
# ============================================================

NUM_RECORDS = 1000

START_DATE = datetime(2026, 8, 1)

OUTPUT_PATH = Path(
    "data/raw/reconciliation_data.csv"
)


SCENARIO_DISTRIBUTION = {
    "normal": 500,
    "processing_fee": 100,
    "delayed_settlement": 60,
    "missing_settlement": 60,
    "payment_amount_mismatch": 50,
    "explainable_settlement_mismatch": 70,
    "unexplainable_settlement_mismatch": 50,
    "conflicting_settlement_evidence": 30,
    "duplicate_payment": 40,
    "duplicate_settlement": 10,
    "failed_payment": 30,
}


PAYMENT_METHODS = [
    "UPI",
    "Card",
    "Netbanking",
    "Wallet"
]


# ============================================================
# Helper Functions
# ============================================================

def generate_order_amount():
    """
    Generate a realistic synthetic order amount.
    """

    common_amounts = [
        299,
        499,
        799,
        999,
        1499,
        1999,
        2499,
        2999,
        3999,
        4999,
        5999,
        7499,
        9999
    ]

    if random.random() < 0.7:
        return random.choice(common_amounts)

    return random.randint(200, 15000)


def generate_order_date():
    """
    Generate a random order date within the dataset period.
    """

    random_days = random.randint(0, 30)

    return START_DATE + timedelta(
        days=random_days
    )


def calculate_fee(amount, payment_method):
    """
    Calculate a synthetic processing fee.

    These rates are fictional and are only used
    for our synthetic dataset.
    """

    fee_rates = {
        "UPI": 0.01,
        "Card": 0.02,
        "Netbanking": 0.015,
        "Wallet": 0.018
    }

    fee_rate = fee_rates[payment_method]

    return round(
        amount * fee_rate,
        2
    )


def create_scenario_list():
    """
    Create and shuffle the list of scenarios.
    """

    if sum(SCENARIO_DISTRIBUTION.values()) != NUM_RECORDS:

        raise ValueError(
            "Scenario distribution does not equal "
            "NUM_RECORDS."
        )

    scenarios = []

    for scenario, count in SCENARIO_DISTRIBUTION.items():

        scenarios.extend(
            [scenario] * count
        )

    random.shuffle(scenarios)

    return scenarios


# ============================================================
# Generate One Record
# ============================================================

def generate_record(index, scenario):

    try:

        # ====================================================
        # ORDER INFORMATION
        # ====================================================

        order_id = f"ORD{index:06d}"

        customer_id = (
            f"CUST{random.randint(1, 300):04d}"
        )

        order_date = generate_order_date()

        order_amount = generate_order_amount()


        # ====================================================
        # PAYMENT INFORMATION
        # ====================================================

        payment_id = f"PAY{index:06d}"

        payment_date = order_date + timedelta(
            days=random.randint(0, 1)
        )

        payment_method = random.choice(
            PAYMENT_METHODS
        )

        payment_status = "Success"

        payment_amount = order_amount

        payment_count = 1


        # ====================================================
        # SETTLEMENT INFORMATION
        # ====================================================

        settlement_id = f"SET{index:06d}"

        settlement_reference = (
            f"STLREF-{random.randint(100000, 999999)}"
        )

        settlement_date = (
            payment_date + timedelta(days=1)
        )

        fee = calculate_fee(
            payment_amount,
            payment_method
        )

        adjustment = 0.0

        settlement_amount = round(
            payment_amount
            - fee
            + adjustment,
            2
        )

        settlement_status = "Settled"

        settlement_count = 1


        # ====================================================
        # AI INVESTIGATION EVIDENCE
        # ====================================================

        adjustment_type = "None"

        adjustment_reason = "None"

        settlement_note = (
            "No additional deductions recorded."
        )

        refund_amount = 0.0

        refund_status = "None"


        # ====================================================
        # APPLY SCENARIO
        # ====================================================

        # ----------------------------------------------------
        # 1. NORMAL
        # ----------------------------------------------------

        if scenario == "normal":

            pass


        # ----------------------------------------------------
        # 2. PROCESSING FEE
        # ----------------------------------------------------

        elif scenario == "processing_fee":

            # A legitimate processing fee is already
            # reflected in the settlement calculation.

            adjustment_type = "None"

            adjustment_reason = "None"

            settlement_note = (
                "Settlement processed after standard "
                "payment processing fee."
            )


        # ----------------------------------------------------
        # 3. DELAYED SETTLEMENT
        # ----------------------------------------------------

        elif scenario == "delayed_settlement":

            settlement_date = (
                payment_date
                + timedelta(
                    days=random.randint(3, 7)
                )
            )

            settlement_note = (
                "Settlement processed after the "
                "standard settlement window."
            )


        # ----------------------------------------------------
        # 4. MISSING SETTLEMENT
        # ----------------------------------------------------

        elif scenario == "missing_settlement":

            settlement_id = None

            settlement_reference = None

            settlement_date = None

            settlement_amount = None

            fee = 0.0

            settlement_status = "Missing"

            settlement_note = (
                "No settlement record available."
            )


        # ----------------------------------------------------
        # 5. PAYMENT AMOUNT MISMATCH
        # ----------------------------------------------------

        elif scenario == "payment_amount_mismatch":

            payment_amount = round(
                order_amount
                * random.uniform(0.80, 0.95),
                2
            )

            fee = calculate_fee(
                payment_amount,
                payment_method
            )

            settlement_amount = round(
                payment_amount - fee,
                2
            )

            settlement_note = (
                "Settlement amount calculated "
                "from recorded payment amount."
            )


        # ----------------------------------------------------
        # 6. EXPLAINABLE SETTLEMENT MISMATCH
        # ----------------------------------------------------

        elif scenario == "explainable_settlement_mismatch":

            difference = random.randint(
                100,
                min(
                    1000,
                    max(
                        100,
                        int(settlement_amount * 0.30)
                    )
                )
            )

            settlement_amount = round(
                settlement_amount - difference,
                2
            )

            # The financial adjustment remains 0 because
            # this deduction has NOT been recorded as a
            # formal financial adjustment.
            adjustment = 0.0

            # These fields provide supporting evidence
            # for the AI investigator.
            adjustment_type = "Manual Deduction"

            adjustment_reason = (
                "Settlement processing deduction"
            )

            settlement_note = (
                f"Manual deduction of INR "
                f"{difference:.2f} applied during "
                "settlement processing."
            )

            refund_amount = 0.0

            refund_status = "None"


        # ----------------------------------------------------
        # 7. UNEXPLAINABLE SETTLEMENT MISMATCH
        # ----------------------------------------------------

        elif scenario == "unexplainable_settlement_mismatch":

            difference = random.randint(
                100,
                min(
                    1000,
                    max(
                        100,
                        int(settlement_amount * 0.30)
                    )
                )
            )

            settlement_amount = round(
                settlement_amount - difference,
                2
            )

            settlement_note = (
                "No additional deductions recorded."
            )

            adjustment_type = "None"

            adjustment_reason = "None"

            refund_amount = 0.0

            refund_status = "None"


        # ----------------------------------------------------
        # 8. CONFLICTING SETTLEMENT EVIDENCE
        # ----------------------------------------------------

        elif scenario == "conflicting_settlement_evidence":

            difference = random.randint(
                100,
                min(
                    1000,
                    max(
                        100,
                        int(settlement_amount * 0.30)
                    )
                )
            )

            settlement_amount = round(
                settlement_amount - difference,
                2
            )

            # The note claims that a manual deduction happened.
            settlement_note = (
                f"Manual deduction of INR "
                f"{difference:.2f} applied during "
                "settlement processing."
            )

            # BUT there is no corresponding financial
            # adjustment recorded.
            adjustment = 0.0

            adjustment_type = "None"

            adjustment_reason = "None"

            refund_amount = 0.0

            refund_status = "None"


        # ----------------------------------------------------
        # 9. DUPLICATE PAYMENT
        # ----------------------------------------------------

        elif scenario == "duplicate_payment":

            payment_count = 2

            settlement_note = (
                "Multiple successful payment records "
                "are associated with this order."
            )


        # ----------------------------------------------------
        # 10. DUPLICATE SETTLEMENT
        # ----------------------------------------------------

        elif scenario == "duplicate_settlement":

            settlement_count = 2

            settlement_note = (
                "Multiple settlement records are "
                "associated with this payment."
            )


        # ----------------------------------------------------
        # 11. FAILED PAYMENT
        # ----------------------------------------------------

        elif scenario == "failed_payment":

            payment_status = "Failed"

            settlement_id = None

            settlement_reference = None

            settlement_date = None

            settlement_amount = None

            fee = 0.0

            settlement_status = "Not Applicable"

            settlement_note = (
                "Payment failed. No settlement expected."
            )


        # ----------------------------------------------------
        # Invalid Scenario
        # ----------------------------------------------------

        else:

            raise ValueError(
                f"Unknown scenario: {scenario}"
            )


        # ====================================================
        # CREATE RECORD
        # ====================================================

        record = {

            # ------------------------------------------------
            # Order
            # ------------------------------------------------

            "order_id": order_id,

            "customer_id": customer_id,

            "order_date": order_date.date(),

            "order_amount": order_amount,


            # ------------------------------------------------
            # Payment
            # ------------------------------------------------

            "payment_id": payment_id,

            "payment_date": payment_date.date(),

            "payment_amount": payment_amount,

            "payment_method": payment_method,

            "payment_status": payment_status,

            "payment_count": payment_count,


            # ------------------------------------------------
            # Settlement
            # ------------------------------------------------

            "settlement_id": settlement_id,

            "settlement_reference": (
                settlement_reference
            ),

            "settlement_date": (
                settlement_date.date()
                if settlement_date
                else None
            ),

            "settlement_amount": (
                settlement_amount
            ),

            "fee": fee,

            "adjustment": adjustment,

            "settlement_status": (
                settlement_status
            ),

            "settlement_count": settlement_count,


            # ------------------------------------------------
            # Investigation Evidence
            # ------------------------------------------------

            "adjustment_type": (
                adjustment_type
            ),

            "adjustment_reason": (
                adjustment_reason
            ),

            "settlement_note": (
                settlement_note
            ),

            "refund_amount": (
                refund_amount
            ),

            "refund_status": (
                refund_status
            ),


            # ------------------------------------------------
            # Ground Truth
            # ------------------------------------------------

            "scenario": scenario,
        }

        return record


    except Exception as error:

        logging.error(
            f"Error generating record {index}: {error}"
        )

        raise CustomException(
            error,
            sys
        )


# ============================================================
# Generate Dataset
# ============================================================

def generate_dataset():

    try:

        logging.info(
            "Starting synthetic dataset generation."
        )


        # ----------------------------------------------------
        # Create scenario list
        # ----------------------------------------------------

        scenarios = create_scenario_list()


        # ----------------------------------------------------
        # Generate records
        # ----------------------------------------------------

        records = []

        for index, scenario in enumerate(
            scenarios,
            start=1
        ):

            record = generate_record(
                index,
                scenario
            )

            records.append(record)


        # ----------------------------------------------------
        # Create DataFrame
        # ----------------------------------------------------

        df = pd.DataFrame(records)


        # ----------------------------------------------------
        # Basic validation
        # ----------------------------------------------------

        if len(df) != NUM_RECORDS:

            raise ValueError(
                f"Expected {NUM_RECORDS} records, "
                f"but generated {len(df)}."
            )


        if df["order_id"].duplicated().any():

            raise ValueError(
                "Duplicate order IDs detected."
            )


        if df["payment_id"].duplicated().any():

            raise ValueError(
                "Duplicate payment IDs detected."
            )


        # ----------------------------------------------------
        # Save Dataset
        # ----------------------------------------------------

        OUTPUT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        df.to_csv(
            OUTPUT_PATH,
            index=False
        )


        # ----------------------------------------------------
        # Logging
        # ----------------------------------------------------

        logging.info(
            f"Dataset generated successfully: "
            f"{len(df)} records."
        )

        logging.info(
            f"Dataset saved to: {OUTPUT_PATH}"
        )

        logging.info(
            "Scenario distribution:"
        )

        logging.info(
            "\n"
            + str(
                df["scenario"].value_counts()
            )
        )


        return df


    except Exception as error:

        logging.error(
            "Dataset generation failed."
        )

        raise CustomException(
            error,
            sys
        )


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    generate_dataset()