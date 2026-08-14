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

from core.renderer.engine import Renderer


@unittest.skipUnless(GL_AVAILABLE, "当前环境无法创建 OpenGL 上下文")
class RendererTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ctx = moderngl.create_context(standalone=True)
        cls.renderer = Renderer()
        cls.renderer.initialize(ctx=cls.ctx)
        cls.fbo = cls.ctx.simple_framebuffer((64, 64), components=3)

    def test_draws_frame_with_background_and_texture(self) -> None:
        self.fbo.use()
        self.renderer.resize(64, 64)
        self.renderer.update(0.0)
        self.renderer.render()

        pixels = np.frombuffer(self.fbo.read(components=3), dtype=np.uint8).reshape(64, 64, 3)
        background = np.array([13, 15, 26], dtype=np.int64)  # 0.05/0.06/0.10 * 255

        corner = pixels[0, 0].astype(np.int64)
        self.assertTrue(
            np.all(np.abs(corner - background) <= 2),
            f"角落应为背景色，实际: {corner}",
        )

        center = pixels[32, 32].astype(np.int64)
        self.assertTrue(
            np.any(np.abs(center - background) > 8),
            f"中心应包含纹理内容，实际: {center}",
        )


if __name__ == "__main__":
    unittest.main()
