"""渲染器引擎（Renderer）。

Renderer 是 AuroraMV 核心：负责生成每一帧画面。

架构规则（规格第 9 节）：
- UI 与渲染器分离：UI 只调用本模块公开方法，不直接调用 OpenGL；
- 预览与导出共用渲染器：导出阶段将复用同一渲染管线。

阶段 2：OpenGL 上下文、着色器加载器、纹理管理器、摄像机；
演示：背景颜色 + 图片纹理 + 简单动画。
阶段 3：接入 AudioState（音频响应）——圆形大小随低频变化。

完整帧渲染管线（获取场景 → 更新音频 → 背景 → 效果 → 歌词 → 后期处理 → 输出帧，
见规格 17.2 节）将在后续阶段（场景 / 效果 / 歌词系统）逐步接入；
load_scene 将在阶段 5 场景系统实现。
"""

from __future__ import annotations

import math

import numpy as np
import numpy.typing as npt

import moderngl

from core.audio.state import AudioState
from core.renderer.camera import Camera
from core.renderer.shader import (
    CIRCLE_FRAGMENT_SHADER,
    CIRCLE_VERTEX_SHADER,
    create_program,
)
from core.renderer.texture import TextureManager, make_test_texture

Mat4 = npt.NDArray[np.float32]

# 音频响应圆形：半径 = 基础 + 低频 × 缩放（阶段 3 演示）
BASE_RADIUS = 0.12
RADIUS_SCALE = 0.25

# 全屏四边形（两个三角形）
QUAD_POSITIONS = np.array(
    [
        -1.0, -1.0, 0.0,
        1.0, -1.0, 0.0,
        1.0, 1.0, 0.0,
        -1.0, 1.0, 0.0,
    ],
    dtype=np.float32,
)

QUAD_UVS = np.array(
    [
        0.0, 0.0,
        1.0, 0.0,
        1.0, 1.0,
        0.0, 1.0,
    ],
    dtype=np.float32,
)

QUAD_INDICES = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)


def _rotation_y(angle: float) -> Mat4:
    """绕 Y 轴旋转矩阵（模型矩阵，用于简单动画）。"""
    c = math.cos(angle)
    s = math.sin(angle)
    mat = np.eye(4, dtype=np.float32)
    mat[0, 0] = c
    mat[0, 2] = s
    mat[2, 0] = -s
    mat[2, 2] = c
    return mat


class Renderer:
    """生成每一帧画面的渲染器核心。"""

    def __init__(self) -> None:
        self.ctx: moderngl.Context | None = None
        self.program: moderngl.Program | None = None
        self.circle_program: moderngl.Program | None = None
        self.vao: moderngl.VertexArray | None = None
        self.circle_vao: moderngl.VertexArray | None = None
        self.textures: TextureManager | None = None
        self.camera = Camera()
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
        self.program = create_program(self.ctx)
        self.circle_program = create_program(
            self.ctx, CIRCLE_VERTEX_SHADER, CIRCLE_FRAGMENT_SHADER
        )
        self.circle_program["u_color"].value = (0.25, 0.8, 1.0)

        vbo_positions = self.ctx.buffer(QUAD_POSITIONS.tobytes())
        vbo_uvs = self.ctx.buffer(QUAD_UVS.tobytes())
        ibo = self.ctx.buffer(QUAD_INDICES.tobytes())
        content = [
            (vbo_positions, "3f", "in_position"),
            (vbo_uvs, "2f", "in_uv"),
        ]
        self.vao = self.ctx.vertex_array(self.program, content, ibo)
        self.circle_vao = self.ctx.vertex_array(self.circle_program, content, ibo)

        self.textures = TextureManager(self.ctx)
        self.textures.create("test", make_test_texture())
        self.program["u_texture"].value = 0

    def update(self, time: float, audio_state: AudioState | None = None) -> None:
        """更新帧状态：摄像机摆动 + 圆形半径随低频变化。

        audio_state 为 None（未接入音频）时用正弦模拟低频，保证演示可用。
        """
        self._time = time
        self.camera.update(time)
        if audio_state is not None:
            bass = float(audio_state.bass)
        else:
            bass = 0.5 + 0.5 * math.sin(time * 2.0)
        self._circle_radius = BASE_RADIUS + bass * RADIUS_SCALE

    def render(self) -> None:
        """渲染一帧：背景颜色 → 纹理四边形（旋转）→ 音频响应圆形。"""
        assert self.ctx is not None and self.program is not None
        assert self.circle_program is not None and self.circle_vao is not None
        assert self.vao is not None and self.textures is not None

        self.ctx.viewport = (0, 0, self._width, self._height)
        # 1) 背景颜色
        self.ctx.clear(0.05, 0.06, 0.10, 1.0)

        # 2) 纹理四边形（简单动画：缓慢绕 Y 轴旋转）
        texture = self.textures.get("test")
        assert texture is not None
        texture.use(0)
        model = _rotation_y(self._time * 0.5)
        mvp = self.camera.projection_matrix() @ self.camera.view_matrix() @ model
        self.program["u_mvp"].write(
            np.ascontiguousarray(mvp.T, dtype=np.float32).tobytes()
        )
        self.vao.render(moderngl.TRIANGLES)

        # 3) 音频响应圆形（半径 = 基础 + 低频 × 缩放）
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
