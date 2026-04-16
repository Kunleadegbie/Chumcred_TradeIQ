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
    page_title="TradeIQ™ | Market Overview",
    page_icon="📈",
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
    get_summary_tables,
    cumulative_returns,
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
    render_custom_sidebar("Market Overview")

# ---------------------------
# MAIN CONTENT
# ---------------------------
with right_col:
    st.markdown('<div class="tiq-page-title">📈 Market Overview</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="tiq-page-subtitle">Understand how the loaded NGX basket is behaving as a market group.</div>',
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
        returns, summary = get_summary_tables(prices)
        st.session_state.returns_data = returns

        # Summary cards
        s1, s2, s3, s4 = st.columns(4, gap="large")

        with s1:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Best Performer</div>
                    <div class="tiq-kpi-value">{summary.iloc[0]['Stock']}</div>
                </div>
            """, unsafe_allow_html=True)

        with s2:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Worst Performer</div>
                    <div class="tiq-kpi-value">{summary.iloc[-1]['Stock']}</div>
                </div>
            """, unsafe_allow_html=True)

        with s3:
            most_volatile = summary.sort_values("Annualized Volatility", ascending=False).iloc[0]["Stock"]
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Most Volatile</div>
                    <div class="tiq-kpi-value">{most_volatile}</div>
                </div>
            """, unsafe_allow_html=True)

        with s4:
            avg_total_return = summary["Total Return"].mean()
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Average Basket Return</div>
                    <div class="tiq-kpi-value">{safe_pct(avg_total_return)}</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Relative performance chart
        st.markdown("""
            <div class="tiq-panel">
                <div class="tiq-panel-title">Relative Performance</div>
                <div class="tiq-panel-subtitle">Compare cumulative performance across all loaded stocks.</div>
            </div>
        """, unsafe_allow_html=True)

        cum_ret = cumulative_returns(returns)
        cumulative_long = cum_ret.reset_index().melt(
            id_vars=cum_ret.index.name or "index",
            var_name="Stock",
            value_name="Cumulative Return"
        )
        cumulative_long.rename(columns={cumulative_long.columns[0]: "Date"}, inplace=True)

        fig_perf = px.line(
            cumulative_long,
            x="Date",
            y="Cumulative Return",
            color="Stock",
            title="Relative Performance of Loaded Stocks"
        )
        fig_perf.update_layout(height=480, legend_title_text="Stocks")
        st.plotly_chart(fig_perf, use_container_width=True)

        # Rankings
        left_rank, right_rank = st.columns(2, gap="large")

        with left_rank:
            st.markdown("""
                <div class="tiq-panel">
                    <div class="tiq-panel-title">Returns Ranking</div>
                    <div class="tiq-panel-subtitle">Annualized return comparison across the basket.</div>
                </div>
            """, unsafe_allow_html=True)

            returns_rank = summary.sort_values("Annualized Return", ascending=False)
            fig_ret = px.bar(
                returns_rank,
                x="Stock",
                y="Annualized Return",
                color="Annualized Return",
                title="Annualized Return by Stock"
            )
            fig_ret.update_layout(height=420, coloraxis_showscale=False)
            st.plotly_chart(fig_ret, use_container_width=True)

        with right_rank:
            st.markdown("""
                <div class="tiq-panel">
                    <div class="tiq-panel-title">Volatility Ranking</div>
                    <div class="tiq-panel-subtitle">Annualized volatility comparison across the basket.</div>
                </div>
            """, unsafe_allow_html=True)

            vol_rank = summary.sort_values("Annualized Volatility", ascending=False)
            fig_vol = px.bar(
                vol_rank,
                x="Stock",
                y="Annualized Volatility",
                color="Annualized Volatility",
                title="Annualized Volatility by Stock"
            )
            fig_vol.update_layout(height=420, coloraxis_showscale=False)
            st.plotly_chart(fig_vol, use_container_width=True)

        # Correlation heatmap
        st.markdown("""
            <div class="tiq-panel">
                <div class="tiq-panel-title">Correlation Heatmap</div>
                <div class="tiq-panel-subtitle">See which stocks tend to move together based on daily returns.</div>
            </div>
        """, unsafe_allow_html=True)

        corr_matrix = returns.corr()

        fig_corr, ax_corr = plt.subplots(figsize=(10, 6))
        sns.heatmap(corr_matrix, annot=True, cmap="Blues", fmt=".2f", ax=ax_corr)
        ax_corr.set_title("Daily Returns Correlation")
        st.pyplot(fig_corr)

        # Top gainers and laggards tables
        g1, g2 = st.columns(2, gap="large")

        with g1:
            st.markdown("""
                <div class="tiq-panel">
                    <div class="tiq-panel-title">Top Gainers</div>
                    <div class="tiq-panel-subtitle">Strongest performers in the loaded stock basket.</div>
                </div>
            """, unsafe_allow_html=True)

            top_gainers = summary.head(5).copy()
            top_gainers["Total Return"] = top_gainers["Total Return"].map(safe_pct)
            top_gainers["Annualized Volatility"] = top_gainers["Annualized Volatility"].map(safe_pct)
            st.dataframe(
                top_gainers[["Stock", "Total Return", "Annualized Volatility"]],
                use_container_width=True,
                hide_index=True
            )

        with g2:
            st.markdown("""
                <div class="tiq-panel">
                    <div class="tiq-panel-title">Top Laggards</div>
                    <div class="tiq-panel-subtitle">Weakest performers in the loaded stock basket.</div>
                </div>
            """, unsafe_allow_html=True)

            top_laggards = summary.tail(5).sort_values("Total Return", ascending=True).copy()
            top_laggards["Total Return"] = top_laggards["Total Return"].map(safe_pct)
            top_laggards["Annualized Volatility"] = top_laggards["Annualized Volatility"].map(safe_pct)
            st.dataframe(
                top_laggards[["Stock", "Total Return", "Annualized Volatility"]],
                use_container_width=True,
                hide_index=True
            )

        # Market concentration note
        best_stock = summary.iloc[0]["Stock"]
        worst_stock = summary.iloc[-1]["Stock"]
        most_volatile = summary.sort_values("Annualized Volatility", ascending=False).iloc[0]["Stock"]

        st.markdown(f"""
            <div class="tiq-note">
                <strong>Market Intelligence Note:</strong><br>
                The current basket is led by <strong>{best_stock}</strong>, while <strong>{worst_stock}</strong> has lagged the most over the selected period.
                <strong>{most_volatile}</strong> currently shows the highest volatility, which may affect portfolio stability if overweighted.
            </div>
        """, unsafe_allow_html=True)

        # Download overview data
        st.markdown("""
            <div class="tiq-panel">
                <div class="tiq-panel-title">Download Overview Data</div>
                <div class="tiq-panel-subtitle">Export the market overview summary for reporting or further analysis.</div>
            </div>
        """, unsafe_allow_html=True)

        download_df = summary.copy()
        download_df["Total Return"] = download_df["Total Return"].map(safe_pct)
        download_df["Annualized Return"] = download_df["Annualized Return"].map(safe_pct)
        download_df["Annualized Volatility"] = download_df["Annualized Volatility"].map(safe_pct)

        csv = download_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Market Overview CSV",
            data=csv,
            file_name="market_overview_summary.csv",
            mime="text/csv"
        )

        # Quick actions
        st.markdown("<br>", unsafe_allow_html=True)
        a1, a2, a3 = st.columns(3, gap="large")

        with a1:
            if st.button("Open Stock Analyzer"):
                go_to("pages/3_🔍_Stock_Analyzer.py")
        with a2:
            if st.button("Back to Dashboard"):
                go_to("pages/1_📊_Dashboard.py")
        with a3:
            if st.button("Open Risk Monitor"):
                go_to("pages/7_📉_Risk_Monitor.py")