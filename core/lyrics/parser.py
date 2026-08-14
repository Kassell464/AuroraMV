"""LRC 解析器（规格 24 节）。

输入：[00:12.50] Hello World → 输出 LyricLine(text="Hello World", start=12.5, end=16.0)。

支持：
- [m:ss.xx] / [mm:ss.xxx] 时间标签（分秒 + 1~3 位小数）
- 单行多时间标签（重复段落）
- [ti:] [ar:] [al:] [by:] 等元数据
- [offset:] 整体偏移（毫秒）
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_TIMESTAMP_RE = re.compile(r"\[(\d{1,3}):(\d{2})(?:[.:](\d{1,3}))?\]")
_METADATA_RE = re.compile(r"\[([a-zA-Z]+):(.*)\]")

# 最后一行歌词的默认持续时长（秒）
LAST_LINE_DURATION = 5.0


@dataclass(frozen=True, slots=True)
class LyricLine:
    """一行歌词及其时间范围（秒）。"""

    text: str
    start: float
    end: float


def parse_lrc(content: str) -> tuple[dict[str, str], list[LyricLine]]:
    """解析 LRC 文本，返回 (元数据, 按时间升序的歌词行)。"""
    metadata: dict[str, str] = {}
    offset = 0.0
    entries: list[tuple[float, str]] = []

    for raw in content.splitlines():
        line = raw.strip()
        if not line:
            continue
        tags = list(_TIMESTAMP_RE.finditer(line))
        if tags:
            text = _TIMESTAMP_RE.sub("", line).strip()
            if text:
                for tag in tags:
                    minutes = int(tag.group(1))
                    seconds = int(tag.group(2))
                    fraction = tag.group(3)
                    millis = 0.0
                    if fraction:
                        millis = int(fraction) / (10 ** len(fraction))
                    entries.append((minutes * 60 + seconds + millis, text))
            continue
        meta = _METADATA_RE.match(line)
        if meta and meta.group(2).strip():
            key = meta.group(1).lower()
            value = meta.group(2).strip()
            if key == "offset":
                try:
                    offset = float(value) / 1000.0  # LRC 偏移单位：毫秒
                except ValueError:
                    pass
            else:
                metadata[key] = value

    entries.sort(key=lambda entry: entry[0])
    lines: list[LyricLine] = []
    for index, (start, text) in enumerate(entries):
        start += offset
        if index + 1 < len(entries):
            end = entries[index + 1][0] + offset
        else:
            end = start + LAST_LINE_DURATION
        lines.append(
            LyricLine(
                text=text,
                start=round(start, 3),
                end=round(max(end, start + 0.1), 3),
            )
        )
    return metadata, lines
