# PyQt Portfolio Analyzer (Template)

このテンプレートは、TradingView からエクスポートした複数の `.xlsx` を読み込み、
パフォーマンス指標を計算し PyQt6 GUI で表示するアプリのひな形です。

## セットアップ

```bash
python -m venv .venv
source .venv/bin/activate  # Windows は .venv\Scripts\activate
pip install -r requirements.txt
python -m pyqt_portfolio_analyzer
```

## ディレクトリ構成

```
pyqt_portfolio_analyzer/
    __init__.py
    main.py
    controller.py
    models/
        __init__.py
        data_loader.py
        metrics.py
    views/
        __init__.py
        main_window.py
tests/
    test_metrics.py
```
