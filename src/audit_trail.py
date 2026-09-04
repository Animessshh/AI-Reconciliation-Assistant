import os
from datetime import datetime

import pandas as pd


class AuditTrail:

    def __init__(
        self,
        audit_path="data/audit/ai_investigations.csv"
    ):

        self.audit_path = audit_path

        os.makedirs(
            os.path.dirname(self.audit_path),
            exist_ok=True
        )

    def record_investigation(
        self,
        order_id,
        exception_type,
        decision,
        reason,
        evidence,
        confidence,
        status="SUCCESS"
    ):

        record = {
            "timestamp": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "order_id": order_id,
            "exception_type": exception_type,
            "decision": decision,
            "reason": reason,
            "evidence": "|".join(evidence),
            "confidence": confidence,
            "status": status
        }

        record_df = pd.DataFrame([record])

        if os.path.exists(self.audit_path):

            record_df.to_csv(
                self.audit_path,
                mode="a",
                header=False,
                index=False
            )

        else:

            record_df.to_csv(
                self.audit_path,
                mode="w",
                header=True,
                index=False
            )
            
    def get_history(self):
        """
        Return all recorded AI investigations.
        """

        if not os.path.exists(self.audit_path):
            return pd.DataFrame(
                columns=[
                    "timestamp",
                    "order_id",
                    "exception_type",
                    "decision",
                    "reason",
                    "evidence",
                    "confidence",
                    "status"
                ]
            )

        return pd.read_csv(
            self.audit_path
    )