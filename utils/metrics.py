import pandas as pd
import numpy as np

def compute_returns(prices: pd.DataFrame):
    return prices.pct_change().dropna()

def total_returns(prices: pd.DataFrame):
    return (prices.iloc[-1] / prices.iloc[0]) - 1

def annualized_returns(returns: pd.DataFrame):
    return returns.mean() * 252

def annualized_volatility(returns: pd.DataFrame):
    return returns.std() * np.sqrt(252)

def normalized_prices(prices: pd.DataFrame):
    return prices / prices.iloc[0]

def cumulative_returns(returns: pd.DataFrame):
    return (1 + returns).cumprod()

def calculate_max_drawdown(series: pd.Series):
    running_max = series.cummax()
    drawdown = (series / running_max) - 1
    return drawdown.min()

def get_summary_tables(prices: pd.DataFrame):
    returns = compute_returns(prices)
    total_ret = total_returns(prices)
    annual_ret = annualized_returns(returns)
    annual_vol = annualized_volatility(returns)

    summary = pd.DataFrame({
        "Stock": prices.columns,
        "Total Return": total_ret.reindex(prices.columns).values,
        "Annualized Return": annual_ret.reindex(prices.columns).values,
        "Annualized Volatility": annual_vol.reindex(prices.columns).values
    })

    summary = summary.sort_values("Total Return", ascending=False).reset_index(drop=True)
    return returns, summary

def get_market_summary(prices: pd.DataFrame):
    returns = compute_returns(prices)
    total_ret = total_returns(prices).sort_values(ascending=False)
    annual_vol = annualized_volatility(returns).sort_values(ascending=False)

    best_stock = total_ret.idxmax()
    worst_stock = total_ret.idxmin()
    highest_vol_stock = annual_vol.idxmax()
    lowest_vol_stock = annual_vol.idxmin()
    avg_return = total_ret.mean()

    corr_matrix = returns.corr()
    if corr_matrix.shape[0] > 1:
        corr_unstacked = corr_matrix.where(~np.eye(corr_matrix.shape[0], dtype=bool)).stack()
        most_corr_pair = corr_unstacked.idxmax()
        most_corr_value = corr_unstacked.max()
    else:
        most_corr_pair = ("N/A", "N/A")
        most_corr_value = np.nan

    return {
        "returns": returns,
        "total_returns": total_ret,
        "annualized_vol": annual_vol,
        "best_stock": best_stock,
        "worst_stock": worst_stock,
        "highest_vol_stock": highest_vol_stock,
        "lowest_vol_stock": lowest_vol_stock,
        "avg_return": avg_return,
        "most_corr_pair": most_corr_pair,
        "most_corr_value": most_corr_value,
    }

def get_risk_label(volatility):
    if volatility < 0.20:
        return "Low"
    elif volatility < 0.35:
        return "Medium"
    return "High"

def get_trend_label(price_series):
    if len(price_series) < 50:
        return "Neutral"

    ma20 = price_series.rolling(20).mean().iloc[-1]
    ma50 = price_series.rolling(50).mean().iloc[-1]
    current = price_series.iloc[-1]

    if pd.isna(ma20) or pd.isna(ma50):
        return "Neutral"

    if current > ma20 and ma20 > ma50:
        return "Strong Uptrend"
    elif current > ma20:
        return "Mild Uptrend"
    elif current < ma20 and ma20 < ma50:
        return "Downtrend"
    return "Neutral"

def get_stock_score(total_return, annual_volatility, max_drawdown):
    score = 50

    if total_return > 0.30:
        score += 20
    elif total_return > 0.10:
        score += 10
    elif total_return < 0:
        score -= 15

    if annual_volatility < 0.20:
        score += 15
    elif annual_volatility < 0.35:
        score += 5
    else:
        score -= 10

    if max_drawdown > -0.15:
        score += 15
    elif max_drawdown > -0.30:
        score += 5
    else:
        score -= 10

    return int(max(0, min(100, score)))