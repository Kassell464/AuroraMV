"""背景渲染器最小验证（阶段 4）。

图片背景（jpg/png/webp 加载）与动态着色器背景（银河/波形/霓虹网格）各渲染一帧。
需要 OpenGL 上下文；环境无法创建时自动跳过。
"""

import os
import unittest

import numpy as np

try:
    import moderngl

    _probe = moderngl.create_context(standalone=True)
    _probe.release()
    GL_AVAILABLE = True
except Exception:
    GL_AVAILABLE = False

from core.audio.state import AudioState
from core.renderer.background import create_background

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _state(t: float = 1.0) -> AudioState:
    return AudioState(timestamp=t, volume=0.5, bass=0.7, mid=0.4, treble=0.3, beat=False, bpm=120.0)


@unittest.skipUnless(GL_AVAILABLE, "当前环境无法创建 OpenGL 上下文")
class BackgroundTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ctx = moderngl.create_context(standalone=True)
        cls.fbo = cls.ctx.simple_framebuffer((64, 64), components=3)
        cls.ctx.viewport = (0, 0, 64, 64)

    def _render(self, background, t: float = 1.0, waveform=None) -> np.ndarray:
        self.fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0)
        background.update(t, _state(t), waveform)
        background.render()
        return np.frombuffer(self.fbo.read(components=3), dtype=np.uint8).reshape(64, 64, 3)

    def test_image_background_loads_jpg_png_webp(self) -> None:
        """图片背景：jpg / png / webp 三种格式均可加载并渲染。"""
        for ext in ("jpg", "png", "webp"):
            with self.subTest(ext=ext):
                path = os.path.join(FIXTURES, f"test_bg.{ext}")
                if not os.path.exists(path):
                    self.skipTest(f"缺少 fixture: {path}")
                bg = create_background(self.ctx, "image", path)
                pixels = self._render(bg)
                self.assertGreater(int(pixels.std()), 5, f"{ext} 画面应有内容")
                bg.release()

    def test_shader_backgrounds_render(self) -> None:
        """银河 / 波形 / 霓虹网格均能成功绘制一帧。"""
        for kind in ("galaxy", "waveform", "neon_grid"):
            with self.subTest(kind=kind):
                bg = create_background(self.ctx, kind)
                pixels = self._render(bg)
                self.assertGreater(int(pixels.max()), 5, f"{kind} 不应为纯黑")
                bg.release()

    def test_waveform_reacts_to_samples(self) -> None:
        """波形背景：不同波形采样应产生不同画面。"""
        bg = create_background(self.ctx, "waveform")
        up = np.full(512, 1.0, dtype=np.float32)
        down = np.full(512, -1.0, dtype=np.float32)
        a = self._render(bg, waveform=up)
        b = self._render(bg, waveform=down)
        self.assertFalse(np.array_equal(a, b), "波形变化应影响画面")
        bg.release()


if __name__ == "__main__":
    unittest.main()
