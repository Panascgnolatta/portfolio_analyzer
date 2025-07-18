"""Controller layer: glues the model and the view"""
from .models.data_loader import DataLoader
from .models.metrics import MetricsCalculator

class Controller:
    def __init__(self, view):
        self.view = view
        self.loader = DataLoader()
        self.metrics = MetricsCalculator()

    def load_files(self, paths: list[str]):
        df = self.loader.load_multiple(paths)
        self.view.update_table(df.head())
        equity = self.metrics.equity_curve(df)
        stats  = self.metrics.all_metrics(equity)
        self.view.update_chart(equity)
        self.view.update_metrics(stats)
