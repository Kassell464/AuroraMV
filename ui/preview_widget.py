"""预览控件（PreviewWidget）。

宿主 OpenGL 表面，并把生命周期事件转发给 Renderer。
本控件不包含渲染逻辑：所有绘制都经由 Renderer API 完成
（对应架构规则 1：UI → Renderer API → OpenGL）。
"""

from __future__ import annotations

import time
from collections.abc import Callable

from PySide6.QtCore import QTimer
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QWidget

from core.audio.state import AudioState
from core.renderer.engine import Renderer

AudioStateProvider = Callable[[], AudioState]


class PreviewWidget(QOpenGLWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
        audio_state_provider: AudioStateProvider | None = None,
    ) -> None:
        super().__init__(parent)
        self.setMinimumSize(640, 360)

        # ModernGL 需要 OpenGL 3.3+ Core Profile
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        fmt.setDepthBufferSize(24)
        self.setFormat(fmt)

        self.renderer = Renderer()
        self._audio_state_provider = audio_state_provider
        self._start = time.perf_counter()

        self._timer = QTimer(self)
        self._timer.setInterval(16)  # 约 60 FPS
        self._timer.timeout.connect(self.update)
        self._timer.start()

    def set_audio_state_provider(self, provider: AudioStateProvider) -> None:
        """注入音频状态来源（阶段 3：AudioEngine.get_state）。"""
        self._audio_state_provider = provider

    def initializeGL(self) -> None:
        self.renderer.initialize()

    def paintGL(self) -> None:
        now = time.perf_counter() - self._start
        state = (
            self._audio_state_provider()
            if self._audio_state_provider is not None
            else None
        )
        self.renderer.update(now, state)
        self.renderer.render()

    def resizeGL(self, width: int, height: int) -> None:
        self.renderer.resize(width, height)
