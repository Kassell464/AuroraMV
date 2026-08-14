"""歌词渲染器（Lyrics Renderer）。

把当前歌词行渲染为带动画的文本（规格 25 节）：
生命周期：开始之前 → 入场动画 → 激活 → 退场动画。
动画：enter（淡入 + 上浮）、idle（呼吸辉光）、beat（节拍缩放）。

文本经 Pillow 渲染为 RGBA 纹理（按行缓存）；本模块不直接读取音频。
"""

from __future__ import annotations

import math

import numpy as np

import moderngl
from PIL import Image, ImageDraw, ImageFont

from core.audio.state import AudioState
from core.lyrics.parser import LyricLine
from core.lyrics.template import LyricTemplate, resolve_font
from core.renderer.shader import (
    LYRIC_FRAGMENT_SHADER,
    LYRIC_VERTEX_SHADER,
    create_program,
)

FONT_SIZE = 56
STROKE_WIDTH = 6
ENTER_DURATION = 0.35
EXIT_DURATION = 0.3
BEAT_SCALE = 0.06
CACHE_LIMIT = 64

DEFAULT_LYRIC_TEMPLATE = LyricTemplate(name="minimal")


class LyricsRenderer:
    """把当前歌词行渲染为带动画的文本。"""

    def __init__(
        self, ctx: moderngl.Context, template: LyricTemplate | None = None
    ) -> None:
        self._ctx = ctx
        self._program = create_program(ctx, LYRIC_VERTEX_SHADER, LYRIC_FRAGMENT_SHADER)
        self._vao = _quad_vao(ctx, self._program)
        self._program["u_text"].value = 0
        self._template = template if template is not None else DEFAULT_LYRIC_TEMPLATE
        self._font_path = resolve_font(self._template.font)
        self._visible = True
        self._line: LyricLine | None = None
        self._alpha = 0.0
        self._scale = 1.0
        self._rise = 0.0
        self._beat_pulse = 0.0
        self._cache: dict[str, tuple[moderngl.Texture, tuple[int, int]]] = {}

    def set_template(self, template: LyricTemplate) -> None:
        """切换歌词模板（字体/颜色/动画）。"""
        self._template = template
        self._font_path = resolve_font(template.font)
        self._cache.clear()  # 颜色/描边变化 → 清空纹理缓存

    def set_visible(self, visible: bool) -> None:
        """歌词开关。"""
        self._visible = visible
        if not visible:
            self._line = None

    def update(
        self,
        time: float,
        line: LyricLine | None,
        audio_state: AudioState | None = None,
    ) -> None:
        """更新歌词状态。time 为音乐时间（秒）。"""
        self._line = line
        if line is None or not self._visible:
            self._line = None
            return
        animation = self._template.animation

        enter = 1.0
        if animation.enter == "fade":
            enter = min(1.0, max(0.0, (time - line.start) / ENTER_DURATION))
        exit_progress = min(1.0, max(0.0, (line.end - time) / EXIT_DURATION))
        self._alpha = enter * exit_progress
        self._rise = (1.0 - enter) * 0.03  # 入场时自下方上浮

        if animation.idle == "glow":
            self._alpha *= 0.85 + 0.15 * math.sin(time * 2.5)

        beat = audio_state is not None and audio_state.beat
        self._beat_pulse = 1.0 if beat else self._beat_pulse * 0.9
        pulse = self._beat_pulse if animation.beat == "scale" else 0.0
        self._scale = 1.0 + pulse * BEAT_SCALE

    def render(self, screen_width: int, screen_height: int) -> None:
        """把当前歌词行画到屏幕（alpha 混合）。"""
        if self._line is None or self._alpha <= 0.01 or not self._visible:
            return
        texture, size = self._get_texture(self._line)
        if texture is None:
            return
        texture.use(0)
        half_x = (size[0] / max(screen_width, 1)) * self._scale
        half_y = (size[1] / max(screen_height, 1)) * self._scale
        if half_x > 0.45:  # 长行压缩，避免超出屏幕
            factor = 0.45 / half_x
            half_x *= factor
            half_y *= factor
        # 歌词位于画面上方（不被粒子/圆形遮挡）
        self._program["u_center"].value = (0.0, 0.38 + self._rise)
        self._program["u_half_size"].value = (half_x, half_y)
        self._program["u_alpha"].value = self._alpha
        self._ctx.enable(moderngl.BLEND)
        self._vao.render(moderngl.TRIANGLES)
        self._ctx.disable(moderngl.BLEND)

    def release(self) -> None:
        for texture, _ in self._cache.values():
            texture.release()
        self._cache.clear()
        self._vao.release()
        self._program.release()

    # ---------- 内部实现 ----------

    def _get_texture(
        self, line: LyricLine
    ) -> tuple[moderngl.Texture | None, tuple[int, int]]:
        cached = self._cache.get(line.text)
        if cached is not None:
            return cached
        if len(self._cache) >= CACHE_LIMIT:
            self._cache.clear()
        texture = self._render_text_texture(line.text)
        if texture is not None:
            size = (texture.size[0], texture.size[1])
            self._cache[line.text] = (texture, size)
            return texture, size
        return None, (1, 1)

    def _render_text_texture(self, text: str) -> moderngl.Texture | None:
        try:
            font = (
                ImageFont.truetype(self._font_path, FONT_SIZE)
                if self._font_path
                else ImageFont.load_default()
            )
        except OSError:
            font = ImageFont.load_default()
        color = tuple(int(c * 255) for c in self._template.color) + (255,)
        glow = tuple(int(c * 255) for c in self._template.glow) + (255,)
        stroke = STROKE_WIDTH if self._template.glow != self._template.color else 0

        probe = Image.new("RGBA", (8, 8))
        draw = ImageDraw.Draw(probe)
        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
        width = bbox[2] - bbox[0] + stroke * 2 + 8
        height = bbox[3] - bbox[1] + stroke * 2 + 8
        image = Image.new("RGBA", (max(width, 1), max(height, 1)), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.text(
            (stroke + 4 - bbox[0], stroke + 4 - bbox[1]),
            text,
            font=font,
            fill=color,
            stroke_width=stroke,
            stroke_fill=glow,
        )
        # 垂直翻转：Pillow 行序自上而下，OpenGL 纹理坐标原点在左下
        rgba = np.ascontiguousarray(np.asarray(image, dtype=np.uint8)[::-1])
        texture = self._ctx.texture((image.width, image.height), 4, data=rgba.tobytes())
        texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        return texture


def _quad_vao(ctx: moderngl.Context, program: moderngl.Program) -> moderngl.VertexArray:
    positions = np.array(
        [-1.0, -1.0, 0.0, 1.0, -1.0, 0.0, 1.0, 1.0, 0.0, -1.0, 1.0, 0.0],
        dtype=np.float32,
    )
    uvs = np.array([0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0], dtype=np.float32)
    indices = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)
    return ctx.vertex_array(
        program,
        [
            (ctx.buffer(positions.tobytes()), "3f", "in_position"),
            (ctx.buffer(uvs.tobytes()), "2f", "in_uv"),
        ],
        ctx.buffer(indices.tobytes()),
    )
