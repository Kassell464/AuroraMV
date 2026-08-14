"""示例：程序化导出多格式视频（演示导出系统的多种选项）。

用法：
    python examples/export_video.py [音频路径] [输出目录]

无参数时使用内置演示曲，输出到项目根目录的 exports/。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # 项目根目录

from export.ffmpeg import ExportProject, ExportSettings, Exporter


def main(argv: list[str] | None = None) -> int:
    args = list(argv or sys.argv[1:])
    root = Path(__file__).resolve().parent.parent
    audio = args[0] if args else str(root / "assets" / "audio" / "demo.wav")
    out_dir = Path(args[1]) if len(args) > 1 else root / "exports"
    out_dir.mkdir(exist_ok=True)

    # 三种典型输出：横屏 MP4、竖屏 WebM、方形 MOV
    combos = [
        (
            "demo-1080p.mp4",
            ExportSettings(format="mp4", resolution="1080p", fps=30),
        ),
        (
            "demo-vertical.webm",
            ExportSettings(format="webm", resolution="720p", fps=24, aspect="9:16"),
        ),
        (
            "demo-square.mov",
            ExportSettings(format="mov", resolution="480p", fps=30, aspect="1:1"),
        ),
    ]

    exporter = Exporter()
    for name, settings in combos:
        output = exporter.export(
            ExportProject(audio_path=audio),
            settings,
            str(out_dir / name),
            on_progress=lambda d, t, n=name: print(f"{n}: {d}/{t} 帧", end="\r"),
        )
        print(f"完成: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
