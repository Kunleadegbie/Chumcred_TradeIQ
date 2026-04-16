import streamlit as st

DEFAULTS = {
    "loaded_prices": None,
    "returns_data": None,
    "selected_stock": None,
    "selected_portfolio_style": None,
    "optimized_weights": None,
    "builder_weights": None,
    "data_source": "Not loaded",
    "date_range": "Not selected",
    "risk_free_rate": 0.0,
    "stocks_loaded": 0,
    "trading_days": 0,
    "is_authenticated": False,
    "current_user": None,
}

GLOBAL_CSS = """
<style>
    html, body, .stApp {
        background: #ffffff !important;
        overflow-x: hidden !important;
        max-width: 100vw !important;
    }

    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewBlockContainer"],
    section.main,
    .main,
    .block-container,
    div[data-testid="stHorizontalBlock"],
    div[data-testid="column"],
    .element-container {
        max-width: 100% !important;
        box-sizing: border-box !important;
        overflow-x: hidden !important;
    }

    [data-testid="stSidebar"] {display: none !important;}
    [data-testid="stSidebarNav"] {display: none !important;}
    [data-testid="collapsedControl"] {display: none !important;}
    [data-testid="stSidebarCollapsedControl"] {display: none !important;}
    section[data-testid="stSidebarCollapsedControl"] {display: none !important;}
    div[data-testid="stSidebarCollapsedControl"] {display: none !important;}

    button[aria-label="Open sidebar"] {display: none !important;}
    button[aria-label="Close sidebar"] {display: none !important;}
    button[aria-label="View sidebar"] {display: none !important;}
    button[title="View sidebar"] {display: none !important;}
    button[title="Open sidebar"] {display: none !important;}
    button[kind="header"] {display: none !important;}
    button[data-testid="baseButton-headerNoPadding"] {display: none !important;}

    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    [data-testid="stHeader"] {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}
    [data-testid="stStatusWidget"] {display: none !important;}

    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        max-width: 100% !important;
        width: 100% !important;
    }

    div[data-testid="column"] {
        min-width: 0 !important;
    }

    .tiq-brand-card {
        background: linear-gradient(180deg, #0b1f3a 0%, #102b52 100%);
        color: white;
        border-radius: 18px;
        padding: 1.1rem 1rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.10);
    }

    .tiq-brand {
        font-size: 1.55rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
        color: #ffffff;
        line-height: 1.1;
        word-break: break-word;
    }

    .tiq-tagline {
        font-size: 0.9rem;
        color: #dbe7ff;
        line-height: 1.45;
        word-break: break-word;
    }

    .tiq-side-card {
        background: #ffffff;
        border: 1px solid #e6edf7;
        border-radius: 16px;
        padding: 0.9rem 0.95rem;
        margin-top: 0.8rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 8px 20px rgba(16,43,82,0.05);
    }

    .tiq-side-title {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #6a7f9c;
        margin-bottom: 0.55rem;
        font-weight: 700;
    }

    .tiq-status-box {
        background: #f7fbff;
        border: 1px solid #e1ebf8;
        border-radius: 12px;
        padding: 0.75rem 0.8rem;
        margin-top: 0.45rem;
        margin-bottom: 0.55rem;
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        overflow-x: hidden !important;
    }

    .tiq-status-row {
        margin-bottom: 0.6rem;
    }

    .tiq-status-row:last-child {
        margin-bottom: 0;
    }

    .tiq-status-label {
        font-size: 0.76rem;
        color: #6a7f9c;
        margin-bottom: 0.08rem;
    }

    .tiq-status-value {
        font-size: 0.92rem;
        font-weight: 700;
        color: #0b1f3a;
        word-break: break-word;
        line-height: 1.35;
    }

    .tiq-help-text {
        font-size: 0.84rem;
        color: #4d6788;
        line-height: 1.5;
    }

    .tiq-page-title {
        font-size: 2rem;
        font-weight: 800;
        color: #0b1f3a;
        margin-bottom: 0.25rem;
        word-break: break-word;
    }

    .tiq-page-subtitle {
        font-size: 1rem;
        color: #4d6788;
        margin-bottom: 1rem;
        word-break: break-word;
    }

    .tiq-hero,
    .tiq-panel,
    .tiq-card,
    .tiq-module,
    .tiq-kpi,
    .tiq-note,
    .tiq-warning,
    .tiq-simple {
        max-width: 100% !important;
        box-sizing: border-box !important;
        overflow-x: hidden !important;
    }

    .tiq-hero {
        background: linear-gradient(135deg, #f8fbff 0%, #eef5ff 100%);
        border: 1px solid #dde9ff;
        border-radius: 22px;
        padding: 2rem 2rem 1.5rem 2rem;
        margin-bottom: 1.15rem;
    }

    .tiq-hero-title {
        font-size: 2rem;
        font-weight: 800;
        color: #0b1f3a;
        margin-bottom: 0.35rem;
        word-break: break-word;
    }

    .tiq-hero-subtitle {
        font-size: 1.05rem;
        color: #31507a;
        margin-bottom: 0.8rem;
        word-break: break-word;
    }

    .tiq-panel {
        background: #ffffff;
        border: 1px solid #e6edf7;
        border-radius: 18px;
        padding: 1rem;
        box-shadow: 0 8px 20px rgba(16,43,82,0.05);
        margin-bottom: 1rem;
    }

    .tiq-panel-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #0b1f3a;
        margin-bottom: 0.25rem;
        word-break: break-word;
    }

    .tiq-panel-subtitle {
        font-size: 0.9rem;
        color: #617996;
        margin-bottom: 0.8rem;
        word-break: break-word;
    }

    .tiq-card {
        background: #ffffff;
        border: 1px solid #e6edf7;
        border-radius: 18px;
        padding: 1.15rem;
        box-shadow: 0 8px 20px rgba(16,43,82,0.05);
        height: 100%;
    }

    .tiq-card-title {
        font-size: 1rem;
        font-weight: 700;
        color: #0b1f3a;
        margin-bottom: 0.35rem;
        word-break: break-word;
    }

    .tiq-card-text {
        font-size: 0.92rem;
        color: #4a6487;
        line-height: 1.45;
        word-break: break-word;
    }

    .tiq-module {
        background: #ffffff;
        border: 1px solid #e6edf7;
        border-radius: 16px;
        padding: 0.95rem 1rem;
        margin-bottom: 0.7rem;
    }

    .tiq-module-title {
        font-size: 0.98rem;
        font-weight: 700;
        color: #0b1f3a;
        margin-bottom: 0.15rem;
        word-break: break-word;
    }

    .tiq-module-text {
        font-size: 0.88rem;
        color: #57708f;
        word-break: break-word;
    }

    .tiq-kpi {
        background: #ffffff;
        border: 1px solid #e6edf7;
        border-radius: 18px;
        padding: 1rem 1rem 0.9rem 1rem;
        box-shadow: 0 8px 20px rgba(16,43,82,0.05);
    }

    .tiq-kpi-label {
        font-size: 0.82rem;
        color: #6a7f9c;
        margin-bottom: 0.3rem;
        word-break: break-word;
    }

    .tiq-kpi-value {
        font-size: 1.15rem;
        font-weight: 800;
        color: #0b1f3a;
        word-break: break-word;
    }

    .tiq-note {
        background: #eef5ff;
        border: 1px solid #dbe8ff;
        border-radius: 16px;
        padding: 0.95rem 1rem;
        color: #29496f;
        margin-bottom: 1rem;
        line-height: 1.5;
    }

    .tiq-warning {
        background: #fff4eb;
        border: 1px solid #ffd9b8;
        border-radius: 16px;
        padding: 0.95rem 1rem;
        color: #8a4b08;
        margin-bottom: 1rem;
        line-height: 1.5;
    }

    .tiq-simple {
        background: #f7fafc;
        border: 1px solid #e5edf7;
        border-radius: 16px;
        padding: 0.95rem 1rem;
        color: #35506f;
        margin-bottom: 1rem;
        line-height: 1.5;
    }

    div.stButton > button {
        width: 100%;
        max-width: 100% !important;
        border-radius: 12px;
        font-weight: 700;
        border: 1px solid #d8e4f6;
        background: white;
        color: #0b1f3a;
        padding: 0.58rem 0.8rem;
        box-sizing: border-box !important;
    }

    div.stButton > button:hover {
        border-color: #5a8dee;
        color: #0b1f3a;
    }
</style>
"""


def init_session_state():
    for key, value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def apply_global_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def go_to(page_path: str):
    st.switch_page(page_path)


def safe_pct(x):
    try:
        return f"{x:.2%}"
    except Exception:
        return "N/A"


def safe_num(x):
    try:
        return f"{x:.2f}"
    except Exception:
        return "N/A"


def reset_optimizer_state():
    st.session_state.loaded_prices = None
    st.session_state.returns_data = None
    st.session_state.optimized_weights = None
    st.session_state.builder_weights = None
    st.session_state.data_source = "Not loaded"
    st.session_state.date_range = "Not selected"
    st.session_state.stocks_loaded = 0
    st.session_state.trading_days = 0


def login_user_session(user: dict):
    st.session_state.is_authenticated = True
    st.session_state.current_user = user


def logout_user_session():
    st.session_state.is_authenticated = False
    st.session_state.current_user = None


def require_auth():
    if not st.session_state.get("is_authenticated", False):
        st.warning("Please log in to access this page.")
        st.stop()


def require_super_admin():
    require_auth()
    current_user = st.session_state.get("current_user") or {}
    if current_user.get("role") != "super_admin":
        st.error("Access denied. Super admin only.")
        st.stop()


def require_institution_admin():
    require_auth()
    current_user = st.session_state.get("current_user") or {}
    if current_user.get("role") != "institution_admin":
        st.error("Access denied. Institution admin only.")
        st.stop()


def render_custom_sidebar(current_page: str):
    st.markdown(
        '''
        <div class="tiq-brand-card">
            <div class="tiq-brand">TradeIQ™</div>
            <div class="tiq-tagline">AI-Powered Investment Intelligence for NGX</div>
        </div>
        ''',
        unsafe_allow_html=True
    )

    current_user = st.session_state.get("current_user") or {}
    user_role = current_user.get("role", "")

    if st.session_state.get("is_authenticated", False) and current_user:
        st.markdown(
            f'''
            <div class="tiq-side-card">
                <div class="tiq-side-title">User</div>
                <div class="tiq-status-box">
                    <div class="tiq-status-row">
                        <div class="tiq-status-label">Name</div>
                        <div class="tiq-status-value">{current_user.get("name", "")}</div>
                    </div>
                    <div class="tiq-status-row">
                        <div class="tiq-status-label">Email</div>
                        <div class="tiq-status-value">{current_user.get("email", "")}</div>
                    </div>
                    <div class="tiq-status-row">
                        <div class="tiq-status-label">Role</div>
                        <div class="tiq-status-value">{current_user.get("role", "")}</div>
                    </div>
                </div>
            </div>
            ''',
            unsafe_allow_html=True
        )

        if st.button("🚪 Logout", key="logout_btn"):
            logout_user_session()
            go_to("app.py")

    st.markdown('<div class="tiq-side-card"><div class="tiq-side-title">Navigation</div></div>', unsafe_allow_html=True)

    nav_items = [
        ("📊 Dashboard", "Dashboard", "pages/1_📊_Dashboard.py"),
        ("⚖️ Portfolio Optimizer", "Portfolio Optimizer", "pages/6_⚖️_Portfolio_Optimizer.py"),
        ("📈 Market Overview", "Market Overview", "pages/2_📈_Market_Overview.py"),
        ("🔍 Stock Analyzer", "Stock Analyzer", "pages/3_🔍_Stock_Analyzer.py"),
        ("🧠 AI Insights", "AI Insights", "pages/4_🧠_AI_Insights.py"),
        ("💼 Portfolio Builder", "Portfolio Builder", "pages/5_💼_Portfolio_Builder.py"),
        ("📉 Risk Monitor", "Risk Monitor", "pages/7_📉_Risk_Monitor.py"),        
    ]

    if user_role == "super_admin":
        nav_items.append(("💳 Subscription", "Subscription", "pages/8_💳_Subscription.py"))
        nav_items.append(("🛡️ Super Admin", "Super Admin", "pages/9_🛡️_Super_Admin.py"))
       

    if user_role == "institution_admin":
        nav_items.append(("🏢 Institution Admin", "Institution Admin", "pages/10_🏢_Institution_Admin.py"))

    for label, page_name, path in nav_items:
        if st.button(label, key=f"nav_{page_name}"):
            if page_name == current_page:
                st.rerun()
            else:
                go_to(path)

    st.markdown('<div class="tiq-side-card"><div class="tiq-side-title">Current Page</div></div>', unsafe_allow_html=True)
    st.markdown(
        f'''
        <div class="tiq-status-box">
            <div class="tiq-status-row">
                <div class="tiq-status-label">Module</div>
                <div class="tiq-status-value">{current_page}</div>
            </div>
        </div>
        ''',
        unsafe_allow_html=True
    )

    st.markdown('<div class="tiq-side-card"><div class="tiq-side-title">Data Status</div></div>', unsafe_allow_html=True)
    st.markdown(
        f'''
        <div class="tiq-status-box">
            <div class="tiq-status-row">
                <div class="tiq-status-label">Source</div>
                <div class="tiq-status-value">{st.session_state.data_source}</div>
            </div>
            <div class="tiq-status-row">
                <div class="tiq-status-label">Stocks Loaded</div>
                <div class="tiq-status-value">{st.session_state.stocks_loaded}</div>
            </div>
            <div class="tiq-status-row">
                <div class="tiq-status-label">Period</div>
                <div class="tiq-status-value">{st.session_state.date_range}</div>
            </div>
            <div class="tiq-status-row">
                <div class="tiq-status-label">Trading Days</div>
                <div class="tiq-status-value">{st.session_state.trading_days}</div>
            </div>
        </div>
        ''',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="tiq-side-card"><div class="tiq-side-title">Quick Help</div><div class="tiq-help-text">Navigate across modules to analyze stocks, build portfolios, optimize allocations, and monitor risk.</div></div>',
        unsafe_allow_html=True
    )