"""背景渲染器（Background Renderer，规格 19-21 节）。

Layer 0（背景层）：
- 图片背景（jpg / png / webp）：加载、缩放（镜头推进）、平移、颜色调整；
- 动态着色器背景：银河（粒子/星空）、波形（音频波形）、霓虹网格（科幻网格），
  均支持 AudioState 响应（如低频增强 → 粒子速度加快）。

阶段 8：全部背景参数化（params 数据类 + templates/background/*.json 模板），
与效果系统一致：模板可调，运行时直接改 params 字段即可。

注：模糊效果与流体背景（Fluid）留待后续阶段。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, fields

import numpy as np
import numpy.typing as npt

import moderngl
from PIL import Image

from core.audio.state import AudioState
from core.renderer.shader import (
    FULLSCREEN_VERTEX_SHADER,
    GALAXY_FRAGMENT_SHADER,
    IMAGE_FRAGMENT_SHADER,
    NEON_GRID_FRAGMENT_SHADER,
    WAVEFORM_FRAGMENT_SHADER,
    create_program,
)
from core.renderer.texture import upload_texture

# 全屏四边形几何（背景层通用）
FULLSCREEN_POSITIONS = np.array(
    [
        -1.0, -1.0, 0.0,
        1.0, -1.0, 0.0,
        1.0, 1.0, 0.0,
        -1.0, 1.0, 0.0,
    ],
    dtype=np.float32,
)

FULLSCREEN_UVS = np.array(
    [
        0.0, 0.0,
        1.0, 0.0,
        1.0, 1.0,
        0.0, 1.0,
    ],
    dtype=np.float32,
)

FULLSCREEN_INDICES = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)

PAN_DIRECTIONS = {
    "left": (-1.0, 0.0),
    "right": (1.0, 0.0),
    "up": (0.0, 1.0),
    "down": (0.0, -1.0),
}


# ---------- 参数（全部可调节） ----------


@dataclass
class ImageParams:
    """图片背景参数。"""

    zoom_speed: float = 0.4  # 缩放动画速度（Hz）
    zoom_amount: float = 0.2  # 缩放幅度（1.0 → 1.0+amount，模拟镜头推进）
    pan: str | None = None  # left / right / up / down
    tint: tuple[float, float, float] = (1.0, 1.0, 1.0)


@dataclass
class GalaxyParams:
    """银河背景参数。"""

    spin_speed: float = 1.0
    star_brightness: float = 1.0
    star_density: float = 0.86
    arm_color: tuple[float, float, float] = (0.30, 0.15, 0.60)


@dataclass
class WaveformParams:
    """波形背景参数。"""

    color: tuple[float, float, float] = (0.3, 0.9, 1.0)


@dataclass
class NeonGridParams:
    """霓虹网格背景参数。"""

    color: tuple[float, float, float] = (0.1, 0.9, 1.0)
    speed: float = 1.0


def _pick(cls: type, params: dict[str, object]) -> dict[str, object]:
    names = {field.name for field in fields(cls)}
    return {key: value for key, value in params.items() if key in names}


def _fullscreen_vao(
    ctx: moderngl.Context, program: moderngl.Program
) -> moderngl.VertexArray:
    vbo_positions = ctx.buffer(FULLSCREEN_POSITIONS.tobytes())
    vbo_uvs = ctx.buffer(FULLSCREEN_UVS.tobytes())
    ibo = ctx.buffer(FULLSCREEN_INDICES.tobytes())
    return ctx.vertex_array(
        program,
        [
            (vbo_positions, "3f", "in_position"),
            (vbo_uvs, "2f", "in_uv"),
        ],
        ibo,
    )


class BackgroundRenderer:
    """背景渲染器接口（规格 19 节）：load / update / render。"""

    def load(self, source: str) -> None:
        raise NotImplementedError

    def update(
        self,
        time: float,
        audio_state: AudioState | None = None,
        waveform: npt.NDArray[np.float32] | None = None,
    ) -> None:
        """更新背景状态；动态背景必须响应 AudioState。"""

    def render(self) -> None:
        raise NotImplementedError

    def set_aspect(self, aspect: float) -> None:
        """窗口宽高比变化（默认忽略）。"""

    def release(self) -> None:
        """释放 GPU 资源。"""


class ImageBackgroundRenderer(BackgroundRenderer):
    """图片背景：加载（jpg/png/webp）、缩放（镜头推进）、平移、颜色调整。"""

    def __init__(self, ctx: moderngl.Context, params: ImageParams | None = None) -> None:
        self._ctx = ctx
        self.params = params or ImageParams()
        self._program = create_program(ctx, FULLSCREEN_VERTEX_SHADER, IMAGE_FRAGMENT_SHADER)
        self._vao = _fullscreen_vao(ctx, self._program)
        self._texture: moderngl.Texture | None = None
        self._tex_aspect = 1.0
        self._screen_aspect = 16.0 / 9.0
        self._zoom = 1.0
        self._offset = np.zeros(2, dtype=np.float32)
        self._pan_direction = np.zeros(2, dtype=np.float32)
        self._program["u_image"].value = 0

    def load(self, source: str) -> None:
        """加载图片文件（jpg / png / webp）。"""
        with Image.open(source) as img:
            rgba = np.asarray(img.convert("RGBA"), dtype=np.uint8)
        height, width = rgba.shape[:2]
        self._texture = upload_texture(self._ctx, rgba)
        self._tex_aspect = width / height

    def set_pan(self, direction: str) -> None:
        """设置平移方向：left / right / up / down。"""
        if direction not in PAN_DIRECTIONS:
            raise ValueError(f"未知平移方向: {direction}（可选 {', '.join(PAN_DIRECTIONS)}）")
        self.params.pan = direction

    def set_tint(self, r: float, g: float, b: float) -> None:
        """颜色调整（乘法叠加）。"""
        self.params.tint = (r, g, b)

    def set_aspect(self, aspect: float) -> None:
        self._screen_aspect = aspect

    def update(
        self,
        time: float,
        audio_state: AudioState | None = None,
        waveform: npt.NDArray[np.float32] | None = None,
    ) -> None:
        # 缩放：1.0 → 1.0+amount 缓慢往复，模拟镜头推进（参数可调）
        self._zoom = 1.0 + self.params.zoom_amount * (
            0.5 + 0.5 * math.sin(time * self.params.zoom_speed * 2.0 * math.pi)
        )
        # 平移：沿设定方向缓慢往返
        pan = self.params.pan
        if pan:
            self._pan_direction[:] = PAN_DIRECTIONS.get(pan, (0.0, 0.0))
        else:
            self._pan_direction[:] = 0.0
        if np.any(self._pan_direction):
            drift = 0.5 + 0.5 * math.sin(time * 0.25)
            self._offset = self._pan_direction * drift * 0.08
        self._program["u_tint"].value = (*self.params.tint, 1.0)

    def render(self) -> None:
        assert self._texture is not None, "图片背景请先 load 图片"
        self._texture.use(0)
        self._program["u_zoom"].value = self._zoom
        self._program["u_offset"].value = (float(self._offset[0]), float(self._offset[1]))
        self._program["u_tex_aspect"].value = self._tex_aspect
        self._program["u_screen_aspect"].value = self._screen_aspect
        self._vao.render(moderngl.TRIANGLES)

    def release(self) -> None:
        if self._texture is not None:
            self._texture.release()
        self._vao.release()
        self._program.release()


class _ShaderBackground(BackgroundRenderer):
    """动态着色器背景基类（全屏 shader，支持 AudioState 响应）。"""

    def __init__(
        self,
        ctx: moderngl.Context,
        fragment_shader: str,
    ) -> None:
        self._ctx = ctx
        self._program = create_program(ctx, FULLSCREEN_VERTEX_SHADER, fragment_shader)
        self._vao = _fullscreen_vao(ctx, self._program)
        self._aspect = 16.0 / 9.0

    def set_aspect(self, aspect: float) -> None:
        self._aspect = aspect

    def render(self) -> None:
        self._vao.render(moderngl.TRIANGLES)

    def release(self) -> None:
        self._vao.release()
        self._program.release()


class GalaxyBackground(_ShaderBackground):
    """银河：旋臂 + 恒星 + 核心；低频增强 → 旋转/闪烁加快（规格 21 节）。"""

    def __init__(self, ctx: moderngl.Context, params: GalaxyParams | None = None) -> None:
        super().__init__(ctx, GALAXY_FRAGMENT_SHADER)
        self.params = params or GalaxyParams()

    def update(
        self,
        time: float,
        audio_state: AudioState | None = None,
        waveform: npt.NDArray[np.float32] | None = None,
    ) -> None:
        bass = float(audio_state.bass) if audio_state is not None else 0.5
        self._program["u_time"].value = time
        self._program["u_bass"].value = bass
        self._program["u_aspect"].value = self._aspect
        self._program["u_spin_speed"].value = self.params.spin_speed
        self._program["u_star_brightness"].value = self.params.star_brightness
        self._program["u_star_density"].value = self.params.star_density
        self._program["u_arm_color"].value = self.params.arm_color


class WaveformBackground(_ShaderBackground):
    """波形：真实音频波形；低频增强 → 颜色更亮。"""

    def __init__(
        self,
        ctx: moderngl.Context,
        params: WaveformParams | None = None,
        n_samples: int = 512,
    ) -> None:
        super().__init__(ctx, WAVEFORM_FRAGMENT_SHADER)
        self.params = params or WaveformParams()
        self._n = n_samples
        self._samples = np.zeros(n_samples, dtype=np.float32)
        self._wave_texture = ctx.texture(
            (n_samples, 1), 1, dtype="f4", data=self._samples.tobytes()
        )
        self._wave_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self._program["u_wave"].value = 0

    def update(
        self,
        time: float,
        audio_state: AudioState | None = None,
        waveform: npt.NDArray[np.float32] | None = None,
    ) -> None:
        self._samples[:] = 0.0
        if waveform is not None:
            w = np.asarray(waveform, dtype=np.float32).reshape(-1)
            k = min(w.size, self._n)
            self._samples[-k:] = w[-k:]
        self._wave_texture.write(self._samples.tobytes())
        self._program["u_color"].value = self.params.color
        if audio_state is not None:
            self._program["u_bass"].value = float(audio_state.bass)
            self._program["u_time"].value = time

    def render(self) -> None:
        self._wave_texture.use(0)
        super().render()

    def release(self) -> None:
        self._wave_texture.release()
        super().release()


class NeonGridBackground(_ShaderBackground):
    """霓虹网格：科幻透视网格；低频增强 → 流动加快；节拍 → 闪光。"""

    def __init__(self, ctx: moderngl.Context, params: NeonGridParams | None = None) -> None:
        super().__init__(ctx, NEON_GRID_FRAGMENT_SHADER)
        self.params = params or NeonGridParams()
        self._flash = 0.0

    def update(
        self,
        time: float,
        audio_state: AudioState | None = None,
        waveform: npt.NDArray[np.float32] | None = None,
    ) -> None:
        beat = audio_state is not None and audio_state.beat
        self._flash = 1.0 if beat else self._flash * 0.9
        bass = float(audio_state.bass) if audio_state is not None else 0.5
        self._program["u_time"].value = time
        self._program["u_bass"].value = bass
        self._program["u_flash"].value = self._flash
        self._program["u_aspect"].value = self._aspect
        self._program["u_color"].value = self.params.color
        self._program["u_speed"].value = self.params.speed


def create_background(
    ctx: moderngl.Context,
    kind: str,
    source: str | None = None,
    params: dict[str, object] | None = None,
) -> BackgroundRenderer:
    """按类型创建背景（参数可调）。kind: image / galaxy / waveform / neon_grid。"""
    values = dict(params or {})
    if kind == "image":
        background: BackgroundRenderer = ImageBackgroundRenderer(
            ctx, ImageParams(**_pick(ImageParams, values))
        )
        if source is not None:
            background.load(source)
        return background
    if kind == "galaxy":
        return GalaxyBackground(ctx, GalaxyParams(**_pick(GalaxyParams, values)))
    if kind == "waveform":
        return WaveformBackground(ctx, WaveformParams(**_pick(WaveformParams, values)))
    if kind == "neon_grid":
        return NeonGridBackground(ctx, NeonGridParams(**_pick(NeonGridParams, values)))
    raise ValueError(f"未知背景类型: {kind}（可选 image/galaxy/waveform/neon_grid）")
