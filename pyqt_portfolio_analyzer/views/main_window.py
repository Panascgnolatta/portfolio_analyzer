from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QMainWindow, QFileDialog, QWidget, QVBoxLayout, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QSlider, QHBoxLayout, QGroupBox, QAbstractItemView, QHeaderView,
    QStackedLayout
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from pathlib import Path
from ..controller import Controller


# ---------- ファイル一覧テーブル ----------
class FileTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["ファイル名", "削除"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)


# ---------- ドラッグ&ドロップ領域（ヒント + テーブル） ----------
class FileDropArea(QWidget):
    filesDropped = pyqtSignal(list)  # list[str]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

        self.stack = QStackedLayout(self)

        self.hint = QLabel("ここに .xlsx ファイルを\nドラッグ＆ドロップ\nまたは『Excelファイルを開く』")
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint.setStyleSheet("""
        QLabel {
            color:#888; border:1px dashed #555; padding:24px;
            background:#2a2d30; font-size:14px; border-radius:6px;
        }""")

        self.table = FileTable()
        self.stack.addWidget(self.hint)
        self.stack.addWidget(self.table)
        self.stack.setCurrentWidget(self.hint)

        self._highlight = "QWidget { border: 2px dashed #55aaff; border-radius:6px; }"
        self._normal = ""

    def show_hint(self): self.stack.setCurrentWidget(self.hint)
    def show_table(self): self.stack.setCurrentWidget(self.table)

    # ---- Drag & Drop events ----
    def dragEnterEvent(self, event):
        if self._contains_xlsx(event):
            event.acceptProposedAction()
            self.setStyleSheet(self._highlight)
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if self._contains_xlsx(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self._normal)

    def dropEvent(self, event):
        self.setStyleSheet(self._normal)
        if not self._contains_xlsx(event):
            event.ignore()
            return
        paths = []
        for url in event.mimeData().urls():
            local = url.toLocalFile()
            if local and local.lower().endswith(".xlsx"):
                paths.append(local)
        if paths:
            self.filesDropped.emit(paths)
        event.acceptProposedAction()

    def _contains_xlsx(self, event):
        if not event.mimeData().hasUrls():
            return False
        return any(u.toLocalFile().lower().endswith(".xlsx") for u in event.mimeData().urls())


# ---------- メインウィンドウ ----------
class MainWindow(QMainWindow):
    """メイン UI"""

    # モンテカルロ試行回数プリセット
    N_SIMS_PRESETS = [1000, 2000, 5000, 10000, 20000, 50000, 100000]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Portfolio Analyzer")
        self.controller = Controller(self)
        self._ruin_rate = 0.20          # 許容最大DD（比率）
        self._n_sims_index = 3          # 初期 10,000 回
        self.file_paths: list[str] = []
        self._build_ui()

    # ---------- UI構築 ----------
    def _build_ui(self):
        central = QWidget()
        main_vbox = QVBoxLayout(central)
        self.statusBar().showMessage("Ready")

        # (1) ファイル操作
        top_box = QHBoxLayout()
        self.btn_open = QPushButton("Excelファイルを開く")
        self.btn_open.clicked.connect(self.open_files)
        top_box.addWidget(self.btn_open)

        self.btn_reset = QPushButton("全ファイルリセット")
        self.btn_reset.clicked.connect(self.reset_files)
        top_box.addWidget(self.btn_reset)
        main_vbox.addLayout(top_box)

        # (2) 許容DDスライダー
        dd_box = QHBoxLayout()
        self.dd_label = QLabel(f"許容する最大DD: {int(self._ruin_rate * 100)} %")
        self.dd_slider = QSlider(Qt.Orientation.Horizontal)
        self.dd_slider.setMinimum(10)
        self.dd_slider.setMaximum(50)
        self.dd_slider.setValue(int(self._ruin_rate * 100))
        self.dd_slider.setTickInterval(1)
        self.dd_slider.valueChanged.connect(self.on_dd_slider_changed)
        dd_box.addWidget(QLabel("最大DD"))
        dd_box.addWidget(self.dd_slider)
        dd_box.addWidget(self.dd_label)
        main_vbox.addLayout(dd_box)

        # (3) MonteCarlo 試行回数スライダー
        sims_box = QHBoxLayout()
        self.sims_slider = QSlider(Qt.Orientation.Horizontal)
        self.sims_slider.setMinimum(0)
        self.sims_slider.setMaximum(len(self.N_SIMS_PRESETS) - 1)
        self.sims_slider.setValue(self._n_sims_index)
        self.sims_slider.setTickInterval(1)
        self.sims_slider.setSingleStep(1)
        self.sims_slider.valueChanged.connect(self.on_sims_slider_changed)
        self.sims_label = QLabel(self._format_sims_label())
        sims_box.addWidget(QLabel("MonteCarlo"))
        sims_box.addWidget(self.sims_slider)
        sims_box.addWidget(self.sims_label)
        main_vbox.addLayout(sims_box)

        # (4) チャート
        self.canvas = FigureCanvas(Figure(figsize=(6, 3)))
        self.ax = self.canvas.figure.subplots()
        self._init_chart_appearance()
        main_vbox.addWidget(self.canvas)

        # (5) 指標テーブル
        self.table = QTableWidget()
        main_vbox.addWidget(self.table)

        # (6) ファイル管理
        file_group = QGroupBox("")
        file_vbox = QVBoxLayout(file_group)

        self.drop_area = FileDropArea()
        self.drop_area.filesDropped.connect(self.on_files_dropped)
        file_vbox.addWidget(self.drop_area)

        onoff_box = QHBoxLayout()
        self.btn_all_on = QPushButton("全ON")
        self.btn_all_on.clicked.connect(self.file_list_all_on)
        onoff_box.addWidget(self.btn_all_on)

        self.btn_all_off = QPushButton("全OFF")
        self.btn_all_off.clicked.connect(self.file_list_all_off)
        onoff_box.addWidget(self.btn_all_off)
        file_vbox.addLayout(onoff_box)

        self.btn_update = QPushButton("再計算（チェックのみ）")
        self.btn_update.clicked.connect(self.recalculate_metrics)
        file_vbox.addWidget(self.btn_update)

        main_vbox.addWidget(file_group)
        self.setCentralWidget(central)

        # (7) ダークテーマ
        self.setStyleSheet("""
        QWidget { background: #232629; color: #eaeaea; font-size: 13px; }
        QPushButton {
            background: #35393e; border-radius: 5px; border: 1px solid #444;
            padding: 4px 10px;
        }
        QPushButton:hover { background: #44484e; }
        QTableWidget { background: #282c34; color: #eaeaea; }
        QHeaderView::section { background: #393e46; color: #eaeaea; }
        QSlider::groove:horizontal { background: #282c34; height:6px; }
        QSlider::handle:horizontal { background: #eaeaea; width:14px; }
        QGroupBox { border: 1px solid #35393e; margin-top: 8px; }
        """)

    # ---------- チャート外観 ----------
    def _init_chart_appearance(self):
        self.ax.set_facecolor("#282c34")
        self.canvas.figure.set_facecolor("#282c34")
        self.ax.set_title("Equity Curve", color="white")
        self.ax.tick_params(colors="white")
        for spine in self.ax.spines.values():
            spine.set_color("white")

    # ---------- スライダー変更 ----------
    def on_dd_slider_changed(self, value: int):
        self._ruin_rate = value / 100
        self.dd_label.setText(f"許容する最大DD: {value} %")
        self.recalculate_metrics()

    def on_sims_slider_changed(self, value: int):
        self._n_sims_index = value
        self.sims_label.setText(self._format_sims_label())
        # 重い場合は次行をコメントアウトし「再計算」ボタン運用へ
        self.recalculate_metrics()

    def _format_sims_label(self):
        n = self.get_n_sims()
        step = 100 / n
        return f"{n:,} 回 (刻み≈{step:.3f}%)"

    # ---------- ファイル操作 ----------
    def open_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Excel Files", "", "Excel Files (*.xlsx)"
        )
        if paths:
            self._append_files(paths)

    def on_files_dropped(self, paths: list[str]):
        self._append_files(paths)

    def _append_files(self, paths: list[str]):
        added = 0
        for p in paths:
            if p not in self.file_paths and p.lower().endswith(".xlsx"):
                self.file_paths.append(p)
                added += 1
        if added:
            self.refresh_file_list()
            self.recalculate_metrics()
            self.statusBar().showMessage(f"{added} file(s) added")
        else:
            self.statusBar().showMessage("No new files added")

    def refresh_file_list(self):
        table = self.drop_area.table
        table.setRowCount(len(self.file_paths))
        for i, path in enumerate(self.file_paths):
            file_name = Path(path).name
            item = QTableWidgetItem(file_name)
            item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            item.setCheckState(Qt.CheckState.Checked)
            item.setToolTip(str(path))
            table.setItem(i, 0, item)

            btn = QPushButton("🗑")
            btn.setStyleSheet("color:#e74c3c; background:transparent; border:none; font-size:16px;")
            btn.clicked.connect(lambda _, row=i: self.remove_file_row(row))
            table.setCellWidget(i, 1, btn)

        if len(self.file_paths) == 0:
            self.drop_area.show_hint()
        else:
            self.drop_area.show_table()

    def remove_file_row(self, row: int):
        if 0 <= row < len(self.file_paths):
            del self.file_paths[row]
            self.refresh_file_list()
            self.recalculate_metrics()
            self.statusBar().showMessage("File removed")

    def file_list_all_on(self):
        t = self.drop_area.table
        for i in range(t.rowCount()):
            t.item(i, 0).setCheckState(Qt.CheckState.Checked)
        self.recalculate_metrics()

    def file_list_all_off(self):
        t = self.drop_area.table
        for i in range(t.rowCount()):
            t.item(i, 0).setCheckState(Qt.CheckState.Unchecked)
        self.recalculate_metrics()

    def reset_files(self):
        self.file_paths.clear()
        self.drop_area.table.setRowCount(0)
        self.clear_chart_and_metrics()
        self.drop_area.show_hint()
        self.statusBar().showMessage("All files cleared")

    # ---------- 再計算 ----------
    def recalculate_metrics(self):
        paths = self.get_checked_paths()
        if paths:
            self.controller.load_files(paths)
        else:
            self.clear_chart_and_metrics()

    def get_checked_paths(self) -> list[str]:
        t = self.drop_area.table
        return [
            self.file_paths[i]
            for i in range(t.rowCount())
            if t.item(i, 0).checkState() == Qt.CheckState.Checked
        ]

    # ---------- View 更新 ----------
    def clear_chart_and_metrics(self):
        self.ax.clear()
        self._init_chart_appearance()
        self.canvas.draw()
        self.table.clearContents()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)

    def update_chart(self, equity):
        self.ax.clear()
        self._init_chart_appearance()
        self.ax.plot(equity.index, equity.values, color="#ff4444", linewidth=1.3)
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
                # "Step" と "CI" はそのまま数値表示（%記号はキーに含めていない）
                display = f"{v:.2f}"
            else:
                display = str(v)
            self.table.setItem(row, col + 1, QTableWidgetItem(display))

    # ---------- Getter ----------
    def get_ruin_rate(self) -> float:
        return self._ruin_rate

    def get_n_sims(self) -> int:
        return self.N_SIMS_PRESETS[self._n_sims_index]
