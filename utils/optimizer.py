import numpy as np
import pandas as pd
from scipy.optimize import minimize

def portfolio_performance(weights, mean_returns, cov_matrix, rf_rate, daily_returns, metric):
    annual_return = np.sum(mean_returns * weights) * 252
    annual_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))) * np.sqrt(252)
    portfolio_daily_returns = daily_returns.dot(weights)

    if metric == "Sharpe Ratio":
        if annual_volatility == 0:
            return np.inf
        sharpe_ratio = (annual_return - rf_rate / 100) / annual_volatility
        return -sharpe_ratio

    downside = portfolio_daily_returns[portfolio_daily_returns < 0]
    downside_std = np.std(downside) * np.sqrt(252)

    if downside_std == 0:
        return np.inf

    sortino_ratio = (annual_return - rf_rate / 100) / downside_std
    return -sortino_ratio

def optimize_portfolio(prices: pd.DataFrame, rf_rate: float, metric: str):
    daily_returns = prices.pct_change().dropna()
    mean_returns = daily_returns.mean()
    cov_matrix = daily_returns.cov()

    num_assets = len(mean_returns)
    args = (mean_returns, cov_matrix, rf_rate, daily_returns, metric)
    constraints = ({"type": "eq", "fun": lambda x: np.sum(x) - 1},)
    bounds = tuple((0, 1) for _ in range(num_assets))

    result = minimize(
        portfolio_performance,
        x0=np.array(num_assets * [1.0 / num_assets]),
        args=args,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
    )

    return result, daily_returns, mean_returns, cov_matrix