from PyQt6.QtCore import Qt, pyqtSignal, QSignalBlocker
from PyQt6.QtWidgets import (
    QMainWindow, QFileDialog, QWidget, QVBoxLayout, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QSlider, QHBoxLayout, QGroupBox, QAbstractItemView, QHeaderView,
    QStackedLayout, QDoubleSpinBox, QSpinBox
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from pathlib import Path
from ..controller import Controller

# ---------- 翻訳辞書 ----------
TRANSLATIONS = {
    "ja": {
        "CAGR (%)":"CAGR (%)","Max Drawdown (%)":"最大ドローダウン (%)","Sharpe Ratio":"シャープレシオ",
        "Sortino Ratio":"ソルティノレシオ","Profit Factor":"プロフィットファクター","Expectancy":"期待値",
        "Payoff Ratio":"ペイオフレシオ","Win Rate (%)":"勝率 (%)","Avg Win":"平均利益","Avg Loss":"平均損失",
        "Max Win Streak":"最大連勝","Max Lose Streak":"最大連敗","Trade Count":"トレード数",
        "Risk of Ruin (%)":"破産確率 (%)","RoR Step (%)":"刻み幅 (%)","RoR 95% CI (±%)":"95%信頼区間 (±%)",
        "Excelファイルを開く":"Excelファイルを開く","Open Excel Files":"Excelファイルを開く",
        "全ファイルリセット":"全ファイルリセット","Reset All":"全ファイルリセット",
        "最大DD":"最大DD","Max DD":"最大DD","許容する最大DD:":"許容する最大DD:","Max DD Allowed:":"許容する最大DD:",
        "MonteCarlo":"モンテカルロ","再計算（チェックのみ）":"再計算（チェックのみ）","Recalculate (checked)":"再計算（チェックのみ）",
        "全ON":"全ON","All ON":"全ON","全OFF":"全OFF","All OFF":"全OFF",
        "ここに .xlsx ファイルを\nドラッグ＆ドロップ\nまたは『Excelファイルを開く』":"ここに .xlsx ファイルを\nドラッグ＆ドロップ\nまたは『Excelファイルを開く』",
        "Drop .xlsx files here\nor click 'Open Excel Files'":"ここに .xlsx ファイルを\nドラッグ＆ドロップ\nまたは『Excelファイルを開く』",
        "Equity Curve":"エクイティカーブ","エクイティカーブ":"エクイティカーブ",
        "ファイル名":"ファイル名","File Name":"ファイル名","削除":"削除","Remove":"削除",
        "Ready":"準備完了","準備完了":"準備完了","file(s) added":"件追加","No new files added":"新規ファイルなし",
        "File removed":"ファイル削除","All files cleared":"全ファイルをクリア"
    },
    "en": {
        "CAGR (%)":"CAGR (%)","最大ドローダウン (%)":"Max Drawdown (%)","Max Drawdown (%)":"Max Drawdown (%)",
        "シャープレシオ":"Sharpe Ratio","ソルティノレシオ":"Sortino Ratio","プロフィットファクター":"Profit Factor",
        "期待値":"Expectancy","ペイオフレシオ":"Payoff Ratio","勝率 (%)":"Win Rate (%)",
        "平均利益":"Avg Win","平均損失":"Avg Loss","最大連勝":"Max Win Streak","最大連敗":"Max Lose Streak",
        "トレード数":"Trade Count","破産確率 (%)":"Risk of Ruin (%)","刻み幅 (%)":"RoR Step (%)",
        "95%信頼区間 (±%)":"RoR 95% CI (±%)",
        "Excelファイルを開く":"Open Excel Files","全ファイルリセット":"Reset All",
        "最大DD":"Max DD","許容する最大DD:":"Max DD Allowed:","モンテカルロ":"MonteCarlo",
        "再計算（チェックのみ）":"Recalculate (checked)","全ON":"All ON","全OFF":"All OFF",
        "ここに .xlsx ファイルを\nドラッグ＆ドロップ\nまたは『Excelファイルを開く』":"Drop .xlsx files here\nor click 'Open Excel Files'",
        "エクイティカーブ":"Equity Curve","ファイル名":"File Name","削除":"Remove",
        "準備完了":"Ready","件追加":"file(s) added","新規ファイルなし":"No new files added",
        "ファイル削除":"File removed","全ファイルをクリア":"All files cleared"
    }
}


# ---------- ファイル一覧テーブル ----------
class FileTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(2)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)


# ---------- ドラッグ&ドロップ領域 ----------
class FileDropArea(QWidget):
    filesDropped = pyqtSignal(list)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.stack = QStackedLayout(self)
        self.hint = QLabel()
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint.setStyleSheet("""
        QLabel { color:#888; border:1px dashed #555; padding:24px;
                 background:#2a2d30; font-size:14px; border-radius:6px; }""")
        self.table = FileTable()
        self.stack.addWidget(self.hint)
        self.stack.addWidget(self.table)
        self.stack.setCurrentWidget(self.hint)
        self._highlight = "QWidget { border: 2px dashed #55aaff; border-radius:6px; }"
        self._normal = ""

    def show_hint(self): self.stack.setCurrentWidget(self.hint)
    def show_table(self): self.stack.setCurrentWidget(self.table)

    def dragEnterEvent(self, event):
        if self._contains_xlsx(event):
            event.acceptProposedAction()
            self.setStyleSheet(self._highlight)
        else:
            event.ignore()
    def dragMoveEvent(self, event):
        if self._contains_xlsx(event): event.acceptProposedAction()
        else: event.ignore()
    def dragLeaveEvent(self, event): self.setStyleSheet(self._normal)
    def dropEvent(self, event):
        self.setStyleSheet(self._normal)
        if not self._contains_xlsx(event):
            event.ignore(); return
        paths = []
        for url in event.mimeData().urls():
            local = url.toLocalFile()
            if local.lower().endswith(".xlsx"):
                paths.append(local)
        if paths: self.filesDropped.emit(paths)
        event.acceptProposedAction()
    def _contains_xlsx(self,event):
        if not event.mimeData().hasUrls(): return False
        return any(u.toLocalFile().lower().endswith(".xlsx") for u in event.mimeData().urls())


# ---------- メインウィンドウ ----------
class MainWindow(QMainWindow):
    N_SIMS_PRESETS = [1000, 2000, 5000, 10000, 20000, 50000, 100000]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Portfolio Analyzer")
        self.controller = Controller(self)
        self.lang = "ja"  # 'ja' or 'en'
        self._ruin_rate = 0.20
        self._n_sims_index = 3
        self.file_paths: list[str] = []
        self._building = False
        self._build_ui()

    # ---------- 翻訳ヘルパ ----------
    def tr_key(self, text: str) -> str:
        # 現在言語辞書で解決（なければそのまま）
        d = TRANSLATIONS.get(self.lang, {})
        return d.get(text, text)

    # ---------- UI構築 ----------
    def _build_ui(self):
        self._building = True
        central = QWidget()
        main_vbox = QVBoxLayout(central)
        self.statusBar().showMessage(self.tr_key("Ready"))

        # 言語切替ボタン
        lang_box = QHBoxLayout()
        self.language_button = QPushButton("🌐 EN")
        self.language_button.clicked.connect(self.toggle_language)
        lang_box.addWidget(self.language_button)
        lang_box.addStretch()
        main_vbox.addLayout(lang_box)

        # (1) ファイル操作
        top_box = QHBoxLayout()
        self.btn_open = QPushButton()
        self.btn_open.clicked.connect(self.open_files)
        top_box.addWidget(self.btn_open)
        self.btn_reset = QPushButton()
        self.btn_reset.clicked.connect(self.reset_files)
        top_box.addWidget(self.btn_reset)
        main_vbox.addLayout(top_box)

        # (2) 最大DD
        dd_box = QHBoxLayout()
        self.dd_caption = QLabel()
        dd_box.addWidget(self.dd_caption)
        self.dd_slider = QSlider(Qt.Orientation.Horizontal)
        self.dd_slider.setRange(0, 100)
        self.dd_slider.setValue(int(self._ruin_rate * 100))
        self.dd_slider.setTickInterval(5)
        self.dd_slider.valueChanged.connect(self.on_dd_slider_changed)
        self.dd_spin = QDoubleSpinBox()
        self.dd_spin.setRange(0.0, 100.0)
        self.dd_spin.setDecimals(1)
        self.dd_spin.setSingleStep(0.5)
        self.dd_spin.setValue(self._ruin_rate * 100)
        self.dd_spin.valueChanged.connect(self.on_dd_spin_changed)
        self.dd_label = QLabel()
        dd_box.addWidget(self.dd_slider, stretch=1)
        dd_box.addWidget(self.dd_spin)
        dd_box.addWidget(self.dd_label)
        main_vbox.addLayout(dd_box)

        # (3) MonteCarlo
        sims_box = QHBoxLayout()
        self.sims_caption = QLabel()
        sims_box.addWidget(self.sims_caption)
        self.sims_slider = QSlider(Qt.Orientation.Horizontal)
        self.sims_slider.setRange(0, len(self.N_SIMS_PRESETS) - 1)
        self.sims_slider.setValue(self._n_sims_index)
        self.sims_slider.valueChanged.connect(self.on_sims_slider_changed)
        self.sims_spin = QSpinBox()
        self.sims_spin.setRange(100, 500_000)
        self.sims_spin.setSingleStep(100)
        self.sims_spin.setValue(self.N_SIMS_PRESETS[self._n_sims_index])
        self.sims_spin.valueChanged.connect(self.on_sims_spin_changed)
        self.sims_label = QLabel()
        sims_box.addWidget(self.sims_slider, stretch=1)
        sims_box.addWidget(self.sims_spin)
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
        self.btn_all_on = QPushButton()
        self.btn_all_on.clicked.connect(self.file_list_all_on)
        onoff_box.addWidget(self.btn_all_on)
        self.btn_all_off = QPushButton()
        self.btn_all_off.clicked.connect(self.file_list_all_off)
        onoff_box.addWidget(self.btn_all_off)
        file_vbox.addLayout(onoff_box)

        self.btn_update = QPushButton()
        self.btn_update.clicked.connect(self.recalculate_metrics)
        file_vbox.addWidget(self.btn_update)

        main_vbox.addWidget(file_group)
        self.setCentralWidget(central)

        # ダークテーマ
        self.setStyleSheet("""
        QWidget { background: #232629; color: #eaeaea; font-size: 13px; }
        QPushButton {
            background: #35393e; border-radius: 5px; border: 1px solid #444; padding: 4px 10px;
        }
        QPushButton:hover { background: #44484e; }
        QTableWidget { background: #282c34; color: #eaeaea; }
        QHeaderView::section { background: #393e46; color: #eaeaea; }
        QSlider::groove:horizontal { background: #282c34; height:6px; }
        QSlider::handle:horizontal { background: #eaeaea; width:14px; }
        """)

        # 最初の翻訳適用
        self._building = False
        self.retranslate_ui()

    # ---------- 言語切替 ----------
    def toggle_language(self):
        self.lang = "en" if self.lang == "ja" else "ja"
        self.retranslate_ui()
        # テーブル再描画
        self.recalculate_metrics()

    def retranslate_ui(self):
        # ボタン/ラベル
        self.language_button.setText("🌐 JP" if self.lang == "en" else "🌐 EN")
        self.btn_open.setText(self.tr_key("Excelファイルを開く"))
        self.btn_reset.setText(self.tr_key("全ファイルリセット"))
        self.dd_caption.setText(self.tr_key("最大DD"))
        self.sims_caption.setText(self.tr_key("MonteCarlo"))
        self.btn_all_on.setText(self.tr_key("全ON"))
        self.btn_all_off.setText(self.tr_key("全OFF"))
        self.btn_update.setText(self.tr_key("再計算（チェックのみ）"))

        # ステータスバー（翻訳できるなら）
        current_msg = self.statusBar().currentMessage()
        self.statusBar().showMessage(self.tr_key(current_msg))

        # ドロップヒント
        self.drop_area.hint.setText(self.tr_key("ここに .xlsx ファイルを\nドラッグ＆ドロップ\nまたは『Excelファイルを開く』"))

        # DDラベル / MonteCarloラベル
        self.dd_label.setText(f"{self.tr_key('許容する最大DD:')}{self.dd_spin.value():.1f} %")
        self.sims_label.setText(self._format_sims_label())

        # チャートタイトル
        self.ax.set_title(self.tr_key("Equity Curve"), color="white")
        self.canvas.draw()

        # テーブルヘッダは update_metrics で再設定（呼び出し先で翻訳）

    # ---------- チャート外観 ----------
    def _init_chart_appearance(self):
        self.ax.set_facecolor("#282c34")
        self.canvas.figure.set_facecolor("#282c34")
        self.ax.tick_params(colors="white")
        for spine in self.ax.spines.values():
            spine.set_color("white")

    # ---------- スライダー/Spin 同期 ----------
    def on_dd_slider_changed(self, value: int):
        if self._building: return
        with QSignalBlocker(self.dd_spin):
            self.dd_spin.setValue(float(value))
        self._ruin_rate = value / 100.0
        self.dd_label.setText(f"{self.tr_key('許容する最大DD:')}{value:.1f} %")
        self.recalculate_metrics()

    def on_dd_spin_changed(self, value: float):
        if self._building: return
        with QSignalBlocker(self.dd_slider):
            self.dd_slider.setValue(int(round(value)))
        self._ruin_rate = value / 100.0
        self.dd_label.setText(f"{self.tr_key('許容する最大DD:')}{value:.1f} %")
        self.recalculate_metrics()

    def on_sims_slider_changed(self, idx: int):
        if self._building: return
        idx = max(0, min(idx, len(self.N_SIMS_PRESETS)-1))
        self._n_sims_index = idx
        preset = self.N_SIMS_PRESETS[idx]
        with QSignalBlocker(self.sims_spin):
            self.sims_spin.setValue(preset)
        self.sims_label.setText(self._format_sims_label())
        self.recalculate_metrics()

    def on_sims_spin_changed(self, val: int):
        if self._building: return
        diffs = [abs(val - p) for p in self.N_SIMS_PRESETS]
        nearest = diffs.index(min(diffs))
        with QSignalBlocker(self.sims_slider):
            self.sims_slider.setValue(nearest)
        self._n_sims_index = nearest
        self.sims_label.setText(self._format_sims_label())
        self.recalculate_metrics()

    def _format_sims_label(self):
        n = self.get_n_sims()
        step = 100 / n
        base = f"{n:,} {self.tr_key('回') if self.lang=='ja' else 'runs'} (Δ≈{step:.3f}%)"
        return base

    # ---------- ファイル操作 ----------
    def open_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, self.tr_key("Excelファイルを開く"), "", "Excel Files (*.xlsx)"
        )
        if paths: self._append_files(paths)

    def on_files_dropped(self, paths: list[str]):
        self._append_files(paths)

    def _append_files(self, paths: list[str]):
        added = 0
        for p in paths:
            if p not in self.file_paths and p.lower().endswith(".xlsx"):
                self.file_paths.append(p); added += 1
        if added:
            self.refresh_file_list()
            self.recalculate_metrics()
            self.statusBar().showMessage(f"{added} {self.tr_key('file(s) added')}")
        else:
            self.statusBar().showMessage(self.tr_key("No new files added"))

    def refresh_file_list(self):
        table = self.drop_area.table
        table.setRowCount(len(self.file_paths))
        # ヘッダ翻訳
        table.setHorizontalHeaderLabels([self.tr_key("ファイル名"), self.tr_key("削除")])
        for i, path in enumerate(self.file_paths):
            item = QTableWidgetItem(Path(path).name)
            item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            item.setCheckState(Qt.CheckState.Checked)
            item.setToolTip(str(path))
            table.setItem(i, 0, item)
            btn = QPushButton("🗑")
            btn.setStyleSheet("color:#e74c3c; background:transparent; border:none; font-size:16px;")
            btn.clicked.connect(lambda _, row=i: self.remove_file_row(row))
            table.setCellWidget(i, 1, btn)
        if len(self.file_paths)==0: self.drop_area.show_hint()
        else: self.drop_area.show_table()

    def remove_file_row(self, row: int):
        if 0 <= row < len(self.file_paths):
            del self.file_paths[row]
            self.refresh_file_list()
            self.recalculate_metrics()
            self.statusBar().showMessage(self.tr_key("File removed"))

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
        self.statusBar().showMessage(self.tr_key("All files cleared"))

    # ---------- 再計算 ----------
    def recalculate_metrics(self):
        paths = self.get_checked_paths()
        if paths:
            self.controller.load_files(paths)
        else:
            self.clear_chart_and_metrics()

    def get_checked_paths(self):
        t = self.drop_area.table
        return [
            self.file_paths[i]
            for i in range(t.rowCount())
            if t.item(i,0).checkState() == Qt.CheckState.Checked
        ]

    # ---------- View 更新 ----------
    def clear_chart_and_metrics(self):
        self.ax.clear()
        self._init_chart_appearance()
        self.ax.set_title(self.tr_key("Equity Curve"), color="white")
        self.canvas.draw()
        self.table.clearContents()
        self.table.setRowCount(0); self.table.setColumnCount(0)

    def update_chart(self, equity):
        self.ax.clear()
        self._init_chart_appearance()
        self.ax.set_title(self.tr_key("Equity Curve"), color="white")
        self.ax.plot(equity.index, equity.values, color="#ff4444", linewidth=1.2)
        self.canvas.draw()

    def update_metrics(self, stats: dict):
        row_count, col_count = 5, 6
        self.table.setRowCount(row_count)
        self.table.setColumnCount(col_count)
        # 3ブロック * (Metric, Value)
        headers = []
        for _ in range(3):
            headers.extend([self.tr_key("Metric") if self.lang=="en" else self.tr_key("指標") if self.lang=="ja" else "Metric",
                            self.tr_key("Value") if self.lang=="en" else self.tr_key("値") if self.lang=="ja" else "Value"])
        self.table.setHorizontalHeaderLabels(headers)

        self.table.clearContents()
        for idx, (k, v) in enumerate(stats.items()):
            row = idx % row_count
            col = (idx // row_count) * 2
            if col >= col_count: continue
            disp_key = self.tr_key(k)
            self.table.setItem(row, col, QTableWidgetItem(disp_key))
            if isinstance(v, (int,float)):
                display = f"{v:.2f}"
            else:
                display = str(v)
            self.table.setItem(row, col+1, QTableWidgetItem(display))

    # ---------- Getter ----------
    def get_ruin_rate(self) -> float:
        return self._ruin_rate
    def get_n_sims(self) -> int:
        return int(self.sims_spin.value())
