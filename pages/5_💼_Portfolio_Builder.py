import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------
# PAGE CONFIG - MUST BE FIRST
# ---------------------------
st.set_page_config(
    page_title="TradeIQ™ | Portfolio Builder",
    page_icon="💼",
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


from utils.metrics import (
    compute_returns,
    annualized_returns,
    annualized_volatility,
    total_returns,
)
from utils.risk import normalize_weights


# ---------------------------
# GLOBAL SETUP
# ---------------------------
init_session_state()
apply_global_css()

# ---------------------------
# HELPERS
# ---------------------------
def compute_asset_metrics(prices: pd.DataFrame):
    returns = compute_returns(prices)
    annual_ret = annualized_returns(returns)
    annual_vol = annualized_volatility(returns)
    total_ret = total_returns(prices)

    metrics = pd.DataFrame({
        "Stock": prices.columns,
        "Total Return": total_ret.reindex(prices.columns).values,
        "Annualized Return": annual_ret.reindex(prices.columns).values,
        "Annualized Volatility": annual_vol.reindex(prices.columns).values
    })
    return metrics, returns

def portfolio_metrics(prices: pd.DataFrame, weights: pd.Series):
    returns = compute_returns(prices)
    aligned_weights = weights.reindex(prices.columns).fillna(0)
    portfolio_daily_returns = returns.dot(aligned_weights)

    annual_return = portfolio_daily_returns.mean() * 252
    annual_vol = portfolio_daily_returns.std() * (252 ** 0.5)

    corr = returns.corr()
    if corr.shape[0] > 1:
        corr_no_diag = corr.where(~(corr.index.values[:, None] == corr.columns.values))
        avg_corr = corr_no_diag.stack().mean()
        if pd.isna(avg_corr):
            avg_corr = 0
    else:
        avg_corr = 1

    concentration = float((aligned_weights ** 2).sum())
    diversification_score = int(max(0, min(100, 100 - (concentration * 100) - (max(avg_corr, 0) * 30))))

    return annual_return, annual_vol, diversification_score

def build_style_portfolio(prices: pd.DataFrame, style: str):
    metrics, _ = compute_asset_metrics(prices)

    if style == "Low Risk":
        ranked = metrics.sort_values("Annualized Volatility", ascending=True)
        selected = ranked.head(min(4, len(ranked))).copy()
        raw_weights = 1 / (selected["Annualized Volatility"] + 1e-6)
        weights = raw_weights / raw_weights.sum()
        rationale = "This portfolio prioritizes lower-volatility stocks to reduce sharp price swings and improve stability."

    elif style == "Balanced":
        metrics["Balance Score"] = (
            metrics["Annualized Return"].rank(pct=True) -
            metrics["Annualized Volatility"].rank(pct=True) * 0.6
        )
        selected = metrics.sort_values("Balance Score", ascending=False).head(min(5, len(metrics))).copy()
        raw_weights = selected["Annualized Return"].clip(lower=0) + 0.05
        weights = raw_weights / raw_weights.sum()
        rationale = "This portfolio seeks a middle ground between return potential and risk control."

    elif style == "Growth":
        selected = metrics.sort_values("Annualized Return", ascending=False).head(min(4, len(metrics))).copy()
        raw_weights = selected["Annualized Return"].clip(lower=0) + 0.05
        weights = raw_weights / raw_weights.sum()
        rationale = "This portfolio emphasizes higher-return names and is more suitable for investors comfortable with stronger volatility."

    elif style == "Dividend Focus":
        selected = metrics.sort_values("Annualized Volatility", ascending=True).head(min(3, len(metrics))).copy()

        for candidate in ["GTCO", "ZENITHBANK", "UBA"]:
            if candidate in metrics["Stock"].values and candidate not in selected["Stock"].values:
                selected = pd.concat([selected, metrics[metrics["Stock"] == candidate]]).drop_duplicates("Stock")

        selected = selected.head(min(5, len(selected))).copy()
        raw_weights = 1 / (selected["Annualized Volatility"] + 1e-6)
        weights = raw_weights / raw_weights.sum()
        rationale = "This portfolio leans toward relatively stable, income-oriented names often associated with dividend-seeking strategies."

    else:  # Custom
        selected = metrics.copy()
        weights = pd.Series([1 / len(selected)] * len(selected))
        rationale = "This portfolio starts from an equal-weight base so you can customize it further in the optimizer."

    portfolio = pd.DataFrame({
        "Stock": selected["Stock"].values,
        "Weight": weights.values
    })
    return portfolio, rationale

def style_description(style: str):
    descriptions = {
        "Low Risk": "Designed for investors who prefer steadier holdings and lower portfolio turbulence.",
        "Balanced": "Designed for investors who want a mix of return opportunity and manageable risk.",
        "Growth": "Designed for investors seeking stronger upside potential and willing to accept higher volatility.",
        "Dividend Focus": "Designed for investors who value steadier, income-style holdings and conservative exposure.",
        "Custom": "Designed for investors who want a simple starting point they can refine later."
    }
    return descriptions.get(style, "")

# ---------------------------
# LAYOUT
# ---------------------------
left_col, right_col = st.columns([1, 4], gap="large")

# ---------------------------
# CUSTOM SIDEBAR
# ---------------------------
with left_col:
    render_custom_sidebar("Portfolio Builder")

# ---------------------------
# MAIN CONTENT
# ---------------------------
with right_col:
    st.markdown('<div class="tiq-page-title">💼 Portfolio Builder</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="tiq-page-subtitle">Build an NGX portfolio based on your goal, not just optimization math.</div>',
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
                <div class="tiq-panel-title">Select Portfolio Style</div>
                <div class="tiq-panel-subtitle">Choose the portfolio type that best matches your investment objective.</div>
            </div>
        """, unsafe_allow_html=True)

        style_options = ["Low Risk", "Balanced", "Growth", "Dividend Focus", "Custom"]
        default_style_index = 0
        if st.session_state.selected_portfolio_style in style_options:
            default_style_index = style_options.index(st.session_state.selected_portfolio_style)

        portfolio_style = st.selectbox(
            "Portfolio Style",
            style_options,
            index=default_style_index
        )
        st.session_state.selected_portfolio_style = portfolio_style

        st.markdown(f"""
            <div class="tiq-note">
                <strong>Style Description:</strong><br>
                {style_description(portfolio_style)}
            </div>
        """, unsafe_allow_html=True)

        portfolio_df, rationale = build_style_portfolio(prices, portfolio_style)
        weights = pd.Series(portfolio_df["Weight"].values, index=portfolio_df["Stock"].values)
        weights = normalize_weights(weights)

        st.session_state.builder_weights = weights

        annual_return, annual_volatility, diversification_score = portfolio_metrics(prices[weights.index], weights)

        # Suggested composition
        st.markdown("""
            <div class="tiq-panel">
                <div class="tiq-panel-title">Suggested Portfolio Composition</div>
                <div class="tiq-panel-subtitle">A recommended stock mix based on the selected objective.</div>
            </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns([2, 1], gap="large")

        with c1:
            fig_alloc = px.pie(
                values=weights.values,
                names=weights.index,
                title=f"{portfolio_style} Portfolio Allocation"
            )
            fig_alloc.update_layout(height=420)
            st.plotly_chart(fig_alloc, use_container_width=True)

        with c2:
            display_portfolio = pd.DataFrame({
                "Stock": weights.index,
                "Weight %": [f"{w:.2%}" for w in weights.values]
            }).sort_values("Weight %", ascending=False)
            st.dataframe(display_portfolio, use_container_width=True, hide_index=True)

        # Expected metrics
        st.markdown("""
            <div class="tiq-panel">
                <div class="tiq-panel-title">Expected Portfolio Metrics</div>
                <div class="tiq-panel-subtitle">A quick view of return, risk, and diversification quality for this style.</div>
            </div>
        """, unsafe_allow_html=True)

        m1, m2, m3 = st.columns(3, gap="large")
        with m1:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Expected Annual Return</div>
                    <div class="tiq-kpi-value">{safe_pct(annual_return)}</div>
                </div>
            """, unsafe_allow_html=True)

        with m2:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Expected Volatility</div>
                    <div class="tiq-kpi-value">{safe_pct(annual_volatility)}</div>
                </div>
            """, unsafe_allow_html=True)

        with m3:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Diversification Score</div>
                    <div class="tiq-kpi-value">{diversification_score}/100</div>
                </div>
            """, unsafe_allow_html=True)

        # Why this fits
        st.markdown(f"""
            <div class="tiq-note">
                <strong>Why this portfolio fits the goal:</strong><br>
                {rationale}
            </div>
        """, unsafe_allow_html=True)

        # Underlying stock metrics
        metrics_df, _ = compute_asset_metrics(prices)
        selected_metrics = metrics_df[metrics_df["Stock"].isin(weights.index)].copy()
        selected_metrics["Weight %"] = selected_metrics["Stock"].map(weights).map(lambda x: f"{x:.2%}")
        selected_metrics["Annualized Return"] = selected_metrics["Annualized Return"].map(safe_pct)
        selected_metrics["Annualized Volatility"] = selected_metrics["Annualized Volatility"].map(safe_pct)
        selected_metrics["Total Return"] = selected_metrics["Total Return"].map(safe_pct)

        st.markdown("""
            <div class="tiq-panel">
                <div class="tiq-panel-title">Selected Holdings Snapshot</div>
                <div class="tiq-panel-subtitle">Performance and risk profile of the stocks included in this portfolio style.</div>
            </div>
        """, unsafe_allow_html=True)

        st.dataframe(
            selected_metrics[["Stock", "Weight %", "Total Return", "Annualized Return", "Annualized Volatility"]],
            use_container_width=True,
            hide_index=True
        )

        # Actions
        st.markdown("<br>", unsafe_allow_html=True)
        a1, a2, a3 = st.columns(3, gap="large")

        with a1:
            if st.button("Use in Portfolio Optimizer"):
                st.session_state.optimized_weights = weights
                st.success("This builder portfolio has been saved and can now be reviewed in the Portfolio Optimizer or Risk Monitor.")
        with a2:
            if st.button("Open Risk Monitor"):
                go_to("pages/7_📉_Risk_Monitor.py")
        with a3:
            if st.button("Back to Dashboard"):
                go_to("pages/1_📊_Dashboard.py")