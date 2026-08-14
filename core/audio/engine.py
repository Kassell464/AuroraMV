"""音频引擎（AudioEngine）。

职责（规格 14.1 节）：音频加载、音频播放同步、音频分析、提供实时 AudioState。
"""

from __future__ import annotations

import os
import time

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")  # 隐藏 pygame 启动提示

import pygame.mixer  # noqa: E402

from core.audio.analyzer import AudioAnalyzer, AudioLoadError
from core.audio.state import AudioState

__all__ = ["AudioEngine", "AudioLoadError"]


class AudioEngine:
    """负责音频加载、播放与实时状态同步。"""

    def __init__(self) -> None:
        self._analyzer = AudioAnalyzer()
        self._playing = False
        self._play_started_at = 0.0
        self._clock = time.monotonic

    @property
    def is_playing(self) -> bool:
        """是否正在播放。"""
        return self._playing

    def load(self, path: str) -> None:
        """加载并预分析音频；加载失败抛出 AudioLoadError。"""
        self.stop()
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        self._analyzer.load(path)
        pygame.mixer.music.load(path)

    def play(self) -> None:
        """开始播放。"""
        pygame.mixer.music.play()
        self._playing = True
        self._play_started_at = self._clock()

    def stop(self) -> None:
        """停止播放。"""
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
        self._playing = False

    def get_state(self) -> AudioState:
        """当前播放位置的 AudioState。"""
        position = 0.0
        if self._playing:
            position = pygame.mixer.music.get_pos() / 1000.0  # ms → s
            if position < 0:  # 部分后端可能返回 -1
                position = self._clock() - self._play_started_at
        return self._analyzer.get_state(position)
