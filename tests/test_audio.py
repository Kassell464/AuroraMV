"""音频引擎最小验证。

对应规格第 47 节「Audio: load mp3 successfully」。
fixture 为 120 BPM 合成音频（底鼓在 0.0 / 0.5 / 1.0 ... 秒）。

节拍断言以检测到的 beat_times 为准（librosa 的相位估计可能整体偏移，
这里验证的是分析器的一致性，而非第三方库的绝对相位）。
"""

import os
import unittest

import numpy as np

from core.audio.analyzer import AudioAnalyzer
from core.audio.state import AudioState

FIXTURE_MP3 = os.path.join(os.path.dirname(__file__), "fixtures", "demo.mp3")


@unittest.skipUnless(os.path.exists(FIXTURE_MP3), "缺少测试音频 fixtures/demo.mp3")
class AudioAnalyzerTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.analyzer = AudioAnalyzer()
        cls.analyzer.load(FIXTURE_MP3)

    def test_load_mp3_successfully(self) -> None:
        """mp3 加载成功且时长有效。"""
        self.assertGreater(self.analyzer.duration, 1.0)

    def test_bpm_in_reasonable_range(self) -> None:
        self.assertGreater(self.analyzer.bpm, 60.0)
        self.assertLess(self.analyzer.bpm, 200.0)

    def test_get_state_returns_audio_state(self) -> None:
        state = self.analyzer.get_state(1.0)
        self.assertIsInstance(state, AudioState)
        for value in (state.volume, state.bass, state.mid, state.treble):
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)

    def test_beat_intervals_around_half_second(self) -> None:
        """120 BPM 合成音频：节拍间隔中位数应约 0.5 秒。"""
        beats = self.analyzer.beat_times
        self.assertGreater(len(beats), 4)
        intervals = np.diff(beats)
        self.assertGreater(float(np.median(intervals)), 0.4)
        self.assertLess(float(np.median(intervals)), 0.6)

    def test_beat_true_at_detected_beat_times(self) -> None:
        """检测到的节拍时刻应返回 beat=True。"""
        beats = self.analyzer.beat_times
        for t in (float(beats[0]), float(beats[len(beats) // 2]), float(beats[-1])):
            self.assertTrue(self.analyzer.get_state(t).beat, f"t={t} 应为 beat=True")

    def test_beat_false_between_beats(self) -> None:
        """相邻两拍的中间点不应判定为节拍。"""
        beats = self.analyzer.beat_times
        mid = float((beats[0] + beats[1]) / 2.0)
        self.assertFalse(self.analyzer.get_state(mid).beat)


class AudioEnginePauseTestCase(unittest.TestCase):
    """暂停后继续播放：进度保持，不从头（修复轮）。"""

    def test_pause_resume_keeps_position(self) -> None:
        import time

        from core.audio.engine import AudioEngine

        demo_wav = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "assets", "audio", "demo.wav",
        )
        if not os.path.exists(demo_wav):
            self.skipTest("缺少演示音频")
        engine = AudioEngine()
        try:
            engine.load(demo_wav)
            engine.play()
            time.sleep(0.6)
            engine.pause()
            paused_at = engine.position
            self.assertGreater(paused_at, 0.3)
            time.sleep(0.4)
            self.assertAlmostEqual(engine.position, paused_at, delta=0.15)  # 暂停时位置不动
            engine.play()  # 续播
            time.sleep(0.4)
            self.assertGreater(engine.position, paused_at)  # 继续前进而非从头
        finally:
            engine.stop()


if __name__ == "__main__":
    unittest.main()
