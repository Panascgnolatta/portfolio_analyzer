import pandas as pd
from pyqt_portfolio_analyzer.models.metrics import MetricsCalculator

def test_cagr():
    equity = pd.Series([100, 110, 121], index=pd.date_range("2020-01-01", periods=3, freq='Y'))
    calc = MetricsCalculator()
    cagr = calc.calc_cagr(equity)
    assert round(cagr, 4) == 0.1000
