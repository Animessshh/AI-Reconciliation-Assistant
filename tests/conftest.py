import pytest

from src.reconciliation_engine import ReconciliationEngine


INPUT_PATH = "data/raw/reconciliation_data.csv"


@pytest.fixture
def engine():

    return ReconciliationEngine(
        input_path=INPUT_PATH
    )