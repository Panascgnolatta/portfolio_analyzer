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
    QListWidget,
    QListWidgetItem,
    QGroupBox,
    QAbstractItemView,
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from pathlib import Path
from ..controller import Controller


class MainWindow(QMainWindow):
    """
    メイン GUI。
    - Excel ファイル読み込み
    - 損益曲線チャート
    - 指標テーブル
    - ファイルON/OFFリスト＋リセット＋再計算
    - 破産閾値スライダー
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Portfolio Analyzer")
        self.controller = Controller(self)
        self._ruin_rate = 0.20  # 20% デフォルト
        self.file_paths = []    # 管理している全ファイルのパスリスト
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        main_vbox = QVBoxLayout(central)

        # --- ファイル選択ボタン ---
        btn_hbox = QHBoxLayout()
        self.btn_open = QPushButton("Excelファイルを開く")
        self.btn_open.clicked.connect(self.open_files)
        btn_hbox.addWidget(self.btn_open)

        self.btn_reset = QPushButton("全ファイルリセット")
        self.btn_reset.clicked.connect(self.reset_files)
        btn_hbox.addWidget(self.btn_reset)
        main_vbox.addLayout(btn_hbox)

        # --- 破産閾値スライダー ---
        slider_box = QHBoxLayout()
        self.ror_label = QLabel(f"破産閾値: {int(self._ruin_rate * 100)} %")
        self.ror_slider = QSlider(Qt.Orientation.Horizontal)
        self.ror_slider.setMinimum(10)
        self.ror_slider.setMaximum(50)
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

        # --- 指標テーブル（5行×6列=Metric/Value×3組） ---
        self.table = QTableWidget()
        main_vbox.addWidget(self.table)

        # --- ファイル管理グループ ---
        file_group = QGroupBox("追加ファイル管理")
        file_vbox = QVBoxLayout(file_group)

        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        file_vbox.addWidget(self.file_list)

        self.btn_update = QPushButton("再計算（チェックのみ）")
        self.btn_update.clicked.connect(self.recalculate_metrics)
        file_vbox.addWidget(self.btn_update)

        main_vbox.addWidget(file_group)
        self.setCentralWidget(central)

    def on_ror_slider_changed(self, value: int):
        self._ruin_rate = value / 100  # 0.1〜0.5
        self.ror_label.setText(f"破産閾値: {value} %")
        self.recalculate_metrics()

    def open_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Excel Files", "", "Excel Files (*.xlsx)"
        )
        if paths:
            # 追加: ファイルリストに追記（重複不可）
            for p in paths:
                if p not in self.file_paths:
                    self.file_paths.append(p)
            self.refresh_file_list()
            self.recalculate_metrics()  # 全ONで再計算

    def refresh_file_list(self):
        self.file_list.clear()
        for path in self.file_paths:
            item = QListWidgetItem(Path(path).name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.file_list.addItem(item)

    def reset_files(self):
        self.file_paths.clear()
        self.file_list.clear()
        self.clear_chart_and_metrics()

    def recalculate_metrics(self):
        checked_paths = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                checked_paths.append(self.file_paths[i])
        if checked_paths:
            self.controller.load_files(checked_paths)
        else:
            self.clear_chart_and_metrics()

    def clear_chart_and_metrics(self):
        self.ax.clear()
        self.ax.set_title("Equity Curve")
        self.canvas.draw()
        self.table.clearContents()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)

    def update_chart(self, equity):
        self.ax.clear()
        self.ax.plot(equity.index, equity.values)
        self.ax.set_title("Equity Curve")
        self.canvas.draw()

    def update_metrics(self, stats: dict):
        # 5行×3組（Metric, Value）で並べる
        stats_items = list(stats.items())
        row_count = 5
        col_count = 6  # 3組×Metric/Value

        self.table.setRowCount(row_count)
        self.table.setColumnCount(col_count)

        headers = []
        for i in range(3):
            headers.extend([f"Metric", f"Value"])
        self.table.setHorizontalHeaderLabels(headers)
        self.table.clearContents()

        for idx, (k, v) in enumerate(stats_items):
            row = idx % row_count
            col = (idx // row_count) * 2
            if col >= col_count:
                continue  # 15個超は非表示
            self.table.setItem(row, col, QTableWidgetItem(str(k)))
            if isinstance(v, (int, float)):
                display = f"{v:.2f}" if "Rate" not in k and "%" not in k else f"{v:.2f} %"
            else:
                display = str(v)
            self.table.setItem(row, col + 1, QTableWidgetItem(display))

    def get_ruin_rate(self) -> float:
        return self._ruin_rate
