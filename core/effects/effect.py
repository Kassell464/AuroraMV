"""效果引擎（规格 27 节）。

Effect 负责所有非核心视觉效果（闪光 / 震动 / 故障 / 粒子…）。
所有效果参数可调节：params 数据类 + set_params 运行时调整。
"""

from __future__ import annotations

import time

import numpy as np

from core.audio.state import AudioState


class PostState:
    """后期处理状态：效果系统写入、渲染器消费（每帧重置）。"""

    def __init__(self) -> None:
        self.offset = np.zeros(2, dtype=np.float32)  # 屏幕偏移（uv 单位，如震动）
        self.flash = 0.0  # 闪光强度 0..1
        self.flash_color = np.ones(3, dtype=np.float32)

    def reset(self) -> None:
        self.offset[:] = 0.0
        self.flash = 0.0
        self.flash_color[:] = 1.0


class Effect:
    """效果接口（规格 27 节）：update / render。"""

    name = "effect"

    def __init__(self) -> None:
        self._last_time = 0.0
        self._last_wall = time.monotonic()

    def _wall_dt(self) -> float:
        """真实时间增量（秒，上限 0.1）。"""
        now = time.monotonic()
        dt = min(max(0.0, now - self._last_wall), 0.1)
        self._last_wall = now
        return dt

    def _effect_dt(self, time: float) -> float:
        """效果时间增量。

        优先用音乐时间（播放/导出时逐帧推进，保证导出与预览一致）；
        音乐时间冻结或回跳（暂停/seek）时退回真实时钟，
        保证衰减不随音乐时间一起冻结。
        """
        music_dt = time - self._last_time
        self._last_time = time
        if 0.0 < music_dt <= 0.1:
            return music_dt
        return self._wall_dt()

    def update(
        self,
        time: float,
        audio_state: AudioState | None = None,
        post_state: PostState | None = None,
    ) -> None:
        """更新效果状态（time 为音乐时间，秒）。"""
        raise NotImplementedError

    def render(self) -> None:
        """绘制效果（需要绘制的效果实现；纯状态类效果为空操作）。"""

    def set_params(self, **kwargs: object) -> None:
        """运行时调整参数（可调节性；未知键忽略）。"""
        params = getattr(self, "params", None)
        for key, value in kwargs.items():
            if params is not None and hasattr(params, key):
                setattr(params, key, value)

    def release(self) -> None:
        """释放 GPU 资源（默认无）。"""
