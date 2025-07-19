import numpy as np
import pandas as pd

class Metrics:
    def __init__(self):
        pass

    # ---- 基本: エクイティカーブ ----
    def equity_curve(self, df: pd.DataFrame, initial_capital: float = 100000.0):
        # 損益列検出（例: '損益' / '損益(ドル)' 等）必要に応じて改善
        col = None
        for c in df.columns:
            if "損" in c and "益" in c:
                col = c
                break
        if col is None:
            raise ValueError("損益列が見つかりません。列名を確認してください。")
        pnl = df[col].astype(float)
        equity = initial_capital + pnl.cumsum()
        equity.index = pd.to_datetime(df['日時']).dt.date if '日時' in df.columns else range(len(equity))
        return equity

    # ---- 各種計算 ----
    def cagr(self, equity: pd.Series):
        if len(equity) < 2:
            return 0.0
        start = equity.iloc[0]
        end = equity.iloc[-1]
        days = (pd.to_datetime(equity.index[-1]) - pd.to_datetime(equity.index[0])).days or len(equity)
        years = days / 365.25
        if years <= 0 or start <= 0:
            return 0.0
        return (end / start) ** (1 / years) - 1

    def max_drawdown(self, equity: pd.Series):
        roll_max = equity.cummax()
        dd = (equity - roll_max) / roll_max
        return dd.min()

    def daily_returns(self, equity: pd.Series):
        return equity.pct_change().dropna()

    def sharpe(self, equity: pd.Series, rf=0.0):
        rets = self.daily_returns(equity)
        if rets.std(ddof=0) == 0:
            return 0.0
        return (rets.mean() - rf / 252) / rets.std(ddof=0) * np.sqrt(252)

    def sortino(self, equity: pd.Series, rf=0.0):
        rets = self.daily_returns(equity)
        neg = rets[rets < 0]
        if neg.std(ddof=0) == 0:
            return 0.0
        return (rets.mean() - rf / 252) / neg.std(ddof=0) * np.sqrt(252)

    def trade_stats(self, df: pd.DataFrame):
        col = None
        for c in df.columns:
            if "損" in c and "益" in c:
                col = c
                break
        if col is None:
            return {}
        pnl = df[col].astype(float)
        wins = pnl[pnl > 0]
        losses = pnl[pnl < 0]

        win_rate = len(wins) / len(pnl) * 100 if len(pnl) else 0
        avg_win = wins.mean() if len(wins) else 0.0
        avg_loss = losses.mean() if len(losses) else 0.0
        payoff = (avg_win / abs(avg_loss)) if avg_loss != 0 else np.nan

        # 連勝/連敗
        streaks = []
        current = 0
        last_sign = None
        for v in pnl:
            sign = 1 if v > 0 else (-1 if v < 0 else 0)
            if sign == last_sign:
                current += 1
            else:
                current = 1
                last_sign = sign
            streaks.append((sign, current))
        max_win_streak = max([s for (sign, s) in streaks if sign == 1], default=0)
        max_lose_streak = max([s for (sign, s) in streaks if sign == -1], default=0)

        expectancy = pnl.mean() if len(pnl) else 0.0
        profit_factor = wins.sum() / abs(losses.sum()) if abs(losses.sum()) > 0 else np.nan

        return dict(
            WinRate=win_rate,
            AvgWin=avg_win,
            AvgLoss=avg_loss,
            PayoffRatio=payoff,
            Expectancy=expectancy,
            ProfitFactor=profit_factor,
            MaxWinStreak=max_win_streak,
            MaxLoseStreak=max_lose_streak,
            TradeCount=len(pnl)
        )

    # ---- Risk of Ruin (モンテカルロ) ----
    def risk_of_ruin(self, df: pd.DataFrame, max_dd_threshold: float, initial_capital: float,
                     n_sims: int = 10000, ci: bool = True):
        """
        max_dd_threshold: 例 0.2 → 初期資本から 20% 減少で '破産' とみなす
        戻り値: ror_percent, step_percent, (optional ci95_half_width)
        """
        col = None
        for c in df.columns:
            if "損" in c and "益" in c:
                col = c
                break
        if col is None or len(df) == 0:
            return 0.0, 100 / n_sims, 0.0

        trade_pnl = df[col].astype(float).values
        if len(trade_pnl) == 0:
            return 0.0, 100 / n_sims, 0.0

        ruin_count = 0
        threshold_value = initial_capital * (1 - max_dd_threshold)

        # 単純：トレード順序をシャッフルしたパス
        for _ in range(n_sims):
            path = np.random.permutation(trade_pnl)
            equity = initial_capital + np.cumsum(path)
            if equity.min() <= threshold_value:
                ruin_count += 1

        p_hat = ruin_count / n_sims
        ror_percent = p_hat * 100
        step = 100 / n_sims
        if ci:
            # 正規近似 95% CI
            se = np.sqrt(p_hat * (1 - p_hat) / n_sims)
            ci95 = 1.96 * se * 100  # %
        else:
            ci95 = 0.0
        return ror_percent, step, ci95

    # ---- 総合計算 ----
    def calculate_all(self, df: pd.DataFrame, initial_capital: float,
                      max_dd_threshold: float, n_sims: int):
        equity = self.equity_curve(df, initial_capital=initial_capital)

        cagr_v = self.cagr(equity) * 100
        mdd_v = self.max_drawdown(equity) * 100  # %
        sharpe_v = self.sharpe(equity)
        sortino_v = self.sortino(equity)

        trade_stats = self.trade_stats(df)

        ror, step, ci95 = self.risk_of_ruin(
            df,
            max_dd_threshold=max_dd_threshold,
            initial_capital=initial_capital,
            n_sims=n_sims,
            ci=True
        )

        stats = {
            "CAGR (%)": cagr_v,
            "Max Drawdown (%)": mdd_v,
            "Sharpe Ratio": sharpe_v,
            "Sortino Ratio": sortino_v,
            "Profit Factor": trade_stats.get("ProfitFactor", np.nan),
            "Expectancy": trade_stats.get("Expectancy", np.nan),
            "Payoff Ratio": trade_stats.get("PayoffRatio", np.nan),
            "Win Rate (%)": trade_stats.get("WinRate", np.nan),
            "Avg Win": trade_stats.get("AvgWin", np.nan),
            "Avg Loss": trade_stats.get("AvgLoss", np.nan),
            "Max Win Streak": trade_stats.get("MaxWinStreak", 0),
            "Max Lose Streak": trade_stats.get("MaxLoseStreak", 0),
            "Trade Count": trade_stats.get("TradeCount", 0),
            "Risk of Ruin (%)": ror,
            "RoR Step (%)": step,
            "RoR 95% CI (±%)": ci95
        }
        return stats
