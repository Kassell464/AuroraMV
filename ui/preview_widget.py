"""预览控件（PreviewWidget）。

宿主 OpenGL 表面，并把生命周期事件转发给 Renderer。
本控件不包含渲染逻辑：所有绘制都经由 Renderer API 完成
（对应架构规则 1：UI → Renderer API → OpenGL）。
"""

from __future__ import annotations

import time
from collections.abc import Callable

import numpy as np
import numpy.typing as npt

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QWidget

from core.audio.state import AudioState
from core.renderer.engine import Renderer

AudioStateProvider = Callable[[], AudioState]
WaveformProvider = Callable[[int], npt.NDArray[np.float32]]


class PreviewWidget(QOpenGLWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
        audio_state_provider: AudioStateProvider | None = None,
        waveform_provider: WaveformProvider | None = None,
    ) -> None:
        super().__init__(parent)
        self.setMinimumSize(640, 360)
        # QOpenGLWidget 不支持样式表背景（Qt 已知限制）：
        # 禁止样式背景绘制，避免全局 QSS 覆盖渲染内容。
        self.setAttribute(Qt.WA_StyledBackground, False)

        # ModernGL 需要 OpenGL 3.3+ Core Profile
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        fmt.setDepthBufferSize(24)
        self.setFormat(fmt)

        self.renderer = Renderer()
        self._audio_state_provider = audio_state_provider
        self._waveform_provider = waveform_provider
        if waveform_provider is not None:
            self.renderer.set_waveform_provider(waveform_provider)
        self._start = time.perf_counter()

        self._timer = QTimer(self)
        self._timer.setInterval(16)  # 约 60 FPS
        self._timer.timeout.connect(self.update)
        self._timer.start()

    def set_audio_state_provider(self, provider: AudioStateProvider) -> None:
        """注入音频状态来源（阶段 3：AudioEngine.get_state）。"""
        self._audio_state_provider = provider

    def set_waveform_provider(self, provider: WaveformProvider) -> None:
        """注入波形采样来源（阶段 4：AudioEngine.get_waveform）。"""
        self._waveform_provider = provider
        self.renderer.set_waveform_provider(provider)

    def set_spectrum_provider(self, provider: WaveformProvider) -> None:
        """注入频谱来源（音域回响背景用）。"""
        self.renderer.set_spectrum_provider(provider)

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
        # QOpenGLWidget 渲染进它的内部 FBO（而非帧缓冲 0）：
        # 每帧把 Qt 的默认帧缓冲包装成渲染目标，否则最终合成会画错地方（黑屏）。
        target = None
        if self.renderer.ctx is not None:
            target = self.renderer.ctx.detect_framebuffer()
        self.renderer.render(target=target)

    def resizeGL(self, width: int, height: int) -> None:
        # 使用物理像素（含设备像素比）：Qt 内部帧缓冲按物理像素分配，
        # 尺寸不一致时画面只会铺满左下角。
        scale = self.devicePixelRatioF()
        self.renderer.resize(max(1, int(width * scale)), max(1, int(height * scale)))
