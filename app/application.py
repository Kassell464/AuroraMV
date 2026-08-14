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

from PySide6.QtCore import QSettings, QThread, QTimer, Signal

from core.audio.engine import AudioEngine
from core.lyrics.provider import LRCProvider
from core.renderer.scene import (
    Scene,
    SceneManager,
    load_scene_presets,
    scenes_from_presets,
)
from export.ffmpeg import ExportProject, ExportSettings, Exporter
from ui.desktop_lyrics import DesktopLyricsWindow
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
        self.window.preview.set_spectrum_provider(self.audio.get_spectrum)

        self.lrc_path = lrc_path
        self._lyrics_provider: LRCProvider | None = None
        self.scenes: list[Scene] = []
        self.presets = load_scene_presets(str(SCENE_PRESETS_DIR))
        self._presets_by_name = {p.name: p for p in self.presets}
        self._selected_preset: str | None = None
        self._export_worker: ExportWorker | None = None
        self._desktop_lyrics: DesktopLyricsWindow | None = None

        if lrc_path:
            self._lyrics_provider = LRCProvider(lrc_path)
            self.window.preview.renderer.set_lyrics_provider(self._lyrics_provider)

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
        self.window.panel.export_requested.connect(self._on_export)
        self.window.panel.audio_file_selected.connect(self._on_audio_file)
        self.window.panel.lrc_file_selected.connect(self._on_lrc_file)
        self.window.panel.cover_file_selected.connect(self._on_cover_file)
        self.window.panel.desktop_lyrics_toggled.connect(self._on_desktop_lyrics_toggled)

        # 播放底栏
        self.window.bar.seek_requested.connect(self._on_seek)
        self.window.bar.play_pause_requested.connect(self._on_play_pause)
        self.window.bar.lyrics_toggled.connect(self._on_lyrics_toggled)
        self.window.bar.set_playing(self.audio.is_playing)
        self._bar_playing = self.audio.is_playing
        self._update_track_info()

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
            self.audio.pause()
        else:
            self.audio.play()  # 暂停中则续播，否则从头
        self._bar_playing = self.audio.is_playing
        self.window.bar.set_playing(self._bar_playing)

    def _update_progress(self) -> None:
        position = self.audio.position
        self.window.bar.set_progress(position, self.audio.duration)
        playing = self.audio.is_playing
        if self._bar_playing != playing:
            # 播放结束（或任何状态变化）时同步底栏播放键
            self._bar_playing = playing
            self.window.bar.set_playing(playing)
        self._update_desktop_lyrics(position)

    def _update_track_info(self) -> None:
        """底栏显示当前歌曲名与歌词名。"""
        title = Path(self.audio_path).stem if self.audio_path else "—"
        subtitle = f"歌词：{Path(self.lrc_path).name}" if self.lrc_path else "无歌词"
        self.window.bar.set_track(title, subtitle)

    def _on_seek(self, seconds: float) -> None:
        self.audio.seek(seconds)
        self._bar_playing = True
        self.window.bar.set_playing(True)

    def _on_lyrics_toggled(self, enabled: bool) -> None:
        self.window.preview.renderer.set_lyrics_visible(enabled)

    def _on_audio_file(self, path: str) -> None:
        try:
            self.audio.load(path)
            self.audio.play()
            self.audio_path = path
            self._selected_preset = None
            self.window.panel.select_preset("auto")
            self._setup_scenes()
            self.window.bar.set_playing(True)
            self._update_track_info()
        except Exception as exc:
            self.window.panel.set_export_state("fail", f"音频加载失败: {exc}")

    def _on_lrc_file(self, path: str) -> None:
        self.lrc_path = path
        self._lyrics_provider = LRCProvider(path)
        self.window.preview.renderer.set_lyrics_provider(self._lyrics_provider)
        self._update_track_info()

    # ---------- 桌面歌词 ----------

    def _on_desktop_lyrics_toggled(self, enabled: bool) -> None:
        """开关置顶桌面歌词小窗（位置记忆）。"""
        if enabled:
            if self._desktop_lyrics is None:
                self._desktop_lyrics = DesktopLyricsWindow()
            settings = QSettings("AuroraMV", "AuroraMV")
            pos = settings.value("desktopLyrics/pos")
            if pos is not None:
                self._desktop_lyrics.move(pos)
            self._desktop_lyrics.show()
            self._update_desktop_lyrics(self.audio.position)
        elif self._desktop_lyrics is not None:
            QSettings("AuroraMV", "AuroraMV").setValue(
                "desktopLyrics/pos", self._desktop_lyrics.pos()
            )
            self._desktop_lyrics.hide()

    def _update_desktop_lyrics(self, position: float) -> None:
        """桌面歌词小窗跟随播放进度更新当前行（颜色跟随歌词模板）。"""
        window = self._desktop_lyrics
        if window is None or not window.isVisible():
            return
        text = ""
        if self._lyrics_provider is not None:
            line = self._lyrics_provider.get_current_line(position)
            text = line.text if line is not None else ""
        color = (1.0, 1.0, 1.0)
        lyrics = self.window.preview.renderer.lyrics
        if lyrics is not None:
            color = lyrics.template.color
        window.set_lyric(text, color)

    def _on_cover_file(self, path: str) -> None:
        """导入专辑封面（黑胶唱片/封面粒子背景使用）。"""
        try:
            self.window.preview.renderer.set_cover_image(path)
        except Exception as exc:
            self.window.panel.set_export_state("fail", f"封面加载失败: {exc}")

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
        worker.finished_ok.connect(
            lambda path: self.window.panel.set_export_state("ok", path)
        )
        worker.failed.connect(lambda msg: self.window.panel.set_export_state("fail", msg))
        worker.finished.connect(worker.deleteLater)
        self._export_worker = worker
        worker.start()

    def show(self) -> None:
        self.window.show()
