"""AuroraMV 程序入口。

启动主窗口；支持 --audio / --lrc 参数（阶段 6：真实歌曲与歌词测试）。
"""

from __future__ import annotations

import argparse
import sys

from PySide6.QtWidgets import QApplication

from app.application import ApplicationController


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="AuroraMV", description="AuroraMV 音乐可视化与 MV 生成"
    )
    parser.add_argument("--audio", help="音频文件路径（默认使用内置演示音频）")
    parser.add_argument("--lrc", help="LRC 歌词文件路径")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    app = QApplication(sys.argv)
    app.setApplicationName("AuroraMV")

    controller = ApplicationController(audio_path=args.audio, lrc_path=args.lrc)
    controller.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
