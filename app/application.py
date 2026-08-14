"""应用控制器（ApplicationController）。

职责：创建主窗口与音频引擎并完成装配；本模块不含渲染逻辑。
阶段 3：加载演示音频并播放，向预览控件注入 AudioState 来源。
阶段 4：注入波形采样来源（波形背景用）。
"""

from __future__ import annotations

import sys
from pathlib import Path

from core.audio.engine import AudioEngine
from ui.main_window import MainWindow

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEMO_AUDIO = PROJECT_ROOT / "assets" / "audio" / "demo.wav"


class ApplicationController:
    def __init__(self) -> None:
        self.window = MainWindow()
        self.audio = AudioEngine()
        self.window.preview.set_audio_state_provider(self.audio.get_state)
        self.window.preview.set_waveform_provider(self.audio.get_waveform)

        if DEMO_AUDIO.exists():
            try:
                self.audio.load(str(DEMO_AUDIO))
                self.audio.play()
            except Exception as exc:  # 无音频设备等场景下优雅降级
                print(f"[AuroraMV] 演示音频加载/播放失败: {exc}", file=sys.stderr)

    def show(self) -> None:
        self.window.show()
