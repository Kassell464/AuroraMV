"""主窗口（MainWindow）。"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from ui.preview_widget import PreviewWidget


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AuroraMV")
        self.resize(1280, 720)

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.preview = PreviewWidget(central)
        self.controls = QLabel("[控件]", central)
        self.controls.setAlignment(Qt.AlignCenter)
        self.controls.setMinimumHeight(48)
        self.controls.setStyleSheet("background-color: #1a1a20; color: #8a8a94;")

        layout.addWidget(self.preview, 1)
        layout.addWidget(self.controls, 0)

        self.setCentralWidget(central)
