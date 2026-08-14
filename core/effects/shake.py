"""节拍震动效果（规格 16 节）：beat=True → 画面偏移（等效摄像机震动）。"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from core.audio.state import AudioState
from core.effects.effect import Effect, PostState


@dataclass
class ShakeParams:
    """震动参数（全部可调节）。"""

    strength: float = 0.02  # 偏移幅度（uv 单位）
    duration: float = 0.3  # 单次震动时长（秒）
    decay: float = 6.0  # 能量衰减速率（/秒）
    frequency: float = 12.0  # 抖动频率（Hz）


class BeatShakeEffect(Effect):
    """节拍震动：beat=True 时产生衰减的随机偏移。"""

    name = "beat_shake"

    def __init__(
        self, ctx: object | None = None, params: ShakeParams | None = None
    ) -> None:
        super().__init__()
        self.params = params or ShakeParams()
        self._energy = 0.0
        self._rng = np.random.default_rng(42)

    def update(
        self,
        time: float,
        audio_state: AudioState | None = None,
        post_state: PostState | None = None,
    ) -> None:
        dt = min(max(0.0, time - self._last_time), 0.1)
        self._last_time = time
        beat = audio_state is not None and audio_state.beat
        if beat:
            self._energy = 1.0
        else:
            self._energy = max(0.0, self._energy - self.params.decay * dt)
        if self._energy <= 0.0 or post_state is None:
            return
        angle = self._rng.uniform(0.0, 2.0 * math.pi)
        wobble = 0.5 + 0.5 * math.sin(
            time * self.params.frequency * 2.0 * math.pi
        )
        magnitude = self.params.strength * self._energy * wobble
        post_state.offset[0] += math.cos(angle) * magnitude
        post_state.offset[1] += math.sin(angle) * magnitude
