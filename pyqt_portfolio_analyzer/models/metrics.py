import pandas as pd
import numpy as np

class MetricsCalculator:
    """Trading戦略の重要指標を網羅したクラス。RoRはモンテカルロ法。"""

    def equity_curve(self, df: pd.DataFrame, initial_cash: float = 100000) -> pd.Series:
        daily = df.groupby('Date')['損益 USD'].sum().sort_index()
        equity = initial_cash + daily.cumsum()
        equity.index = pd.to_datetime(equity.index)
        return equity

    def calc_cagr(self, equity: pd.Series) -> float:
        start, end = equity.iloc[0], equity.iloc[-1]
        n_years = (equity.index[-1] - equity.index[0]).days / 365.25
        if n_years <= 0 or start <= 0:
            return np.nan
        cagr = (end / start) ** (1 / n_years) - 1
        return cagr * 100

    def calc_max_drawdown(self, equity: pd.Series) -> float:
        running_max = equity.cummax()
        drawdown = (running_max - equity) / running_max
        mdd = drawdown.max()
        return mdd * 100

    def calc_sharpe(self, equity: pd.Series) -> float:
        returns = equity.pct_change().dropna()
        if returns.std() == 0:
            return np.nan
        return returns.mean() / returns.std() * np.sqrt(252)

    def calc_sortino(self, equity: pd.Series) -> float:
        returns = equity.pct_change().dropna()
        downside = returns[returns < 0]
        if downside.std() == 0:
            return np.nan
        return returns.mean() / downside.std() * np.sqrt(252)

    def calc_profit_factor(self, trade_list: pd.Series) -> float:
        gross_profit = trade_list[trade_list > 0].sum()
        gross_loss = -trade_list[trade_list < 0].sum()
        if gross_loss == 0:
            return np.nan
        return gross_profit / gross_loss

    def calc_expectancy(self, trade_list: pd.Series) -> float:
        win_trades = trade_list[trade_list > 0]
        lose_trades = trade_list[trade_list < 0]
        win_rate = len(win_trades) / len(trade_list) if len(trade_list) > 0 else 0
        avg_win = win_trades.mean() if len(win_trades) > 0 else 0
        avg_loss = lose_trades.mean() if len(lose_trades) > 0 else 0
        expectancy = win_rate * avg_win + (1 - win_rate) * avg_loss
        return expectancy

    def calc_winrate(self, trade_list: pd.Series) -> float:
        wins = trade_list[trade_list > 0].count()
        total = trade_list.count()
        if total == 0:
            return np.nan
        return wins / total * 100

    def calc_payoff_ratio(self, trade_list: pd.Series) -> float:
        avg_win = trade_list[trade_list > 0].mean()
        avg_loss = trade_list[trade_list < 0].mean()
        if avg_loss == 0 or np.isnan(avg_win) or np.isnan(avg_loss):
            return np.nan
        return abs(avg_win / avg_loss)

    def calc_ror_montecarlo(self, trade_list: pd.Series, initial_cash=100000, ruin_rate=0.2, n_trials=1000) -> float:
        """
        モンテカルロ法で破産確率（Risk of Ruin, %）を推計
        ruin_rate: 例0.2 → 初期資金の20%を割ったら「破産」とみなす
        """
        if len(trade_list) == 0:
            return np.nan
        ruin_count = 0
        for _ in range(n_trials):
            cash = initial_cash
            trade_sample = np.random.permutation(trade_list)
            for pnl in trade_sample:
                cash += pnl
                if cash <= initial_cash * ruin_rate:
                    ruin_count += 1
                    break
        return ruin_count / n_trials * 100

    def calc_avg_win_loss(self, trade_list: pd.Series) -> tuple:
        avg_win = trade_list[trade_list > 0].mean() if (trade_list > 0).any() else 0
        avg_loss = trade_list[trade_list < 0].mean() if (trade_list < 0).any() else 0
        return avg_win, avg_loss

    def calc_max_win_loss_streak(self, trade_list: pd.Series) -> tuple:
        # 最大連勝・最大連敗
        win_streak = lose_streak = max_win = max_lose = 0
        for pnl in trade_list:
            if pnl > 0:
                win_streak += 1
                lose_streak = 0
            elif pnl < 0:
                lose_streak += 1
                win_streak = 0
            else:
                win_streak = lose_streak = 0
            max_win = max(max_win, win_streak)
            max_lose = max(max_lose, lose_streak)
        return max_win, max_lose

    def all_metrics(self, equity: pd.Series, trade_list: pd.Series, initial_cash=100000, ruin_rate=0.2) -> dict:
        cagr = self.calc_cagr(equity)
        sharpe = self.calc_sharpe(equity)
        sortino = self.calc_sortino(equity)
        mdd = self.calc_max_drawdown(equity)
        pf = self.calc_profit_factor(trade_list)
        expectancy = self.calc_expectancy(trade_list)
        winrate = self.calc_winrate(trade_list)
        payoff = self.calc_payoff_ratio(trade_list)
        avg_win, avg_loss = self.calc_avg_win_loss(trade_list)
        max_win_streak, max_lose_streak = self.calc_max_win_loss_streak(trade_list)
        ror = self.calc_ror_montecarlo(trade_list, initial_cash=initial_cash, ruin_rate=ruin_rate)

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
            "Max Win Streak": max_win_streak,
            "Max Lose Streak": max_lose_streak,
            "Risk of Ruin (%)": ror,
        }
