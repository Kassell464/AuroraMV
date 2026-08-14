"""渲染器最小验证：成功绘制一帧。

对应规格第 47 节「Renderer: draw frame successfully」。
需要 OpenGL 上下文；环境无法创建时自动跳过。
"""

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
from core.renderer.engine import Renderer


def _state(t: float) -> AudioState:
    return AudioState(timestamp=t, volume=0.5, bass=0.7, mid=0.4, treble=0.3, beat=False, bpm=120.0)


@unittest.skipUnless(GL_AVAILABLE, "当前环境无法创建 OpenGL 上下文")
class RendererTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ctx = moderngl.create_context(standalone=True)
        cls.renderer = Renderer()
        cls.renderer.initialize(ctx=cls.ctx)
        cls.fbo = cls.ctx.simple_framebuffer((64, 64), components=3)

    def _render_frame(self, t: float = 1.0) -> np.ndarray:
        self.fbo.use()
        self.renderer.resize(64, 64)
        self.renderer.update(t, _state(t))
        self.renderer.render()
        return np.frombuffer(self.fbo.read(components=3), dtype=np.uint8).reshape(64, 64, 3)

    def test_draws_frame_with_default_background(self) -> None:
        """默认背景（银河）+ 圆形叠加层应成功绘制。"""
        pixels = self._render_frame()
        self.assertGreater(int(pixels.max()), 5, "画面应有内容（银河背景 + 圆形）")
        self.assertLess(int(pixels.min()), 240, "画面应有明暗层次")

    def test_switches_background(self) -> None:
        """渲染器可在银河 / 波形 / 霓虹网格之间切换背景。"""
        for kind in ("galaxy", "waveform", "neon_grid"):
            with self.subTest(kind=kind):
                self.renderer.set_background(kind)
                pixels = self._render_frame()
                self.assertGreater(int(pixels.max()), 5, f"{kind} 背景应有内容")
        self.renderer.set_background("galaxy")  # 恢复默认


if __name__ == "__main__":
    unittest.main()
