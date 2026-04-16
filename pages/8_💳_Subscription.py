import os
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="TradeIQ™ | Subscription",
    page_icon="💳",
    layout="wide",
)

from utils.helpers import (
    init_session_state,
    apply_global_css,
    render_custom_sidebar,
    require_auth,
    go_to,
)
from utils.subscription import (
    init_subscription_db,
    SUBSCRIPTION_PLANS,
    save_payment_evidence,
    create_subscription_request,
    get_user_subscription_requests,
    get_latest_active_or_pending_status,
)

init_session_state()
apply_global_css()
require_auth()
init_subscription_db()

left_col, right_col = st.columns([1, 4], gap="large")

with left_col:
    render_custom_sidebar("Subscription")

with right_col:
    st.markdown('<div class="tiq-page-title">💳 Subscription</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="tiq-page-subtitle">Choose a plan, pay outside the app, and upload payment evidence for admin approval.</div>',
        unsafe_allow_html=True
    )

    user = st.session_state.current_user or {}
    user_name = user.get("name", "")
    user_email = user.get("email", "")
    institution_name = user.get("company_name", "")
    phone_number = user.get("phone_number", "")

    latest_status = get_latest_active_or_pending_status(user_email)

    if latest_status:
        css_class = {
            "pending": "tiq-warning",
            "approved": "tiq-note",
            "rejected": "tiq-simple",
        }.get(latest_status, "tiq-simple")

        st.markdown(
            f"""
            <div class="{css_class}">
                <strong>Latest Subscription Status:</strong> {latest_status.title()}
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("""
        <div class="tiq-panel">
            <div class="tiq-panel-title">Available Plans</div>
            <div class="tiq-panel-subtitle">Select a subscription plan below.</div>
        </div>
    """, unsafe_allow_html=True)

    p1, p2, p3 = st.columns(3, gap="large")

    with p1:
        st.markdown("""
            <div class="tiq-kpi">
                <div class="tiq-kpi-label">Basic</div>
                <div class="tiq-kpi-value">₦25,000</div>
            </div>
        """, unsafe_allow_html=True)

    with p2:
        st.markdown("""
            <div class="tiq-kpi">
                <div class="tiq-kpi-label">Professional</div>
                <div class="tiq-kpi-value">₦50,000</div>
            </div>
        """, unsafe_allow_html=True)

    with p3:
        st.markdown("""
            <div class="tiq-kpi">
                <div class="tiq-kpi-label">Institutional</div>
                <div class="tiq-kpi-value">₦150,000</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
        <div class="tiq-panel">
            <div class="tiq-panel-title">Submit Payment Evidence</div>
            <div class="tiq-panel-subtitle">Upload your proof of payment for review and approval.</div>
        </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="large")

    with c1:
        st.text_input("Full Name", value=user_name, disabled=True)
        st.text_input("Email Address", value=user_email, disabled=True)
        st.text_input("Institution / Company", value=institution_name, disabled=True)

    with c2:
        st.text_input("Phone Number", value=phone_number, disabled=True)
        selected_plan = st.selectbox("Select Plan", list(SUBSCRIPTION_PLANS.keys()))
        plan_amount = SUBSCRIPTION_PLANS[selected_plan]
        st.text_input("Plan Amount", value=f"₦{plan_amount:,.0f}", disabled=True)

    payment_reference = st.text_input(
        "Payment Reference / Teller Number",
        help="Enter any useful payment reference, teller number, or transaction ID."
    )

    uploaded_evidence = st.file_uploader(
        "Upload Payment Evidence",
        type=["png", "jpg", "jpeg", "pdf"],
        help="Accepted formats: PNG, JPG, JPEG, PDF"
    )

    if st.button("Submit Subscription Request"):
        if not uploaded_evidence:
            st.error("Please upload payment evidence before submitting.")
        else:
            try:
                saved_file = save_payment_evidence(uploaded_evidence, user_email)

                create_subscription_request(
                    user_email=user_email,
                    user_name=user_name,
                    institution_name=institution_name,
                    phone_number=phone_number,
                    plan_name=selected_plan,
                    amount=float(plan_amount),
                    payment_reference=payment_reference.strip(),
                    evidence_file=saved_file,
                )

                st.success("Subscription request submitted successfully. Awaiting admin approval.")
                st.rerun()

            except Exception as e:
                st.error(f"Failed to submit subscription request: {e}")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
        <div class="tiq-panel">
            <div class="tiq-panel-title">My Subscription Requests</div>
            <div class="tiq-panel-subtitle">Track all your submitted subscription requests.</div>
        </div>
    """, unsafe_allow_html=True)

    requests = get_user_subscription_requests(user_email)

    if not requests:
        st.info("You have not submitted any subscription request yet.")
    else:
        df = pd.DataFrame(requests).rename(columns={
            "plan_name": "Plan",
            "amount": "Amount",
            "payment_reference": "Payment Reference",
            "evidence_file": "Evidence File",
            "status": "Status",
            "admin_note": "Admin Note",
            "submitted_at": "Submitted At",
            "approved_at": "Approved At",
        })

        df["Amount"] = df["Amount"].apply(lambda x: f"₦{x:,.0f}")
        df["Evidence File"] = df["Evidence File"].apply(lambda x: os.path.basename(x) if x else "")

        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    if st.button("Back to Dashboard"):
        go_to("pages/1_📊_Dashboard.py")