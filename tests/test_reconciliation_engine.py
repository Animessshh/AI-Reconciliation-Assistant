import pandas as pd
import pytest

from src.reconciliation_engine import ReconciliationEngine


INPUT_PATH = "data/raw/reconciliation_data.csv"


# ============================================================
# Expected Ground Truth
# ============================================================

EXPECTED_STATUS = {

    "normal": "RECONCILED",

    "processing_fee": "RECONCILED",

    "delayed_settlement": "RECONCILED",

    "missing_settlement": "EXCEPTION",

    "payment_amount_mismatch": "EXCEPTION",

    "explainable_settlement_mismatch": "EXCEPTION",

    "unexplainable_settlement_mismatch": "EXCEPTION",

    "conflicting_settlement_evidence": "EXCEPTION",

    "duplicate_payment": "EXCEPTION",

    "duplicate_settlement": "EXCEPTION",

    "failed_payment": "EXCEPTION",
}


EXPECTED_EXCEPTION = {

    "normal": None,

    "processing_fee": None,

    "delayed_settlement": None,

    "missing_settlement": "SETTLEMENT_MISSING",

    "payment_amount_mismatch": "PAYMENT_AMOUNT_MISMATCH",

    "explainable_settlement_mismatch":
        "SETTLEMENT_AMOUNT_MISMATCH",

    "unexplainable_settlement_mismatch":
        "SETTLEMENT_AMOUNT_MISMATCH",

    "conflicting_settlement_evidence":
        "SETTLEMENT_AMOUNT_MISMATCH",

    "duplicate_payment": "DUPLICATE_PAYMENT",

    "duplicate_settlement": "DUPLICATE_SETTLEMENT",

    "failed_payment": "PAYMENT_NOT_SUCCESSFUL",
}


# ============================================================
# Fixture
# ============================================================

@pytest.fixture
def engine():

    engine = ReconciliationEngine(
        input_path=INPUT_PATH
    )

    engine.run()

    return engine


# ============================================================
# Test 1
# ============================================================

def test_total_records_processed(engine):

    assert len(engine.df) == 1000


# ============================================================
# Test 2
# ============================================================

def test_all_scenarios_present(engine):

    scenario_counts = (
        engine.df["scenario"]
        .value_counts()
        .to_dict()
    )

    expected_counts = {

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

    assert scenario_counts == expected_counts


# ============================================================
# Test 3
# ============================================================

def test_reconciliation_status(engine):

    results = engine.run()

    results_with_scenario = engine.df[
        ["order_id", "scenario"]
    ].merge(
        results[
            ["order_id", "reconciliation_status"]
        ],
        on="order_id"
    )

    for scenario, expected_status in EXPECTED_STATUS.items():

        scenario_results = results_with_scenario[
            results_with_scenario["scenario"] == scenario
        ]

        assert not scenario_results.empty

        assert (
            scenario_results[
                "reconciliation_status"
            ] == expected_status
        ).all()


# ============================================================
# Test 4
# ============================================================

def test_exception_types(engine):

    results = engine.run()

    results_with_scenario = engine.df[
        ["order_id", "scenario"]
    ].merge(
        results[
            ["order_id", "exception_type"]
        ],
        on="order_id"
    )

    for scenario, expected_exception in EXPECTED_EXCEPTION.items():

        scenario_results = results_with_scenario[
            results_with_scenario["scenario"] == scenario
        ]

        assert not scenario_results.empty

        if expected_exception is None:

            assert (
                scenario_results[
                    "exception_type"
                ].isna()
            ).all()

        else:

            assert (
                scenario_results[
                    "exception_type"
                ] == expected_exception
            ).all()


# ============================================================
# Test 5
# ============================================================

def test_expected_settlement_calculation(engine):

    results = engine.run()

    source = engine.df.copy()

    source["expected_settlement_test"] = (
        source["payment_amount"]
        - source["fee"]
        + source["adjustment"]
    ).round(2)

    results_with_source = source[
        [
            "order_id",
            "expected_settlement_test",
            "payment_status",
            "settlement_amount",
        ]
    ].merge(
        results[
            [
                "order_id",
                "expected_settlement",
            ]
        ],
        on="order_id"
    )

    valid_records = results_with_source[
        results_with_source["payment_status"] == "Success"
    ]

    valid_records = valid_records[
        valid_records["settlement_amount"].notna()
    ]

    valid_records = valid_records[
        valid_records["expected_settlement"].notna()
    ]

    differences = (
        valid_records["expected_settlement"]
        - valid_records["expected_settlement_test"]
    ).abs()

    assert (
        differences < 0.01
    ).all()


# ============================================================
# Test 6
# ============================================================

def test_settlement_mismatch_records_require_ai(engine):

    results = engine.run()

    mismatch_records = results[
        results["exception_type"]
        == "SETTLEMENT_AMOUNT_MISMATCH"
    ]

    assert len(mismatch_records) == 150

    assert (
        mismatch_records["ai_required"] == True
    ).all()


# ============================================================
# Test 7
# ============================================================

def test_delayed_settlements_are_warnings_not_exceptions(engine):

    results = engine.run()

    source = engine.df[
        [
            "order_id",
            "scenario"
        ]
    ]

    delayed_records = source[
        source["scenario"] == "delayed_settlement"
    ]

    delayed_results = delayed_records.merge(
        results[
            [
                "order_id",
                "reconciliation_status",
                "warning"
            ]
        ],
        on="order_id"
    )

    assert (
        delayed_results[
            "reconciliation_status"
        ] == "RECONCILED"
    ).all()

    assert (
        delayed_results[
            "warning"
        ].notna()
    ).all()


# ============================================================
# Test 8
# ============================================================

def test_ai_required_for_investigative_exceptions(engine):

    results = engine.run()

    ai_exception_types = [

        "PAYMENT_AMOUNT_MISMATCH",

        "DUPLICATE_PAYMENT",

        "SETTLEMENT_MISSING",

        "SETTLEMENT_AMOUNT_MISMATCH",

        "DUPLICATE_SETTLEMENT",
    ]

    ai_records = results[
        results["exception_type"].isin(
            ai_exception_types
        )
    ]

    assert (
        ai_records["ai_required"] == True
    ).all()


# ============================================================
# Test 9
# ============================================================

def test_failed_payments_do_not_require_ai(engine):

    results = engine.run()

    failed_records = results[
        results["exception_type"]
        == "PAYMENT_NOT_SUCCESSFUL"
    ]

    assert len(failed_records) == 30

    assert (
        failed_records["ai_required"] == False
    ).all()