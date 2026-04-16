import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="TradeIQ™ | Super Admin",
    page_icon="🛡️",
    layout="wide",
)

from utils.helpers import (
    init_session_state,
    apply_global_css,
    render_custom_sidebar,
    require_super_admin,
)
from utils.auth import (
    init_auth_db,
    get_all_users,
    create_institution_admin,
)
from utils.subscription import (
    init_subscription_db,
    get_all_subscription_requests,
    approve_subscription_request,
    reject_subscription_request,
)

init_session_state()
apply_global_css()
init_auth_db()
init_subscription_db()
require_super_admin()

left_col, right_col = st.columns([1, 4], gap="large")

with left_col:
    render_custom_sidebar("Super Admin")

with right_col:
    st.markdown('<div class="tiq-page-title">🛡️ Super Admin</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="tiq-page-subtitle">Manage subscription approvals, view users, and create institution admins.</div>',
        unsafe_allow_html=True
    )

    current_user = st.session_state.get("current_user") or {}
    admin_email = current_user.get("email", "")

    tab1, tab2, tab3 = st.tabs([
        "Subscription Requests",
        "All Users",
        "Create Institution Admin"
    ])

    # ---------------------------------------
    # TAB 1 - SUBSCRIPTION REQUESTS
    # ---------------------------------------
    with tab1:
        st.markdown("""
            <div class="tiq-panel">
                <div class="tiq-panel-title">Subscription Approval Workflow</div>
                <div class="tiq-panel-subtitle">Review submitted payment evidence and approve or reject requests.</div>
            </div>
        """, unsafe_allow_html=True)

        status_filter = st.selectbox(
            "Filter Requests",
            ["all", "pending", "approved", "rejected"],
            index=1
        )

        requests = get_all_subscription_requests(status_filter=status_filter)

        c1, c2, c3, c4 = st.columns(4)
        total_requests = len(get_all_subscription_requests(status_filter="all"))
        pending_requests = len(get_all_subscription_requests(status_filter="pending"))
        approved_requests = len(get_all_subscription_requests(status_filter="approved"))
        rejected_requests = len(get_all_subscription_requests(status_filter="rejected"))

        with c1:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Total Requests</div>
                    <div class="tiq-kpi-value">{total_requests}</div>
                </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Pending</div>
                    <div class="tiq-kpi-value">{pending_requests}</div>
                </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Approved</div>
                    <div class="tiq-kpi-value">{approved_requests}</div>
                </div>
            """, unsafe_allow_html=True)

        with c4:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Rejected</div>
                    <div class="tiq-kpi-value">{rejected_requests}</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if not requests:
            st.info("No subscription requests found for the selected filter.")
        else:
            summary_df = pd.DataFrame(requests)[[
                "id", "user_name", "user_email", "institution_name",
                "plan_name", "amount", "status", "submitted_at", "approved_at"
            ]].rename(columns={
                "id": "Request ID",
                "user_name": "User Name",
                "user_email": "Email",
                "institution_name": "Institution",
                "plan_name": "Plan",
                "amount": "Amount",
                "status": "Status",
                "submitted_at": "Submitted At",
                "approved_at": "Actioned At",
            })

            summary_df["Amount"] = summary_df["Amount"].apply(lambda x: f"₦{x:,.0f}")
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

            st.markdown("### Review Individual Requests")

            for req in requests:
                status = req.get("status", "").title()
                exp_title = f"Request #{req['id']} — {req['user_name']} | {req['plan_name']} | {status}"

                with st.expander(exp_title):
                    info1, info2 = st.columns(2)

                    with info1:
                        st.text_input("Full Name", value=req["user_name"], disabled=True, key=f"name_{req['id']}")
                        st.text_input("Email", value=req["user_email"], disabled=True, key=f"email_{req['id']}")
                        st.text_input("Institution", value=req["institution_name"], disabled=True, key=f"institution_{req['id']}")
                        st.text_input("Phone Number", value=req.get("phone_number", ""), disabled=True, key=f"phone_{req['id']}")

                    with info2:
                        st.text_input("Plan", value=req["plan_name"], disabled=True, key=f"plan_{req['id']}")
                        st.text_input("Amount", value=f"₦{req['amount']:,.0f}", disabled=True, key=f"amount_{req['id']}")
                        st.text_input("Payment Reference", value=req.get("payment_reference", "") or "", disabled=True, key=f"ref_{req['id']}")
                        st.text_input("Current Status", value=req["status"].title(), disabled=True, key=f"status_{req['id']}")

                    if req.get("admin_note"):
                        st.text_area(
                            "Existing Admin Note",
                            value=req.get("admin_note", ""),
                            disabled=True,
                            key=f"existing_note_{req['id']}"
                        )

                    evidence_file = req.get("evidence_file")
                    if evidence_file and os.path.exists(evidence_file):
                        filename = os.path.basename(evidence_file)
                        with open(evidence_file, "rb") as f:
                            st.download_button(
                                label=f"Download Evidence: {filename}",
                                data=f.read(),
                                file_name=filename,
                                key=f"download_{req['id']}"
                            )
                    else:
                        st.warning("Evidence file not found on disk.")

                    action_note = st.text_area(
                        "Admin Note",
                        key=f"action_note_{req['id']}",
                        help="Optional note to explain approval or rejection."
                    )

                    if req["status"] == "pending":
                        a1, a2 = st.columns(2)

                        with a1:
                            if st.button("✅ Approve Request", key=f"approve_{req['id']}"):
                                result = approve_subscription_request(
                                    request_id=req["id"],
                                    admin_email=admin_email,
                                    admin_note=action_note
                                )
                                if result["success"]:
                                    st.success(result["message"])
                                    st.rerun()
                                else:
                                    st.error(result["message"])

                        with a2:
                            if st.button("❌ Reject Request", key=f"reject_{req['id']}"):
                                result = reject_subscription_request(
                                    request_id=req["id"],
                                    admin_email=admin_email,
                                    admin_note=action_note
                                )
                                if result["success"]:
                                    st.success(result["message"])
                                    st.rerun()
                                else:
                                    st.error(result["message"])
                    else:
                        st.info("This request has already been actioned.")

    # ---------------------------------------
    # TAB 2 - ALL USERS
    # ---------------------------------------
    with tab2:
        st.markdown("""
            <div class="tiq-panel">
                <div class="tiq-panel-title">User Directory</div>
                <div class="tiq-panel-subtitle">View all registered users across the platform.</div>
            </div>
        """, unsafe_allow_html=True)

        users = get_all_users()

        if not users:
            st.info("No users found.")
        else:
            users_df = pd.DataFrame(users).rename(columns={
                "name": "Name",
                "company_name": "Institution / Company",
                "email": "Email",
                "company_address": "Company Address",
                "phone_number": "Phone Number",
                "role": "Role",
                "is_email_verified": "Email Verified",
                "created_at": "Created At",
            })

            users_df["Email Verified"] = users_df["Email Verified"].apply(lambda x: "Yes" if x else "No")

            preferred_columns = [
                "Name",
                "Email",
                "Institution / Company",
                "Phone Number",
                "Company Address",
                "Role",
                "Email Verified",
                "Created At",
            ]

            users_df = users_df[preferred_columns]
            st.dataframe(users_df, use_container_width=True, hide_index=True)

    # ---------------------------------------
    # TAB 3 - CREATE INSTITUTION ADMIN
    # ---------------------------------------
    with tab3:
        st.markdown("""
            <div class="tiq-panel">
                <div class="tiq-panel-title">Create Institution Admin</div>
                <div class="tiq-panel-subtitle">Create an admin account for a specific institution or company.</div>
            </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2, gap="large")

        with col1:
            admin_name = st.text_input("Full Name", key="inst_admin_name")
            admin_company = st.text_input("Institution / Company Name", key="inst_admin_company")
            admin_email_input = st.text_input("Email Address", key="inst_admin_email")

        with col2:
            admin_address = st.text_area("Company Address", key="inst_admin_address")
            admin_phone = st.text_input("Phone Number", key="inst_admin_phone")
            admin_password = st.text_input("Temporary Password", type="password", key="inst_admin_password")

        if st.button("Create Institution Admin", key="create_inst_admin_btn"):
            if not all([admin_name, admin_company, admin_email_input, admin_address, admin_phone, admin_password]):
                st.error("Please complete all fields.")
            elif len(admin_password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                result = create_institution_admin(
                    name=admin_name,
                    company_name=admin_company,
                    email=admin_email_input,
                    company_address=admin_address,
                    phone_number=admin_phone,
                    password=admin_password,
                )

                if result["success"]:
                    st.success(result["message"])
                else:
                    st.error(result["message"])