import streamlit as st
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# ---------------------------
# PAGE CONFIG - MUST BE FIRST
# ---------------------------
st.set_page_config(
    page_title="TradeIQ™ | Portfolio Optimizer",
    page_icon="⚖️",
    layout="wide",
)


from utils.helpers import (
    init_session_state,
    apply_global_css,
    render_custom_sidebar,
    require_auth,
    go_to,
    safe_pct,
    reset_optimizer_state,
)

# setup
init_session_state()
apply_global_css()
require_auth()

from utils.data_loader import (
    parse_uploaded_csv,
    update_data_session_state,
)
from utils.optimizer import optimize_portfolio


# ---------------------------
# GLOBAL SETUP
# ---------------------------
init_session_state()
apply_global_css()

# ---------------------------
# NGX SYMBOL MAPPING
# ---------------------------
NGX_TICKER_MAP = {
    "AIRTELAFRI": "AIRTELAFRI.XNSA",
    "MTNN": "MTNN.XNSA",
    "DANGCEM": "DANGCEM.XNSA",
    "BUACEMENT": "BUACEMENT.XNSA",
    "ZENITHBANK": "ZENITHBANK.XNSA",
    "ZENITH": "ZENITHBANK.XNSA",
    "GTCO": "GTCO.XNSA",
    "GTB": "GTCO.XNSA",
    "ACCESSCORP": "ACCESSCORP.XNSA",
    "ACCESS": "ACCESSCORP.XNSA",
    "UBA": "UBA.XNSA",
    "FBNH": "FBNH.XNSA",
    "SEPLAT": "SEPLAT.XNSA",
    "NGXGROUP": "NGXGROUP.XNSA",
    "STANBIC": "STANBIC.XNSA",
    "STANBICIBTC": "STANBIC.XNSA",
}

def normalize_ngx_symbol(symbol: str) -> str:
    if not symbol:
        return ""

    s = symbol.strip().upper()

    if s in NGX_TICKER_MAP:
        return NGX_TICKER_MAP[s]

    if s.endswith(".LG"):
        s = s[:-3] + ".XNSA"

    if s.endswith(".XNSA"):
        return s

    if "." not in s:
        return f"{s}.XNSA"

    return s

def normalize_ngx_symbol_list(symbols_text: str) -> list[str]:
    raw_symbols = [s.strip() for s in symbols_text.split(",") if s.strip()]
    normalized = [normalize_ngx_symbol(s) for s in raw_symbols]
    return list(dict.fromkeys(normalized))

def get_display_name(symbol: str) -> str:
    return symbol.replace(".XNSA", "").replace(".LG", "")

# ---------------------------
# EODHD FETCHER
# ---------------------------
def fetch_eodhd_data_ngx(api_token: str, symbols_text: str, start_date, end_date):
    normalized_symbols = normalize_ngx_symbol_list(symbols_text)

    if not normalized_symbols:
        raise ValueError("Please provide at least one NGX ticker.")

    raw_symbols = [s.strip() for s in symbols_text.split(",") if s.strip()]
    mapping_rows = []

    for raw_symbol in raw_symbols:
        mapping_rows.append({
            "User Input": raw_symbol,
            "Normalized Symbol": normalize_ngx_symbol(raw_symbol)
        })

    all_data = pd.DataFrame()
    failed_symbols = []

    for symbol in normalized_symbols:
        url = (
            f"https://eodhd.com/api/eod/{symbol}"
            f"?from={start_date}&to={end_date}"
            f"&api_token={api_token}&period=d&fmt=json"
        )

        try:
            response = requests.get(url, timeout=30)
        except Exception:
            failed_symbols.append(symbol)
            continue

        if response.status_code != 200:
            failed_symbols.append(symbol)
            continue

        try:
            json_data = response.json()
        except Exception:
            failed_symbols.append(symbol)
            continue

        if not isinstance(json_data, list) or len(json_data) == 0:
            failed_symbols.append(symbol)
            continue

        df = pd.DataFrame(json_data)

        if "date" not in df.columns:
            failed_symbols.append(symbol)
            continue

        price_col = "adjusted_close" if "adjusted_close" in df.columns else "close"
        if price_col not in df.columns:
            failed_symbols.append(symbol)
            continue

        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        df[price_col] = pd.to_numeric(df[price_col], errors="coerce")

        display_name = get_display_name(symbol)
        all_data[display_name] = df[price_col]

    prices = all_data.dropna(how="all")

    if prices.empty:
        raise ValueError("No valid data was fetched from EODHD for the selected symbols/date range.")

    mapping_df = pd.DataFrame(mapping_rows)
    return prices, failed_symbols, mapping_df, normalized_symbols

# ---------------------------
# EXTRA METRICS
# ---------------------------
def calculate_var(portfolio_returns: pd.Series, confidence_level: float = 0.95) -> float:
    if portfolio_returns.empty:
        return np.nan
    percentile = np.percentile(portfolio_returns.dropna(), (1 - confidence_level) * 100)
    return abs(percentile)

def build_text_report(
    metric: str,
    rf_rate: float,
    annual_return: float,
    annual_volatility: float,
    var_95: float,
    optimized_weights: pd.Series,
) -> bytes:
    lines = [
        "TRADEIQ PORTFOLIO OPTIMIZATION REPORT",
        "=" * 42,
        "",
        f"Optimization Metric: {metric}",
        f"Risk-Free Rate: {rf_rate:.2f}%",
        f"Annualized Return: {annual_return:.2%}",
        f"Annualized Volatility: {annual_volatility:.2%}",
        f"95% Daily VaR: {var_95:.2%}",
        "",
        "Optimized Weights",
        "-" * 20,
    ]

    for stock, weight in optimized_weights.items():
        lines.append(f"{stock}: {weight:.2%}")

    return "\n".join(lines).encode("utf-8")

# ---------------------------
# LAYOUT
# ---------------------------
left_col, right_col = st.columns([1, 4], gap="large")

# ---------------------------
# CUSTOM SIDEBAR
# ---------------------------
with left_col:
    render_custom_sidebar("Portfolio Optimizer")

# ---------------------------
# MAIN CONTENT
# ---------------------------
with right_col:
    st.markdown('<div class="tiq-page-title">⚖️ Portfolio Optimizer</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="tiq-page-subtitle">Find a more efficient allocation using Sharpe or Sortino optimization.</div>',
        unsafe_allow_html=True
    )

    # ---------------------------
    # LOAD DATA SECTION
    # ---------------------------
    st.markdown("""
        <div class="tiq-panel">
            <div class="tiq-panel-title">Load Data</div>
            <div class="tiq-panel-subtitle">Choose a source for stock prices: upload a CSV file or fetch data through EODHD API.</div>
        </div>
    """, unsafe_allow_html=True)

    source_choice = st.radio(
        "Select data source",
        ["Upload CSV", "Fetch from EODHD API"],
        horizontal=True,
        key="optimizer_source_choice"
    )

    prices = None

    if source_choice == "Upload CSV":
        uploaded_file = st.file_uploader(
            "Upload CSV file",
            type=["csv"],
            help="CSV must contain a Date column and stock price columns."
        )

        if uploaded_file is not None:
            try:
                prices = parse_uploaded_csv(uploaded_file)
                update_data_session_state(st, prices, "CSV Upload")
                st.success("CSV data loaded successfully.")
            except Exception as e:
                st.error(f"Error processing CSV file: {e}")

    else:
        api_col1, api_col2, api_col3 = st.columns(3, gap="large")

        with api_col1:
            api_token = st.text_input("EODHD API Token", type="password")

        with api_col2:
            start_date = st.date_input("Start date")

        with api_col3:
            end_date = st.date_input("End date")

        symbols = st.text_input(
            "Stock symbols (comma-separated)",
            value="AIRTELAFRI, MTNN, DANGCEM, BUACEMENT, ZENITHBANK, GTCO, ACCESSCORP, UBA, SEPLAT, FBNH",
            help="You can type MTNN, MTNN.LG, MTNN.XNSA, GTB, ACCESS, ZENITH etc."
        )

        fetch_button = st.button("Fetch API Data")

        if fetch_button:
            if not api_token:
                st.warning("Please enter your EODHD API token.")
            elif start_date > end_date:
                st.warning("Start date cannot be after end date.")
            else:
                try:
                    with st.spinner("Fetching data from EODHD..."):
                        prices, failed_symbols, mapping_df, normalized_symbols = fetch_eodhd_data_ngx(
                            api_token=api_token,
                            symbols_text=symbols,
                            start_date=start_date,
                            end_date=end_date
                        )

                    update_data_session_state(st, prices, "EODHD API")

                    st.success("API data fetched successfully.")

                    st.markdown("""
                        <div class="tiq-panel">
                            <div class="tiq-panel-title">Symbol Mapping</div>
                            <div class="tiq-panel-subtitle">How your inputs were normalized for NGX on EODHD.</div>
                        </div>
                    """, unsafe_allow_html=True)
                    st.dataframe(mapping_df, use_container_width=True, hide_index=True)

                    st.markdown("""
                        <div class="tiq-panel">
                            <div class="tiq-panel-title">Normalized Symbols</div>
                            <div class="tiq-panel-subtitle">These are the EODHD symbols used for fetching.</div>
                        </div>
                    """, unsafe_allow_html=True)
                    st.write(", ".join(normalized_symbols))

                    if failed_symbols:
                        st.warning(f"Some symbols failed to load: {', '.join(failed_symbols)}")

                except Exception as e:
                    st.error(f"Error fetching data: {e}")

    # Use session prices if already loaded
    if prices is None and isinstance(st.session_state.loaded_prices, pd.DataFrame):
        prices = st.session_state.loaded_prices.copy()

    # ---------------------------
    # DATA PREVIEW
    # ---------------------------
    st.markdown("""
        <div class="tiq-panel">
            <div class="tiq-panel-title">Uploaded / Fetched Data Preview</div>
            <div class="tiq-panel-subtitle">The first rows of your loaded stock price table.</div>
        </div>
    """, unsafe_allow_html=True)

    if prices is not None and not prices.empty:
        st.dataframe(prices.head(), use_container_width=True)

        info1, info2, info3, info4 = st.columns(4, gap="large")

        with info1:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Data Source</div>
                    <div class="tiq-kpi-value">{st.session_state.data_source}</div>
                </div>
            """, unsafe_allow_html=True)

        with info2:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Stocks Loaded</div>
                    <div class="tiq-kpi-value">{prices.shape[1]}</div>
                </div>
            """, unsafe_allow_html=True)

        with info3:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Trading Days</div>
                    <div class="tiq-kpi-value">{prices.shape[0]}</div>
                </div>
            """, unsafe_allow_html=True)

        with info4:
            st.markdown(f"""
                <div class="tiq-kpi">
                    <div class="tiq-kpi-label">Date Range</div>
                    <div class="tiq-kpi-value">{st.session_state.date_range}</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Please upload a CSV file or fetch data via API to begin optimization.")

    # ---------------------------
    # OPTIMIZATION SETTINGS
    # ---------------------------
    st.markdown("""
        <div class="tiq-panel">
            <div class="tiq-panel-title">Optimization Settings</div>
            <div class="tiq-panel-subtitle">Configure the risk-free rate and optimization method.</div>
        </div>
    """, unsafe_allow_html=True)

    settings_col1, settings_col2 = st.columns(2, gap="large")

    with settings_col1:
        rf_rate = st.number_input(
            "Risk-free rate (%)",
            min_value=0.0,
            value=float(st.session_state.risk_free_rate),
            step=0.1
        )
        st.session_state.risk_free_rate = rf_rate

    with settings_col2:
        opt_metric = st.selectbox(
            "Optimize for",
            ["Sharpe Ratio", "Sortino Ratio"],
            index=0
        )

    with st.expander("What is the difference between Sharpe and Sortino?"):
        st.markdown("""
        **Sharpe Ratio** measures return relative to total volatility.  
        It treats both upside and downside movement as risk.

        **Sortino Ratio** measures return relative to downside volatility only.  
        It focuses more on harmful risk, which many investors find more practical.

        **Simple guide:**  
        - Use **Sharpe** if you want a broad risk-adjusted measure.  
        - Use **Sortino** if you care more about limiting downside moves.
        """)

    action_col1, action_col2 = st.columns(2, gap="large")
    with action_col1:
        optimize_button = st.button("🚀 Optimize Portfolio")
    with action_col2:
        reset_button = st.button("Reset Inputs")

    if reset_button:
        reset_optimizer_state()
        st.success("Optimizer state has been reset.")
        st.rerun()

    # ---------------------------
    # OPTIMIZATION EXECUTION
    # ---------------------------
    if optimize_button:
        if prices is None or prices.empty:
            st.warning("Please load price data first.")
        elif prices.shape[1] < 2:
            st.warning("Please load at least two stocks for portfolio optimization.")
        else:
            try:
                with st.spinner("Optimizing portfolio..."):
                    result, daily_returns, mean_returns, cov_matrix = optimize_portfolio(
                        prices=prices,
                        rf_rate=rf_rate,
                        metric=opt_metric
                    )

                if not result.success:
                    st.error(f"Optimization failed: {result.message}")
                else:
                    optimized_weights = pd.Series(result.x, index=prices.columns).round(6)
                    optimized_weights = optimized_weights / optimized_weights.sum()

                    st.session_state.optimized_weights = optimized_weights
                    st.session_state.returns_data = daily_returns

                    annual_return = (mean_returns * result.x).sum() * 252
                    annual_volatility = (result.x.T @ cov_matrix.values @ result.x) ** 0.5 * (252 ** 0.5)
                    portfolio_daily_returns = daily_returns.dot(result.x)
                    var_95 = calculate_var(portfolio_daily_returns, confidence_level=0.95)

                    st.success(f"Portfolio optimized successfully for {opt_metric}.")

                    # ---------------------------
                    # ALLOCATION CHART + TABLE
                    # ---------------------------
                    st.markdown("""
                        <div class="tiq-panel">
                            <div class="tiq-panel-title">Optimized Portfolio Allocation</div>
                            <div class="tiq-panel-subtitle">Recommended weights across the loaded stocks.</div>
                        </div>
                    """, unsafe_allow_html=True)

                    alloc_col1, alloc_col2 = st.columns([2, 1], gap="large")

                    with alloc_col1:
                        fig_alloc = px.pie(
                            values=optimized_weights.values,
                            names=optimized_weights.index,
                            title="Optimized Asset Allocation"
                        )
                        fig_alloc.update_layout(height=420)
                        st.plotly_chart(fig_alloc, use_container_width=True)

                    with alloc_col2:
                        alloc_df = pd.DataFrame({
                            "Stock": optimized_weights.index,
                            "Weight %": [f"{w:.2%}" for w in optimized_weights.values]
                        }).sort_values("Weight %", ascending=False)
                        st.dataframe(alloc_df, use_container_width=True, hide_index=True)

                    # ---------------------------
                    # HISTORICAL PRICE CHART
                    # ---------------------------
                    st.markdown("""
                        <div class="tiq-panel">
                            <div class="tiq-panel-title">Historical Price Chart</div>
                            <div class="tiq-panel-subtitle">Track the behavior of all loaded stocks over time.</div>
                        </div>
                    """, unsafe_allow_html=True)

                    fig_prices, ax_prices = plt.subplots(figsize=(12, 5))
                    prices.plot(ax=ax_prices)
                    ax_prices.set_xlabel("Date")
                    ax_prices.set_ylabel("Price")
                    ax_prices.set_title("Historical Stock Prices")
                    st.pyplot(fig_prices)

                    # ---------------------------
                    # CUMULATIVE RETURNS
                    # ---------------------------
                    st.markdown("""
                        <div class="tiq-panel">
                            <div class="tiq-panel-title">Cumulative Returns</div>
                            <div class="tiq-panel-subtitle">Compare how the loaded assets have compounded over time.</div>
                        </div>
                    """, unsafe_allow_html=True)

                    cumulative_returns = (1 + daily_returns).cumprod()
                    fig_cum = px.line(
                        cumulative_returns,
                        x=cumulative_returns.index,
                        y=cumulative_returns.columns,
                        title="Cumulative Returns"
                    )
                    st.plotly_chart(fig_cum, use_container_width=True)

                    # ---------------------------
                    # CORRELATION HEATMAP
                    # ---------------------------
                    st.markdown("""
                        <div class="tiq-panel">
                            <div class="tiq-panel-title">Correlation Heatmap</div>
                            <div class="tiq-panel-subtitle">Understand how the assets move relative to one another.</div>
                        </div>
                    """, unsafe_allow_html=True)

                    fig_corr, ax_corr = plt.subplots(figsize=(10, 4.8))
                    sns.heatmap(daily_returns.corr(), annot=True, cmap="Blues", fmt=".2f", ax=ax_corr)
                    ax_corr.set_title("Asset Correlation Heatmap")
                    st.pyplot(fig_corr)

                    # ---------------------------
                    # DAILY RETURNS DISTRIBUTION
                    # ---------------------------
                    st.markdown("""
                        <div class="tiq-panel">
                            <div class="tiq-panel-title">Daily Returns Distribution</div>
                            <div class="tiq-panel-subtitle">Distribution of daily returns across the loaded assets.</div>
                        </div>
                    """, unsafe_allow_html=True)

                    fig_ret, ax_ret = plt.subplots(figsize=(10, 4.5))
                    for col in daily_returns.columns:
                        sns.kdeplot(daily_returns[col], ax=ax_ret, label=col, fill=False)
                    ax_ret.set_title("Daily Returns Distribution")
                    ax_ret.legend()
                    st.pyplot(fig_ret)

                    # ---------------------------
                    # RISK-RETURN SUMMARY
                    # ---------------------------
                    st.markdown("""
                        <div class="tiq-panel">
                            <div class="tiq-panel-title">Portfolio Risk-Return Summary</div>
                            <div class="tiq-panel-subtitle">Key metrics for the optimized portfolio.</div>
                        </div>
                    """, unsafe_allow_html=True)

                    m1, m2, m3, m4 = st.columns(4, gap="large")

                    with m1:
                        st.markdown(f"""
                            <div class="tiq-kpi">
                                <div class="tiq-kpi-label">Annualized Return</div>
                                <div class="tiq-kpi-value">{safe_pct(annual_return)}</div>
                            </div>
                        """, unsafe_allow_html=True)

                    with m2:
                        st.markdown(f"""
                            <div class="tiq-kpi">
                                <div class="tiq-kpi-label">Annualized Volatility</div>
                                <div class="tiq-kpi-value">{safe_pct(annual_volatility)}</div>
                            </div>
                        """, unsafe_allow_html=True)

                    with m3:
                        st.markdown(f"""
                            <div class="tiq-kpi">
                                <div class="tiq-kpi-label">95% Daily VaR</div>
                                <div class="tiq-kpi-value">{safe_pct(var_95)}</div>
                            </div>
                        """, unsafe_allow_html=True)

                    with m4:
                        st.markdown(f"""
                            <div class="tiq-kpi">
                                <div class="tiq-kpi-label">Risk-Free Rate</div>
                                <div class="tiq-kpi-value">{rf_rate:.2f}%</div>
                            </div>
                        """, unsafe_allow_html=True)

                    summary_df = pd.DataFrame({
                        "Metric": [
                            "Annualized Return",
                            "Annualized Volatility",
                            "95% Daily VaR",
                            "Risk-Free Rate",
                            "Optimization Metric"
                        ],
                        "Value": [
                            safe_pct(annual_return),
                            safe_pct(annual_volatility),
                            safe_pct(var_95),
                            f"{rf_rate:.2f}%",
                            opt_metric
                        ]
                    })
                    st.dataframe(summary_df, use_container_width=True, hide_index=True)

                    # ---------------------------
                    # DOWNLOAD SECTION
                    # ---------------------------
                    st.markdown("""
                        <div class="tiq-panel">
                            <div class="tiq-panel-title">Download Outputs</div>
                            <div class="tiq-panel-subtitle">Export the optimized portfolio allocation and report.</div>
                        </div>
                    """, unsafe_allow_html=True)

                    download_df = pd.DataFrame({
                        "Stock": optimized_weights.index,
                        "Weight": optimized_weights.values
                    })
                    csv = download_df.to_csv(index=False).encode("utf-8")

                    st.download_button(
                        label="📥 Download Allocation CSV",
                        data=csv,
                        file_name="optimized_portfolio.csv",
                        mime="text/csv"
                    )

                    report_bytes = build_text_report(
                        metric=opt_metric,
                        rf_rate=rf_rate,
                        annual_return=annual_return,
                        annual_volatility=annual_volatility,
                        var_95=var_95,
                        optimized_weights=optimized_weights,
                    )

                    st.download_button(
                        label="📄 Download Text Report",
                        data=report_bytes,
                        file_name="tradeiq_portfolio_report.txt",
                        mime="text/plain"
                    )

            except Exception as e:
                st.error(f"Optimization error: {e}")