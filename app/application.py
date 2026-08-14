"""应用控制器（ApplicationController）。

职责：创建主窗口与音频引擎并完成装配；本模块不含渲染逻辑。
阶段 3-4：注入 AudioState / 波形采样来源。
阶段 5：加载场景预设，按音乐时间自动切换场景。
阶段 6：支持 --audio / --lrc 装配歌词提供器。
阶段 10：控制面板装配（预设选择 / 效果调参 / 播放控制 / 后台导出）。
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QThread, QTimer, Signal

from core.audio.engine import AudioEngine
from core.lyrics.provider import LRCProvider
from core.renderer.scene import (
    Scene,
    SceneManager,
    load_scene_presets,
    scenes_from_presets,
)
from export.ffmpeg import ExportProject, ExportSettings, Exporter
from ui.main_window import MainWindow

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEMO_AUDIO = PROJECT_ROOT / "assets" / "audio" / "demo.wav"
SCENE_PRESETS_DIR = PROJECT_ROOT / "templates" / "scene"


class ExportWorker(QThread):
    """后台导出线程（阶段 10：导出时 UI 保持响应）。"""

    progress = Signal(int, int)
    finished_ok = Signal(str)
    failed = Signal(str)

    def __init__(
        self,
        project: ExportProject,
        settings: ExportSettings,
        output: str,
        parent: object | None = None,
    ) -> None:
        super().__init__(parent)
        self._project = project
        self._settings = settings
        self._output = output

    def run(self) -> None:
        try:
            result = Exporter().export(
                self._project,
                self._settings,
                self._output,
                on_progress=lambda done, total: self.progress.emit(done, total),
            )
            self.finished_ok.emit(result)
        except Exception as exc:  # 含 ExportError
            self.failed.emit(str(exc))


class ApplicationController:
    def __init__(
        self, audio_path: str | None = None, lrc_path: str | None = None
    ) -> None:
        self.window = MainWindow()
        self.audio = AudioEngine()
        self.window.preview.set_audio_state_provider(self.audio.get_state)
        self.window.preview.set_waveform_provider(self.audio.get_waveform)

        self.lrc_path = lrc_path
        self.scenes: list[Scene] = []
        self.presets = load_scene_presets(str(SCENE_PRESETS_DIR))
        self._presets_by_name = {p.name: p for p in self.presets}
        self._selected_preset: str | None = None
        self._export_worker: ExportWorker | None = None

        if lrc_path:
            self.window.preview.renderer.set_lyrics_provider(LRCProvider(lrc_path))

        chosen_audio = audio_path or (str(DEMO_AUDIO) if DEMO_AUDIO.exists() else None)
        self.audio_path = chosen_audio
        if chosen_audio:
            try:
                self.audio.load(chosen_audio)
                self.audio.play()
                self._setup_scenes()
            except Exception as exc:  # 无音频设备等场景下优雅降级
                print(f"[AuroraMV] 音频加载/播放失败: {exc}", file=sys.stderr)

        # 面板装配
        self.window.panel.set_presets(self.presets)
        self.window.panel.preset_selected.connect(self._on_preset_selected)
        self.window.panel.effect_param_changed.connect(self._on_effect_param)
        self.window.panel.play_pause_requested.connect(self._on_play_pause)
        self.window.panel.export_requested.connect(self._on_export)
        self.window.panel.seek_requested.connect(self._on_seek)
        self.window.panel.audio_file_selected.connect(self._on_audio_file)
        self.window.panel.lrc_file_selected.connect(self._on_lrc_file)
        self.window.panel.set_playing(self.audio.is_playing)

        # 进度轮询（拖动进度条期间不覆盖）
        self._progress_timer = QTimer()  # 控制器非 QObject，不能作 parent
        self._progress_timer.setInterval(250)
        self._progress_timer.timeout.connect(self._update_progress)
        self._progress_timer.start()

    def _setup_scenes(self) -> None:
        """把场景预设均分到整首曲目（阶段 5：自动切换）。"""
        if not self.presets or self.audio.duration <= 0:
            return
        self.scenes = scenes_from_presets(self.presets, self.audio.duration)
        self.window.preview.renderer.set_scene_manager(SceneManager(self.scenes))

    # ---------- 面板回调 ----------

    def _on_preset_selected(self, name: str) -> None:
        """选择视觉风格：'auto' 恢复自动切换，否则固定为该预设。"""
        self._selected_preset = None if name == "auto" else name
        renderer = self.window.preview.renderer
        if renderer.ctx is None:
            return  # 渲染器尚未初始化（正常在窗口显示后才会发生点击）
        if name == "auto":
            renderer.set_scene_manager(SceneManager(self.scenes))
            if self.scenes:
                renderer.load_scene(self.scenes[0])
            return
        preset = self._presets_by_name[name]
        scene = Scene(
            id=1,
            start_time=0.0,
            end_time=1e9,
            background=preset.background,
            lyric_template=preset.lyric_template,
            effects=list(preset.effects),
        )
        renderer.set_scene_manager(None)
        renderer.load_scene(scene)

    def _on_effect_param(self, name: str, key: str, value: float) -> None:
        self.window.preview.renderer.set_effect_param(name, **{key: value})

    def _on_play_pause(self) -> None:
        if self.audio.is_playing:
            self.audio.stop()
        else:
            self.audio.play()
        self.window.panel.set_playing(self.audio.is_playing)

    def _update_progress(self) -> None:
        self.window.panel.set_progress(self.audio.position, self.audio.duration)

    def _on_seek(self, seconds: float) -> None:
        self.audio.seek(seconds)
        self.window.panel.set_playing(True)

    def _on_audio_file(self, path: str) -> None:
        try:
            self.audio.load(path)
            self.audio.play()
            self.audio_path = path
            self._selected_preset = None
            self.window.panel.select_preset("auto")
            self._setup_scenes()
            self.window.panel.set_playing(True)
        except Exception as exc:
            self.window.panel.set_export_state("fail", f"音频加载失败: {exc}")

    def _on_lrc_file(self, path: str) -> None:
        self.lrc_path = path
        self.window.preview.renderer.set_lyrics_provider(LRCProvider(path))

    def _on_export(self, settings: ExportSettings, output: str) -> None:
        if not output:
            self.window.panel.set_export_state("fail", "请先选择输出路径")
            return
        if self._export_worker is not None and self._export_worker.isRunning():
            return
        scenes = None
        if self._selected_preset is not None:
            preset = self._presets_by_name[self._selected_preset]
            scenes = [
                Scene(
                    id=1,
                    start_time=0.0,
                    end_time=self.audio.duration or 8.0,
                    background=preset.background,
                    lyric_template=preset.lyric_template,
                    effects=list(preset.effects),
                )
            ]
        project = ExportProject(
            audio_path=self.audio_path or "", lrc_path=self.lrc_path, scenes=scenes
        )
        self.window.panel.set_export_state("running")
        worker = ExportWorker(project, settings, output, self)
        worker.progress.connect(self.window.panel.set_export_progress)
        worker.finished_ok.connect(lambda _: self.window.panel.set_export_state("ok"))
        worker.failed.connect(lambda msg: self.window.panel.set_export_state("fail", msg))
        worker.finished.connect(worker.deleteLater)
        self._export_worker = worker
        worker.start()

    def show(self) -> None:
        self.window.show()
