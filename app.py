import streamlit as st

from utils.helpers import (
    init_session_state,
    apply_global_css,
    go_to,
)

# ---------------------------
# PAGE CONFIG - MUST BE FIRST
# ---------------------------
st.set_page_config(
    page_title="TradeIQ™ | AI-Powered Investment Intelligence for NGX",
    page_icon="📈",
    layout="wide",
)

# ---------------------------
# GLOBAL SETUP
# ---------------------------
init_session_state()
apply_global_css()

# ---------------------------
# PAGE-LEVEL CLEANUP
# ---------------------------
st.markdown("""
<style>
    html, body, .stApp, [data-testid="stAppViewContainer"], section.main {
        overflow-x: hidden !important;
        max-width: 100vw !important;
    }

    .block-container {
        overflow-x: hidden !important;
        max-width: 100% !important;
    }

    div[data-testid="stHorizontalBlock"] {
        max-width: 100% !important;
        overflow-x: hidden !important;
    }

    div[data-testid="column"] {
        min-width: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# LOGO (TOP CENTER)
# ---------------------------
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.image("assets/logo.png", width=280)


# ---------------------------
# MAIN CONTENT ONLY
# ---------------------------
st.markdown("""
    <div class="tiq-hero">
        <div class="tiq-hero-title">Welcome to TradeIQ™</div>
        <div class="tiq-hero-subtitle">See the market clearly. Decide with confidence.</div>
        <div style="color:#486581; font-size:0.98rem; line-height:1.6;">
            TradeIQ helps Nigerian investors and stockbrokers understand NGX stocks through
            analytics, portfolio intelligence, and AI-powered decision support.
        </div>
    </div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3, gap="large")

with c1:
    st.markdown("""
        <div class="tiq-card">
            <div class="tiq-card-title">📈 Market Intelligence</div>
            <div class="tiq-card-text">
                Understand price behavior, volatility, market movement, and relative stock performance.
            </div>
        </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
        <div class="tiq-card">
            <div class="tiq-card-title">⚖️ Portfolio Intelligence</div>
            <div class="tiq-card-text">
                Build and optimize portfolios using risk-adjusted metrics like Sharpe and Sortino ratios.
            </div>
        </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
        <div class="tiq-card">
            <div class="tiq-card-title">🧠 Decision Support</div>
            <div class="tiq-card-text">
                Turn market and portfolio data into clear, actionable insight for better investment decisions.
            </div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("### How TradeIQ works")
step1, step2, step3, step4, step5 = st.columns(5, gap="medium")

with step1:
    st.info("**1. Load Data**\n\nUpload stock prices from CSV or fetch from API.")
with step2:
    st.info("**2. Explore Dashboard**\n\nSee market summaries, leaders, laggards, and key metrics.")
with step3:
    st.info("**3. Analyze Stocks**\n\nInspect individual stock behavior, returns, and volatility.")
with step4:
    st.info("**4. Optimize Portfolio**\n\nGenerate efficient weights using Sharpe or Sortino logic.")
with step5:
    st.info("**5. Monitor Risk**\n\nCheck diversification, concentration, and portfolio vulnerability.")

st.markdown("### Product Modules")

st.markdown("""
    <div class="tiq-module">
        <div class="tiq-module-title">📊 Dashboard</div>
        <div class="tiq-module-text">Your command center for market status, top movers, volatility, and quick intelligence.</div>
    </div>

    <div class="tiq-module">
        <div class="tiq-module-title">📈 Market Overview</div>
        <div class="tiq-module-text">See how your selected NGX basket is performing as a whole across time and risk dimensions.</div>
    </div>

    <div class="tiq-module">
        <div class="tiq-module-title">🔍 Stock Analyzer</div>
        <div class="tiq-module-text">Study one stock deeply with performance, volatility, trend, and stock-level intelligence.</div>
    </div>

    <div class="tiq-module">
        <div class="tiq-module-title">🧠 AI Insights</div>
        <div class="tiq-module-text">Translate raw analytics into plain-English interpretation and decision guidance.</div>
    </div>

    <div class="tiq-module">
        <div class="tiq-module-title">💼 Portfolio Builder</div>
        <div class="tiq-module-text">Create portfolios by style such as low risk, balanced, growth, or dividend-focused.</div>
    </div>

    <div class="tiq-module">
        <div class="tiq-module-title">⚖️ Portfolio Optimizer</div>
        <div class="tiq-module-text">Find efficient allocation weights using optimization metrics and your selected stock universe.</div>
    </div>

    <div class="tiq-module">
        <div class="tiq-module-title">📉 Risk Monitor</div>
        <div class="tiq-module-text">Identify concentration risk, volatility, weak diversification, and downside exposure.</div>
    </div>
""", unsafe_allow_html=True)

st.markdown("### Get Started")

auth1, auth2 = st.columns(2, gap="large")

with auth1:
    if st.button("🔐 Login", key="home_login"):
        go_to("pages/0_🔐_Login_Signup.py")

with auth2:
    if st.button("📝 Create Account", key="home_signup"):
        go_to("pages/0_🔐_Login_Signup.py")