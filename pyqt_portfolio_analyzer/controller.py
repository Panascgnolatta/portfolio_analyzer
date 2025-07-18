from pathlib import Path
from .models.data_loader import DataLoader
from .models.metrics import MetricsCalculator


class Controller:
    """
    View ↔ Model の仲介。
    View（MainWindow）から呼ばれ、結果を再度 View に渡す。
    """

    def __init__(self, view):
        self.view = view
        self.loader = DataLoader()
        self.metrics = MetricsCalculator()

        # 状態保持（再計算用）
        self.df = None
        self.equity = None
        self.trade_list = None
        self.initial_cash = 100_000  # デフォルト初期資金

    # --------------------------------------------------
    # ファイル読み込み & 初回計算
    # --------------------------------------------------
    def load_files(self, paths: list[str | Path]):
        # ① Excel読み込み
        self.df = self.loader.load_multiple(paths)

        # ② エクイティカーブ / トレードリスト
        self.equity = self.metrics.equity_curve(
            self.df, initial_cash=self.initial_cash
        )
        self.trade_list = self.df["損益 USD"].dropna()

        # ③ 指標計算（破産閾値は View 側スライダー値を参照）
        ruin_rate = self.view.get_ruin_rate()  # 0.1〜0.5 の小数
        stats = self.metrics.all_metrics(
            self.equity,
            self.trade_list,
            initial_cash=self.initial_cash,
            ruin_rate=ruin_rate,
        )

        # ④ View へ反映
        self.view.update_chart(self.equity)
        self.view.update_metrics(stats)

    # --------------------------------------------------
    # 破産閾値スライダー変更時の再計算
    # --------------------------------------------------
    def update_metrics_with_ruin_rate(self, ruin_rate: float):
        if self.equity is None or self.trade_list is None:
            return  # データ未ロード
        stats = self.metrics.all_metrics(
            self.equity,
            self.trade_list,
            initial_cash=self.initial_cash,
            ruin_rate=ruin_rate,
        )
        self.view.update_metrics(stats)
