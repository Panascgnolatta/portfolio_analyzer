import pandas as pd
import numpy as np

class MetricsCalculator:
    """Calculates portfolio-level metrics like CAGR, Sharpe, etc., with % output for key metrics."""

    def equity_curve(self, df: pd.DataFrame, initial_cash: float = 100000) -> pd.Series:
        """
        日次損益から初期資金を加えたエクイティカーブを返す。
        """
        daily = df.groupby('Date')['損益 USD'].sum().sort_index()
        equity = initial_cash + daily.cumsum()
        equity.index = pd.to_datetime(equity.index)
        return equity

    def calc_cagr(self, equity: pd.Series) -> float:
        """
        年率複利リターン（CAGR, %で返す）。
        """
        start, end = equity.iloc[0], equity.iloc[-1]
        n_years = (equity.index[-1] - equity.index[0]).days / 365.25
        if n_years <= 0 or start <= 0:
            return np.nan
        cagr = (end / start) ** (1 / n_years) - 1
        return cagr * 100  # パーセント

    def calc_max_drawdown(self, equity: pd.Series) -> float:
        """
        最大ドローダウン率（%で返す）。
        """
        running_max = equity.cummax()
        drawdown = (running_max - equity) / running_max
        mdd = drawdown.max()
        return mdd * 100  # パーセント

    def calc_sharpe(self, equity: pd.Series) -> float:
        """
        日次エクイティからシャープレシオ（リスクフリーレートは0と仮定）
        """
        returns = equity.pct_change().dropna()
        if returns.std() == 0:
            return np.nan
        return returns.mean() / returns.std() * np.sqrt(252)  # 年率換算

    def all_metrics(self, equity: pd.Series) -> dict:
        cagr = self.calc_cagr(equity)
        sharpe = self.calc_sharpe(equity)
        mdd = self.calc_max_drawdown(equity)
        return {
            "CAGR (%)": cagr,
            "Sharpe": sharpe,
            "Max Drawdown (%)": mdd,
        }
