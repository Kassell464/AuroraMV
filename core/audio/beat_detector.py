"""节拍检测（beat detector）。

基于 librosa 的节拍跟踪：返回 BPM 与节拍时间点（秒）。
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
import librosa

BeatTimes = npt.NDArray[np.float32]


def detect_beats(y: npt.NDArray[np.float32], sr: int) -> tuple[float, BeatTimes]:
    """检测 BPM 与节拍时间点。

    返回 (bpm, beat_times)；beat_times 为升序的节拍时刻（秒）。
    """
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    bpm = float(np.atleast_1d(tempo)[0])  # 兼容返回标量或单元素数组的版本
    beat_times = librosa.frames_to_time(beat_frames, sr=sr).astype(np.float32)
    return bpm, beat_times
