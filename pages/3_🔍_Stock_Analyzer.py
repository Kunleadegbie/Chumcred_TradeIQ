import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------------
# PAGE CONFIG - MUST BE FIRST
# ---------------------------
st.set_page_config(
    page_title="TradeIQ™ | Stock Analyzer",
    page_icon="🔍",
    layout="wide",
)


from utils.helpers import (
    init_session_state,
    apply_global_css,
    render_custom_sidebar,
    require_auth,
    go_to,
    safe_pct,
    safe_num,
)

# setup
init_session_state()
apply_global_css()
require_auth()


from utils.metrics import (
    calculate_max_drawdown,
    get_risk_label,
    get_trend_label,
    get_stock_score,
)


# ---------------------------
# GLOBAL SETUP
# ---------------------------
init_session_state()
apply_global_css()

# ---------------------------
# HELPERS
# ---------------------------
def get_stock_summary(stock, total_return, annual_return, annual_volatility, max_drawdown, trend_label):
    risk_label = get_risk_label(annual_volatility)

    if trend_label in ["Strong Uptrend", "Mild Uptrend"] and risk_label == "Low":
        tone = "shows relatively stable strength"
    elif trend_label in ["Strong Uptrend", "Mild Uptrend"] and risk_label == "Medium":
        tone = "shows growth momentum with moderate risk"
    elif trend_label == "Downtrend":
        tone = "is currently under pressure and may require caution"
    else:
        tone = "shows mixed behavior with no strong directional edge"

    return (
        f"{stock} {tone}. "
        f"It has delivered a total return of {safe_pct(total_return)} over the selected period, "
        f"with annualized volatility of {safe_pct(annual_volatility)} and a maximum drawdown of {safe_pct(max_drawdown)}. "
        f"This makes it more suitable for {risk_label.lower()}-to-medium risk investors depending on portfolio context."
    )

# ---------------------------
# LAYOUT
# ---------------------------
left_col, right_col = st.columns([1, 4], gap="large")

# ---------------------------
# CUSTOM SIDEBAR
# ---------------------------
with left_col:
    render_custom_sidebar("Stock Analyzer")

# ---------------------------
# MAIN CONTENT
# ---------------------------
with right_col:
    st.markdown('<div class="tiq-page-title">🔍 Stock Analyzer</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="tiq-page-subtitle">Evaluate one NGX stock with clarity using performance, risk, and trend intelligence.</div>',
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
        selector_col1, selector_col2 = st.columns([2, 1], gap="large")

        with selector_col1:
            stock_options = list(prices.columns)
            default_index = 0
            if st.session_state.selected_stock in stock_options:
                default_index = stock_options.index(st.session_state.selected_stock)

            selected_stock = st.selectbox(
                "Select a stock",
                stock_options,
                index=default_index
            )
            st.session_state.selected_stock = selected_stock

        with selector_col2:
            latest_price = prices[selected_stock].iloc[-1]
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Latest Price</div>
                    <div class="tiq-kpi-value">{safe_num(latest_price)}</div>
                </div>
            """, unsafe_allow_html=True)

        stock_prices = prices[selected_stock].dropna()
        stock_returns = stock_prices.pct_change().dropna()

        total_return = (stock_prices.iloc[-1] / stock_prices.iloc[0]) - 1
        annual_return = stock_returns.mean() * 252
        annual_volatility = stock_returns.std() * (252 ** 0.5)
        max_drawdown = calculate_max_drawdown(stock_prices)
        risk_label = get_risk_label(annual_volatility)
        trend_label = get_trend_label(stock_prices)
        stock_score = get_stock_score(total_return, annual_volatility, max_drawdown)

        basket_returns = prices.pct_change().dropna()
        basket_avg_return = ((prices.iloc[-1] / prices.iloc[0]) - 1).mean()
        basket_avg_vol = (basket_returns.std() * (252 ** 0.5)).mean()

        # Historical Price Chart
        st.markdown("""
            <div class="tiq-panel">
                <div class="tiq-panel-title">Historical Price Chart</div>
                <div class="tiq-panel-subtitle">Price behavior of the selected stock over the loaded period.</div>
            </div>
        """, unsafe_allow_html=True)

        price_df = stock_prices.reset_index()
        price_df.columns = ["Date", "Price"]
        fig_price = px.line(price_df, x="Date", y="Price", title=f"{selected_stock} Price Trend")
        fig_price.update_layout(height=430)
        st.plotly_chart(fig_price, use_container_width=True)

        # Daily Returns Distribution
        st.markdown("""
            <div class="tiq-panel">
                <div class="tiq-panel-title">Daily Returns Distribution</div>
                <div class="tiq-panel-subtitle">See how the stock's day-to-day return behavior is distributed.</div>
            </div>
        """, unsafe_allow_html=True)

        fig_ret, ax_ret = plt.subplots(figsize=(10, 4.5))
        sns.histplot(stock_returns, kde=True, ax=ax_ret, bins=35)
        ax_ret.set_title(f"{selected_stock} Daily Returns Distribution")
        st.pyplot(fig_ret)

        # Metrics cards
        m1, m2, m3, m4, m5 = st.columns(5, gap="medium")

        with m1:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Total Return</div>
                    <div class="tiq-kpi-value">{safe_pct(total_return)}</div>
                </div>
            """, unsafe_allow_html=True)

        with m2:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Annualized Return</div>
                    <div class="tiq-kpi-value">{safe_pct(annual_return)}</div>
                </div>
            """, unsafe_allow_html=True)

        with m3:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Volatility</div>
                    <div class="tiq-kpi-value">{safe_pct(annual_volatility)}</div>
                </div>
            """, unsafe_allow_html=True)

        with m4:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Max Drawdown</div>
                    <div class="tiq-kpi-value">{safe_pct(max_drawdown)}</div>
                </div>
            """, unsafe_allow_html=True)

        with m5:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Stock Score</div>
                    <div class="tiq-kpi-value">{stock_score}/100</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Trend Indicators
        st.markdown("""
            <div class="tiq-panel">
                <div class="tiq-panel-title">Trend Indicators</div>
                <div class="tiq-panel-subtitle">Simple moving average and trend-based interpretation.</div>
            </div>
        """, unsafe_allow_html=True)

        trend_df = pd.DataFrame(index=stock_prices.index)
        trend_df["Price"] = stock_prices
        trend_df["MA20"] = stock_prices.rolling(20).mean()
        trend_df["MA50"] = stock_prices.rolling(50).mean()

        fig_trend = px.line(
            trend_df.reset_index(),
            x=trend_df.reset_index().columns[0],
            y=["Price", "MA20", "MA50"],
            title=f"{selected_stock} Price vs Moving Averages"
        )
        fig_trend.update_layout(height=430, legend_title_text="Series")
        st.plotly_chart(fig_trend, use_container_width=True)

        t1, t2, t3 = st.columns(3, gap="large")

        current_price = stock_prices.iloc[-1]
        ma20 = trend_df["MA20"].iloc[-1]
        ma50 = trend_df["MA50"].iloc[-1]

        with t1:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Trend Label</div>
                    <div class="tiq-kpi-value">{trend_label}</div>
                </div>
            """, unsafe_allow_html=True)

        with t2:
            above_ma20 = "Yes" if pd.notna(ma20) and current_price > ma20 else "No"
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Above 20-Day Avg</div>
                    <div class="tiq-kpi-value">{above_ma20}</div>
                </div>
            """, unsafe_allow_html=True)

        with t3:
            above_ma50 = "Yes" if pd.notna(ma50) and current_price > ma50 else "No"
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Above 50-Day Avg</div>
                    <div class="tiq-kpi-value">{above_ma50}</div>
                </div>
            """, unsafe_allow_html=True)

        # Intelligence Summary
        stock_summary = get_stock_summary(
            selected_stock,
            total_return,
            annual_return,
            annual_volatility,
            max_drawdown,
            trend_label
        )

        st.markdown(f"""
            <div class="tiq-note">
                <strong>Stock Intelligence Summary:</strong><br>
                {stock_summary}<br><br>
                <strong>Risk Label:</strong> {risk_label} &nbsp;|&nbsp;
                <strong>Trend:</strong> {trend_label}
            </div>
        """, unsafe_allow_html=True)

        # Basket Comparison
        st.markdown("""
            <div class="tiq-panel">
                <div class="tiq-panel-title">Compare Against Basket Average</div>
                <div class="tiq-panel-subtitle">See how this stock compares with the average of all loaded stocks.</div>
            </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2, gap="large")

        with c1:
            comp_df_return = pd.DataFrame({
                "Category": [selected_stock, "Basket Average"],
                "Value": [total_return, basket_avg_return]
            })
            fig_comp_ret = px.bar(
                comp_df_return,
                x="Category",
                y="Value",
                color="Category",
                title="Total Return Comparison"
            )
            fig_comp_ret.update_layout(height=380, yaxis_tickformat=".0%")
            st.plotly_chart(fig_comp_ret, use_container_width=True)

        with c2:
            comp_df_vol = pd.DataFrame({
                "Category": [selected_stock, "Basket Average"],
                "Value": [annual_volatility, basket_avg_vol]
            })
            fig_comp_vol = px.bar(
                comp_df_vol,
                x="Category",
                y="Value",
                color="Category",
                title="Volatility Comparison"
            )
            fig_comp_vol.update_layout(height=380, yaxis_tickformat=".0%")
            st.plotly_chart(fig_comp_vol, use_container_width=True)

        # Quick actions
        st.markdown("<br>", unsafe_allow_html=True)
        a1, a2, a3 = st.columns(3, gap="large")

        with a1:
            if st.button("Back to Market Overview"):
                go_to("pages/2_📈_Market_Overview.py")

        with a2:
            if st.button("Open Portfolio Optimizer"):
                go_to("pages/6_⚖️_Portfolio_Optimizer.py")

        with a3:
            if st.button("Open Risk Monitor"):
                go_to("pages/7_📉_Risk_Monitor.py")