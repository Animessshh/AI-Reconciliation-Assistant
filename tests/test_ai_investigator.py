import pytest

from src.ai_investigator import (
    InvestigationCase,
    InvestigationCaseBuilder,
    InvestigationResult,
)

from src.reconciliation_engine import ReconciliationEngine

def test_valid_investigation_result():

    result = InvestigationResult(

        decision="RESOLVED",

        reason=(
            "Settlement note explains the "
            "entire discrepancy."
        ),

        evidence=[
            "settlement_note"
        ],

        confidence=0.95
    )

    assert result.validate() is True


def test_invalid_decision():

    result = InvestigationResult(

        decision="MAYBE",

        reason="Unclear discrepancy.",

        evidence=[
            "settlement_note"
        ],

        confidence=0.5
    )

    with pytest.raises(ValueError):

        result.validate()


def test_invalid_confidence():

    result = InvestigationResult(

        decision="RESOLVED",

        reason="Discrepancy explained.",

        evidence=[
            "settlement_note"
        ],

        confidence=1.5
    )

    with pytest.raises(ValueError):

        result.validate()


def test_missing_evidence():

    result = InvestigationResult(

        decision="HUMAN_REVIEW",

        reason="Evidence is insufficient.",

        evidence=[],

        confidence=0.9
    )

    with pytest.raises(ValueError):

        result.validate()
        
def test_investigation_case_builder(engine):

    results = engine.run()

    source = engine.df

    result = results[
        results["exception_type"]
        == "SETTLEMENT_AMOUNT_MISMATCH"
    ].iloc[0]

    order_id = result["order_id"]

    row = source[
        source["order_id"] == order_id
    ].iloc[0]

    case = InvestigationCaseBuilder.build(
        row,
        result
    )

    assert isinstance(
        case,
        InvestigationCase
    )

    assert (
        case.order["order_id"]
        == order_id
    )

    assert (
        case.engine_finding[
            "exception_type"
        ]
        == "SETTLEMENT_AMOUNT_MISMATCH"
    )

    assert case.engine_finding["ai_required"]
    
def test_investigation_case_contains_evidence(engine):

    results = engine.run()

    source = engine.df

    explainable_ids = source[
        source["scenario"]
        == "explainable_settlement_mismatch"
    ]["order_id"]

    order_id = explainable_ids.iloc[0]

    row = source[
        source["order_id"] == order_id
    ].iloc[0]

    result = results[
        results["order_id"] == order_id
    ].iloc[0]

    case = InvestigationCaseBuilder.build(
        row,
        result
    )

    assert (
        case.supporting_evidence[
            "adjustment_type"
        ]
        == "Manual Deduction"
    )

    assert (
        "Manual deduction"
        in case.supporting_evidence[
            "settlement_note"
        ]
    )
    
def test_investigation_case_generates_prompt(engine):

    results = engine.run()

    source = engine.df

    result = results[
        results["exception_type"]
        == "SETTLEMENT_AMOUNT_MISMATCH"
    ].iloc[0]

    order_id = result["order_id"]

    row = source[
        source["order_id"] == order_id
    ].iloc[0]

    case = InvestigationCaseBuilder.build(
        row,
        result
    )

    prompt = case.to_prompt()

    assert isinstance(prompt, str)

    assert "Investigate" in prompt

    assert '"order"' in prompt
    assert '"payment"' in prompt
    assert '"settlement"' in prompt
    assert '"financial_evidence"' in prompt
    assert '"supporting_evidence"' in prompt
    assert '"engine_finding"' in prompt

    assert "RESOLVED" in prompt
    assert "HUMAN_REVIEW" in prompt
    
def test_prompt_contains_case_data(engine):

    results = engine.run()

    source = engine.df

    result = results[
        results["exception_type"]
        == "SETTLEMENT_AMOUNT_MISMATCH"
    ].iloc[0]

    order_id = result["order_id"]

    row = source[
        source["order_id"] == order_id
    ].iloc[0]

    case = InvestigationCaseBuilder.build(
        row,
        result
    )

    prompt = case.to_prompt()

    assert order_id in prompt

    assert str(
        row["payment_id"]
    ) in prompt

    assert (
        "SETTLEMENT_AMOUNT_MISMATCH"
        in prompt
    )