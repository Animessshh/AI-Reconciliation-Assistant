import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from src.logger import logging
from src.exception import CustomException
import sys


# ============================================================
# Configuration
# ============================================================

NUM_RECORDS = 1000

START_DATE = datetime(2026, 8, 1)

OUTPUT_PATH = Path("data/raw/reconciliation_data.csv")


SCENARIO_DISTRIBUTION = {
    "normal": 550,
    "processing_fee": 120,
    "delayed_settlement": 60,
    "missing_settlement": 60,
    "payment_amount_mismatch": 50,
    "settlement_amount_mismatch": 50,
    "duplicate_payment": 40,
    "duplicate_settlement": 30,
    "failed_payment": 30,
    "unexplained_discrepancy": 10,
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
    Generate a random order date.
    """

    random_days = random.randint(0, 30)

    return START_DATE + timedelta(days=random_days)


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

    return round(amount * fee_rate, 2)


def create_scenario_list():
    """
    Create a shuffled list containing all scenarios.
    """

    if sum(SCENARIO_DISTRIBUTION.values()) != NUM_RECORDS:
        raise ValueError(
            "Scenario distribution does not equal NUM_RECORDS."
        )

    scenarios = []

    for scenario, count in SCENARIO_DISTRIBUTION.items():
        scenarios.extend([scenario] * count)

    random.shuffle(scenarios)

    return scenarios


# ============================================================
# Generate One Record
# ============================================================

def generate_record(index, scenario):

    try:

        # ----------------------------------------------------
        # Order
        # ----------------------------------------------------

        order_id = f"ORD{index:06d}"

        customer_id = f"CUST{random.randint(1, 300):04d}"

        order_date = generate_order_date()

        order_amount = generate_order_amount()


        # ----------------------------------------------------
        # Payment
        # ----------------------------------------------------

        payment_id = f"PAY{index:06d}"

        payment_date = order_date + timedelta(
            days=random.randint(0, 1)
        )

        payment_method = random.choice(PAYMENT_METHODS)

        payment_status = "Success"

        payment_amount = order_amount

        payment_count = 1


        # ----------------------------------------------------
        # Settlement
        # ----------------------------------------------------

        settlement_id = f"SET{index:06d}"

        settlement_date = payment_date + timedelta(days=1)

        fee = calculate_fee(
            payment_amount,
            payment_method
        )

        adjustment = 0.0

        settlement_amount = round(
            payment_amount - fee + adjustment,
            2
        )

        settlement_status = "Settled"

        settlement_count = 1


        # ====================================================
        # Apply Scenario
        # ====================================================

        if scenario == "normal":

            pass


        elif scenario == "processing_fee":

            # Normal settlement after processing fee.
            pass


        elif scenario == "delayed_settlement":

            settlement_date = payment_date + timedelta(
                days=random.randint(3, 7)
            )


        elif scenario == "missing_settlement":

            settlement_id = None
            settlement_date = None
            settlement_amount = None
            fee = 0.0

            settlement_status = "Missing"


        elif scenario == "payment_amount_mismatch":

            payment_amount = round(
                order_amount * random.uniform(0.80, 0.95),
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


        elif scenario == "settlement_amount_mismatch":

            difference = random.randint(
                100,
                max(100, int(settlement_amount * 0.4))
            )

            settlement_amount = round(
                settlement_amount - difference,
                2
            )


        elif scenario == "duplicate_payment":

            payment_count = 2


        elif scenario == "duplicate_settlement":

            settlement_count = 2


        elif scenario == "failed_payment":

            payment_status = "Failed"

            settlement_id = None
            settlement_date = None
            settlement_amount = None

            fee = 0.0

            settlement_status = "Not Applicable"


        elif scenario == "unexplained_discrepancy":

            difference = random.randint(
                100,
                max(100, int(settlement_amount * 0.4))
            )

            settlement_amount = round(
                settlement_amount - difference,
                2
            )


        else:

            raise ValueError(
                f"Unknown scenario: {scenario}"
            )


        # ====================================================
        # Final Record
        # ====================================================

        return {

            # Order
            "order_id": order_id,
            "customer_id": customer_id,
            "order_date": order_date.date(),
            "order_amount": order_amount,

            # Payment
            "payment_id": payment_id,
            "payment_date": payment_date.date(),
            "payment_amount": payment_amount,
            "payment_method": payment_method,
            "payment_status": payment_status,
            "payment_count": payment_count,

            # Settlement
            "settlement_id": settlement_id,
            "settlement_date": (
                settlement_date.date()
                if settlement_date
                else None
            ),
            "settlement_amount": settlement_amount,
            "fee": fee,
            "adjustment": adjustment,
            "settlement_status": settlement_status,
            "settlement_count": settlement_count,

            # Ground truth
            "scenario": scenario
        }


    except Exception as error:

        logging.error(
            f"Error generating record {index}: {error}"
        )

        raise CustomException(
            error,
            sys
        )


# ============================================================
# Dataset Generation
# ============================================================

def generate_dataset():

    try:

        logging.info(
            "Starting synthetic dataset generation."
        )


        # ----------------------------------------------------
        # Create scenarios
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


        # ----------------------------------------------------
        # Save
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
            "\n" + str(
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