"""粒子效果（规格 16 节公式）：particle_count = base_count + bass * multiplier。

GPU 点精灵粒子：从底部升起、横向漂移；低频增强 → 粒子数量增加。
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

import moderngl

from core.audio.state import AudioState
from core.effects.effect import Effect, PostState
from core.renderer.shader import (
    PARTICLE_FRAGMENT_SHADER,
    PARTICLE_VERTEX_SHADER,
    create_program,
)

_SPAWN_PER_FRAME = 30


@dataclass
class ParticleParams:
    """粒子参数（全部可调节）。"""

    base_count: int = 60  # 基础粒子数
    bass_multiplier: int = 140  # 低频乘数（规格 16：count = base + bass × multiplier）
    speed: float = 0.35  # 粒子速度（uv/秒）
    rise: float = 0.3  # 上升速度
    spread: float = 0.6  # 横向扩散
    sway: float = 0.3  # 横向摆动
    size: float = 4.0  # 粒子尺寸（像素）
    lifetime: float = 2.5  # 生命周期（秒）
    color: tuple[float, float, float] = (0.4, 0.9, 1.0)


class ParticleEffect(Effect):
    """GPU 点精灵粒子：从底部升起、随低频增减数量。"""

    name = "particle"

    def __init__(self, ctx: moderngl.Context, params: ParticleParams | None = None) -> None:
        super().__init__()
        self._ctx = ctx
        self.params = params or ParticleParams()
        self._max = max(8, self.params.base_count + self.params.bass_multiplier)
        self._positions = np.zeros((self._max, 2), dtype=np.float32)
        self._velocities = np.zeros((self._max, 2), dtype=np.float32)
        self._lives = np.zeros(self._max, dtype=np.float32)
        self._sizes = np.full(self._max, self.params.size, dtype=np.float32)
        self._active = 0
        self._rng = np.random.default_rng(7)

        self._program = create_program(
            ctx, PARTICLE_VERTEX_SHADER, PARTICLE_FRAGMENT_SHADER
        )
        self._program["u_color"].value = self.params.color
        self._vbo = ctx.buffer(reserve=self._max * 16, dynamic=True)  # x, y, life01, size
        self._vao = ctx.vertex_array(
            self._program,
            [(self._vbo, "2f 1f 1f", "in_position", "in_life", "in_size")],
            mode=moderngl.POINTS,
        )

    def update(
        self,
        time: float,
        audio_state: AudioState | None = None,
        post_state: PostState | None = None,
    ) -> None:
        dt = min(max(0.0, time - self._last_time), 0.1)
        self._last_time = time

        bass = float(audio_state.bass) if audio_state is not None else 0.5
        target = int(self.params.base_count + bass * self.params.bass_multiplier)
        target = min(max(target, 0), self._max)

        # 推进现有粒子
        self._lives[: self._active] -= dt
        self._positions[: self._active] += self._velocities[: self._active] * dt
        sway = math.sin(time * 2.0) * self.params.sway * dt
        self._positions[: self._active, 0] += sway

        # 回收过期粒子（与末尾交换）
        index = 0
        while index < self._active:
            if self._lives[index] <= 0.0:
                self._active -= 1
                self._positions[index] = self._positions[self._active]
                self._velocities[index] = self._velocities[self._active]
                self._lives[index] = self._lives[self._active]
                self._sizes[index] = self._sizes[self._active]
            else:
                index += 1

        # 生成新粒子（限制每帧生成数，避免爆发）
        spawned = 0
        while self._active < target and spawned < _SPAWN_PER_FRAME:
            self._positions[self._active, 0] = self._rng.uniform(
                -self.params.spread, self.params.spread
            )
            self._positions[self._active, 1] = -0.95
            self._velocities[self._active, 0] = (
                self._rng.uniform(-self.params.speed, self.params.speed)
                * self.params.spread
            )
            self._velocities[self._active, 1] = self.params.rise * self._rng.uniform(
                0.5, 1.5
            )
            self._lives[self._active] = self.params.lifetime * self._rng.uniform(0.5, 1.0)
            self._sizes[self._active] = self.params.size * self._rng.uniform(0.6, 1.4)
            self._active += 1
            spawned += 1

        # 上传数据
        if self._active > 0:
            data = np.empty((self._active, 4), dtype=np.float32)
            data[:, 0] = self._positions[: self._active, 0]
            data[:, 1] = self._positions[: self._active, 1]
            data[:, 2] = np.clip(
                self._lives[: self._active] / max(self.params.lifetime, 0.01), 0.0, 1.0
            )
            data[:, 3] = self._sizes[: self._active]
            self._vbo.write(data.tobytes())

    def render(self) -> None:
        if self._active == 0:
            return
        self._program["u_color"].value = self.params.color
        self._ctx.enable(moderngl.BLEND)
        self._ctx.enable(moderngl.PROGRAM_POINT_SIZE)
        self._vao.render(moderngl.POINTS, vertices=self._active)
        self._ctx.disable(moderngl.PROGRAM_POINT_SIZE)
        self._ctx.disable(moderngl.BLEND)

    def release(self) -> None:
        self._vao.release()
        self._vbo.release()
        self._program.release()
