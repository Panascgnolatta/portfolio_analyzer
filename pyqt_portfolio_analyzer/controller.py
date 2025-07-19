from .models.data_loader import DataLoader
from .models.metrics import Metrics

class Controller:
    def __init__(self, view):
        self.view = view
        self.loader = DataLoader()
        self.metrics = Metrics()

    def load_files(self, paths):
        df = self.loader.load_multiple(paths)
        equity = self.metrics.equity_curve(df)
        stats = self.metrics.calculate_all(
            df,
            initial_capital=100000,
            max_dd_threshold=self.view.get_ruin_rate(),
            n_sims=self.view.get_n_sims()
        )
        self.view.update_chart(equity)
        self.view.update_metrics(stats)
