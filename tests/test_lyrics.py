"""歌词引擎测试（阶段 6）。

LRC 解析、歌词提供器、模板加载（无需 OpenGL）；
歌词渲染器 GL 测试（环境无 OpenGL 时跳过）。
"""

import glob
import os
import unittest

import numpy as np

from core.lyrics.parser import LyricLine, parse_lrc
from core.lyrics.provider import LRCProvider
from core.lyrics.template import LyricTemplate, load_lyric_template

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LYRICS_TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "templates", "lyrics")

LRC_SAMPLE = """
[ti:Test Song]
[ar:Someone]
[offset:+500]
[00:10.00]Hello
[00:15.00]World
[00:20.00][01:00.00]Chorus
"""

try:
    import moderngl

    _probe = moderngl.create_context(standalone=True)
    _probe.release()
    GL_AVAILABLE = True
except Exception:
    GL_AVAILABLE = False


class LrcParserTestCase(unittest.TestCase):
    def test_parses_lines_with_timestamps(self) -> None:
        _, lines = parse_lrc(LRC_SAMPLE)
        # offset +500ms 已应用
        self.assertEqual(lines[0], LyricLine(text="Hello", start=10.5, end=15.5))
        self.assertEqual(lines[1], LyricLine(text="World", start=15.5, end=20.5))

    def test_parses_metadata(self) -> None:
        metadata, _ = parse_lrc(LRC_SAMPLE)
        self.assertEqual(metadata["ti"], "Test Song")
        self.assertEqual(metadata["ar"], "Someone")

    def test_multiple_timestamps_per_line(self) -> None:
        _, lines = parse_lrc(LRC_SAMPLE)
        chorus = [line for line in lines if line.text == "Chorus"]
        self.assertEqual([line.start for line in chorus], [20.5, 60.5])

    def test_lines_sorted_and_ranges_valid(self) -> None:
        _, lines = parse_lrc(LRC_SAMPLE)
        starts = [line.start for line in lines]
        self.assertEqual(starts, sorted(starts))
        for line in lines:
            self.assertGreater(line.end, line.start)


class LrcProviderTestCase(unittest.TestCase):
    def test_get_current_line(self) -> None:
        provider = LRCProvider()
        provider.load_text(LRC_SAMPLE)
        line = provider.get_current_line(12.0)
        self.assertIsNotNone(line)
        self.assertEqual(line.text, "Hello")  # type: ignore[union-attr]
        chorus = provider.get_current_line(25.0)
        self.assertIsNotNone(chorus)
        self.assertEqual(chorus.text, "Chorus")  # type: ignore[union-attr]
        self.assertIsNone(provider.get_current_line(8.0))

    def test_real_lrc_file_if_present(self) -> None:
        """用户提供的真实 LRC（存在时验证）。"""
        candidates = glob.glob(os.path.join(PROJECT_ROOT, "*.lrc"))
        if not candidates:
            self.skipTest("仓库根目录没有 LRC 文件")
        provider = LRCProvider(candidates[0])
        self.assertGreater(len(provider.lines), 10)
        starts = [line.start for line in provider.lines]
        self.assertEqual(starts, sorted(starts))
        for line in provider.lines:
            self.assertTrue(line.text.strip())
            self.assertGreater(line.end, line.start)


class LyricTemplateTestCase(unittest.TestCase):
    def test_loads_all_templates(self) -> None:
        names = set()
        for filename in ("neon.json", "cinema.json", "minimal.json"):
            template = load_lyric_template(os.path.join(LYRICS_TEMPLATES_DIR, filename))
            self.assertIsInstance(template, LyricTemplate)
            names.add(template.name)
        self.assertEqual(names, {"neon", "cinema", "minimal"})

    def test_template_colors_in_range(self) -> None:
        template = load_lyric_template(os.path.join(LYRICS_TEMPLATES_DIR, "neon.json"))
        for channel in template.color:
            self.assertGreaterEqual(channel, 0.0)
            self.assertLessEqual(channel, 1.0)


@unittest.skipUnless(GL_AVAILABLE, "当前环境无法创建 OpenGL 上下文")
class LyricsRendererGLTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from core.renderer.lyrics import LyricsRenderer

        cls.ctx = moderngl.create_context(standalone=True)
        cls.renderer = LyricsRenderer(cls.ctx)
        cls.fbo = cls.ctx.simple_framebuffer((128, 128), components=3)
        cls.ctx.viewport = (0, 0, 128, 128)

    def test_renders_animated_text(self) -> None:
        from core.audio.state import AudioState

        self.fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0)
        line = LyricLine(text="你好，世界 Hello", start=0.0, end=4.0)
        state = AudioState(timestamp=1.0, volume=0.5, bass=0.5, mid=0.5, treble=0.5, beat=False, bpm=120.0)
        self.renderer.update(1.0, line, state)
        self.renderer.render(128, 128)
        pixels = np.frombuffer(self.fbo.read(components=3), dtype=np.uint8).reshape(128, 128, 3)
        self.assertGreater(int(pixels.max()), 100, "歌词文本应渲染出亮色像素")

    def test_beat_pulse_makes_lyrics_brighter_and_bigger(self) -> None:
        """节拍动效：beat 触发时歌词更亮（缩放 + 提亮），画面像素总和增大。"""
        from core.audio.state import AudioState

        line = LyricLine(text="Beat 节拍", start=0.0, end=4.0)

        def frame(beat: bool) -> np.ndarray:
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0)
            state = AudioState(
                timestamp=1.0, volume=0.5, bass=0.5, mid=0.5, treble=0.5,
                beat=beat, bpm=120.0,
            )
            self.renderer.update(1.0, line, state)
            self.renderer.render(128, 128)
            return np.frombuffer(self.fbo.read(components=3), dtype=np.uint8).astype(np.int64)

        quiet = frame(False)
        beat = frame(True)
        self.assertGreater(int(beat.sum()), int(quiet.sum()), "节拍时歌词应更亮/更大")


if __name__ == "__main__":
    unittest.main()
