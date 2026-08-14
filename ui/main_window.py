"""主窗口（MainWindow）：控制面板 + 实时预览。"""

from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QWidget

from ui.panels.control_panel import ControlPanel
from ui.preview_widget import PreviewWidget


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AuroraMV")
        self.resize(1360, 780)

        central = QWidget(self)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.panel = ControlPanel(central)
        self.preview = PreviewWidget(central)
        layout.addWidget(self.panel)
        layout.addWidget(self.preview, 1)

        self.setCentralWidget(central)
