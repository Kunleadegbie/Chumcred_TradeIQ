import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------
# PAGE CONFIG - MUST BE FIRST
# ---------------------------
st.set_page_config(
    page_title="TradeIQ™ | Dashboard",
    page_icon="📊",
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
    get_market_summary,
    normalized_prices,
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
    render_custom_sidebar("Dashboard")

# ---------------------------
# MAIN CONTENT
# ---------------------------
with right_col:
    st.markdown('<div class="tiq-page-title">📊 Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="tiq-page-subtitle">Your command center for NGX investment intelligence.</div>',
        unsafe_allow_html=True
    )

    prices = st.session_state.loaded_prices

    if prices is None or not isinstance(prices, pd.DataFrame) or prices.empty:
        st.info("No market data loaded yet. Please load data in the Portfolio Optimizer page first.")

        action1, action2 = st.columns(2, gap="large")
        with action1:
            if st.button("Open Portfolio Optimizer"):
                go_to("pages/6_⚖️_Portfolio_Optimizer.py")
        with action2:
            if st.button("Back to Home"):
                go_to("app.py")

    else:
        summary = get_market_summary(prices)
        total_returns = summary["total_returns"]
        annualized_vol = summary["annualized_vol"]
        returns = summary["returns"]

        st.session_state.returns_data = returns
        st.session_state.stocks_loaded = prices.shape[1]
        st.session_state.trading_days = prices.shape[0]
        st.session_state.date_range = f"{prices.index.min().date()} to {prices.index.max().date()}"

        # ---------------------------
        # DATA STATUS STRIP
        # ---------------------------
        d1, d2, d3, d4 = st.columns(4, gap="large")

        with d1:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Data Source</div>
                    <div class="tiq-kpi-value">{st.session_state.data_source}</div>
                </div>
            """, unsafe_allow_html=True)

        with d2:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Stocks Loaded</div>
                    <div class="tiq-kpi-value">{prices.shape[1]}</div>
                </div>
            """, unsafe_allow_html=True)

        with d3:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Date Range</div>
                    <div class="tiq-kpi-value">{st.session_state.date_range}</div>
                </div>
            """, unsafe_allow_html=True)

        with d4:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Trading Days</div>
                    <div class="tiq-kpi-value">{prices.shape[0]}</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ---------------------------
        # KPI CARDS
        # ---------------------------
        k1, k2, k3, k4, k5 = st.columns(5, gap="medium")

        with k1:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Best Performer</div>
                    <div class="tiq-kpi-value">{summary["best_stock"]}</div>
                </div>
            """, unsafe_allow_html=True)

        with k2:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Worst Performer</div>
                    <div class="tiq-kpi-value">{summary["worst_stock"]}</div>
                </div>
            """, unsafe_allow_html=True)

        with k3:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Average Return</div>
                    <div class="tiq-kpi-value">{safe_pct(summary["avg_return"])}</div>
                </div>
            """, unsafe_allow_html=True)

        with k4:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Highest Volatility</div>
                    <div class="tiq-kpi-value">{summary["highest_vol_stock"]}</div>
                </div>
            """, unsafe_allow_html=True)

        with k5:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Lowest Volatility</div>
                    <div class="tiq-kpi-value">{summary["lowest_vol_stock"]}</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ---------------------------
        # MARKET SNAPSHOT
        # ---------------------------
        st.markdown("""
            <div class="tiq-panel">
                <div class="tiq-panel-title">Market Snapshot</div>
                <div class="tiq-panel-subtitle">
                    Compare how all loaded stocks have performed over the selected period.
                </div>
            </div>
        """, unsafe_allow_html=True)

        norm_prices = normalized_prices(prices)
        norm_long = norm_prices.reset_index().melt(
            id_vars=norm_prices.index.name or "index",
            var_name="Stock",
            value_name="Normalized Price"
        )
        norm_long.rename(columns={norm_long.columns[0]: "Date"}, inplace=True)

        fig_market = px.line(
            norm_long,
            x="Date",
            y="Normalized Price",
            color="Stock",
            title="Normalized Performance of Loaded Stocks"
        )
        fig_market.update_layout(height=480, legend_title_text="Stocks")
        st.plotly_chart(fig_market, use_container_width=True)

        # ---------------------------
        # TOP MOVERS
        # ---------------------------
        left_table, right_table = st.columns(2, gap="large")

        top_gainers = pd.DataFrame({
            "Stock": total_returns.index[:5],
            "Return %": [f"{x:.2%}" for x in total_returns.values[:5]],
            "Volatility": [f"{annualized_vol[s]:.2%}" for s in total_returns.index[:5]]
        })

        top_laggards = pd.DataFrame({
            "Stock": total_returns.index[-5:][::-1],
            "Return %": [f"{x:.2%}" for x in total_returns.values[-5:][::-1]],
            "Volatility": [f"{annualized_vol[s]:.2%}" for s in total_returns.index[-5:][::-1]]
        })

        with left_table:
            st.markdown("""
                <div class="tiq-panel">
                    <div class="tiq-panel-title">Top Gainers</div>
                    <div class="tiq-panel-subtitle">Highest-return stocks in the loaded basket.</div>
                </div>
            """, unsafe_allow_html=True)
            st.dataframe(top_gainers, use_container_width=True, hide_index=True)

        with right_table:
            st.markdown("""
                <div class="tiq-panel">
                    <div class="tiq-panel-title">Top Laggards</div>
                    <div class="tiq-panel-subtitle">Lowest-return stocks in the loaded basket.</div>
                </div>
            """, unsafe_allow_html=True)
            st.dataframe(top_laggards, use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ---------------------------
        # QUICK INSIGHTS
        # ---------------------------
        i1, i2 = st.columns(2, gap="large")

        with i1:
            st.markdown("""
                <div class="tiq-panel">
                    <div class="tiq-panel-title">Quick Insights</div>
                    <div class="tiq-panel-subtitle">Fast intelligence from the current market basket.</div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div class="tiq-note">
                    <strong>Best Performer:</strong> {summary["best_stock"]} • {safe_pct(total_returns[summary["best_stock"]])}
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div class="tiq-note">
                    <strong>Most Volatile:</strong> {summary["highest_vol_stock"]} • {safe_pct(annualized_vol[summary["highest_vol_stock"]])}
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div class="tiq-note">
                    <strong>Most Stable:</strong> {summary["lowest_vol_stock"]} • {safe_pct(annualized_vol[summary["lowest_vol_stock"]])}
                </div>
            """, unsafe_allow_html=True)

        with i2:
            st.markdown("""
                <div class="tiq-panel">
                    <div class="tiq-panel-title">Diversification Signal</div>
                    <div class="tiq-panel-subtitle">A quick read on co-movement across stocks.</div>
                </div>
            """, unsafe_allow_html=True)

            if isinstance(summary["most_corr_pair"], tuple) and summary["most_corr_pair"][0] != "N/A":
                pair_text = f"{summary['most_corr_pair'][0]} & {summary['most_corr_pair'][1]}"
                corr_text = f"{summary['most_corr_value']:.2f}"
            else:
                pair_text = "N/A"
                corr_text = "N/A"

            st.markdown(f"""
                <div class="tiq-note">
                    <strong>Most Correlated Pair:</strong> {pair_text}
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div class="tiq-note">
                    <strong>Correlation Strength:</strong> {corr_text}
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div class="tiq-note">
                    <strong>Basket Average Return:</strong> {safe_pct(summary["avg_return"])}
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ---------------------------
        # QUICK ACTIONS
        # ---------------------------
        st.markdown("""
            <div class="tiq-panel">
                <div class="tiq-panel-title">Quick Actions</div>
                <div class="tiq-panel-subtitle">Move directly to the next best workflow.</div>
            </div>
        """, unsafe_allow_html=True)

        a1, a2, a3 = st.columns(3, gap="large")

        with a1:
            if st.button("Analyze a Stock"):
                go_to("pages/3_🔍_Stock_Analyzer.py")

        with a2:
            if st.button("Optimize Portfolio"):
                go_to("pages/6_⚖️_Portfolio_Optimizer.py")

        with a3:
            if st.button("Open Risk Monitor"):
                go_to("pages/7_📉_Risk_Monitor.py")