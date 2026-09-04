import streamlit as st
import pandas as pd

from src.reconciliation_service import ReconciliationService
from src.ai_investigator import AIInvestigationError


INPUT_PATH = "data/raw/reconciliation_data.csv"


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="AI Reconciliation Assistant",
    page_icon="💰",
    layout="wide"
)


# --------------------------------------------------
# Backend service
# --------------------------------------------------

@st.cache_resource
def get_service():

    return ReconciliationService(
        input_path=INPUT_PATH
    )


service = get_service()


# --------------------------------------------------
# Run reconciliation
# --------------------------------------------------

with st.spinner("Running reconciliation engine..."):

    summary = service.get_summary()
    exceptions = service.get_exceptions()
    ai_cases = service.get_ai_cases()


# --------------------------------------------------
# Header
# --------------------------------------------------

st.title("AI Reconciliation Assistant")

st.markdown(
    """
    **Financial reconciliation and AI-assisted exception investigation**
    
    Automatically reconcile transactions, identify financial exceptions,
    and investigate settlement discrepancies using evidence-based AI.
    """
)

st.divider()


# --------------------------------------------------
# Summary metrics
# --------------------------------------------------

st.subheader("Reconciliation Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Transactions",
        summary["total_transactions"]
    )

with col2:
    st.metric(
        "Reconciled",
        summary["reconciled"]
    )

with col3:
    st.metric(
        "Exceptions",
        summary["exceptions"]
    )

with col4:
    st.metric(
        "AI Investigable",
        len(ai_cases)
    )

st.caption(
    "AI investigations are triggered only when requested by the user."
)

# --------------------------------------------------
# Exception breakdown
# --------------------------------------------------

st.subheader("Exception Breakdown")

exception_breakdown = (
    exceptions["exception_type"]
    .value_counts()
    .reset_index()
)

exception_breakdown.columns = [
    "Exception Type",
    "Count"
]



col1, col2 = st.columns([1, 1])

with col1:

    st.dataframe(
        exception_breakdown,
        use_container_width=True,
        hide_index=True
    )

with col2:

    chart_data = exception_breakdown.set_index(
        "Exception Type"
    )

    st.bar_chart(
        chart_data,
        use_container_width=True
    )
    
# --------------------------------------------------
# Exception cases
# --------------------------------------------------

st.divider()

st.subheader("Exception Cases")

st.caption(
    "Review detected reconciliation exceptions and select a "
    "settlement discrepancy for AI investigation."
)

display_columns = [
    "order_id",
    "exception_type",
    "difference"
]

exception_table = exceptions[display_columns].copy()

exception_table["difference"] = (
    exception_table["difference"]
    .abs()
)

exception_table = exception_table.rename(
    columns={
        "order_id": "Order ID",
        "exception_type": "Exception Type",
        "difference": "Amount Difference"
    }
)

st.dataframe(
    exception_table,
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# AI Investigation
# --------------------------------------------------


st.divider()

st.subheader("AI Investigation")

st.markdown(
    """
    Investigate settlement discrepancies using the financial
    evidence identified by the reconciliation engine.
    """
)

st.info(
    "Select a case below to investigate it with AI. "
    "AI investigation is performed only when requested."
)


# --------------------------------------------------
# Case selection
# --------------------------------------------------

case_options = ai_cases["order_id"].tolist()

selected_order = st.selectbox(
    "Select an exception to investigate",
    case_options
)


# --------------------------------------------------
# Selected case details
# --------------------------------------------------

selected_case = ai_cases[
    ai_cases["order_id"] == selected_order
].iloc[0]

selected_transaction = service.get_transaction(
    selected_order
)

st.markdown(
    f"### Selected Case: `{selected_order}`"
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Order Amount",
        f"₹{selected_transaction['order_amount']:,.2f}"
    )

with col2:
    st.metric(
        "Expected Settlement",
        f"₹{selected_case['expected_settlement']:,.2f}"
    )

with col3:
    st.metric(
        "Actual Settlement",
        f"₹{selected_transaction['settlement_amount']:,.2f}"
        if pd.notna(selected_transaction["settlement_amount"])
        else "Missing"
    )

with col4:
    st.metric(
        "Difference",
        f"₹{abs(selected_case['difference']):,.2f}"
    )





# --------------------------------------------------
# Case information
# --------------------------------------------------

with st.expander("View transaction details"):

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("#### Order")

        st.write(
            f"**Order ID:** {selected_transaction['order_id']}"
        )

        st.write(
            f"**Customer ID:** {selected_transaction['customer_id']}"
        )

        st.write(
            f"**Order Date:** {selected_transaction['order_date']}"
        )

        st.write(
            f"**Order Amount:** "
            f"₹{selected_transaction['order_amount']:,.2f}"
        )

    with col2:

        st.markdown("#### Payment")

        st.write(
            f"**Payment ID:** {selected_transaction['payment_id']}"
        )

        st.write(
            f"**Payment Method:** "
            f"{selected_transaction['payment_method']}"
        )

        st.write(
            f"**Payment Status:** "
            f"{selected_transaction['payment_status']}"
        )

        st.write(
            f"**Payment Amount:** "
            f"₹{selected_transaction['payment_amount']:,.2f}"
        )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("#### Settlement")

        st.write(
            f"**Settlement ID:** "
            f"{selected_transaction['settlement_id']}"
        )

        st.write(
            f"**Settlement Date:** "
            f"{selected_transaction['settlement_date']}"
        )

        settlement_amount = (
            selected_transaction["settlement_amount"]
        )

        if pd.notna(settlement_amount):

            st.write(
                f"**Settlement Amount:** "
                f"₹{settlement_amount:,.2f}"
            )

        else:

            st.write(
                "**Settlement Amount:** Missing"
            )

        st.write(
            f"**Settlement Status:** "
            f"{selected_transaction['settlement_status']}"
        )

    with col2:

        st.markdown("#### Financial Evidence")

        st.write(
            f"**Fee:** "
            f"₹{selected_transaction['fee']:,.2f}"
        )

        st.write(
            f"**Adjustment:** "
            f"₹{selected_transaction['adjustment']:,.2f}"
        )

        st.write(
            f"**Adjustment Type:** "
            f"{selected_transaction['adjustment_type']}"
        )

        st.write(
            f"**Adjustment Reason:** "
            f"{selected_transaction['adjustment_reason']}"
        )

        st.write(
            f"**Settlement Note:** "
            f"{selected_transaction['settlement_note']}"
        )


# --------------------------------------------------
# AI Investigation button
# --------------------------------------------------

if st.button(
    "🔍 Investigate with AI",
    type="primary"
):

    with st.spinner(
        "AI is investigating the financial evidence..."
    ):

        try:

            investigation = (
                service.investigate_with_ai(
                    selected_order
                )
            )

            st.session_state[
                "investigation_result"
            ] = investigation

            st.session_state[
                "investigated_order"
            ] = selected_order

        except AIInvestigationError as e:

            st.error(
                f"⚠️ {e}"
            )

        except Exception:

            st.error(
                "⚠️ An unexpected error occurred during "
                "the AI investigation. Please try again."
            )


# --------------------------------------------------
# Display AI result
# --------------------------------------------------

if (
    "investigation_result" in st.session_state
    and
    st.session_state.get("investigated_order")
    == selected_order
):

    investigation = (
        st.session_state[
            "investigation_result"
        ]
    )

    st.divider()

    st.subheader("AI Investigation Result")

    # ----------------------------------------------
    # Decision
    # ----------------------------------------------

    if investigation.decision == "RESOLVED":

        st.success(
            "✓ Case Resolved"
        )

        st.markdown(
            "**Decision:** The discrepancy can be explained "
            "by the available evidence."
        )

    else:

        st.warning(
            "⚠ Human Review Required"
        )

        st.markdown(
            "**Decision:** The discrepancy requires manual review."
        )

    # ----------------------------------------------
    # Investigation reason
    # ----------------------------------------------

    st.markdown("### Investigation Summary")

    st.write(
        investigation.reason
    )

    # ----------------------------------------------
    # Confidence
    # ----------------------------------------------

    st.markdown("### AI Confidence")

    st.progress(
        investigation.confidence
    )

    st.caption(
        f"{investigation.confidence:.0%} confidence "
        "in this investigation decision"
    )

    # ----------------------------------------------
    # Supporting evidence
    # ----------------------------------------------

    st.markdown("### Evidence Supporting Decision")

    evidence_labels = {
        "order.order_id": "Order ID",
        "order.order_amount": "Order Amount",

        "payment.payment_id": "Payment ID",
        "payment.payment_amount": "Payment Amount",
        "payment.payment_status": "Payment Status",

        "settlement.expected_settlement":
            "Expected Settlement",

        "settlement.settlement_amount":
            "Actual Settlement",

        "settlement.difference":
            "Settlement Difference",

        "settlement.settlement_status":
            "Settlement Status",

        "settlement.settlement_date":
            "Settlement Date",

        "financial_evidence.fee":
            "Processing Fee",

        "financial_evidence.adjustment":
            "Recorded Adjustment",

        "financial_evidence.refund_amount":
            "Refund Amount",

        "financial_evidence.refund_status":
            "Refund Status",

        "supporting_evidence.adjustment_type":
            "Adjustment Type",

        "supporting_evidence.adjustment_reason":
            "Adjustment Reason",

        "supporting_evidence.settlement_note":
            "Settlement Note",
    }

    for evidence in investigation.evidence:

        label = evidence_labels.get(
            evidence,
            evidence.replace(
                "_", " "
            ).replace(
                ".", " → "
            ).title()
        )

        st.write(
            f"✓ **{label}**"
        )

    # ----------------------------------------------
    # Recommended action
    # ----------------------------------------------

    st.markdown("### Recommended Action")

    if investigation.decision == "RESOLVED":

        st.info(
            "No further investigation is required for this exception."
        )

    else:

        st.info(
            "Review the transaction and settlement records manually "
            "before taking any financial action."
        )
        
# --------------------------------------------------
# Investigation History
# --------------------------------------------------

st.divider()

st.subheader("Investigation History")

st.caption(
    "Audit trail of AI investigations performed on reconciliation exceptions."
)

audit_history = service.get_audit_history()

if audit_history.empty:

    st.info(
        "No AI investigations have been recorded yet."
    )

else:

    history_display = audit_history[
        [
            "timestamp",
            "order_id",
            "decision",
            "confidence",
            "status"
        ]
    ].copy()

    history_display = history_display.rename(
        columns={
            "timestamp": "Timestamp",
            "order_id": "Order ID",
            "decision": "Decision",
            "confidence": "Confidence",
            "status": "Status"
        }
    )

    history_display["Confidence"] = (
        history_display["Confidence"]
        .apply(lambda x: f"{x:.0%}")
    )

    st.dataframe(
        history_display,
        use_container_width=True,
        hide_index=True
    )