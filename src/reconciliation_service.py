import pandas as pd
from src.audit_trail import AuditTrail
from src.reconciliation_engine import ReconciliationEngine
from src.ai_investigator import (
    AIInvestigator,
    InvestigationCaseBuilder
)


class ReconciliationService:

    def __init__(self, input_path: str):
        self.input_path = input_path
        self.engine = ReconciliationEngine(
            input_path=input_path
        )

        self._results = None
        self.audit_trail = AuditTrail()

    def run_reconciliation(self):
        """
        Run the deterministic reconciliation engine.
        """

        if self._results is None:
            self._results = self.engine.run()

        return self._results

    def get_source_data(self):
        """
        Return the original transaction data.
        """

        return self.engine.df

    def get_summary(self):
        """
        Return high-level reconciliation metrics.
        """

        results = self.run_reconciliation()

        total = len(results)

        reconciled = (
            results["reconciliation_status"] == "RECONCILED"
        ).sum()

        exceptions = (
            results["reconciliation_status"] == "EXCEPTION"
        ).sum()

        return {
            "total_transactions": total,
            "reconciled": int(reconciled),
            "exceptions": int(exceptions)
        }

    def get_exceptions(self):
        """
        Return all reconciliation exceptions.
        """

        results = self.run_reconciliation()

        return results[
            results["reconciliation_status"] == "EXCEPTION"
        ].copy()

    def get_ai_cases(self):
        """
        Return cases that require AI investigation.
        """

        results = self.run_reconciliation()

        return results[
            results["exception_type"]
            == "SETTLEMENT_AMOUNT_MISMATCH"
        ].copy()

    def build_investigation_case(self, order_id: str):
        """
        Build an InvestigationCase for a specific order.
        """

        results = self.run_reconciliation()
        source = self.get_source_data()

        result_rows = results[
            results["order_id"] == order_id
        ]

        if result_rows.empty:
            raise ValueError(
                f"No reconciliation result found "
                f"for order {order_id}."
            )

        result = result_rows.iloc[0]

        source_rows = source[
            source["order_id"] == order_id
        ]

        if source_rows.empty:
            raise ValueError(
                f"No source transaction found "
                f"for order {order_id}."
            )

        row = source_rows.iloc[0]

        return InvestigationCaseBuilder.build(
            row,
            result
        )

    def investigate_with_ai(self, order_id: str):
        """
        Investigate one selected case using AI
        and record the investigation in the audit trail.
        """

        case = self.build_investigation_case(
            order_id
        )

        investigator = AIInvestigator()

        investigation = investigator.investigate(
            case
        )

        self.audit_trail.record_investigation(
            order_id=order_id,
            exception_type=case.engine_finding[
                "exception_type"
            ],
            decision=investigation.decision,
            reason=investigation.reason,
            evidence=investigation.evidence,
            confidence=investigation.confidence
        )

        return investigation
    
    def get_audit_history(self):
        """
        Return the history of AI investigations.
        """

        return self.audit_trail.get_history()
    
    def get_transaction(self, order_id: str):
        """
        Return the original transaction for a specific order.
        """

        source = self.get_source_data()

        transaction = source[
            source["order_id"] == order_id
        ]

        if transaction.empty:
            raise ValueError(
                f"No transaction found for order {order_id}."
            )

        return transaction.iloc[0]