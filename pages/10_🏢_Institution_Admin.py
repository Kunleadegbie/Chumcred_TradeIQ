import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="TradeIQ™ | Institution Admin",
    page_icon="🏢",
    layout="wide",
)

from utils.helpers import (
    init_session_state,
    apply_global_css,
    render_custom_sidebar,
    require_institution_admin,
)
from utils.auth import (
    init_auth_db,
    create_institution_user,
    get_users_by_company,
)

init_session_state()
apply_global_css()
init_auth_db()
require_institution_admin()

current_user = st.session_state.get("current_user") or {}
institution_name = current_user.get("company_name", "")
institution_admin_name = current_user.get("name", "")
institution_admin_email = current_user.get("email", "")

left_col, right_col = st.columns([1, 4], gap="large")

with left_col:
    render_custom_sidebar("Institution Admin")

with right_col:
    st.markdown('<div class="tiq-page-title">🏢 Institution Admin</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="tiq-page-subtitle">Create users for your institution and view only users within your institution.</div>',
        unsafe_allow_html=True
    )

    st.markdown(f"""
        <div class="tiq-note">
            <strong>Institution:</strong> {institution_name}<br>
            <strong>Admin:</strong> {institution_admin_name} ({institution_admin_email})
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Create Institution User", "Institution User List"])

    # ---------------------------------------
    # TAB 1 - CREATE INSTITUTION USER
    # ---------------------------------------
    with tab1:
        st.markdown("""
            <div class="tiq-panel">
                <div class="tiq-panel-title">Create User for This Institution</div>
                <div class="tiq-panel-subtitle">All users created here will automatically belong to your institution.</div>
            </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2, gap="large")

        with col1:
            user_name = st.text_input("Full Name", key="institution_user_name")
            user_email = st.text_input("Email Address", key="institution_user_email")
            user_phone = st.text_input("Phone Number", key="institution_user_phone")

        with col2:
            user_address = st.text_area("Company Address", key="institution_user_address")
            user_password = st.text_input("Temporary Password", type="password", key="institution_user_password")
            st.text_input("Institution / Company Name", value=institution_name, disabled=True, key="institution_user_company")

        if st.button("Create Institution User", key="create_institution_user_btn"):
            if not all([user_name, user_email, user_phone, user_address, user_password]):
                st.error("Please complete all fields.")
            elif len(user_password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                result = create_institution_user(
                    institution_name=institution_name,
                    name=user_name,
                    email=user_email,
                    company_address=user_address,
                    phone_number=user_phone,
                    password=user_password,
                )

                if result["success"]:
                    st.success(result["message"])
                else:
                    st.error(result["message"])

    # ---------------------------------------
    # TAB 2 - INSTITUTION USER LIST
    # ---------------------------------------
    with tab2:
        st.markdown("""
            <div class="tiq-panel">
                <div class="tiq-panel-title">Institution User List</div>
                <div class="tiq-panel-subtitle">View all users registered under your institution only.</div>
            </div>
        """, unsafe_allow_html=True)

        institution_users = get_users_by_company(institution_name)

        if not institution_users:
            st.info("No users found for this institution.")
        else:
            total_users = len(institution_users)
            total_admins = len([u for u in institution_users if u.get("role") == "institution_admin"])
            total_standard_users = len([u for u in institution_users if u.get("role") == "user"])
            total_verified = len([u for u in institution_users if u.get("is_email_verified")])

            k1, k2, k3, k4 = st.columns(4)

            with k1:
                st.markdown(f"""
                    <div class="tiq-kpi">
                        <div class="tiq-kpi-label">Total Institution Users</div>
                        <div class="tiq-kpi-value">{total_users}</div>
                    </div>
                """, unsafe_allow_html=True)

            with k2:
                st.markdown(f"""
                    <div class="tiq-kpi">
                        <div class="tiq-kpi-label">Institution Admins</div>
                        <div class="tiq-kpi-value">{total_admins}</div>
                    </div>
                """, unsafe_allow_html=True)

            with k3:
                st.markdown(f"""
                    <div class="tiq-kpi">
                        <div class="tiq-kpi-label">Standard Users</div>
                        <div class="tiq-kpi-value">{total_standard_users}</div>
                    </div>
                """, unsafe_allow_html=True)

            with k4:
                st.markdown(f"""
                    <div class="tiq-kpi">
                        <div class="tiq-kpi-label">Verified Emails</div>
                        <div class="tiq-kpi-value">{total_verified}</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            users_df = pd.DataFrame(institution_users).rename(columns={
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