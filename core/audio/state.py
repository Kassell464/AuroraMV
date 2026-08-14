"""音频状态（AudioState）。

渲染器不应该直接读取音频，只读取 AudioState（规格第 15 节）。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AudioState:
    """某一时刻的音频特征快照。"""

    timestamp: float
    volume: float
    bass: float
    mid: float
    treble: float
    beat: bool
    bpm: float
