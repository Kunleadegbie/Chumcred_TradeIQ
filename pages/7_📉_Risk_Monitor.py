import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np


# ---------------------------
# PAGE CONFIG - MUST BE FIRST
# ---------------------------
st.set_page_config(
    page_title="TradeIQ™ | Risk Monitor",
    page_icon="📉",
    layout="wide",
)


from utils.helpers import (
    init_session_state,
    apply_global_css,
    render_custom_sidebar,
    require_auth,
    go_to,
    safe_pct,
)

# setup
init_session_state()
apply_global_css()
require_auth()


from utils.risk import (
    normalize_weights,
    build_equal_weights,
    portfolio_risk_summary,
    get_risk_commentary,
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
    render_custom_sidebar("Risk Monitor")

# ---------------------------
# MAIN CONTENT
# ---------------------------
with right_col:
    st.markdown('<div class="tiq-page-title">📉 Risk Monitor</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="tiq-page-subtitle">Understand where your portfolio is vulnerable and how well it is diversified.</div>',
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
                <div class="tiq-panel-title">Portfolio Input Source</div>
                <div class="tiq-panel-subtitle">Choose which weights to evaluate for portfolio risk.</div>
            </div>
        """, unsafe_allow_html=True)

        source_mode = st.radio(
            "Select portfolio source",
            ["Use Optimized Portfolio", "Use Equal Weight Portfolio", "Use Custom Weights"],
            horizontal=True
        )

        weights = None

        if source_mode == "Use Optimized Portfolio":
            if isinstance(st.session_state.optimized_weights, pd.Series):
                weights = normalize_weights(
                    st.session_state.optimized_weights.reindex(prices.columns).fillna(0)
                )
                st.success("Using optimized portfolio weights from the Portfolio Optimizer page.")
            else:
                st.warning("No optimized portfolio found. Falling back to equal weights.")
                weights = build_equal_weights(prices.columns)

        elif source_mode == "Use Equal Weight Portfolio":
            weights = build_equal_weights(prices.columns)

        else:
            st.markdown("""
                <div class="tiq-panel">
                    <div class="tiq-panel-title">Custom Weight Entry</div>
                    <div class="tiq-panel-subtitle">Enter weights manually. They will be normalized automatically if they do not sum to 1.</div>
                </div>
            """, unsafe_allow_html=True)

            custom_weights = {}
            cols = st.columns(3, gap="large")
            for i, stock in enumerate(prices.columns):
                with cols[i % 3]:
                    custom_weights[stock] = st.number_input(
                        f"{stock}",
                        min_value=0.0,
                        value=float(1 / len(prices.columns)),
                        step=0.01,
                        format="%.4f"
                    )

            weights = pd.Series(custom_weights)
            if weights.sum() > 0:
                weights = normalize_weights(weights)

        risk_metrics = portfolio_risk_summary(prices, weights)

        # ---------------------------
        # RISK KPI CARDS
        # ---------------------------
        k1, k2, k3, k4, k5 = st.columns(5, gap="medium")

        with k1:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Portfolio Volatility</div>
                    <div class="tiq-kpi-value">{safe_pct(risk_metrics["annualized_volatility"])}</div>
                </div>
            """, unsafe_allow_html=True)

        with k2:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Max Drawdown</div>
                    <div class="tiq-kpi-value">{safe_pct(risk_metrics["max_drawdown"])}</div>
                </div>
            """, unsafe_allow_html=True)

        with k3:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">VaR (95%)</div>
                    <div class="tiq-kpi-value">{safe_pct(risk_metrics["var_95"])}</div>
                </div>
            """, unsafe_allow_html=True)

        with k4:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Diversification Score</div>
                    <div class="tiq-kpi-value">{risk_metrics["diversification_score"]}/100</div>
                </div>
            """, unsafe_allow_html=True)

        with k5:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Concentration Score</div>
                    <div class="tiq-kpi-value">{risk_metrics["concentration_score"]}/100</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ---------------------------
        # CONCENTRATION ANALYSIS
        # ---------------------------
        st.markdown("""
            <div class="tiq-panel">
                <div class="tiq-panel-title">Concentration Analysis</div>
                <div class="tiq-panel-subtitle">See how portfolio weight is distributed across holdings.</div>
            </div>
        """, unsafe_allow_html=True)

        weight_df = pd.DataFrame({
            "Stock": weights.index,
            "Weight": weights.values
        }).sort_values("Weight", ascending=False)

        fig_weights = px.bar(
            weight_df,
            x="Stock",
            y="Weight",
            color="Weight",
            title="Portfolio Weight by Stock"
        )
        fig_weights.update_layout(height=420, yaxis_tickformat=".0%")
        st.plotly_chart(fig_weights, use_container_width=True)

        # ---------------------------
        # CORRELATION STRUCTURE
        # ---------------------------
        st.markdown("""
            <div class="tiq-panel">
                <div class="tiq-panel-title">Correlation Structure</div>
                <div class="tiq-panel-subtitle">High correlation reduces diversification benefits even when many stocks are included.</div>
            </div>
        """, unsafe_allow_html=True)

        fig_corr, ax_corr = plt.subplots(figsize=(10, 6))
        sns.heatmap(risk_metrics["corr_matrix"], annot=True, cmap="Oranges", fmt=".2f", ax=ax_corr)
        ax_corr.set_title("Daily Returns Correlation")
        st.pyplot(fig_corr)

        corr_matrix = risk_metrics["corr_matrix"]
        if corr_matrix.shape[0] > 1:
            corr_no_diag = corr_matrix.where(~np.eye(corr_matrix.shape[0], dtype=bool))
            avg_corr = corr_no_diag.stack().mean()
        else:
            avg_corr = 1.0

        if avg_corr > 0.70:
            st.markdown("""
                <div class="tiq-warning">
                    <strong>Correlation Warning:</strong><br>
                    Several holdings are moving very similarly. This reduces the real diversification benefit of the portfolio.
                </div>
            """, unsafe_allow_html=True)
        elif avg_corr > 0.40:
            st.markdown("""
                <div class="tiq-note">
                    <strong>Correlation Note:</strong><br>
                    Correlation is moderate. The portfolio has some diversification, but common market movement is still meaningful.
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="tiq-note">
                    <strong>Diversification Note:</strong><br>
                    Correlation is relatively contained, which improves diversification potential.
                </div>
            """, unsafe_allow_html=True)

        # ---------------------------
        # PORTFOLIO RETURN PROFILE
        # ---------------------------
        st.markdown("""
            <div class="tiq-panel">
                <div class="tiq-panel-title">Portfolio Return Profile</div>
                <div class="tiq-panel-subtitle">Inspect the daily return distribution of the selected portfolio weights.</div>
            </div>
        """, unsafe_allow_html=True)

        fig_ret, ax_ret = plt.subplots(figsize=(10, 4.5))
        sns.histplot(risk_metrics["portfolio_daily_returns"], kde=True, ax=ax_ret, bins=35)
        ax_ret.set_title("Portfolio Daily Returns Distribution")
        st.pyplot(fig_ret)

        # ---------------------------
        # RISK EXPOSURE SUMMARY
        # ---------------------------
        st.markdown("""
            <div class="tiq-panel">
                <div class="tiq-panel-title">Risk Exposure Summary</div>
                <div class="tiq-panel-subtitle">A plain-language view of key vulnerabilities in the current portfolio.</div>
            </div>
        """, unsafe_allow_html=True)

        comments = get_risk_commentary(weights, risk_metrics)
        comment_html = "<br>".join([f"• {c}" for c in comments])

        st.markdown(f"""
            <div class="tiq-note">
                <strong>Portfolio Risk Commentary:</strong><br>
                {comment_html}
            </div>
        """, unsafe_allow_html=True)

        max_weight_stock = weights.idxmax()
        max_weight_value = weights.max()

        st.markdown(f"""
            <div class="tiq-warning">
                <strong>Stress Note:</strong><br>
                If <strong>{max_weight_stock}</strong>, the largest holding at <strong>{max_weight_value:.2%}</strong>, experiences a sharp adverse move,
                total portfolio losses could be amplified due to concentration. This matters more if the stock is also highly volatile or highly correlated with other holdings.
            </div>
        """, unsafe_allow_html=True)

        # ---------------------------
        # WEIGHT TABLE
        # ---------------------------
        st.markdown("""
            <div class="tiq-panel">
                <div class="tiq-panel-title">Weight Table</div>
                <div class="tiq-panel-subtitle">Current portfolio weights used for risk analysis.</div>
            </div>
        """, unsafe_allow_html=True)

        display_weights = weight_df.copy()
        display_weights["Weight"] = display_weights["Weight"].map(lambda x: f"{x:.2%}")
        st.dataframe(display_weights, use_container_width=True, hide_index=True)

        # ---------------------------
        # QUICK ACTIONS
        # ---------------------------
        st.markdown("<br>", unsafe_allow_html=True)
        a1, a2, a3 = st.columns(3, gap="large")

        with a1:
            if st.button("Back to Dashboard"):
                go_to("pages/1_📊_Dashboard.py")

        with a2:
            if st.button("Open Portfolio Optimizer"):
                go_to("pages/6_⚖️_Portfolio_Optimizer.py")

        with a3:
            if st.button("Open Portfolio Builder"):
                go_to("pages/5_💼_Portfolio_Builder.py")