"""渲染器引擎（Renderer）。

Renderer 是 AuroraMV 核心：负责生成每一帧画面。

架构规则（规格第 9 节）：
- UI 与渲染器分离：UI 只调用本模块公开方法，不直接调用 OpenGL；
- 预览与导出共用渲染器：导出阶段将复用同一渲染管线。

阶段 2：OpenGL 上下文、摄像机、着色器/纹理基础设施。
阶段 3：AudioState 音频响应（圆形大小随低频变化）。
阶段 4：背景系统（Layer 0）——图片背景与动态着色器背景
（银河 / 波形 / 霓虹网格，均响应 AudioState）。

渲染顺序（规格 18 节图层系统）：背景 → 粒子/效果 → 歌词（最上层）。
load_scene / SceneManager 将在阶段 5 场景系统接入。
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

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
    FULLSCREEN_VERTEX_SHADER,
    POST_FRAGMENT_SHADER,
    create_program,
)
from core.renderer.scene import Scene, SceneManager
from core.lyrics.provider import LyricsProvider
from core.lyrics.template import load_lyric_template
from core.renderer.lyrics import DEFAULT_LYRIC_TEMPLATE, LyricsRenderer
from core.effects.effect import PostState
from core.effects.manager import EffectManager, create_effect
from core.effects.template import load_effect_spec
from core.templates.loader import TemplateError

WaveformProvider = Callable[[int], npt.NDArray[np.float32]]

WAVEFORM_SAMPLES = 512

# 歌词模板目录（templates/lyrics）
LYRICS_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates" / "lyrics"

# 效果模板目录（templates/effects）
EFFECTS_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates" / "effects"


class Renderer:
    """生成每一帧画面的渲染器核心。"""

    def __init__(self) -> None:
        self.ctx: moderngl.Context | None = None
        self.background: BackgroundRenderer | None = None
        self.camera = Camera()
        self._scene_manager: SceneManager | None = None
        self._active_scene_id: int | None = None
        self._active_scene: Scene | None = None
        self.lyrics: LyricsRenderer | None = None
        self._lyrics_provider: LyricsProvider | None = None
        self.effects = EffectManager()
        self._effect_param_overrides: dict[str, dict[str, object]] = {}
        self._post_state = PostState()
        self._scene_texture: moderngl.Texture | None = None
        self._scene_fbo: moderngl.Framebuffer | None = None
        self._post_program: moderngl.Program | None = None
        self._post_vao: moderngl.VertexArray | None = None
        self._waveform_provider: WaveformProvider | None = None
        self._spectrum_provider: WaveformProvider | None = None
        self._cover_rgba: np.ndarray | None = None
        self._cover_texture: moderngl.Texture | None = None
        self._width = 1280
        self._height = 720
        self._time = 0.0

    def initialize(self, ctx: moderngl.Context | None = None) -> None:
        """创建（或接管）OpenGL 上下文并准备渲染资源。

        Qt 集成路径：initializeGL 已保证当前线程持有 GL 上下文，
        不传 ctx 时自动检测并包装当前上下文；测试可显式传入独立上下文。
        """
        self.ctx = ctx if ctx is not None else moderngl.create_context()

        # 默认背景：银河（阶段 4）
        self.background = create_background(self.ctx, "galaxy")

        # 歌词渲染器（阶段 6，Layer 3）
        self.lyrics = LyricsRenderer(self.ctx)

        # 后期处理管线（阶段 7：震动偏移 + 闪光）
        self._post_program = create_program(
            self.ctx, FULLSCREEN_VERTEX_SHADER, POST_FRAGMENT_SHADER
        )
        self._post_program["u_scene"].value = 0
        vbo_positions = self.ctx.buffer(FULLSCREEN_POSITIONS.tobytes())
        vbo_uvs = self.ctx.buffer(FULLSCREEN_UVS.tobytes())
        ibo = self.ctx.buffer(FULLSCREEN_INDICES.tobytes())
        self._post_vao = self.ctx.vertex_array(
            self._post_program,
            [
                (vbo_positions, "3f", "in_position"),
                (vbo_uvs, "2f", "in_uv"),
            ],
            ibo,
        )
        self._create_scene_fbo()
        self._apply_cover()

    def set_background(
        self,
        kind: str,
        source: str | None = None,
        params: dict[str, object] | None = None,
    ) -> None:
        """切换背景（阶段 4/8）。kind: image / galaxy / waveform / neon_grid。"""
        assert self.ctx is not None, "请先调用 initialize()"
        new = create_background(self.ctx, kind, source, params)
        if self.background is not None:
            self.background.release()
        self.background = new
        self.background.set_aspect(self._width / self._height)
        if self._cover_texture is not None and hasattr(new, "set_cover"):
            new.set_cover(self._cover_texture)

    def set_waveform_provider(self, provider: WaveformProvider) -> None:
        """注入波形采样来源（阶段 4 波形背景用；渲染器不直接读音频）。"""
        self._waveform_provider = provider

    def set_spectrum_provider(self, provider: WaveformProvider) -> None:
        """注入频谱来源（音域回响背景用）。"""
        self._spectrum_provider = provider

    def set_cover_image(self, path: str) -> None:
        """导入专辑封面（供黑胶唱片/封面粒子背景使用）。"""
        from PIL import Image

        import numpy as np

        with Image.open(path) as img:
            self._cover_rgba = np.asarray(img.convert("RGBA"), dtype=np.uint8)
        self._apply_cover()

    def _apply_cover(self) -> None:
        """上传封面纹理并应用到当前背景（支持封面的背景）。"""
        if self._cover_rgba is None or self.ctx is None:
            return
        from core.renderer.texture import upload_texture

        if self._cover_texture is not None:
            self._cover_texture.release()
        self._cover_texture = upload_texture(self.ctx, self._cover_rgba)
        if self.background is not None and hasattr(self.background, "set_cover"):
            self.background.set_cover(self._cover_texture)

    def set_effect_param(self, name: str, **kwargs: object) -> None:
        """持久化调整效果参数（阶段 10 UI 滑杆）。

        立即应用到当前效果，并记录覆盖值；后续场景加载效果时自动重放，
        保证用户调参跨场景保持。
        """
        override = self._effect_param_overrides.setdefault(name, {})
        override.update(kwargs)
        self.effects.set_params(name, **kwargs)

    def set_scene_manager(self, manager: SceneManager | None) -> None:
        """注入场景管理器（阶段 5）：update 时按音乐时间自动切换场景。"""
        self._scene_manager = manager
        self._active_scene_id = None

    def load_scene(self, scene: Scene | None) -> None:
        """加载场景（规格 17.1 接口）。scene 为 None 时恢复默认背景与歌词模板。"""
        if scene is None:
            self.set_background("galaxy")
            self._active_scene = None
            self.set_lyric_template(None)
            self.effects.clear()
            return
        self.set_background(
            scene.background.kind, scene.background.source, scene.background.params
        )
        self._active_scene = scene
        if scene.lyric_template:
            self.set_lyric_template(scene.lyric_template)
        self._load_effects(scene.effects)

    def set_lyrics_provider(self, provider: LyricsProvider | None) -> None:
        """注入歌词提供器（阶段 6）。"""
        self._lyrics_provider = provider

    def set_lyrics_visible(self, visible: bool) -> None:
        """歌词开关。"""
        if self.lyrics is not None:
            self.lyrics.set_visible(visible)

    def set_lyric_template(self, name: str | None) -> None:
        """按名称切换歌词模板（templates/lyrics/<name>.json）。

        name 为 None 时恢复默认模板；文件缺失时保持当前模板。
        """
        if self.lyrics is None:
            return
        if name is None:
            self.lyrics.set_template(DEFAULT_LYRIC_TEMPLATE)
            return
        path = LYRICS_TEMPLATES_DIR / f"{name}.json"
        if not path.exists():
            return
        try:
            self.lyrics.set_template(load_lyric_template(str(path)))
        except TemplateError:
            return  # 模板无效时保持当前模板

    def _load_effects(self, names: list[str]) -> None:
        """按场景效果名从模板加载效果（阶段 7）。"""
        self.effects.clear()
        if self.ctx is None:
            return
        for name in names:
            path = EFFECTS_TEMPLATES_DIR / f"{name}.json"
            if not path.exists():
                continue
            try:
                self.effects.add(create_effect(self.ctx, load_effect_spec(str(path))))
                self.effects.set_params(name, **self._effect_param_overrides.get(name, {}))
            except TemplateError:
                continue  # 无效模板跳过

    def update(self, time: float, audio_state: AudioState | None = None) -> None:
        """更新帧状态：摄像机、背景、场景、歌词。"""
        self._time = time
        self.camera.update(time)

        music_time = audio_state.timestamp if audio_state is not None else self._time

        waveform = None
        if self._waveform_provider is not None:
            waveform = self._waveform_provider(WAVEFORM_SAMPLES)
        if (
            self._spectrum_provider is not None
            and self.background is not None
            and hasattr(self.background, "set_spectrum")
        ):
            self.background.set_spectrum(self._spectrum_provider(64))
        self._update_scene(music_time)
        if self.background is not None:
            # 背景用音乐时间驱动：随节拍/低频动态变化，暂停时随音乐一起冻结
            self.background.update(music_time, audio_state, waveform)

        line = None
        if self._lyrics_provider is not None:
            line = self._lyrics_provider.get_current_line(music_time)
        if self.lyrics is not None:
            self.lyrics.update(music_time, line, audio_state)

        self._post_state.reset()
        self.effects.update(music_time, audio_state, self._post_state)

    def _update_scene(self, music_time: float) -> None:
        """按音乐时间自动切换场景（阶段 5）。"""
        if self._scene_manager is None:
            return
        scene = self._scene_manager.get_scene(music_time)
        scene_id = scene.id if scene is not None else None
        if scene_id == self._active_scene_id:
            return
        self._active_scene_id = scene_id
        if scene is not None:
            self.load_scene(scene)

    def render(self, target: moderngl.Framebuffer | None = None) -> None:
        """渲染一帧：场景（背景/粒子/歌词）→ 后期处理（震动/闪光）。"""
        assert self.ctx is not None
        assert self.background is not None
        assert self._scene_fbo is not None and self._scene_texture is not None
        assert self._post_program is not None and self._post_vao is not None

        # 1) 场景渲染到离屏帧缓冲
        self._scene_fbo.use()
        self.ctx.viewport = (0, 0, self._width, self._height)
        self.ctx.clear(0.03, 0.03, 0.06, 1.0)

        self.background.render()
        self.effects.render()

        # 歌词在最上层（画面上方），不被粒子/效果遮挡
        if self.lyrics is not None:
            self.lyrics.render(self._width, self._height)

        # 2) 后期处理：震动偏移 + 闪光叠加
        out = target if target is not None else self.ctx.screen
        out.use()
        self.ctx.viewport = (0, 0, self._width, self._height)
        self._scene_texture.use(0)
        self._post_program["u_offset"].value = (
            float(self._post_state.offset[0]),
            float(self._post_state.offset[1]),
        )
        self._post_program["u_flash"].value = self._post_state.flash
        self._post_program["u_flash_color"].value = (
            float(self._post_state.flash_color[0]),
            float(self._post_state.flash_color[1]),
            float(self._post_state.flash_color[2]),
        )
        self._post_vao.render(moderngl.TRIANGLES)

    def _create_scene_fbo(self) -> None:
        """（重新）创建与视口同尺寸的离屏场景缓冲。"""
        assert self.ctx is not None
        self._scene_texture = self.ctx.texture((self._width, self._height), 4)
        self._scene_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self._scene_fbo = self.ctx.framebuffer(color_attachments=[self._scene_texture])

    def resize(self, width: int, height: int) -> None:
        """更新视口尺寸与摄像机宽高比。"""
        self._width = max(1, width)
        self._height = max(1, height)
        if self.ctx is not None:
            self.ctx.viewport = (0, 0, self._width, self._height)
        self.camera.set_aspect(self._width / self._height)
        if self.background is not None:
            self.background.set_aspect(self._width / self._height)
        if self.ctx is not None and self._scene_fbo is not None:
            self._create_scene_fbo()
