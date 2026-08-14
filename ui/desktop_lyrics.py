"""桌面歌词小窗（第二批：MineRadio 概念灵感，原创实现）。

独立无边框、置顶、半透明小窗，实时显示当前歌词行，
文字颜色跟随当前歌词模板（与预览内歌词一致），不抢焦点、可拖动。
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class DesktopLyricsWindow(QWidget):
    """置顶半透明桌面歌词小窗。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            parent,
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowDoesNotAcceptFocus,
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(680, 132)
        self.setStyleSheet(
            "background-color: rgba(10, 12, 20, 175);"
            "border-radius: 20px;"
            "border: 1px solid rgba(120, 150, 255, 80);"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        self.label = QLabel("♪", self)
        self.label.setAlignment(Qt.AlignCenter)
        self._apply_text_style((1.0, 1.0, 1.0))
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(0, 0, 0, 210))
        self.label.setGraphicsEffect(shadow)
        layout.addWidget(self.label)

        self._drag_offset: QPoint | None = None

    def _apply_text_style(self, color: tuple[float, float, float]) -> None:
        r, g, b = (max(0, min(255, int(c * 255))) for c in color)
        self.label.setStyleSheet(
            "background: transparent; border: none;"
            "font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;"
            "font-size: 32px; font-weight: 600;"
            f"color: rgb({r}, {g}, {b});"
        )

    def set_lyric(self, text: str, color: tuple[float, float, float]) -> None:
        """更新当前歌词与颜色（颜色跟随歌词模板）。"""
        self.label.setText(text or "♪")
        self._apply_text_style(color)

    # ---------- 拖动 ----------

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            self._drag_offset = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._drag_offset = None
        super().mouseReleaseEvent(event)
