from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow, QFileDialog, QWidget, QVBoxLayout, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QSlider, QHBoxLayout, QGroupBox, QAbstractItemView
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
        self._ruin_rate = 0.20
        self.file_paths: list[str] = []
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        main_vbox = QVBoxLayout(central)

        # ファイル選択・リセットボタン
        btn_hbox = QHBoxLayout()
        self.btn_open = QPushButton("Excelファイルを開く")
        self.btn_open.clicked.connect(self.open_files)
        btn_hbox.addWidget(self.btn_open)
        self.btn_reset = QPushButton("全ファイルリセット")
        self.btn_reset.clicked.connect(self.reset_files)
        btn_hbox.addWidget(self.btn_reset)
        main_vbox.addLayout(btn_hbox)

        # 許容DDスライダー
        dd_box = QHBoxLayout()
        self.dd_label = QLabel(f"許容する最大DD: {int(self._ruin_rate * 100)} %")
        self.dd_slider = QSlider(Qt.Orientation.Horizontal)
        self.dd_slider.setMinimum(10)
        self.dd_slider.setMaximum(50)
        self.dd_slider.setValue(int(self._ruin_rate * 100))
        self.dd_slider.setTickInterval(1)
        self.dd_slider.valueChanged.connect(self.on_dd_slider_changed)
        self.dd_slider.setToolTip("左: 小さいDD許容 / 右: 大きいDD許容")
        dd_box.addWidget(self.dd_slider)
        dd_box.addWidget(self.dd_label)
        main_vbox.addLayout(dd_box)

        # チャート
        self.canvas = FigureCanvas(Figure(figsize=(6, 3)))
        self.ax = self.canvas.figure.subplots()
        # ←ここで初期時も背景を黒っぽく
        self.ax.set_facecolor("#282c34")
        self.canvas.figure.set_facecolor("#282c34")
        self.ax.set_title("Equity Curve", color="white")
        self.ax.tick_params(colors="white")
        self.ax.xaxis.label.set_color("white")
        self.ax.yaxis.label.set_color("white")
        for spine in self.ax.spines.values():
            spine.set_color("white")
        main_vbox.addWidget(self.canvas)

        # 指標テーブル
        self.table = QTableWidget()
        main_vbox.addWidget(self.table)

        # ファイル管理パネル
        file_group = QGroupBox("")
        file_vbox = QVBoxLayout(file_group)

        self.file_table = QTableWidget()
        self.file_table.setColumnCount(2)
        self.file_table.setHorizontalHeaderLabels(["ファイル名", "削除"])
        self.file_table.horizontalHeader().setStretchLastSection(True)
        self.file_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        file_vbox.addWidget(self.file_table)

        btn2_hbox = QHBoxLayout()
        self.btn_all_on = QPushButton("全ON")
        self.btn_all_on.clicked.connect(self.file_list_all_on)
        btn2_hbox.addWidget(self.btn_all_on)
        self.btn_all_off = QPushButton("全OFF")
        self.btn_all_off.clicked.connect(self.file_list_all_off)
        btn2_hbox.addWidget(self.btn_all_off)
        file_vbox.addLayout(btn2_hbox)

        self.btn_update = QPushButton("再計算（チェックのみ）")
        self.btn_update.clicked.connect(self.recalculate_metrics)
        file_vbox.addWidget(self.btn_update)
        main_vbox.addWidget(file_group)

        self.setCentralWidget(central)

        # ダークテーマQSS
        self.setStyleSheet("""
        QWidget { background: #232629; color: #eaeaea; font-size: 13px; }
        QPushButton {
            background: #35393e;
            border-radius: 5px;
            border: 1px solid #444;
            padding: 4px 8px;
        }
        QPushButton:hover { background: #44484e; }
        QTableWidget, QListWidget { background: #282c34; color: #eaeaea; }
        QHeaderView::section { background: #393e46; color: #eaeaea; }
        QSlider::groove:horizontal { background: #282c34; }
        QSlider::handle:horizontal { background: #eaeaea; }
        QGroupBox { border: 1px solid #35393e; margin-top: 8px; }
        """)

    def on_dd_slider_changed(self, value: int):
        self._ruin_rate = value / 100
        self.dd_label.setText(f"許容する最大DD: {value} %")
        self.recalculate_metrics()

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

    def refresh_file_list(self):
        self.file_table.setRowCount(len(self.file_paths))
        for i, path in enumerate(self.file_paths):
            file_name = Path(path).name
            item = QTableWidgetItem(file_name)
            item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            item.setCheckState(Qt.CheckState.Checked)
            item.setToolTip(str(path))
            self.file_table.setItem(i, 0, item)
            btn = QPushButton("🗑")
            btn.setStyleSheet("color: #e74c3c; background: transparent; border: none; font-size:18px;")
            btn.clicked.connect(lambda _, row=i: self.remove_file_row(row))
            self.file_table.setCellWidget(i, 1, btn)

    def remove_file_row(self, row):
        del self.file_paths[row]
        self.refresh_file_list()
        self.recalculate_metrics()

    def file_list_all_on(self):
        for i in range(self.file_table.rowCount()):
            self.file_table.item(i, 0).setCheckState(Qt.CheckState.Checked)
        self.recalculate_metrics()

    def file_list_all_off(self):
        for i in range(self.file_table.rowCount()):
            self.file_table.item(i, 0).setCheckState(Qt.CheckState.Unchecked)
        self.recalculate_metrics()

    def reset_files(self):
        self.file_paths.clear()
        self.file_table.setRowCount(0)
        self.clear_chart_and_metrics()

    def recalculate_metrics(self):
        checked_paths = self.get_checked_paths()
        if checked_paths:
            self.controller.load_files(checked_paths)
        else:
            self.clear_chart_and_metrics()

    def get_checked_paths(self) -> list[str]:
        return [
            self.file_paths[i]
            for i in range(self.file_table.rowCount())
            if self.file_table.item(i, 0).checkState() == Qt.CheckState.Checked
        ]

    # View 更新
    def clear_chart_and_metrics(self):
        self.ax.clear()
        # 背景・枠を常時ダークグレー
        self.ax.set_facecolor("#282c34")
        self.canvas.figure.set_facecolor("#282c34")
        self.ax.set_title("Equity Curve", color="white")
        self.ax.tick_params(colors="white")
        self.ax.xaxis.label.set_color("white")
        self.ax.yaxis.label.set_color("white")
        for spine in self.ax.spines.values():
            spine.set_color("white")
        self.canvas.draw()
        self.table.clearContents()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)

    def update_chart(self, equity):
        self.ax.clear()
        # ダークグレー背景を維持
        self.ax.set_facecolor("#282c34")
        self.canvas.figure.set_facecolor("#282c34")
        # 赤色でやや細めのライン（linewidth=1.3）
        self.ax.plot(equity.index, equity.values, color="#ff4444", linewidth=1.3)
        self.ax.set_title("Equity Curve", color="white")
        self.ax.tick_params(colors="white")
        self.ax.xaxis.label.set_color("white")
        self.ax.yaxis.label.set_color("white")
        for spine in self.ax.spines.values():
            spine.set_color("white")
        self.canvas.draw()

    def update_metrics(self, stats: dict):
        row_count, col_count = 5, 6
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

    def get_ruin_rate(self) -> float:
        return self._ruin_rate
