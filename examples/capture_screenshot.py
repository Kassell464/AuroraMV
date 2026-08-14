"""示例：截取一帧渲染画面保存为 PNG（截图 / 宣传图）。

用法：
    python examples/capture_screenshot.py [音频路径] [输出路径]

默认在节拍闪光时刻截取「赛博朋克」场景，输出到 docs/assets/screenshot.png。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # 项目根目录

import moderngl
import numpy as np
from PIL import Image

from core.audio.analyzer import AudioAnalyzer
from core.renderer.engine import Renderer
from core.renderer.scene import BackgroundSpec, Scene

WIDTH, HEIGHT = 1280, 720


def main(argv: list[str] | None = None) -> int:
    args = list(argv or sys.argv[1:])
    root = Path(__file__).resolve().parent.parent
    audio = args[0] if args else str(root / "assets" / "audio" / "demo.wav")
    output = args[1] if len(args) > 1 else str(root / "docs" / "assets" / "screenshot.png")
    Path(output).parent.mkdir(parents=True, exist_ok=True)

    ctx = moderngl.create_context(standalone=True)
    renderer = Renderer()
    try:
        renderer.initialize(ctx=ctx)
        renderer.resize(WIDTH, HEIGHT)
        fbo = ctx.simple_framebuffer((WIDTH, HEIGHT), components=4)

        # 赛博朋克风格场景（品红网格 + 霓虹歌词模板 + 闪光/震动）
        scene = Scene(
            id=1,
            start_time=0.0,
            end_time=1e9,
            background=BackgroundSpec(
                "neon_grid", params={"color": [1.0, 0.15, 0.65], "speed": 1.4}
            ),
            lyric_template="neon",
            effects=["flash", "beat_shake"],
        )
        renderer.load_scene(scene)

        analyzer = AudioAnalyzer()
        analyzer.load(audio)
        # 取第三个节拍时刻：闪光与震动处于峰值
        t = float(analyzer.beat_times[2]) if len(analyzer.beat_times) > 2 else 2.0
        renderer.update(t, analyzer.get_state(t))
        renderer.render(target=fbo)

        rgba = np.frombuffer(fbo.read(components=4), dtype=np.uint8).reshape(
            HEIGHT, WIDTH, 4
        )
        Image.fromarray(rgba, "RGBA").save(output)
        print("已保存截图:", output)
    finally:
        ctx.release()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
