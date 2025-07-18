from pathlib import Path
from .models.data_loader import DataLoader
from .models.metrics import MetricsCalculator


class Controller:
    """
    View ↔ Model の仲介。毎回 view から ruin_rate を受け取り
    Metrics へ渡して再計算する。
    """

    def __init__(self, view):
        self.view = view
        self.loader = DataLoader()
        self.metrics = MetricsCalculator()
        self.initial_cash = 100_000  # デフォルト初期資金

    # --------------------------------------------------
    # 指定ファイル群で全指標を計算
    # --------------------------------------------------
    def load_files(self, paths: list[str | Path]):
        # 1) データロード
        df = self.loader.load_multiple(paths)

        # 2) エクイティカーブ & トレードリスト
        equity = self.metrics.equity_curve(df, initial_cash=self.initial_cash)
        trade_list = df["損益 USD"].dropna()

        # 3) view から許容DD(=ruin_rate) を取得
        ruin_rate = self.view.get_ruin_rate()

        # 4) 全指標算出
        stats = self.metrics.all_metrics(
            equity,
            trade_list,
            initial_cash=self.initial_cash,
            ruin_rate=ruin_rate,   # ← ここが重要
        )

        # 5) View 更新
        self.view.update_chart(equity)
        self.view.update_metrics(stats)
