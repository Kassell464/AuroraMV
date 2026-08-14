"""歌词提供器（规格 23 节）。

统一接口 LyricsProvider：load / get_current_line(time)。
实现：LRCProvider（LRC 文件）；后续阶段将加入 ManualProvider / WhisperProvider。
"""

from __future__ import annotations

from core.lyrics.parser import LyricLine, parse_lrc


class LyricsProvider:
    """歌词提供器统一接口。"""

    def load(self) -> None:
        raise NotImplementedError

    def get_current_line(self, time: float) -> LyricLine | None:
        raise NotImplementedError


def _read_text_file(path: str) -> str:
    """按 UTF-8 → GBK 顺序尝试解码文本文件（兼容常见 LRC 编码）。"""
    for encoding in ("utf-8-sig", "utf-8", "gbk"):
        try:
            with open(path, encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError(f"无法解码歌词文件: {path}")


class LRCProvider(LyricsProvider):
    """从 LRC 文件提供歌词。"""

    def __init__(self, path: str | None = None) -> None:
        self.metadata: dict[str, str] = {}
        self._lines: list[LyricLine] = []
        if path is not None:
            self.load_file(path)

    @property
    def lines(self) -> list[LyricLine]:
        return list(self._lines)

    def load_file(self, path: str) -> None:
        """加载 LRC 文件（自动识别 UTF-8 / GBK 编码）。"""
        self.metadata, self._lines = parse_lrc(_read_text_file(path))

    def load_text(self, content: str) -> None:
        """从 LRC 文本加载。"""
        self.metadata, self._lines = parse_lrc(content)

    def load(self) -> None:
        """接口占位：请使用 load_file(path) 或 load_text(content)。"""
        raise NotImplementedError("请使用 load_file(path) 或 load_text(content)")

    def get_current_line(self, time: float) -> LyricLine | None:
        """返回覆盖 time 的歌词行；无覆盖时返回 None。"""
        for line in self._lines:
            if line.start <= time < line.end:
                return line
        return None
