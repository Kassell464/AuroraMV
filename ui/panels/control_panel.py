"""控制面板（阶段 10）：深色主题、动画、卡片、可视化选择器。

本面板属于 UI 层，不包含渲染逻辑：所有操作经信号转发给控制器
（对应架构规则 1：UI → Renderer API → OpenGL）。
"""

from __future__ import annotations

from PySide6.QtCore import (
    QAbstractAnimation,
    QPropertyAnimation,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from core.renderer.scene import ScenePreset
from export.ffmpeg import ExportSettings

PRESET_DISPLAY = {
    "cinema": ("电影镜头", "星云 · 暖色 · 慢推进", "#f2e8d8"),
    "aurora": ("极光星云", "紫色旋臂 · 粒子", "#8a6dff"),
    "cyberpunk": ("赛博朋克", "品红网格 · 闪光震动", "#ff26a6"),
    "stage": ("歌词舞台", "青色网格 · 节拍闪光", "#19e6ff"),
    "synthwave": ("合成波", "橙红网格 · 复古", "#ff7433"),
    "dj": ("DJ 现场", "波形 · 粒子风暴", "#4de6ff"),
}

_RESOLUTIONS = ("360p", "480p", "720p", "1080p", "1440p")
_FPS_OPTIONS = ("24", "30", "60")
_ASPECTS = ("16:9", "9:16", "1:1")
_FORMATS = ("mp4", "webm", "mov")


def _format_time(seconds: float) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"


class PresetCard(QFrame):
    """预设卡片：可点击，带选中高亮。"""

    clicked = Signal(str)

    def __init__(
        self,
        name: str,
        title: str,
        subtitle: str,
        color: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.name = name
        self.setProperty("card", True)
        self.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(10)

        dot = QLabel(self)
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(f"background: {color}; border-radius: 5px;")

        texts = QVBoxLayout()
        texts.setSpacing(2)
        title_label = QLabel(title, self)
        title_label.setProperty("cardTitle", True)
        subtitle_label = QLabel(subtitle, self)
        subtitle_label.setProperty("cardSub", True)
        texts.addWidget(title_label)
        texts.addWidget(subtitle_label)

        layout.addWidget(dot)
        layout.addLayout(texts, 1)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.name)
        super().mousePressEvent(event)


class ControlPanel(QFrame):
    """控制面板：视觉风格卡片、效果调节、导出、播放控制。"""

    preset_selected = Signal(str)  # 预设名；"auto" = 自动切换
    effect_param_changed = Signal(str, str, float)  # 效果名, 参数名, 值
    play_pause_requested = Signal()
    export_requested = Signal(object, str)  # (ExportSettings, 输出路径)
    seek_requested = Signal(float)  # 秒
    audio_file_selected = Signal(str)
    lrc_file_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("controlPanel")
        self.setFixedWidth(320)
        self.cards: dict[str, PresetCard] = {}
        self._fade_done = False
        self._playing = False
        self._pulse_on = False
        self._dragging = False
        self._duration = 1.0
        self._build()

    # ---------- 构建 ----------

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("AuroraMV", content)
        title.setProperty("appTitle", True)
        subtitle = QLabel("音乐可视化 · MV 生成", content)
        subtitle.setProperty("muted", True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # 视觉风格卡片
        layout.addWidget(self._section("视觉风格", content))
        self._auto_card = self._make_card(
            "auto", "自动切换", "随音乐时间轮换六套预设", "#7fb2ff", content
        )
        layout.addWidget(self._auto_card)
        self._cards_layout = QVBoxLayout()
        self._cards_layout.setSpacing(6)
        layout.addLayout(self._cards_layout)

        # 效果调节
        layout.addWidget(self._section("效果调节", content))
        self._shake_row, self._shake_slider, self._shake_value = self._make_slider(
            "节拍震动", 0, 100, 50, "%", content
        )
        layout.addLayout(self._shake_row)
        self._flash_row, self._flash_slider, self._flash_value = self._make_slider(
            "闪光强度", 0, 100, 40, "%", content
        )
        layout.addLayout(self._flash_row)
        self._particle_row, self._particle_slider, self._particle_value = self._make_slider(
            "粒子数量", 0, 300, 60, "", content
        )
        layout.addLayout(self._particle_row)

        self._shake_slider.valueChanged.connect(
            lambda v: self._on_slider("beat_shake", "strength", v * 0.0006, v, self._shake_value)
        )
        self._flash_slider.valueChanged.connect(
            lambda v: self._on_slider("flash", "intensity", v * 0.008, v, self._flash_value)
        )
        self._particle_slider.valueChanged.connect(
            lambda v: self._on_slider("particle", "base_count", float(v), v, self._particle_value)
        )

        # 导出视频
        layout.addWidget(self._section("导出视频", content))
        self._format_combo = self._combo_row("格式", _FORMATS, layout, content)
        self._resolution_combo = self._combo_row("分辨率", _RESOLUTIONS, layout, content)
        self._fps_combo = self._combo_row("帧率", _FPS_OPTIONS, layout, content)
        self._aspect_combo = self._combo_row("宽高比", _ASPECTS, layout, content)
        self._resolution_combo.setCurrentText("1080p")
        self._fps_combo.setCurrentText("30")

        output_row = QHBoxLayout()
        self._output_edit = QLineEdit("output.mp4", content)
        browse = QPushButton("…", content)
        browse.setFixedWidth(34)
        browse.clicked.connect(self._browse_output)
        output_row.addWidget(self._output_edit, 1)
        output_row.addWidget(browse)
        layout.addLayout(output_row)

        self._export_button = QPushButton("导出视频", content)
        self._export_button.setProperty("accent", True)
        self._export_button.clicked.connect(self._export_clicked)
        layout.addWidget(self._export_button)

        self._progress = QProgressBar(content)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._export_status = QLabel("", content)
        self._export_status.setProperty("muted", True)
        self._export_status.setWordWrap(True)
        layout.addWidget(self._export_status)

        # 播放进度（可拖动）
        layout.addWidget(self._section("播放进度", content))
        progress_row = QHBoxLayout()
        self._time_label = QLabel("0:00 / 0:00", content)
        self._time_label.setProperty("muted", True)
        self._seek_slider = QSlider(Qt.Horizontal, content)
        self._seek_slider.setRange(0, 1000)
        self._seek_slider.sliderPressed.connect(lambda: setattr(self, "_dragging", True))
        self._seek_slider.sliderReleased.connect(self._on_seek_released)
        progress_row.addWidget(self._time_label)
        progress_row.addWidget(self._seek_slider, 1)
        layout.addLayout(progress_row)

        # 导入
        layout.addWidget(self._section("导入", content))
        import_row = QHBoxLayout()
        self._audio_button = QPushButton("打开音频", content)
        self._audio_button.clicked.connect(self._import_audio)
        self._lrc_button = QPushButton("打开歌词", content)
        self._lrc_button.clicked.connect(self._import_lrc)
        import_row.addWidget(self._audio_button, 1)
        import_row.addWidget(self._lrc_button, 1)
        layout.addLayout(import_row)

        # 播放控制
        self._play_button = QPushButton("⏸ 暂停", content)
        self._play_button.setProperty("accent", True)
        self._play_button.clicked.connect(self._on_play_clicked)
        layout.addWidget(self._play_button)

        layout.addStretch(1)
        scroll.setWidget(content)
        outer.addWidget(scroll)

        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(600)
        self._pulse_timer.timeout.connect(self._toggle_pulse)

    def _section(self, text: str, parent: QWidget) -> QLabel:
        label = QLabel(text, parent)
        label.setProperty("sectionLabel", True)
        return label

    def _make_card(
        self, name: str, title: str, subtitle: str, color: str, parent: QWidget
    ) -> PresetCard:
        card = PresetCard(name, title, subtitle, color, parent)
        card.clicked.connect(self._on_card_clicked)
        return card

    def _make_slider(
        self, text: str, minimum: int, maximum: int, default: int, unit: str, parent: QWidget
    ) -> tuple[QHBoxLayout, QSlider, QLabel]:
        row = QHBoxLayout()
        label = QLabel(text, parent)
        label.setFixedWidth(64)
        slider = QSlider(Qt.Horizontal, parent)
        slider.setRange(minimum, maximum)
        slider.setValue(default)
        value = QLabel(parent)
        value.setProperty("muted", True)
        value.setFixedWidth(42)
        value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        value.setText(f"{default}{unit}")
        row.addWidget(label)
        row.addWidget(slider, 1)
        row.addWidget(value)
        return row, slider, value

    def _combo_row(
        self, text: str, options: tuple[str, ...], layout: QVBoxLayout, parent: QWidget
    ) -> QComboBox:
        row = QHBoxLayout()
        label = QLabel(text, parent)
        label.setFixedWidth(64)
        combo = QComboBox(parent)
        combo.addItems(options)
        row.addWidget(label)
        row.addWidget(combo, 1)
        layout.addLayout(row)
        return combo

    # ---------- 事件 ----------

    def _on_slider(
        self, name: str, key: str, value: float, raw: int, label: QLabel
    ) -> None:
        if key == "base_count":
            label.setText(str(int(value)))
        else:
            label.setText(f"{raw}%")
        self.effect_param_changed.emit(name, key, value)

    def _on_card_clicked(self, name: str) -> None:
        self.select_preset(name)
        self.preset_selected.emit(name)

    def _on_play_clicked(self) -> None:
        self.play_pause_requested.emit()

    def _on_seek_released(self) -> None:
        self._dragging = False
        seconds = self._seek_slider.value() / 1000.0 * self._duration
        self.seek_requested.emit(seconds)

    def _import_audio(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "选择音频", "", "音频 (*.wav *.mp3 *.flac)"
        )
        if path:
            self.audio_file_selected.emit(path)

    def _import_lrc(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "选择歌词", "", "歌词 (*.lrc)")
        if path:
            self.lrc_file_selected.emit(path)

    def _browse_output(self) -> None:
        fmt = self._format_combo.currentText()
        path, _ = QFileDialog.getSaveFileName(
            self, "选择导出位置", self._output_edit.text(), f"{fmt.upper()} (*.{fmt})"
        )
        if path:
            self._output_edit.setText(path)

    def _export_clicked(self) -> None:
        settings = ExportSettings(
            format=self._format_combo.currentText(),
            resolution=self._resolution_combo.currentText(),
            fps=int(self._fps_combo.currentText()),
            aspect=self._aspect_combo.currentText(),
        )
        self.export_requested.emit(settings, self._output_edit.text().strip())

    def _toggle_pulse(self) -> None:
        self._pulse_on = not self._pulse_on
        self._update_play_button()

    def _update_play_button(self) -> None:
        self._play_button.setProperty("pulse", self._playing and self._pulse_on)
        self._play_button.style().unpolish(self._play_button)
        self._play_button.style().polish(self._play_button)

    # ---------- 公开接口 ----------

    def set_presets(self, presets: list[ScenePreset]) -> None:
        """按预设列表构建卡片。"""
        for preset in presets:
            if preset.name not in PRESET_DISPLAY:
                continue
            title, subtitle, color = PRESET_DISPLAY[preset.name]
            card = self._make_card(
                preset.name, title, subtitle, color, self._cards_parent()
            )
            self.cards[preset.name] = card
            self._cards_layout.addWidget(card)
        self.select_preset("auto")

    def _cards_parent(self) -> QWidget:
        return self._cards_layout.parentWidget() if self._cards_layout.parentWidget() else self

    def select_preset(self, name: str) -> None:
        """高亮选中的卡片（不触发信号）。"""
        for card_name, card in self.cards.items():
            card.set_selected(card_name == name)
        self._auto_card.set_selected(name == "auto")

    def set_playing(self, playing: bool) -> None:
        self._playing = playing
        self._play_button.setText("⏸ 暂停" if playing else "▶ 播放")
        if playing:
            self._pulse_timer.start()
        else:
            self._pulse_timer.stop()
            self._pulse_on = False
        self._update_play_button()

    def set_progress(self, position: float, duration: float) -> None:
        """更新播放进度显示（由控制器轮询）。"""
        self._duration = max(duration, 0.01)
        if not self._dragging:
            fraction = max(0.0, min(1.0, position / self._duration))
            self._seek_slider.blockSignals(True)
            self._seek_slider.setValue(int(fraction * 1000))
            self._seek_slider.blockSignals(False)
        self._time_label.setText(f"{_format_time(position)} / {_format_time(duration)}")

    def set_export_progress(self, done: int, total: int) -> None:
        self._progress.setVisible(True)
        self._progress.setRange(0, total)
        self._progress.setValue(done)

    def set_export_state(self, state: str, message: str = "") -> None:
        """state: running / ok / fail。"""
        self._export_button.setEnabled(state != "running")
        if state == "running":
            self._export_status.setText("导出中…")
            self._progress.setVisible(True)
        elif state == "ok":
            self._export_status.setText("导出完成 ✓")
            self._progress.setVisible(False)
        elif state == "fail":
            self._export_status.setText(f"导出失败: {message}")
            self._progress.setVisible(False)

    def showEvent(self, event) -> None:  # noqa: N802
        """入场淡入动画。"""
        super().showEvent(event)
        if self._fade_done:
            return
        self._fade_done = True
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(350)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.start(QAbstractAnimation.DeleteWhenStopped)
        self._fade_animation = animation
