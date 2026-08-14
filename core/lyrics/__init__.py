"""AuroraMV 歌词引擎包。

解析歌词、时间同步、动画（规格 22 节）。
渲染实现在 core.renderer.lyrics（歌词渲染器）。
"""

from core.lyrics.parser import LyricLine, parse_lrc

__all__ = ["LyricLine", "parse_lrc"]
