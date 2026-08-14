"""应用控制器（ApplicationController）。

职责：创建主窗口与音频引擎并完成装配；本模块不含渲染逻辑。
阶段 3：加载演示音频并播放，注入 AudioState 来源。
阶段 4：注入波形采样来源（波形背景用）。
阶段 5：加载场景预设（MineRadio 概念灵感），按音乐时间自动切换场景。
阶段 6：支持 --audio / --lrc 装配歌词提供器。
"""

from __future__ import annotations

import sys
from pathlib import Path

from core.audio.engine import AudioEngine
from core.lyrics.provider import LRCProvider
from core.renderer.scene import SceneManager, load_scene_presets, scenes_from_presets
from ui.main_window import MainWindow

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEMO_AUDIO = PROJECT_ROOT / "assets" / "audio" / "demo.wav"
SCENE_PRESETS_DIR = PROJECT_ROOT / "templates" / "scene"


class ApplicationController:
    def __init__(
        self, audio_path: str | None = None, lrc_path: str | None = None
    ) -> None:
        self.window = MainWindow()
        self.audio = AudioEngine()
        self.window.preview.set_audio_state_provider(self.audio.get_state)
        self.window.preview.set_waveform_provider(self.audio.get_waveform)

        if lrc_path:
            self.window.preview.renderer.set_lyrics_provider(LRCProvider(lrc_path))

        chosen_audio = audio_path or (str(DEMO_AUDIO) if DEMO_AUDIO.exists() else None)
        if chosen_audio:
            try:
                self.audio.load(chosen_audio)
                self.audio.play()
                self._setup_scenes()
            except Exception as exc:  # 无音频设备等场景下优雅降级
                print(f"[AuroraMV] 音频加载/播放失败: {exc}", file=sys.stderr)

    def _setup_scenes(self) -> None:
        """把场景预设均分到整首曲目（阶段 5 演示：背景随时间自动切换）。"""
        presets = load_scene_presets(str(SCENE_PRESETS_DIR))
        if not presets or self.audio.duration <= 0:
            return
        scenes = scenes_from_presets(presets, self.audio.duration)
        self.window.preview.renderer.set_scene_manager(SceneManager(scenes))

    def show(self) -> None:
        self.window.show()
