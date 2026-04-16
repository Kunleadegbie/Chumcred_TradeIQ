import streamlit as st

from utils.helpers import (
    init_session_state,
    apply_global_css,
    go_to,
    login_user_session,
)
from utils.auth import (
    init_auth_db,
    create_user,
    authenticate_user,
    verify_email_token,
)

st.set_page_config(
    page_title="TradeIQ™ | Login / Signup",
    page_icon="🔐",
    layout="wide",
)

init_session_state()
apply_global_css()
init_auth_db()

# Page-only cleanup: no sidebar layout on auth page
st.markdown("""
<style>
    html, body, .stApp, [data-testid="stAppViewContainer"], section.main {
        overflow-x: hidden !important;
        max-width: 100vw !important;
    }

    .block-container {
        overflow-x: hidden !important;
        max-width: 1100px !important;
        margin: 0 auto !important;
        padding-top: 1.2rem !important;
    }
</style>
""", unsafe_allow_html=True)

# If already logged in, send user to dashboard
if st.session_state.get("is_authenticated", False) and st.session_state.get("current_user"):
    go_to("pages/1_📊_Dashboard.py")

# Email verification from URL
query_params = st.query_params
verify_token = query_params.get("verify_token", None)

if verify_token:
    if isinstance(verify_token, list):
        verify_token = verify_token[0]

    verified = verify_email_token(verify_token)
    if verified:
        st.success("Email verified successfully. You can now log in.")
    else:
        st.error("Invalid or expired verification link.")

# ---------------------------
# SMALL LOGO
# ---------------------------
col1, col2, col3 = st.columns([1, 1, 1])

with col2:
    st.image("assets/logo.png", width=160)

st.markdown('<div class="tiq-page-title">🔐 Login / Signup</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="tiq-page-subtitle">Create an account or log in to access TradeIQ.</div>',
    unsafe_allow_html=True
)

tab1, tab2 = st.tabs(["Login", "Signup"])

with tab1:
    st.markdown("### Login")

    login_email = st.text_input("Email Address", key="login_email")
    login_password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login", key="login_btn"):
        if not login_email or not login_password:
            st.error("Please enter both email and password.")
        else:
            result = authenticate_user(login_email, login_password)

            if result["success"]:
                login_user_session(result["user"])
                st.success("Login successful. Redirecting...")
                go_to("pages/1_📊_Dashboard.py")
            else:
                st.error(result["message"])

with tab2:
    st.markdown("### Signup")

    signup_name = st.text_input("Full Name", key="signup_name")
    signup_company = st.text_input("Company Name / Institution", key="signup_company")
    signup_email = st.text_input("Email Address", key="signup_email")
    signup_address = st.text_area("Company Address", key="signup_address")
    signup_phone = st.text_input("Phone Number", key="signup_phone")
    signup_password = st.text_input("Password", type="password", key="signup_password")
    signup_confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")

    if st.button("Create Account", key="signup_btn"):
        if not all([signup_name, signup_company, signup_email, signup_address, signup_phone, signup_password, signup_confirm_password]):
            st.error("Please complete all fields.")
        elif signup_password != signup_confirm_password:
            st.error("Passwords do not match.")
        elif len(signup_password) < 6:
            st.error("Password must be at least 6 characters.")
        else:
            result = create_user(
                name=signup_name,
                company_name=signup_company,
                email=signup_email,
                company_address=signup_address,
                phone_number=signup_phone,
                password=signup_password
            )

            if result["success"]:
                st.success(result["message"])
            else:
                st.error(result["message"])

st.markdown("---")
if st.button("Back to Home", key="back_home_auth"):
    go_to("app.py")