"""歌词模板系统（规格 26 节）。

templates/lyrics/*.json：字体、颜色、动画（enter / idle / beat）。
字体按模板名解析，缺省回退到系统 CJK 字体（微软雅黑 / 黑体 / 宋体）。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from core.templates.loader import TemplateLoader

_FONT_CANDIDATES = ("msyh.ttc", "msyhbd.ttc", "simhei.ttf", "simsun.ttc")
_WINDOWS_FONT_DIR = r"C:\Windows\Fonts"
_OTHER_FONT_DIRS = ("/usr/share/fonts", "/System/Library/Fonts")


@dataclass(frozen=True, slots=True)
class LyricAnimation:
    """歌词动画配置：enter（入场）/ idle（待机）/ beat（节拍）。"""

    enter: str = "fade"
    idle: str | None = None
    beat: str | None = None


@dataclass(frozen=True, slots=True)
class LyricTemplate:
    """歌词模板：字体、颜色与动画（规格 26 节 JSON 结构）。"""

    name: str
    font: str = "msyh.ttc"
    color: tuple[float, float, float] = (1.0, 1.0, 1.0)
    glow: tuple[float, float, float] = (1.0, 1.0, 1.0)
    animation: LyricAnimation = field(default_factory=LyricAnimation)


def hex_to_rgb(value: str) -> tuple[float, float, float]:
    """'#ffffff' → (1.0, 1.0, 1.0)。"""
    value = value.strip().lstrip("#")
    return (
        int(value[0:2], 16) / 255.0,
        int(value[2:4], 16) / 255.0,
        int(value[4:6], 16) / 255.0,
    )


def load_lyric_template(path: str) -> LyricTemplate:
    """从 JSON 加载歌词模板（经 TemplateLoader 校验）。"""
    data = TemplateLoader().load(path, "lyrics")
    animation = data.get("animation") or {}
    return LyricTemplate(
        name=str(data.get("name", Path(path).stem)),
        font=str(data.get("font", "msyh.ttc")),
        color=hex_to_rgb(str(data.get("color", "#ffffff"))),
        glow=hex_to_rgb(str(data.get("glow", data.get("color", "#ffffff")))),
        animation=LyricAnimation(
            enter=str(animation.get("enter", "fade")),
            idle=animation.get("idle"),
            beat=animation.get("beat"),
        ),
    )


def resolve_font(font: str) -> str | None:
    """在常见目录解析字体文件；找不到返回 None（回退 PIL 默认字体）。"""
    if os.path.exists(font):
        return font
    name = os.path.splitext(os.path.basename(font))[0].lower()
    candidates = list(dict.fromkeys([font, *_FONT_CANDIDATES]))
    directories = [d for d in ("" if False else [])]  # 空目录占位（相对路径按原样尝试）
    if os.path.isdir(_WINDOWS_FONT_DIR):
        directories.append(_WINDOWS_FONT_DIR)
    directories.extend(d for d in _OTHER_FONT_DIRS if os.path.isdir(d))
    for directory in directories:
        for candidate in candidates:
            path = os.path.join(directory, candidate) if directory else candidate
            if os.path.exists(path):
                return path
        if directory:
            for filename in os.listdir(directory):
                base = os.path.splitext(filename)[0].lower()
                if name and base.startswith(name):
                    return os.path.join(directory, filename)
    return None
