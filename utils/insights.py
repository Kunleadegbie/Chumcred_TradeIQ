import numpy as np
import pandas as pd
from .metrics import calculate_max_drawdown, get_risk_label

def get_stock_insight(prices: pd.DataFrame, stock: str):
    s = prices[stock].dropna()
    r = s.pct_change().dropna()

    total_return = (s.iloc[-1] / s.iloc[0]) - 1
    annual_return = r.mean() * 252
    annual_vol = r.std() * np.sqrt(252)
    max_dd = calculate_max_drawdown(s)

    risk = get_risk_label(annual_vol).lower()

    ma20 = s.rolling(20).mean().iloc[-1] if len(s) >= 20 else np.nan
    ma50 = s.rolling(50).mean().iloc[-1] if len(s) >= 50 else np.nan
    current = s.iloc[-1]

    if pd.notna(ma20) and pd.notna(ma50) and current > ma20 and ma20 > ma50:
        trend = "strong upward momentum"
    elif pd.notna(ma20) and current > ma20:
        trend = "mild upward momentum"
    elif pd.notna(ma20) and pd.notna(ma50) and current < ma20 and ma20 < ma50:
        trend = "clear downward pressure"
    else:
        trend = "mixed price behavior"

    detailed = (
        f"{stock} has produced a total return of {total_return:.2%} over the loaded period. "
        f"Its annualized return is {annual_return:.2%} and annualized volatility is {annual_vol:.2%}, "
        f"which places it in the {risk}-risk range relative to the current basket. "
        f"Price structure suggests {trend}. "
        f"The maximum drawdown observed was {max_dd:.2%}, which helps show how painful a bad period could feel for an investor."
    )

    simple = (
        f"In simple terms, {stock} looks like a {risk}-risk stock with {trend}. "
        f"It may suit investors whose risk tolerance matches that profile."
    )

    return detailed, simple

def get_market_insight(prices: pd.DataFrame):
    returns = prices.pct_change().dropna()
    total_returns = (prices.iloc[-1] / prices.iloc[0]) - 1
    annual_vol = returns.std() * np.sqrt(252)

    best_stock = total_returns.idxmax()
    worst_stock = total_returns.idxmin()
    most_volatile = annual_vol.idxmax()
    least_volatile = annual_vol.idxmin()

    corr = returns.corr()
    if corr.shape[0] > 1:
        corr_no_diag = corr.where(~np.eye(corr.shape[0], dtype=bool))
        avg_corr = corr_no_diag.stack().mean()
        if pd.isna(avg_corr):
            avg_corr = 0
    else:
        avg_corr = 1

    if avg_corr > 0.70:
        diversification_read = "many of the stocks are moving very similarly, so diversification is weak"
    elif avg_corr > 0.40:
        diversification_read = "there is moderate overlap in stock movement, so diversification exists but is not strong"
    else:
        diversification_read = "the basket shows fairly healthy variation in movement, which supports diversification"

    detailed = (
        f"Across the loaded basket, {best_stock} is the strongest performer while {worst_stock} is the weakest. "
        f"{most_volatile} is the most volatile stock, while {least_volatile} appears the most stable. "
        f"From a portfolio construction perspective, {diversification_read}. "
        f"This means investors should look beyond returns alone and also consider how holdings behave together."
    )

    simple = (
        f"The current market basket is led by {best_stock}, lagged by {worst_stock}, "
        f"and overall diversification looks {'weak' if avg_corr > 0.70 else 'moderate' if avg_corr > 0.40 else 'fairly healthy'}."
    )

    return detailed, simple

def get_portfolio_insight(prices: pd.DataFrame, weights: pd.Series):
    weights = weights.reindex(prices.columns).fillna(0)
    weights = weights / weights.sum()

    returns = prices.pct_change().dropna()
    portfolio_returns = returns.dot(weights)

    annual_return = portfolio_returns.mean() * 252
    annual_vol = portfolio_returns.std() * np.sqrt(252)
    max_dd = calculate_max_drawdown((1 + portfolio_returns).cumprod())

    largest_stock = weights.idxmax()
    largest_weight = weights.max()

    corr = returns.corr()
    if corr.shape[0] > 1:
        corr_no_diag = corr.where(~np.eye(corr.shape[0], dtype=bool))
        avg_corr = corr_no_diag.stack().mean()
        if pd.isna(avg_corr):
            avg_corr = 0
    else:
        avg_corr = 1

    detailed = (
        f"The portfolio is expected to deliver an annualized return of {annual_return:.2%} "
        f"with annualized volatility of {annual_vol:.2%}. "
        f"The largest holding is {largest_stock} at {largest_weight:.2%}, which is important because concentration can magnify downside risk. "
        f"The portfolio's observed maximum drawdown is {max_dd:.2%}. "
        f"Average correlation across the holdings suggests {'high overlap' if avg_corr > 0.70 else 'moderate overlap' if avg_corr > 0.40 else 'reasonable diversification'}. "
        f"This portfolio should be judged not only by return potential, but also by how balanced and resilient it is."
    )

    simple = (
        f"This portfolio has expected return of {annual_return:.2%} and volatility of {annual_vol:.2%}. "
        f"It is most exposed to {largest_stock}, so that holding deserves close attention."
    )

    return detailed, simple

def get_risk_insight(prices: pd.DataFrame, weights: pd.Series):
    weights = weights.reindex(prices.columns).fillna(0)
    weights = weights / weights.sum()
    returns = prices.pct_change().dropna()
    portfolio_returns = returns.dot(weights)

    annual_vol = portfolio_returns.std() * np.sqrt(252)
    var_95 = np.percentile(portfolio_returns, 5)
    max_dd = calculate_max_drawdown((1 + portfolio_returns).cumprod())
    largest_stock = weights.idxmax()
    largest_weight = weights.max()

    detailed = (
        f"Risk analysis shows annualized volatility of {annual_vol:.2%}, "
        f"a 95% daily Value at Risk of {var_95:.2%}, and a maximum drawdown of {max_dd:.2%}. "
        f"The largest position is {largest_stock} at {largest_weight:.2%}, which may amplify losses if that stock weakens sharply. "
        f"This means the portfolio may look efficient on paper, but concentration and downside behavior still need close monitoring."
    )

    simple = (
        f"In simple terms, the portfolio could still suffer meaningful losses in bad periods, "
        f"especially because {largest_stock} carries the biggest weight."
    )

    return detailed, simple