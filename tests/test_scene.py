"""场景系统最小验证（阶段 5）。

Scene 数据模型、SceneManager 边界行为、预设加载（无需 OpenGL）。
"""

import os
import unittest

from core.renderer.scene import (
    BackgroundSpec,
    Scene,
    SceneManager,
    load_scene_presets,
    scene_from_dict,
    scenes_from_presets,
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRESETS_DIR = os.path.join(PROJECT_ROOT, "templates", "scene")


class SceneFromDictTestCase(unittest.TestCase):
    def test_parses_spec_project_schema(self) -> None:
        """规格 36 节的 scene JSON 对象可正确解析。"""
        data = {
            "id": 1,
            "start": 0,
            "end": 30,
            "background": {"type": "image", "path": "assets/bg/a.jpg"},
            "lyrics": {"template": "neon"},
            "effects": ["beat_shake"],
        }
        scene = scene_from_dict(data)
        self.assertEqual(scene.id, 1)
        self.assertEqual(scene.start_time, 0.0)
        self.assertEqual(scene.end_time, 30.0)
        self.assertEqual(scene.background.kind, "image")
        self.assertEqual(scene.background.source, "assets/bg/a.jpg")
        self.assertEqual(scene.lyric_template, "neon")
        self.assertEqual(scene.effects, ["beat_shake"])


class SceneManagerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = SceneManager()
        self.manager.add(
            Scene(id=2, start_time=10.0, end_time=20.0, background=BackgroundSpec("galaxy"))
        )
        self.manager.add(
            Scene(id=1, start_time=0.0, end_time=10.0, background=BackgroundSpec("neon_grid"))
        )

    def test_scenes_sorted_by_start_time(self) -> None:
        self.assertEqual([s.id for s in self.manager.scenes], [1, 2])

    def test_get_scene_returns_scene_by_time(self) -> None:
        self.assertEqual(self.manager.get_scene(0.0).id, 1)  # type: ignore[union-attr]
        self.assertEqual(self.manager.get_scene(9.99).id, 1)  # type: ignore[union-attr]
        self.assertEqual(self.manager.get_scene(10.0).id, 2)  # 边界切换  # type: ignore[union-attr]
        self.assertEqual(self.manager.get_scene(19.99).id, 2)  # type: ignore[union-attr]

    def test_get_scene_none_outside_scenes(self) -> None:
        self.assertIsNone(self.manager.get_scene(-1.0))
        self.assertIsNone(self.manager.get_scene(20.0))

    def test_add_rejects_invalid_time_range(self) -> None:
        with self.assertRaises(ValueError):
            self.manager.add(Scene(id=9, start_time=5.0, end_time=5.0, background=BackgroundSpec("galaxy")))


class ScenePresetTestCase(unittest.TestCase):
    def test_loads_all_presets(self) -> None:
        presets = load_scene_presets(PRESETS_DIR)
        names = {p.name for p in presets}
        for expected in (
            "cinema", "aurora", "cyberpunk", "stage", "synthwave", "dj",
            "vinyl", "planet", "tunnel", "spectrum",
        ):
            self.assertIn(expected, names)

    def test_presets_have_background_kinds(self) -> None:
        presets = load_scene_presets(PRESETS_DIR)
        kinds = {p.background.kind for p in presets}
        self.assertEqual(
            kinds,
            {"image", "galaxy", "neon_grid", "waveform", "vinyl", "planet", "tunnel", "spectrum"},
        )

    def test_scenes_from_presets_divides_duration(self) -> None:
        presets = load_scene_presets(PRESETS_DIR)
        scenes = scenes_from_presets(presets, duration=8.0)
        self.assertEqual(len(scenes), len(presets))
        self.assertEqual(scenes[0].start_time, 0.0)
        self.assertEqual(scenes[-1].end_time, 8.0)
        # 每个场景时长相等（均分整首曲目）
        slot = 8.0 / len(presets)
        for scene in scenes:
            self.assertAlmostEqual(scene.end_time - scene.start_time, slot, places=6)


if __name__ == "__main__":
    unittest.main()
