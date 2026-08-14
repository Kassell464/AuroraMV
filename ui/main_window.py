"""主窗口（MainWindow）：左侧控制面板 + 右侧预览与播放底栏。"""

from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QVBoxLayout, QWidget

from ui.panels.control_panel import ControlPanel
from ui.panels.player_bar import PlayerBar
from ui.preview_widget import PreviewWidget


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AuroraMV")
        self.resize(1360, 800)

        central = QWidget(self)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.panel = ControlPanel(central)

        right = QWidget(central)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        self.preview = PreviewWidget(right)
        self.bar = PlayerBar(right)
        right_layout.addWidget(self.preview, 1)
        right_layout.addWidget(self.bar)

        layout.addWidget(self.panel)
        layout.addWidget(right, 1)
        self.setCentralWidget(central)
