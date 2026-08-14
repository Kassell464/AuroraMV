"""场景系统（规格 29-31 节）。

AuroraMV V0.1 不使用传统 Timeline，使用 Scene：
一个时间范围内的完整视觉状态（背景 + 歌词模板 + 效果）。

- Scene：场景数据模型（规格 30 节）
- SceneManager：根据当前时间返回场景（规格 31 节）
- ScenePreset / load_scene_presets：场景模板（完整视觉组合，规格 33 节）
- scene_from_dict：解析规格 36 节项目 JSON 中的 scene 对象
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from core.templates.loader import TemplateLoader


@dataclass(frozen=True, slots=True)
class BackgroundSpec:
    """背景规格：类型（image/galaxy/waveform/neon_grid）+ 可选资源路径 + 参数。"""

    kind: str
    source: str | None = None
    params: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class ScenePreset:
    """场景预设（模板）：完整视觉组合，不含时间（规格 33 节）。"""

    name: str
    background: BackgroundSpec
    lyric_template: str | None = None
    effects: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Scene:
    """场景：一个时间范围内的完整视觉状态（规格 30 节）。"""

    id: int
    start_time: float
    end_time: float
    background: BackgroundSpec
    lyric_template: str | None = None
    effects: list[str] = field(default_factory=list)


class SceneManager:
    """场景管理器：根据当前时间返回场景（规格 31 节）。"""

    def __init__(self, scenes: Sequence[Scene] | None = None) -> None:
        self.scenes: list[Scene] = []
        for scene in scenes or []:
            self.add(scene)

    def add(self, scene: Scene) -> None:
        """添加场景并按开始时间排序。"""
        if scene.end_time <= scene.start_time:
            raise ValueError(
                f"场景 {scene.id} 时间范围无效: {scene.start_time}..{scene.end_time}"
            )
        self.scenes.append(scene)
        self.scenes.sort(key=lambda s: s.start_time)

    def get_scene(self, time: float) -> Scene | None:
        """返回覆盖 time 的场景；无覆盖时返回 None。"""
        for scene in self.scenes:
            if scene.start_time <= time < scene.end_time:
                return scene
        return None


def scene_from_dict(data: dict) -> Scene:
    """从规格 36 节的 scene JSON 对象构建场景。"""
    background = data.get("background") or {}
    lyrics = data.get("lyrics") or {}
    params = background.get("params")
    return Scene(
        id=int(data["id"]),
        start_time=float(data["start"]),
        end_time=float(data["end"]),
        background=BackgroundSpec(
            kind=str(background.get("type", "galaxy")),
            source=background.get("path"),
            params=dict(params) if isinstance(params, dict) else None,
        ),
        lyric_template=lyrics.get("template"),
        effects=[str(e) for e in data.get("effects", [])],
    )


def load_scene_presets(directory: str) -> list[ScenePreset]:
    """加载目录下所有场景预设 JSON（按文件名排序，经 TemplateLoader 校验）。

    背景支持两种写法（可混用，内联键覆盖模板键）：
    - {"template": "<名称>"} → 解析 templates/background/<名称>.json；
    - {"type": ..., "path": ..., "params": ...} → 内联定义。
    """
    loader = TemplateLoader()
    background_dir = Path(directory).resolve().parent / "background"
    presets: list[ScenePreset] = []
    for path in sorted(Path(directory).glob("*.json")):
        data = loader.load(str(path), "scene")
        background = _resolve_background(background_dir, data.get("background") or {})
        lyrics = data.get("lyrics") or {}
        presets.append(
            ScenePreset(
                name=str(data.get("name", path.stem)),
                background=background,
                lyric_template=lyrics.get("template"),
                effects=[str(e) for e in data.get("effects", [])],
            )
        )
    return presets


def _resolve_background(background_dir: Path, spec: dict) -> BackgroundSpec:
    """解析背景规格：处理 template 引用与内联参数合并。"""
    background = dict(spec)
    template_name = background.pop("template", None)
    if template_name:
        template_path = background_dir / f"{template_name}.json"
        if template_path.exists():
            template_data = TemplateLoader().load(str(template_path), "background")
            merged = dict(template_data)
            merged.update(background)  # 内联键覆盖模板
            background = merged
        # 模板缺失：退回内联（可能为空 → 默认 galaxy）
    params = background.get("params")
    return BackgroundSpec(
        kind=str(background.get("type", "galaxy")),
        source=background.get("path"),
        params=dict(params) if isinstance(params, dict) else None,
    )


def scenes_from_presets(
    presets: Sequence[ScenePreset], duration: float, start: float = 0.0
) -> list[Scene]:
    """把视觉预设按时间均分到 [start, start+duration)，生成带时间的场景列表。"""
    if not presets or duration <= 0:
        return []
    slot = duration / len(presets)
    scenes: list[Scene] = []
    for index, preset in enumerate(presets):
        scenes.append(
            Scene(
                id=index + 1,
                start_time=start + index * slot,
                end_time=start + (index + 1) * slot,
                background=preset.background,
                lyric_template=preset.lyric_template,
                effects=list(preset.effects),
            )
        )
    return scenes
