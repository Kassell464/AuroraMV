"""AuroraMV 程序入口。

- 默认：启动预览窗口；支持 --audio / --lrc 参数。
- 导出模式（阶段 9）：--export 指定输出文件，不打开窗口，
  支持多格式（mp4/webm/mov）与多选项（分辨率/FPS/宽高比/码率/裁剪）。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.application import ApplicationController

_DEFAULT_AUDIO = Path(__file__).resolve().parent / "assets" / "audio" / "demo.wav"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="AuroraMV", description="AuroraMV 音乐可视化与 MV 生成"
    )
    parser.add_argument("--audio", help="音频文件路径（默认使用内置演示音频）")
    parser.add_argument("--lrc", help="LRC 歌词文件路径")
    parser.add_argument("--export", help="导出视频到指定文件（如 out.mp4；不打开窗口）")
    parser.add_argument(
        "--format", choices=("mp4", "webm", "mov"), default="mp4", help="导出格式"
    )
    parser.add_argument(
        "--resolution",
        choices=("360p", "480p", "720p", "1080p", "1440p"),
        default="1080p",
        help="导出分辨率",
    )
    parser.add_argument("--fps", type=int, choices=(24, 30, 60), default=30, help="导出帧率")
    parser.add_argument(
        "--aspect", choices=("16:9", "9:16", "1:1"), default="16:9", help="导出宽高比"
    )
    parser.add_argument("--bitrate", default="auto", help="码率（auto 或如 8M）")
    parser.add_argument("--trim", type=float, default=None, help="只导出前 N 秒")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.export:
        return _run_export(args)

    app = QApplication(sys.argv)
    app.setApplicationName("AuroraMV")
    controller = ApplicationController(audio_path=args.audio, lrc_path=args.lrc)
    controller.show()
    return app.exec()


def _run_export(args: argparse.Namespace) -> int:
    from export.ffmpeg import ExportError, ExportProject, ExportSettings, Exporter

    audio = args.audio or str(_DEFAULT_AUDIO)
    settings = ExportSettings(
        format=args.format,
        resolution=args.resolution,
        fps=args.fps,
        aspect=args.aspect,
        bitrate=args.bitrate,
        trim=args.trim,
    )
    project = ExportProject(audio_path=audio, lrc_path=args.lrc)

    def on_progress(done: int, total: int) -> None:
        print(f"导出进度: {done}/{total} 帧 ({done * 100 // total}%)", flush=True)

    try:
        output = Exporter().export(project, settings, args.export, on_progress=on_progress)
    except ExportError as exc:
        print(f"导出失败: {exc}", file=sys.stderr)
        return 1
    print("导出完成:", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
