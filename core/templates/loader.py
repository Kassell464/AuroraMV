"""模板加载器（规格 34 节）：load / validate。

统一收口四类 JSON 模板：lyrics / background / effects / scene。
validate 返回错误列表；load 校验失败时抛出 TemplateError。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_BACKGROUND_TYPES = (
    "image",
    "galaxy",
    "waveform",
    "neon_grid",
    "vinyl",
    "planet",
    "tunnel",
    "spectrum",
)
_EFFECT_TYPES = ("beat_shake", "flash", "particle")
_KINDS = ("lyrics", "background", "effects", "scene")

# 各类型必填字段
_REQUIRED_FIELDS = {
    "lyrics": (),
    "background": ("type",),
    "effects": ("type",),
    "scene": ("background",),
}

_HEX_COLOR_RE = re.compile(r"#[0-9a-fA-F]{6}")


class TemplateError(RuntimeError):
    """模板加载或校验失败。"""


class TemplateLoader:
    """模板加载器（规格 34 节）。"""

    def load(self, path: str, kind: str | None = None) -> dict:
        """加载并校验 JSON 模板。kind 缺省时从目录名推断。"""
        resolved_kind = kind or _infer_kind(path)
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, dict):
            raise TemplateError(f"模板根节点必须是对象: {path}")
        errors = self.validate(data, resolved_kind)
        if errors:
            raise TemplateError(f"模板校验失败 {path}: {'; '.join(errors)}")
        return data

    def validate(self, data: dict, kind: str) -> list[str]:
        """校验模板，返回错误列表（空列表 = 通过）。"""
        if kind not in _KINDS:
            return [f"未知模板类型: {kind}（可选 {', '.join(_KINDS)}）"]
        errors: list[str] = []
        for field in _REQUIRED_FIELDS[kind]:
            if not data.get(field):
                errors.append(f"缺少字段: {field}")
        if kind == "background":
            if data.get("type") not in _BACKGROUND_TYPES:
                errors.append(
                    f"未知背景类型: {data.get('type')}（可选 {', '.join(_BACKGROUND_TYPES)}）"
                )
        elif kind == "effects":
            if data.get("type") not in _EFFECT_TYPES:
                errors.append(
                    f"未知效果类型: {data.get('type')}（可选 {', '.join(_EFFECT_TYPES)}）"
                )
        elif kind == "lyrics":
            if "color" in data and not _HEX_COLOR_RE.fullmatch(str(data.get("color", ""))):
                errors.append(f"颜色格式应为 #rrggbb: {data.get('color')}")
        elif kind == "scene":
            background = data.get("background") or {}
            if not (background.get("type") or background.get("template")):
                errors.append("scene.background 需要 type 或 template")
        return errors


def _infer_kind(path: str) -> str:
    parent = Path(path).parent.name
    if parent in _KINDS:
        return parent
    normalized = path.replace("\\", "/")
    for kind in _KINDS:
        if f"/{kind}/" in normalized or normalized.startswith(f"{kind}/"):
            return kind
    return Path(path).stem
