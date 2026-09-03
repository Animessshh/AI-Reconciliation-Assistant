import json
from typing import List

import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from google import genai
from google.genai import types

from dataclasses import dataclass
load_dotenv()

ALLOWED_DECISIONS = {
    "RESOLVED",
    "HUMAN_REVIEW",
}

def _is_missing(value):
    return pd.isna(value)


class InvestigationResult(BaseModel):
    decision: str = Field(
        description="Final investigation decision. Must be RESOLVED or HUMAN_REVIEW."
    )

    reason: str = Field(
        description="Concise explanation of why the discrepancy was resolved or sent for human review."
    )

    evidence: List[str] = Field(
        description="Field names from the case data that directly support the decision."
    )

    confidence: float = Field(
        description="Confidence in the decision, between 0 and 1."
    )

    def validate(self):
        if self.decision not in ALLOWED_DECISIONS:
            raise ValueError(
                f"Invalid decision: {self.decision}. "
                f"Allowed decisions: {ALLOWED_DECISIONS}"
            )

        if not self.reason.strip():
            raise ValueError("Investigation reason cannot be empty.")

        if not self.evidence:
            raise ValueError("Investigation must contain supporting evidence.")

        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1.")

        return True
    
@dataclass
class InvestigationCase:
    """
    Structured case containing the information
    required by the AI investigator.
    """

    order: dict

    payment: dict

    settlement: dict

    financial_evidence: dict

    supporting_evidence: dict

    engine_finding: dict
    
    def to_prompt(self):
        """
        Convert the investigation case into a
        structured prompt for the AI investigator.
        """

        case_data = {
            "order": self.order,
            "payment": self.payment,
            "settlement": self.settlement,
            "financial_evidence": self.financial_evidence,
            "supporting_evidence": self.supporting_evidence,
            "engine_finding": self.engine_finding,
        }

        case_json = json.dumps(
            case_data,
            indent=2,
            default=str
        )

        return f"""
            Investigate the following financial reconciliation case.

            IMPORTANT RULES:

            1. Use only the evidence provided in this case.
            2. Do not invent missing transactions, adjustments,
            fees, refunds, or explanations.
            3. Do not assume that a settlement note is automatically
            correct.
            4. If the available evidence fully explains the
            discrepancy, return RESOLVED.
            5. If evidence is missing, insufficient, or contradictory,
            return HUMAN_REVIEW.
            6. Every conclusion must reference the evidence that
            supports it.
            7. Do not modify or recommend changing any financial
            amount.
            8. This is an investigation task only.

            CASE DATA
            ---------

            {case_json}

            REQUIRED OUTPUT

            Return a structured investigation result containing:

            - decision: RESOLVED or HUMAN_REVIEW
            - reason: concise explanation of the conclusion
            - evidence: list of field names that support the conclusion
            - confidence: number between 0 and 1
            """
    
    



class InvestigationCaseBuilder:

    @staticmethod
    def build(row, reconciliation_result):

        return InvestigationCase(

            order={
                "order_id": row["order_id"],
                "order_amount": float(
                    row["order_amount"]
                ),
                "order_date": row["order_date"],
            },

            payment={
                "payment_id": row["payment_id"],
                "payment_date": row["payment_date"],
                "payment_amount": float(
                    row["payment_amount"]
                ),
                "payment_method": row["payment_method"],
                "payment_status": row["payment_status"],
                "payment_count": int(
                    row["payment_count"]
                ),
            },

            settlement={
                "settlement_id": row["settlement_id"],
                "settlement_reference": row[
                    "settlement_reference"
                ],
                "settlement_date": row[
                    "settlement_date"
                ],
                "settlement_amount": (
                    None
                    if _is_missing(
                        row["settlement_amount"]
                    )
                    else float(
                        row["settlement_amount"]
                    )
                ),

                "expected_settlement": (
                    reconciliation_result[
                        "expected_settlement"
                    ]
                ),

                "difference": (
                    reconciliation_result[
                        "difference"
                    ]
                ),

                "settlement_status": row[
                    "settlement_status"
                ],

                "settlement_count": int(
                    row["settlement_count"]
                ),
            },

            financial_evidence={
                "fee": float(
                    row["fee"]
                ),

                "adjustment": float(
                    row["adjustment"]
                ),

                "refund_amount": float(
                    row["refund_amount"]
                ),

                "refund_status": (
                    None
                    if _is_missing(
                        row["refund_status"]
                    )
                    else row["refund_status"]
                ),
            },

            supporting_evidence={
                "adjustment_type": (
                    None
                    if _is_missing(
                        row["adjustment_type"]
                    )
                    else row["adjustment_type"]
                ),

                "adjustment_reason": (
                    None
                    if _is_missing(
                        row["adjustment_reason"]
                    )
                    else row["adjustment_reason"]
                ),

                "settlement_note": (
                    None
                    if _is_missing(
                        row["settlement_note"]
                    )
                    else row["settlement_note"]
                ),
            },

            engine_finding={
                "reconciliation_status":
                    reconciliation_result[
                        "reconciliation_status"
                    ],

                "exception_type":
                    reconciliation_result[
                        "exception_type"
                    ],

                "exception_description":
                    reconciliation_result[
                        "exception_description"
                    ],

                "ai_required":
                    reconciliation_result[
                        "ai_required"
                    ],

                "warning":
                    reconciliation_result[
                        "warning"
                    ],
            },
        )
        
class AIInvestigator:

    SYSTEM_PROMPT = """
        You are an AI financial reconciliation investigator.

        Your job is to investigate settlement discrepancies identified
        by a deterministic reconciliation engine.

        You are an investigation and explanation system only.

        Rules:

        1. Use ONLY the evidence provided in the case data.

        2. Never invent missing facts, adjustments, fees, refunds,
        or explanations.

        3. Do not assume that a settlement note is automatically correct.

        4. Return RESOLVED only when the provided evidence sufficiently
        explains the settlement discrepancy.

        5. If evidence is missing, insufficient, or contradictory,
        return HUMAN_REVIEW.

        6. Every conclusion must reference specific evidence fields.

        7. Do not modify any financial amount.

        8. Do not recommend changing financial amounts.

        9. Do not approve refunds, payouts, deductions, or other
        financial actions.

        10. When uncertain, return HUMAN_REVIEW.

        CONFIDENCE GUIDELINES:

        Confidence represents how strongly the available evidence
        supports your investigation decision.

        Use the following general scale:

        - 0.90 to 1.00:
        Strong and direct evidence clearly supports the decision.

        - 0.75 to 0.89:
        Evidence reasonably supports the decision but there is
        some uncertainty or limited supporting information.

        - 0.50 to 0.74:
        Evidence is weak, incomplete, or ambiguous.

        - Below 0.50:
        Evidence is highly insufficient or contradictory.

        Do not automatically use 1.0.

        A HUMAN_REVIEW decision can still have high confidence when
        you are highly confident that the provided evidence is
        insufficient or contradictory. In that situation, confidence
        refers to confidence in the investigation decision, not
        confidence about the underlying cause of the discrepancy.

        Do not assign high confidence merely because a discrepancy
        exists. Evaluate the quality and consistency of the evidence.
    """

    def __init__(self, model="gemini-3.5-flash-lite"):

        self.client = genai.Client(
            http_options=types.HttpOptions(
            timeout=120000,
            api_version="v1"
            )
        )
        self.model = model

    def investigate(self, case: InvestigationCase) -> InvestigationResult:

        interaction = self.client.interactions.create(
            model=self.model,
            input=case.to_prompt(),
            system_instruction=self.SYSTEM_PROMPT,
            response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": InvestigationResult.model_json_schema(),
                },
            generation_config={
                "thinking_level": "low"
            }
        )

        if not interaction.output_text:
            raise ValueError(
                "Gemini returned an empty response."
            )

        result = InvestigationResult.model_validate_json(
            interaction.output_text
        )

        result.validate()

        return result
        

    