from PyQt6.QtWidgets import QMainWindow, QFileDialog, QWidget, QVBoxLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from ..controller import Controller

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Portfolio Analyzer")
        self.controller = Controller(self)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        layout = QVBoxLayout(central)

        self.btn_open = QPushButton("Excelファイルを開く")
        self.btn_open.clicked.connect(self.open_files)
        layout.addWidget(self.btn_open)

        self.canvas = FigureCanvas(Figure(figsize=(5, 3)))
        self.ax = self.canvas.figure.subplots()
        layout.addWidget(self.canvas)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Metric", "Value"])
        layout.addWidget(self.table)

        self.setCentralWidget(central)

    def open_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Excel Files", "", "Excel Files (*.xlsx)")
        if paths:
            self.controller.load_files(paths)

    # Callbacks from controller
    def update_chart(self, equity):
        self.ax.clear()
        self.ax.plot(equity.index, equity.values)
        self.ax.set_title("Equity Curve")
        self.canvas.draw()

    def update_metrics(self, stats: dict):
        self.table.setRowCount(len(stats))
        for row, (k, v) in enumerate(stats.items()):
            self.table.setItem(row, 0, QTableWidgetItem(k))
            self.table.setItem(row, 1, QTableWidgetItem(f"{v:.4f}"))

    def update_table(self, df):
        # Placeholder, could show trades preview
        pass
