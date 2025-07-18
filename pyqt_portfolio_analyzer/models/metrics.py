import pandas as pd
import numpy as np


class MetricsCalculator:
    """トレード単位の時系列でエクイティカーブと各種指標を計算"""

    # ------------------------------------------------------------------ #
    # 1) エクイティカーブ
    # ------------------------------------------------------------------ #
    def equity_curve(self, df: pd.DataFrame, initial_cash: float = 100_000) -> pd.Series:
        pnl_col = "損益 USD" if "損益 USD" in df.columns else "損益"
        equity = initial_cash + df[pnl_col].cumsum()
        equity.index = pd.to_datetime(df["DateTime"])
        return equity

    # ------------------------------------------------------------------ #
    # 2) 個別指標
    # ------------------------------------------------------------------ #
    def calc_cagr(self, equity: pd.Series) -> float:
        start, end = equity.iloc[0], equity.iloc[-1]
        years = (equity.index[-1] - equity.index[0]).days / 365.25
        return np.nan if years <= 0 else ((end / start) ** (1 / years) - 1) * 100

    def calc_max_drawdown(self, equity: pd.Series) -> float:
        dd = (equity.cummax() - equity) / equity.cummax()
        return dd.max() * 100

    def calc_sharpe(self, equity: pd.Series) -> float:
        r = equity.pct_change().dropna()
        return np.nan if r.std() == 0 else r.mean() / r.std() * np.sqrt(252)

    def calc_sortino(self, equity: pd.Series) -> float:
        r = equity.pct_change().dropna()
        downside = r[r < 0]
        return np.nan if downside.std() == 0 else r.mean() / downside.std() * np.sqrt(252)

    def calc_profit_factor(self, trade_list: pd.Series) -> float:
        gp = trade_list[trade_list > 0].sum()
        gl = -trade_list[trade_list < 0].sum()
        return np.nan if gl == 0 else gp / gl

    def calc_expectancy(self, trade_list: pd.Series) -> float:
        wins = trade_list[trade_list > 0]
        loses = trade_list[trade_list < 0]
        win_rate = len(wins) / len(trade_list) if len(trade_list) else 0
        return win_rate * wins.mean() + (1 - win_rate) * loses.mean()

    def calc_winrate(self, trade_list: pd.Series) -> float:
        return trade_list[trade_list > 0].count() / trade_list.count() * 100

    def calc_payoff_ratio(self, trade_list: pd.Series) -> float:
        avg_win = trade_list[trade_list > 0].mean()
        avg_loss = trade_list[trade_list < 0].mean()
        return np.nan if avg_loss == 0 else abs(avg_win / avg_loss)

    # ---------- ここを修正 ---------- #
    def calc_ror_montecarlo(
        self,
        trade_list: pd.Series,
        initial_cash: float = 100_000,
        ruin_rate: float = 0.2,          # 許容する最大ドローダウン率
        n_trials: int = 1_000
    ) -> float:
        """
        モンテカルロ法で破産確率 (%).

        ruin_rate = 0.2 → 資金が 20% 減（残高 80%）で「破産」判定
        """
        if trade_list.empty:
            return np.nan

        threshold = initial_cash * (1 - ruin_rate)  # ← 資金がココを割ったら破産
        ruin_count = 0

        for _ in range(n_trials):
            cash = initial_cash
            for pnl in np.random.permutation(trade_list):
                cash += pnl
                if cash <= threshold:
                    ruin_count += 1
                    break

        return ruin_count / n_trials * 100
    # -------------------------------- #

    def calc_avg_win_loss(self, trade_list: pd.Series):
        return (
            trade_list[trade_list > 0].mean() if (trade_list > 0).any() else 0,
            trade_list[trade_list < 0].mean() if (trade_list < 0).any() else 0,
        )

    def calc_max_win_loss_streak(self, trade_list: pd.Series):
        win = lose = max_win = max_lose = 0
        for pnl in trade_list:
            if pnl > 0:
                win += 1
                lose = 0
            elif pnl < 0:
                lose += 1
                win = 0
            else:
                win = lose = 0
            max_win, max_lose = max(max_win, win), max(max_lose, lose)
        return max_win, max_lose

    # ------------------------------------------------------------------ #
    # 3) オールインワン取得
    # ------------------------------------------------------------------ #
    def all_metrics(
        self,
        equity: pd.Series,
        trade_list: pd.Series,
        initial_cash: float = 100_000,
        ruin_rate: float = 0.2,
    ) -> dict:
        cagr = self.calc_cagr(equity)
        sharpe = self.calc_sharpe(equity)
        sortino = self.calc_sortino(equity)
        mdd = self.calc_max_drawdown(equity)
        pf = self.calc_profit_factor(trade_list)
        expectancy = self.calc_expectancy(trade_list)
        winrate = self.calc_winrate(trade_list)
        payoff = self.calc_payoff_ratio(trade_list)
        avg_win, avg_loss = self.calc_avg_win_loss(trade_list)
        streak_win, streak_lose = self.calc_max_win_loss_streak(trade_list)
        ror = self.calc_ror_montecarlo(trade_list, initial_cash, ruin_rate)

        return {
            "CAGR (%)": cagr,
            "Max Drawdown (%)": mdd,
            "Sharpe": sharpe,
            "Sortino": sortino,
            "Profit Factor": pf,
            "Expectancy": expectancy,
            "Payoff Ratio": payoff,
            "Win Rate (%)": winrate,
            "Avg Win": avg_win,
            "Avg Loss": avg_loss,
            "Max Win Streak": streak_win,
            "Max Lose Streak": streak_lose,
            "Risk of Ruin (%)": ror,
        }
