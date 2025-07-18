from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QSlider,
    QHBoxLayout,
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from ..controller import Controller


class MainWindow(QMainWindow):
    """
    メイン GUI。
    - Excel ファイル読み込み
    - 損益曲線チャート
    - 指標テーブル
    - 破産閾値スライダー
    """

    # ----------------------------
    # 初期化
    # ----------------------------
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Portfolio Analyzer")
        self.controller = Controller(self)
        self._ruin_rate = 0.20  # 20% デフォルト
        self._build_ui()

    # ----------------------------
    # UIレイアウト構築
    # ----------------------------
    def _build_ui(self):
        central = QWidget()
        main_vbox = QVBoxLayout(central)

        # --- ファイル選択ボタン ---
        self.btn_open = QPushButton("Excelファイルを開く")
        self.btn_open.clicked.connect(self.open_files)
        main_vbox.addWidget(self.btn_open)

        # --- 破産閾値スライダー ---
        slider_box = QHBoxLayout()
        self.ror_label = QLabel(f"破産閾値: {int(self._ruin_rate * 100)} %")
        self.ror_slider = QSlider(Qt.Orientation.Horizontal)
        self.ror_slider.setMinimum(10)   # 10 %
        self.ror_slider.setMaximum(50)   # 50 %
        self.ror_slider.setValue(int(self._ruin_rate * 100))
        self.ror_slider.setTickInterval(1)
        self.ror_slider.valueChanged.connect(self.on_ror_slider_changed)

        slider_box.addWidget(QLabel("▼低リスク"))
        slider_box.addWidget(self.ror_slider)
        slider_box.addWidget(QLabel("高リスク▲"))
        slider_box.addWidget(self.ror_label)
        main_vbox.addLayout(slider_box)

        # --- Matplotlib チャート ---
        self.canvas = FigureCanvas(Figure(figsize=(6, 3)))
        self.ax = self.canvas.figure.subplots()
        main_vbox.addWidget(self.canvas)

        # --- 指標テーブル ---
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Metric", "Value"])
        main_vbox.addWidget(self.table)

        self.setCentralWidget(central)

    # --------------------------------------------------
    # スライダー変更
    # --------------------------------------------------
    def on_ror_slider_changed(self, value: int):
        self._ruin_rate = value / 100  # 0.1〜0.5
        self.ror_label.setText(f"破産閾値: {value} %")
        # 既にデータがロード済みなら再計算
        self.controller.update_metrics_with_ruin_rate(self._ruin_rate)

    # --------------------------------------------------
    # ファイル選択
    # --------------------------------------------------
    def open_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Excel Files", "", "Excel Files (*.xlsx)"
        )
        if paths:
            self.controller.load_files(paths)

    # --------------------------------------------------
    # Controller から呼ばれる View 更新メソッド
    # --------------------------------------------------
    def update_chart(self, equity):
        self.ax.clear()
        self.ax.plot(equity.index, equity.values)
        self.ax.set_title("Equity Curve")
        self.canvas.draw()

    def update_metrics(self, stats: dict):
        self.table.setRowCount(len(stats))
        for row, (k, v) in enumerate(stats.items()):
            self.table.setItem(row, 0, QTableWidgetItem(k))
            if isinstance(v, (int, float)):
                display = f"{v:.2f}" if "Rate" not in k and "%" not in k else f"{v:.2f} %"
            else:
                display = str(v)
            self.table.setItem(row, 1, QTableWidgetItem(display))

    # --------------------------------------------------
    # Controller から ruin_rate を取得する用
    # --------------------------------------------------
    def get_ruin_rate(self) -> float:
        return self._ruin_rate
