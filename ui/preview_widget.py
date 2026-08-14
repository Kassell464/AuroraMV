"""预览控件（PreviewWidget）。

阶段 1 中仅作占位显示「[预览区域]」。
后续阶段将在此接入 OpenGL 渲染输出（经 Renderer API，而非直接调用 OpenGL）。
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PreviewWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(640, 360)
        self.setStyleSheet("background-color: #101014;")

        layout = QVBoxLayout(self)
        self.label = QLabel("[预览区域]", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: #6a6a76; border: none;")
        layout.addWidget(self.label)
