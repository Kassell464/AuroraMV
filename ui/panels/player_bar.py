"""播放底栏（PlayerBar）。

类似视频播放器的底部控制栏：歌名/歌词名、时间、可拖动进度条、
歌词开关、播放/暂停。UI 层不含渲染逻辑。
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


def _format_time(seconds: float) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"


class PlayerBar(QFrame):
    """右侧预览区底部的播放控制栏。"""

    seek_requested = Signal(float)  # 秒
    play_pause_requested = Signal()
    lyrics_toggled = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("playerBar")
        self.setFixedHeight(78)
        self._dragging = False
        self._duration = 1.0
        self._playing = False
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(6)

        # 第一行：歌名 / 歌词名 + 时间
        info_row = QHBoxLayout()
        texts = QVBoxLayout()
        texts.setSpacing(2)
        self._title_label = QLabel("—", self)
        self._title_label.setProperty("barTitle", True)
        self._subtitle_label = QLabel("", self)
        self._subtitle_label.setProperty("muted", True)
        texts.addWidget(self._title_label)
        texts.addWidget(self._subtitle_label)
        self._time_label = QLabel("0:00 / 0:00", self)
        self._time_label.setProperty("muted", True)
        info_row.addLayout(texts, 1)
        info_row.addWidget(self._time_label)
        layout.addLayout(info_row)

        # 第二行：进度条 + 歌词开关 + 播放
        control_row = QHBoxLayout()
        control_row.setSpacing(10)
        self._seek_slider = QSlider(Qt.Horizontal, self)
        self._seek_slider.setRange(0, 1000)
        self._seek_slider.sliderPressed.connect(lambda: setattr(self, "_dragging", True))
        self._seek_slider.sliderReleased.connect(self._on_seek_released)
        self._lyrics_button = QPushButton("歌词：开", self)
        self._lyrics_button.setCheckable(True)
        self._lyrics_button.setChecked(True)
        self._lyrics_button.toggled.connect(self.lyrics_toggled)
        self._play_button = QPushButton("⏸", self)
        self._play_button.setProperty("accent", True)
        self._play_button.setFixedWidth(64)
        self._play_button.clicked.connect(self.play_pause_requested)
        control_row.addWidget(self._seek_slider, 1)
        control_row.addWidget(self._lyrics_button)
        control_row.addWidget(self._play_button)
        layout.addLayout(control_row)

    # ---------- 事件 ----------

    def _on_seek_released(self) -> None:
        self._dragging = False
        self.seek_requested.emit(self._seek_slider.value() / 1000.0 * self._duration)

    # ---------- 公开接口 ----------

    def set_track(self, title: str, subtitle: str = "") -> None:
        """显示当前歌曲名与歌词名。"""
        self._title_label.setText(title)
        self._subtitle_label.setText(subtitle)

    def set_progress(self, position: float, duration: float) -> None:
        """更新进度（由控制器轮询；拖动期间不覆盖）。"""
        self._duration = max(duration, 0.01)
        if not self._dragging:
            fraction = max(0.0, min(1.0, position / self._duration))
            self._seek_slider.blockSignals(True)
            self._seek_slider.setValue(int(fraction * 1000))
            self._seek_slider.blockSignals(False)
        self._time_label.setText(f"{_format_time(position)} / {_format_time(duration)}")

    def set_playing(self, playing: bool) -> None:
        self._playing = playing
        self._play_button.setText("⏸" if playing else "▶")
