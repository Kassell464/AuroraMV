"""UI 层测试（阶段 10，offscreen 无显示环境）。

控制面板：卡片构建、预设选择信号、效果滑杆信号、导出信号；
渲染器：效果参数持久化（滑杆调参跨场景保持）。
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest

from PySide6.QtWidgets import QApplication

_APP = QApplication.instance() or QApplication([])

from core.renderer.scene import BackgroundSpec, ScenePreset
from ui.panels.control_panel import ControlPanel


def _preset(name: str) -> ScenePreset:
    return ScenePreset(
        name=name,
        background=BackgroundSpec("galaxy"),
        lyric_template="minimal",
        effects=[],
    )


class ControlPanelTestCase(unittest.TestCase):
    def test_builds_cards_for_presets(self) -> None:
        panel = ControlPanel()
        panel.set_presets([_preset("cinema"), _preset("dj")])
        self.assertEqual(len(panel.cards), 2)
        self.assertIn("cinema", panel.cards)
        self.assertIn("dj", panel.cards)
        self.assertIsNotNone(panel._auto_card)

    def test_preset_card_emits_signal(self) -> None:
        panel = ControlPanel()
        panel.set_presets([_preset("aurora")])
        received: list[str] = []
        panel.preset_selected.connect(received.append)
        panel.cards["aurora"].clicked.emit("aurora")
        self.assertEqual(received, ["aurora"])

    def test_effect_slider_emits_scaled_value(self) -> None:
        panel = ControlPanel()
        received: list[tuple[str, str, float]] = []
        panel.effect_param_changed.connect(
            lambda n, k, v: received.append((n, k, v))
        )
        panel._shake_slider.setValue(45)
        self.assertTrue(received)
        name, key, value = received[-1]
        self.assertEqual((name, key), ("beat_shake", "strength"))
        self.assertAlmostEqual(value, 0.027)  # 45 * 0.0006

    def test_export_button_emits_settings(self) -> None:
        panel = ControlPanel()
        received: list[tuple[object, str]] = []
        panel.export_requested.connect(lambda s, o: received.append((s, o)))
        panel._export_button.click()
        self.assertTrue(received)
        settings, output = received[0]
        self.assertEqual(settings.format, "mp4")
        self.assertEqual(settings.resolution, "1080p")
        self.assertEqual(output, "output.mp4")


class RendererEffectParamTestCase(unittest.TestCase):
    def test_set_effect_param_persists(self) -> None:
        from core.renderer.engine import Renderer

        renderer = Renderer()
        renderer.set_effect_param("flash", intensity=0.5)
        self.assertEqual(renderer._effect_param_overrides["flash"]["intensity"], 0.5)
        renderer.set_effect_param("particle", base_count=120)
        self.assertEqual(renderer._effect_param_overrides["particle"]["base_count"], 120)


if __name__ == "__main__":
    unittest.main()
