"""音频分析器（Analyzer）。

职责（规格 14.2 节管线）：加载（mp3 / wav）→ 解码 → PCM 数据 → 分析 → AudioState。
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
import librosa

from core.audio.beat_detector import detect_beats
from core.audio.state import AudioState

_SR = 22050
_N_FFT = 2048
_HOP = 512
_BEAT_WINDOW = 0.15  # 节拍判定窗口（秒）

# 频段划分：低频 / 中频 / 高频（Hz）
_BANDS = (
    ("bass", 20.0, 250.0),
    ("mid", 250.0, 2000.0),
    ("treble", 2000.0, 8000.0),
)


class AudioLoadError(RuntimeError):
    """音频加载或分析失败。"""


class AudioAnalyzer:
    """加载音频并预分析特征，按时间提供 AudioState。"""

    def __init__(self, sr: int = _SR, n_fft: int = _N_FFT, hop_length: int = _HOP) -> None:
        self._sr = sr
        self._n_fft = n_fft
        self._hop = hop_length
        self._duration = 0.0
        self._times = np.zeros(0, dtype=np.float32)
        self._volume = np.zeros(0, dtype=np.float32)
        self._bands: dict[str, npt.NDArray[np.float32]] = {}
        self._beat_times = np.zeros(0, dtype=np.float32)
        self._bpm = 0.0

    @property
    def duration(self) -> float:
        """音频时长（秒）。"""
        return self._duration

    @property
    def bpm(self) -> float:
        """检测到的 BPM。"""
        return self._bpm

    @property
    def beat_times(self) -> npt.NDArray[np.float32]:
        """检测到的节拍时间点（秒，升序）。"""
        return self._beat_times.copy()

    def load(self, path: str) -> None:
        """加载并分析音频文件（mp3 / wav）。"""
        try:
            y, sr = librosa.load(path, sr=self._sr, mono=True)
        except Exception as exc:
            raise AudioLoadError(f"无法加载音频 {path}: {exc}") from exc
        if y.size == 0:
            raise AudioLoadError(f"音频为空: {path}")
        self._analyze(y, sr)

    def get_state(self, time: float) -> AudioState:
        """返回给定时刻（秒）的音频状态，帧间线性插值。"""
        t = max(0.0, min(time, self._duration))
        idx = int(np.searchsorted(self._times, t))
        return AudioState(
            timestamp=t,
            volume=self._interp(self._volume, t, idx),
            bass=self._interp(self._bands.get("bass", self._volume), t, idx),
            mid=self._interp(self._bands.get("mid", self._volume), t, idx),
            treble=self._interp(self._bands.get("treble", self._volume), t, idx),
            beat=self._is_beat(t),
            bpm=self._bpm,
        )

    # ---------- 内部实现 ----------

    def _analyze(self, y: npt.NDArray[np.float32], sr: int) -> None:
        stft = np.abs(librosa.stft(y, n_fft=self._n_fft, hop_length=self._hop))
        n_frames = stft.shape[1]
        times = librosa.frames_to_time(np.arange(n_frames), sr=sr, hop_length=self._hop)

        rms = librosa.feature.rms(y=y, frame_length=self._n_fft, hop_length=self._hop, center=True)[0]
        rms = rms[:n_frames]

        freqs = librosa.fft_frequencies(sr=sr, n_fft=self._n_fft)
        bands: dict[str, npt.NDArray[np.float32]] = {}
        for name, lo, hi in _BANDS:
            mask = (freqs >= lo) & (freqs < hi)
            if mask.any():
                bands[name] = stft[mask].sum(axis=0)
            else:
                bands[name] = np.zeros(n_frames, dtype=np.float32)

        self._times = times.astype(np.float32)
        self._volume = _normalize(rms)
        self._bands = {name: _normalize(bands[name]) for name, _, _ in _BANDS}
        self._bpm, self._beat_times = detect_beats(y, sr)
        self._duration = float(len(y)) / float(sr)

    def _interp(self, arr: npt.NDArray[np.float32], t: float, idx: int) -> float:
        if arr.size == 0:
            return 0.0
        lo = max(idx - 1, 0)
        hi = min(idx, arr.size - 1)
        span = float(self._times[hi] - self._times[lo])
        frac = 0.0 if span <= 0.0 else (t - float(self._times[lo])) / span
        frac = min(max(frac, 0.0), 1.0)
        return float(arr[lo]) * (1.0 - frac) + float(arr[hi]) * frac

    def _is_beat(self, t: float) -> bool:
        if self._beat_times.size == 0:
            return False
        bi = int(np.searchsorted(self._beat_times, t))
        for bt in self._beat_times[max(0, bi - 1) : bi + 1]:
            if abs(float(bt) - t) <= _BEAT_WINDOW:
                return True
        return False


def _normalize(arr: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
    """按整曲峰值归一化到 0..1。"""
    peak = float(arr.max()) if arr.size else 0.0
    if peak <= 0.0:
        return np.zeros(arr.size, dtype=np.float32)
    return (arr / peak).astype(np.float32)
