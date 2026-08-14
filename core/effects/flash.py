"""闪光效果：亮度闪烁（trigger=beat 节拍触发 / bass 随低频）。"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from core.audio.state import AudioState
from core.effects.effect import Effect, PostState


@dataclass
class FlashParams:
    """闪光参数（全部可调节）。"""

    color: tuple[float, float, float] = (1.0, 1.0, 1.0)
    intensity: float = 0.3  # 峰值亮度
    duration: float = 0.2  # 单次持续（秒）
    decay: float = 9.0  # 衰减速率（/秒）
    trigger: str = "beat"  # beat：节拍触发；bass：随低频


class FlashEffect(Effect):
    """亮度闪光：叠加到后期处理。"""

    name = "flash"

    def __init__(
        self, ctx: object | None = None, params: FlashParams | None = None
    ) -> None:
        super().__init__()
        self.params = params or FlashParams()
        self._level = 0.0

    def update(
        self,
        time: float,
        audio_state: AudioState | None = None,
        post_state: PostState | None = None,
    ) -> None:
        dt = min(max(0.0, time - self._last_time), 0.1)
        self._last_time = time
        if self.params.trigger == "bass":
            self._level = float(audio_state.bass) if audio_state is not None else 0.0
        else:
            beat = audio_state is not None and audio_state.beat
            if beat:
                self._level = 1.0
            else:
                self._level = max(0.0, self._level - self.params.decay * dt)
        if post_state is not None and self._level > 0.0:
            post_state.flash += self.params.intensity * self._level
            post_state.flash_color[:] = np.array(self.params.color, dtype=np.float32)
