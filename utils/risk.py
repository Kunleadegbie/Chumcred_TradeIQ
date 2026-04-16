import numpy as np
import pandas as pd
from .metrics import calculate_max_drawdown

def normalize_weights(weights: pd.Series):
    weights = weights.dropna()
    total = weights.sum()
    if total == 0:
        return weights
    return weights / total

def build_equal_weights(columns):
    n = len(columns)
    if n == 0:
        return pd.Series(dtype=float)
    return pd.Series([1 / n] * n, index=columns)

def get_diversification_score(weights: pd.Series, corr_matrix: pd.DataFrame):
    if weights.empty:
        return 0

    concentration = float((weights ** 2).sum())

    if corr_matrix.shape[0] > 1:
        corr_no_diag = corr_matrix.where(~np.eye(corr_matrix.shape[0], dtype=bool))
        avg_corr = corr_no_diag.stack().mean()
        if pd.isna(avg_corr):
            avg_corr = 0
    else:
        avg_corr = 1

    score = 100 - (concentration * 100) - (max(avg_corr, 0) * 30)
    return int(max(0, min(100, score)))

def get_concentration_score(weights: pd.Series):
    if weights.empty:
        return 0
    max_weight = weights.max()
    hhi = float((weights ** 2).sum())
    score = 100 - (max_weight * 100 * 0.7) - (hhi * 100 * 0.3)
    return int(max(0, min(100, score)))

def portfolio_risk_summary(prices: pd.DataFrame, weights: pd.Series):
    daily_returns = prices.pct_change().dropna()
    aligned_weights = weights.reindex(daily_returns.columns).fillna(0)
    portfolio_daily_returns = daily_returns.dot(aligned_weights)

    annualized_vol = portfolio_daily_returns.std() * np.sqrt(252)
    var_95 = np.percentile(portfolio_daily_returns, 5)
    cumulative = (1 + portfolio_daily_returns).cumprod()
    max_drawdown = calculate_max_drawdown(cumulative)

    corr_matrix = daily_returns.corr()
    diversification_score = get_diversification_score(aligned_weights, corr_matrix)
    concentration_score = get_concentration_score(aligned_weights)

    return {
        "daily_returns": daily_returns,
        "portfolio_daily_returns": portfolio_daily_returns,
        "annualized_volatility": annualized_vol,
        "var_95": var_95,
        "max_drawdown": max_drawdown,
        "corr_matrix": corr_matrix,
        "diversification_score": diversification_score,
        "concentration_score": concentration_score,
    }

def get_risk_commentary(weights: pd.Series, risk_metrics: dict):
    comments = []

    max_weight_stock = weights.idxmax()
    max_weight_value = weights.max()

    if max_weight_value > 0.40:
        comments.append(
            f"Portfolio is heavily concentrated in {max_weight_stock} at {max_weight_value:.2%}, which increases single-stock risk."
        )
    elif max_weight_value > 0.25:
        comments.append(
            f"{max_weight_stock} has the largest weight at {max_weight_value:.2%}. Monitor concentration carefully."
        )
    else:
        comments.append(
            "Weight distribution is relatively balanced, which supports diversification."
        )

    if risk_metrics["diversification_score"] < 40:
        comments.append(
            "Diversification is weak. Several holdings may be moving too similarly or concentration is too high."
        )
    elif risk_metrics["diversification_score"] < 65:
        comments.append(
            "Diversification is moderate. There is some protection, but portfolio overlap may still be meaningful."
        )
    else:
        comments.append(
            "Diversification is reasonably strong for the current basket."
        )

    if risk_metrics["annualized_volatility"] > 0.35:
        comments.append(
            "Portfolio volatility is high, suggesting stronger price swings and elevated uncertainty."
        )
    elif risk_metrics["annualized_volatility"] > 0.20:
        comments.append(
            "Portfolio volatility is moderate, which may suit medium-risk investors."
        )
    else:
        comments.append(
            "Portfolio volatility is relatively low compared with more aggressive equity baskets."
        )

    return comments