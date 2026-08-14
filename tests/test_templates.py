"""模板系统测试（阶段 8）。

TemplateLoader 加载/校验、背景模板参数生效（GL，可跳过）、
六套系统预设包（scene）的加载与背景模板解析。
"""

import os
import tempfile
import unittest

import numpy as np

from core.templates.loader import TemplateError, TemplateLoader

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "templates")

try:
    import moderngl

    _probe = moderngl.create_context(standalone=True)
    _probe.release()
    GL_AVAILABLE = True
except Exception:
    GL_AVAILABLE = False


class TemplateLoaderTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.loader = TemplateLoader()

    def test_loads_all_template_kinds(self) -> None:
        for kind, name in (
            ("lyrics", "neon.json"),
            ("background", "aurora.json"),
            ("effects", "flash.json"),
            ("scene", "01-cinema.json"),
        ):
            data = self.loader.load(os.path.join(TEMPLATES_DIR, kind, name), kind)
            self.assertIsInstance(data, dict)

    def test_validate_rejects_missing_type(self) -> None:
        errors = self.loader.validate({}, "background")
        self.assertTrue(any("缺少字段" in e for e in errors))

    def test_validate_rejects_unknown_background_type(self) -> None:
        errors = self.loader.validate({"type": "bogus"}, "background")
        self.assertTrue(any("背景类型" in e for e in errors))

    def test_validate_rejects_bad_color(self) -> None:
        errors = self.loader.validate({"color": "red"}, "lyrics")
        self.assertTrue(any("颜色" in e for e in errors))

    def test_validate_rejects_scene_without_background(self) -> None:
        errors = self.loader.validate({}, "scene")
        self.assertTrue(any("background" in e for e in errors))

    def test_load_raises_on_invalid_template(self) -> None:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False, encoding="utf-8"
        ) as file:
            file.write('{"type": "nope"}')
            path = file.name
        try:
            with self.assertRaises(TemplateError):
                self.loader.load(path, "background")
        finally:
            os.unlink(path)


@unittest.skipUnless(GL_AVAILABLE, "当前环境无法创建 OpenGL 上下文")
class BackgroundTemplateGLTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from core.renderer.background import create_background as _create

        cls.ctx = moderngl.create_context(standalone=True)
        cls.fbo = cls.ctx.simple_framebuffer((64, 64), components=3)
        cls.ctx.viewport = (0, 0, 64, 64)

    def _render(self, background) -> np.ndarray:
        from core.renderer.background import create_background

        self.fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0)
        background.update(1.0)
        background.render()
        return np.frombuffer(self.fbo.read(components=3), dtype=np.uint8).reshape(64, 64, 3)

    def test_neon_grid_color_param_affects_frame(self) -> None:
        """背景模板参数生效：品红 vs 蓝色霓虹网格画面主色调不同。"""
        from core.renderer.background import create_background

        red = create_background(self.ctx, "neon_grid", params={"color": [1.0, 0.1, 0.1]})
        blue = create_background(self.ctx, "neon_grid", params={"color": [0.1, 0.1, 1.0]})
        red_frame = self._render(red)
        blue_frame = self._render(blue)
        self.assertGreater(float(red_frame[..., 0].mean()), float(red_frame[..., 2].mean()))
        self.assertGreater(float(blue_frame[..., 2].mean()), float(blue_frame[..., 0].mean()))
        red.release()
        blue.release()

    def test_galaxy_params_apply(self) -> None:
        from core.renderer.background import create_background

        galaxy = create_background(
            self.ctx, "galaxy", params={"spin_speed": 2.0, "star_brightness": 2.0}
        )
        frame = self._render(galaxy)
        self.assertGreater(int(frame.max()), 5)
        galaxy.release()

    def test_new_visual_backgrounds_render(self) -> None:
        """MineRadio 概念灵感背景（黑胶/星球/隧道/频谱）均能绘制一帧。"""
        from core.renderer.background import create_background

        for kind in ("vinyl", "planet", "tunnel", "spectrum"):
            with self.subTest(kind=kind):
                bg = create_background(self.ctx, kind)
                frame = self._render(bg)
                self.assertGreater(int(frame.max()), 5, f"{kind} 不应为纯黑")
                bg.release()

    def test_vinyl_accepts_cover(self) -> None:
        """黑胶背景可注入封面纹理（封面导入功能）。"""
        import numpy as np
        from PIL import Image

        from core.renderer.background import create_background
        from core.renderer.texture import upload_texture

        cover = np.zeros((32, 32, 4), dtype=np.uint8)
        cover[..., 0] = 255  # 红色封面
        cover[..., 3] = 255
        texture = upload_texture(self.ctx, cover)
        bg = create_background(self.ctx, "vinyl")
        bg.set_cover(texture)
        frame = self._render(bg)
        # 红色封面应让封面环区域偏红（避开中心唱盘孔，取偏 4 像素处）
        center = frame[32, 36].astype(np.int64)
        self.assertGreater(center[0], center[2])
        texture.release()
        bg.release()


class PresetPackTestCase(unittest.TestCase):
    def test_six_systematic_preset_packs(self) -> None:
        from core.renderer.scene import load_scene_presets

        presets = load_scene_presets(os.path.join(TEMPLATES_DIR, "scene"))
        names = {p.name for p in presets}
        self.assertEqual(
            names,
            {
                "cinema", "aurora", "cyberpunk", "stage", "synthwave", "dj",
                "vinyl", "planet", "tunnel", "spectrum",
            },
        )

    def test_presets_resolve_background_templates(self) -> None:
        from core.renderer.scene import load_scene_presets

        presets = {p.name: p for p in load_scene_presets(os.path.join(TEMPLATES_DIR, "scene"))}
        self.assertEqual(presets["cyberpunk"].background.kind, "neon_grid")
        self.assertIsNotNone(presets["cyberpunk"].background.params)
        self.assertEqual(presets["aurora"].background.kind, "galaxy")
        self.assertEqual(presets["cinema"].background.kind, "image")
        self.assertEqual(presets["dj"].background.kind, "waveform")


if __name__ == "__main__":
    unittest.main()
