"""音频引擎（AudioEngine）。

职责（规格 14.1 节）：音频加载、音频播放同步、音频分析、提供实时 AudioState。
"""

from __future__ import annotations

import os
import time

import numpy.typing as npt

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
        self._paused = False
        self._play_started_at = 0.0
        self._seek_origin = 0.0
        self._clock = time.monotonic

    @property
    def is_playing(self) -> bool:
        """是否正在播放。"""
        return self._playing

    @property
    def is_paused(self) -> bool:
        """是否处于暂停状态。"""
        return self._paused

    @property
    def duration(self) -> float:
        """已加载音频时长（秒）。"""
        return self._analyzer.duration

    @property
    def position(self) -> float:
        """当前播放位置（秒）。"""
        return self._position()

    def seek(self, seconds: float) -> None:
        """跳转到指定位置并继续播放（进度条拖动）。"""
        seconds = max(0.0, min(seconds, self.duration))
        pygame.mixer.music.play(0, start=seconds)
        self._playing = True
        self._paused = False
        self._play_started_at = self._clock()
        self._seek_origin = seconds

    def load(self, path: str) -> None:
        """加载并预分析音频；加载失败抛出 AudioLoadError。"""
        self.stop()
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        self._analyzer.load(path)
        pygame.mixer.music.load(path)

    def play(self) -> None:
        """继续播放：暂停中则续播，否则从头播放。"""
        if self._paused:
            pygame.mixer.music.unpause()
            self._paused = False
            self._playing = True
            return
        pygame.mixer.music.play()
        self._playing = True
        self._play_started_at = self._clock()
        self._seek_origin = 0.0

    def pause(self) -> None:
        """暂停播放（保持位置，可续播）。"""
        if self._playing:
            pygame.mixer.music.pause()
        self._paused = True
        self._playing = False

    def stop(self) -> None:
        """停止播放（位置归零）。"""
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
        self._playing = False
        self._paused = False
        self._seek_origin = 0.0

    def get_state(self) -> AudioState:
        """当前播放位置的 AudioState。"""
        return self._analyzer.get_state(self._position())

    def get_waveform(self, n: int) -> npt.NDArray[np.float32]:
        """当前播放位置往前 n 个波形采样（可视化背景用）。"""
        return self._analyzer.get_waveform(self._position(), n)

    def get_spectrum(self, n: int = 64) -> npt.NDArray[np.float32]:
        """当前播放位置的频谱（对数频段，可视化背景用）。"""
        return self._analyzer.get_spectrum(self._position(), n)

    def _position(self) -> float:
        if not (self._playing or self._paused):
            return 0.0
        if self._playing and not pygame.mixer.music.get_busy():
            # 自然播放结束（非暂停）：复位内部状态，位置归零
            #（控制器轮询到 is_playing=False + 位置 0 → 复位 UI）
            self._playing = False
            self._paused = False
            self._seek_origin = 0.0
            return 0.0
        position = pygame.mixer.music.get_pos() / 1000.0  # ms → s
        if position < 0:  # 部分后端可能返回 -1
            position = self._clock() - self._play_started_at + self._seek_origin
        else:
            position += self._seek_origin  # get_pos 不含 seek 偏移（实测）
        return position
