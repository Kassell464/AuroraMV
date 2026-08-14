"""效果模板（可调节参数以 JSON 形式存放于 templates/effects/）。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class EffectSpec:
    """效果规格：类型 + 参数（JSON）。"""

    name: str
    type: str
    params: dict[str, object]


def load_effect_spec(path: str) -> EffectSpec:
    """从 JSON 加载效果规格。"""
    with open(path, encoding="utf-8") as file:
        data = json.load(file)
    return EffectSpec(
        name=str(data.get("name", Path(path).stem)),
        type=str(data.get("type", Path(path).stem)),
        params=dict(data.get("params") or {}),
    )
