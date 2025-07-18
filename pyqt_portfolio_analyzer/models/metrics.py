import pandas as pd
import numpy as np

class MetricsCalculator:
    """Calculates portfolio-level metrics like CAGR, Sharpe, etc."""

    def equity_curve(self, df: pd.DataFrame) -> pd.Series:
        daily = df.groupby('Date')['損益'].sum().sort_index()
        equity = daily.cumsum()
        return equity

    def calc_cagr(self, equity: pd.Series) -> float:
        start, end = equity.iloc[0], equity.iloc[-1]
        n_years = (equity.index[-1] - equity.index[0]).days / 365.25
        return (end / max(start, 1e-9)) ** (1 / n_years) - 1

    def all_metrics(self, equity: pd.Series) -> dict:
        returns = equity.diff().dropna()
        cagr = self.calc_cagr(equity)
        sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() != 0 else np.nan
        mdd = ((equity.cummax() - equity) / equity.cummax()).max()
        return {
            "CAGR": cagr,
            "Sharpe": sharpe,
            "Max Drawdown": mdd,
        }
