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
    """メイン UI"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Portfolio Analyzer")
        self.controller = Controller(self)
        self._ruin_rate = 0.20          # 20 % (=許容DD)
        self.file_paths: list[str] = []  # 取り込んだファイルのフルパス
        self._build_ui()

    # ---------------------------------------------------------------------
    # UI 構築
    # ---------------------------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        main_vbox = QVBoxLayout(central)

        # ── ファイル選択 & 全リセット ────────────────────────────
        btn_hbox = QHBoxLayout()
        self.btn_open = QPushButton("Excelファイルを開く")
        self.btn_open.clicked.connect(self.open_files)
        btn_hbox.addWidget(self.btn_open)

        self.btn_reset = QPushButton("全ファイルリセット")
        self.btn_reset.clicked.connect(self.reset_files)
        btn_hbox.addWidget(self.btn_reset)
        main_vbox.addLayout(btn_hbox)

        # ── 許容DDスライダー ───────────────────────────────
        dd_box = QHBoxLayout()
        self.dd_label = QLabel(f"許容する最大DD: {int(self._ruin_rate * 100)} %")

        self.dd_slider = QSlider(Qt.Orientation.Horizontal)
        self.dd_slider.setMinimum(10)     # 10 %
        self.dd_slider.setMaximum(50)     # 50 %
        self.dd_slider.setValue(int(self._ruin_rate * 100))
        self.dd_slider.setTickInterval(1)
        self.dd_slider.valueChanged.connect(self.on_dd_slider_changed)
        self.dd_slider.setToolTip("左: 小さいDD許容 / 右: 大きいDD許容")

        dd_box.addWidget(self.dd_slider)
        dd_box.addWidget(self.dd_label)
        main_vbox.addLayout(dd_box)

        # ── チャート ─────────────────────────────────────────
        self.canvas = FigureCanvas(Figure(figsize=(6, 3)))
        self.ax = self.canvas.figure.subplots()
        main_vbox.addWidget(self.canvas)

        # ── 指標テーブル 5行×6列 ───────────────────────────
        self.table = QTableWidget()
        main_vbox.addWidget(self.table)

        # ── ファイル管理パネル ─────────────────────────────
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

    # ---------------------------------------------------------------------
    # スライダー変更
    # ---------------------------------------------------------------------
    def on_dd_slider_changed(self, value: int):
        self._ruin_rate = value / 100
        self.dd_label.setText(f"許容する最大DD: {value} %")
        self.recalculate_metrics()

    # ---------------------------------------------------------------------
    # ファイル追加
    # ---------------------------------------------------------------------
    def open_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Excel Files", "", "Excel Files (*.xlsx)"
        )
        if paths:
            for p in paths:
                if p not in self.file_paths:
                    self.file_paths.append(p)
            self.refresh_file_list()
            self.recalculate_metrics()

    # ---------------------------------------------------------------------
    # ファイル一覧表示更新
    # ---------------------------------------------------------------------
    def refresh_file_list(self):
        self.file_list.clear()
        for path in self.file_paths:
            item = QListWidgetItem(Path(path).name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            item.setToolTip(str(path))
            self.file_list.addItem(item)

    # ---------------------------------------------------------------------
    # 全ファイルリセット
    # ---------------------------------------------------------------------
    def reset_files(self):
        self.file_paths.clear()
        self.file_list.clear()
        self.clear_chart_and_metrics()

    # ---------------------------------------------------------------------
    # 再計算（チェックON ファイルのみ）
    # ---------------------------------------------------------------------
    def recalculate_metrics(self):
        checked_paths = self.get_checked_paths()
        if checked_paths:
            self.controller.load_files(checked_paths)
        else:
            self.clear_chart_and_metrics()

    # ヘルパー: 現在チェックされているファイルパスを返す
    def get_checked_paths(self) -> list[str]:
        return [
            self.file_paths[i]
            for i in range(self.file_list.count())
            if self.file_list.item(i).checkState() == Qt.CheckState.Checked
        ]

    # ---------------------------------------------------------------------
    # View 更新メソッド
    # ---------------------------------------------------------------------
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
        row_count, col_count = 5, 6  # 5行×Metric/Value×3組
        self.table.setRowCount(row_count)
        self.table.setColumnCount(col_count)
        headers = sum([["Metric", "Value"] for _ in range(3)], [])
        self.table.setHorizontalHeaderLabels(headers)
        self.table.clearContents()

        for idx, (k, v) in enumerate(stats.items()):
            row = idx % row_count
            col = (idx // row_count) * 2
            if col >= col_count:
                continue
            self.table.setItem(row, col, QTableWidgetItem(str(k)))
            if isinstance(v, (int, float)):
                display = f"{v:.2f}" if "Rate" not in k and "%" not in k else f"{v:.2f} %"
            else:
                display = str(v)
            self.table.setItem(row, col + 1, QTableWidgetItem(display))

    # ruin_rate を Controller へ渡すための getter
    def get_ruin_rate(self) -> float:
        return self._ruin_rate
