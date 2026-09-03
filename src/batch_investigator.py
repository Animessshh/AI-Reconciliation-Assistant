from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

from src.ai_investigator import (
    AIInvestigator,
    InvestigationCaseBuilder
)


class BatchInvestigator:

    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers

    def _investigate_case(self, case):
        """
        Investigate a single case.
        """

        investigator = AIInvestigator()

        try:
            result = investigator.investigate(case)

            return {
                "order_id": case.order["order_id"],
                "exception_type": case.engine_finding["exception_type"],
                "decision": result.decision,
                "reason": result.reason,
                "evidence": "|".join(result.evidence),
                "confidence": result.confidence,
                "status": "SUCCESS"
            }

        except Exception as e:

            return {
                "order_id": case.order["order_id"],
                "exception_type": case.engine_finding["exception_type"],
                "decision": None,
                "reason": None,
                "evidence": None,
                "confidence": None,
                "status": f"FAILED: {str(e)}"
            }

    def investigate_cases(
        self,
        cases: List
    ) -> List[Dict]:
        """
        Investigate multiple cases concurrently.
        """

        results = []

        with ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:

            future_to_case = {
                executor.submit(
                    self._investigate_case,
                    case
                ): case
                for case in cases
            }

            completed = 0
            total = len(cases)

            for future in as_completed(future_to_case):

                result = future.result()

                results.append(result)

                completed += 1

                print(
                    f"Completed {completed}/{total} "
                    f"| Order: {result['order_id']} "
                    f"| Status: {result['status']}"
                )

        return results