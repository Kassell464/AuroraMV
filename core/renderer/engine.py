"""渲染器引擎（Renderer）。

Renderer 是 AuroraMV 核心：负责生成每一帧画面。

架构规则（规格第 9 节）：
- UI 与渲染器分离：UI 只调用本模块公开方法，不直接调用 OpenGL；
- 预览与导出共用渲染器：导出阶段将复用同一渲染管线。

阶段 2：OpenGL 上下文、摄像机、着色器/纹理基础设施。
阶段 3：AudioState 音频响应（圆形大小随低频变化）。
阶段 4：背景系统（Layer 0）——图片背景与动态着色器背景
（银河 / 波形 / 霓虹网格，均响应 AudioState）。

渲染顺序（规格 18 节图层系统）：背景 →（后续：粒子/效果/歌词）→ 圆形叠加层。
load_scene / SceneManager 将在阶段 5 场景系统接入。
"""

from __future__ import annotations

import math
from collections.abc import Callable

import numpy as np
import numpy.typing as npt

import moderngl

from core.audio.state import AudioState
from core.renderer.background import (
    FULLSCREEN_INDICES,
    FULLSCREEN_POSITIONS,
    FULLSCREEN_UVS,
    BackgroundRenderer,
    create_background,
)
from core.renderer.camera import Camera
from core.renderer.shader import (
    CIRCLE_FRAGMENT_SHADER,
    FULLSCREEN_VERTEX_SHADER,
    create_program,
)

WaveformProvider = Callable[[int], npt.NDArray[np.float32]]

# 音频响应圆形：半径 = 基础 + 低频 × 缩放（阶段 3 演示）
BASE_RADIUS = 0.12
RADIUS_SCALE = 0.25
WAVEFORM_SAMPLES = 512


class Renderer:
    """生成每一帧画面的渲染器核心。"""

    def __init__(self) -> None:
        self.ctx: moderngl.Context | None = None
        self.circle_program: moderngl.Program | None = None
        self.circle_vao: moderngl.VertexArray | None = None
        self.background: BackgroundRenderer | None = None
        self.camera = Camera()
        self._waveform_provider: WaveformProvider | None = None
        self._width = 1280
        self._height = 720
        self._time = 0.0
        self._circle_radius = BASE_RADIUS

    def initialize(self, ctx: moderngl.Context | None = None) -> None:
        """创建（或接管）OpenGL 上下文并准备渲染资源。

        Qt 集成路径：initializeGL 已保证当前线程持有 GL 上下文，
        不传 ctx 时自动检测并包装当前上下文；测试可显式传入独立上下文。
        """
        self.ctx = ctx if ctx is not None else moderngl.create_context()
        self.circle_program = create_program(
            self.ctx, FULLSCREEN_VERTEX_SHADER, CIRCLE_FRAGMENT_SHADER
        )
        self.circle_program["u_color"].value = (0.25, 0.8, 1.0)

        vbo_positions = self.ctx.buffer(FULLSCREEN_POSITIONS.tobytes())
        vbo_uvs = self.ctx.buffer(FULLSCREEN_UVS.tobytes())
        ibo = self.ctx.buffer(FULLSCREEN_INDICES.tobytes())
        self.circle_vao = self.ctx.vertex_array(
            self.circle_program,
            [
                (vbo_positions, "3f", "in_position"),
                (vbo_uvs, "2f", "in_uv"),
            ],
            ibo,
        )

        # 默认背景：银河（阶段 4）
        self.background = create_background(self.ctx, "galaxy")

    def set_background(self, kind: str, source: str | None = None) -> None:
        """切换背景（阶段 4）。kind: image / galaxy / waveform / neon_grid。"""
        assert self.ctx is not None, "请先调用 initialize()"
        new = create_background(self.ctx, kind, source)
        if self.background is not None:
            self.background.release()
        self.background = new
        self.background.set_aspect(self._width / self._height)

    def set_waveform_provider(self, provider: WaveformProvider) -> None:
        """注入波形采样来源（阶段 4 波形背景用；渲染器不直接读音频）。"""
        self._waveform_provider = provider

    def update(self, time: float, audio_state: AudioState | None = None) -> None:
        """更新帧状态：摄像机、圆形半径、背景。"""
        self._time = time
        self.camera.update(time)
        if audio_state is not None:
            bass = float(audio_state.bass)
        else:
            bass = 0.5 + 0.5 * math.sin(time * 2.0)
        self._circle_radius = BASE_RADIUS + bass * RADIUS_SCALE

        waveform = None
        if self._waveform_provider is not None:
            waveform = self._waveform_provider(WAVEFORM_SAMPLES)
        if self.background is not None:
            self.background.update(time, audio_state, waveform)

    def render(self) -> None:
        """渲染一帧：清屏 → 背景（Layer 0）→ 音频响应圆形。"""
        assert self.ctx is not None
        assert self.circle_program is not None and self.circle_vao is not None
        assert self.background is not None

        self.ctx.viewport = (0, 0, self._width, self._height)
        self.ctx.clear(0.03, 0.03, 0.06, 1.0)

        self.background.render()

        self.circle_program["u_radius"].value = self._circle_radius
        self.ctx.enable(moderngl.BLEND)
        self.circle_vao.render(moderngl.TRIANGLES)
        self.ctx.disable(moderngl.BLEND)

    def resize(self, width: int, height: int) -> None:
        """更新视口尺寸与摄像机宽高比。"""
        self._width = max(1, width)
        self._height = max(1, height)
        if self.ctx is not None:
            self.ctx.viewport = (0, 0, self._width, self._height)
        self.camera.set_aspect(self._width / self._height)
        if self.background is not None:
            self.background.set_aspect(self._width / self._height)
