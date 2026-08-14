"""导出系统测试（阶段 9）。

选项解析/校验（无需 GL）+ 端到端导出（需 OpenGL 与 FFmpeg，环境不支持时跳过）。
对应规格 47 节验收：生成可播放的 mp4；并验证多格式（mp4/webm/mov）。
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest

from export.ffmpeg import (
    ExportError,
    ExportProject,
    ExportSettings,
    Exporter,
    resolve_size,
    validate_settings,
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO_AUDIO = os.path.join(PROJECT_ROOT, "assets", "audio", "demo.wav")

try:
    import moderngl

    _probe = moderngl.create_context(standalone=True)
    _probe.release()
    GL_AVAILABLE = True
except Exception:
    GL_AVAILABLE = False

FFMPEG_AVAILABLE = (
    shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
)


class ExportSettingsTestCase(unittest.TestCase):
    def test_resolve_size_16_9(self) -> None:
        self.assertEqual(
            resolve_size(ExportSettings(resolution="1080p", aspect="16:9")), (1920, 1080)
        )

    def test_resolve_size_9_16_even_width(self) -> None:
        self.assertEqual(
            resolve_size(ExportSettings(resolution="720p", aspect="9:16")), (406, 720)
        )

    def test_resolve_size_1_1(self) -> None:
        self.assertEqual(
            resolve_size(ExportSettings(resolution="360p", aspect="1:1")), (360, 360)
        )

    def test_rejects_unknown_options(self) -> None:
        for settings in (
            ExportSettings(format="avi"),
            ExportSettings(resolution="4k"),
            ExportSettings(fps=25),
            ExportSettings(aspect="4:3"),
            ExportSettings(format="webm", codec="h264"),
            ExportSettings(trim=0.0),
        ):
            with self.subTest(settings=settings):
                with self.assertRaises(ExportError):
                    validate_settings(settings)


@unittest.skipUnless(GL_AVAILABLE and FFMPEG_AVAILABLE, "需要 OpenGL 与 FFmpeg")
class ExportEndToEndTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="auroramv_export_")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _export(self, settings: ExportSettings, name: str) -> str:
        output = os.path.join(self.tmp, name)
        project = ExportProject(audio_path=DEMO_AUDIO)
        result = Exporter().export(project, settings, output)
        self.assertEqual(result, output)
        return output

    def _ffprobe(self, path: str) -> dict:
        run = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "stream=codec_name,width,height",
                "-show_entries", "format=duration",
                "-of", "json", path,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(run.stdout)

    def test_exports_playable_mp4(self) -> None:
        """规格验收：生成可播放的 mp4（H264，整曲 8 秒）。"""
        output = self._export(
            ExportSettings(format="mp4", resolution="360p", fps=24), "out.mp4"
        )
        self.assertGreater(os.path.getsize(output), 10000)
        info = self._ffprobe(output)
        stream = info["streams"][0]
        self.assertEqual(stream["codec_name"], "h264")
        self.assertEqual(stream["width"], 640)
        self.assertEqual(stream["height"], 360)
        self.assertAlmostEqual(float(info["format"]["duration"]), 8.0, delta=0.6)

    def test_exports_webm_vp9(self) -> None:
        output = self._export(
            ExportSettings(format="webm", resolution="360p", fps=24, trim=2.0),
            "out.webm",
        )
        stream = self._ffprobe(output)["streams"][0]
        self.assertEqual(stream["codec_name"], "vp9")

    def test_exports_mov_h264(self) -> None:
        output = self._export(
            ExportSettings(format="mov", resolution="480p", fps=24, trim=2.0), "out.mov"
        )
        stream = self._ffprobe(output)["streams"][0]
        self.assertEqual(stream["codec_name"], "h264")


if __name__ == "__main__":
    unittest.main()
