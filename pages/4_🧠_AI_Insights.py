import streamlit as st
import pandas as pd

# ---------------------------
# PAGE CONFIG - MUST BE FIRST
# ---------------------------
st.set_page_config(
    page_title="TradeIQ™ | AI Insights",
    page_icon="🧠",
    layout="wide",
)


from utils.helpers import (
    init_session_state,
    apply_global_css,
    render_custom_sidebar,
    require_auth,
    go_to,
)

# setup
init_session_state()
apply_global_css()
require_auth()

from utils.insights import (
    get_market_insight,
    get_stock_insight,
    get_portfolio_insight,
    get_risk_insight,
)


# ---------------------------
# GLOBAL SETUP
# ---------------------------
init_session_state()
apply_global_css()

# ---------------------------
# LAYOUT
# ---------------------------
left_col, right_col = st.columns([1, 4], gap="large")

# ---------------------------
# CUSTOM SIDEBAR
# ---------------------------
with left_col:
    render_custom_sidebar("AI Insights")

# ---------------------------
# MAIN CONTENT
# ---------------------------
with right_col:
    st.markdown('<div class="tiq-page-title">🧠 AI Insights</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="tiq-page-subtitle">Plain-English interpretation of your market, stock, portfolio, and risk data.</div>',
        unsafe_allow_html=True
    )

    prices = st.session_state.loaded_prices

    if prices is None or not isinstance(prices, pd.DataFrame) or prices.empty:
        st.info("No market data loaded yet. Please load data in the Portfolio Optimizer page first.")

        c1, c2 = st.columns(2, gap="large")
        with c1:
            if st.button("Open Portfolio Optimizer"):
                go_to("pages/6_⚖️_Portfolio_Optimizer.py")
        with c2:
            if st.button("Back to Dashboard"):
                go_to("pages/1_📊_Dashboard.py")

    else:
        st.markdown("""
            <div class="tiq-panel">
                <div class="tiq-panel-title">Insight Type</div>
                <div class="tiq-panel-subtitle">Choose the kind of explanation you want to generate.</div>
            </div>
        """, unsafe_allow_html=True)

        insight_type = st.radio(
            "Select insight type",
            ["Market Insight", "Stock Insight", "Portfolio Insight", "Risk Insight"],
            horizontal=True
        )

        detailed_text = ""
        simple_text = ""

        if insight_type == "Market Insight":
            detailed_text, simple_text = get_market_insight(prices)

        elif insight_type == "Stock Insight":
            stock_options = list(prices.columns)
            default_index = 0
            if st.session_state.selected_stock in stock_options:
                default_index = stock_options.index(st.session_state.selected_stock)

            selected_stock = st.selectbox("Select stock", stock_options, index=default_index)
            st.session_state.selected_stock = selected_stock
            detailed_text, simple_text = get_stock_insight(prices, selected_stock)

        elif insight_type == "Portfolio Insight":
            if isinstance(st.session_state.optimized_weights, pd.Series):
                weights = st.session_state.optimized_weights
                source_label = "optimized portfolio"
            elif isinstance(st.session_state.builder_weights, pd.Series):
                weights = st.session_state.builder_weights
                source_label = "builder portfolio"
            else:
                weights = pd.Series([1 / len(prices.columns)] * len(prices.columns), index=prices.columns)
                source_label = "equal-weight reference portfolio"

            st.markdown(f"""
                <div class="tiq-note">
                    <strong>Portfolio Source:</strong> Using the {source_label}.
                </div>
            """, unsafe_allow_html=True)

            detailed_text, simple_text = get_portfolio_insight(prices, weights)

        else:
            if isinstance(st.session_state.optimized_weights, pd.Series):
                weights = st.session_state.optimized_weights
                source_label = "optimized portfolio"
            elif isinstance(st.session_state.builder_weights, pd.Series):
                weights = st.session_state.builder_weights
                source_label = "builder portfolio"
            else:
                weights = pd.Series([1 / len(prices.columns)] * len(prices.columns), index=prices.columns)
                source_label = "equal-weight reference portfolio"

            st.markdown(f"""
                <div class="tiq-note">
                    <strong>Risk Source:</strong> Using the {source_label}.
                </div>
            """, unsafe_allow_html=True)

            detailed_text, simple_text = get_risk_insight(prices, weights)

        # AI Interpretation
        st.markdown("""
            <div class="tiq-panel">
                <div class="tiq-panel-title">AI Interpretation</div>
                <div class="tiq-panel-subtitle">A structured explanation of the selected insight type.</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="tiq-note">
                {detailed_text}
            </div>
        """, unsafe_allow_html=True)

        # Beginner Explanation
        st.markdown("""
            <div class="tiq-panel">
                <div class="tiq-panel-title">Beginner Explanation</div>
                <div class="tiq-panel-subtitle">A simpler interpretation for non-technical users.</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="tiq-simple">
                {simple_text}
            </div>
        """, unsafe_allow_html=True)

        # Disclaimer
        st.markdown("""
            <div class="tiq-warning">
                <strong>Important Note:</strong><br>
                These insights are analytical interpretations based on loaded data. They are decision-support guidance, not guaranteed investment advice or trading instructions.
            </div>
        """, unsafe_allow_html=True)

        # Quick actions
        a1, a2, a3 = st.columns(3, gap="large")

        with a1:
            if st.button("Back to Dashboard"):
                go_to("pages/1_📊_Dashboard.py")

        with a2:
            if st.button("Open Stock Analyzer"):
                go_to("pages/3_🔍_Stock_Analyzer.py")

        with a3:
            if st.button("Open Risk Monitor"):
                go_to("pages/7_📉_Risk_Monitor.py")