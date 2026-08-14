"""导出系统（规格 37 节、42 节阶段 9）。

管线：项目 → 渲染器 → 帧缓冲 → FFmpeg → 视频文件。
Export 不重新实现 Renderer：复用同一渲染管线（“所见即所导出”，规格原则 3）。

支持格式（多种可选）：
- mp4 / mov：H264 + AAC
- webm：VP9 + Opus

导出选项（多种可选）：分辨率 360p–1440p、FPS 24/30/60、
宽高比 16:9 / 9:16 / 1:1、码率 自动（CRF）/ 手动、可选裁剪时长。
"""

from __future__ import annotations

import math
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import moderngl

from core.audio.analyzer import AudioAnalyzer, AudioLoadError
from core.lyrics.provider import LRCProvider
from core.renderer.engine import Renderer
from core.renderer.scene import (
    Scene,
    SceneManager,
    load_scene_presets,
    scenes_from_presets,
)

RESOLUTIONS = {"360p": 360, "480p": 480, "720p": 720, "1080p": 1080, "1440p": 1440}
ASPECT_RATIOS = {"16:9": (16, 9), "9:16": (9, 16), "1:1": (1, 1)}
FPS_OPTIONS = (24, 30, 60)

# 格式 → (默认视频编码器, 音频编码器)
FORMAT_CODECS = {
    "mp4": ("h264", "aac"),
    "mov": ("h264", "aac"),
    "webm": ("vp9", "libopus"),
}

# 各格式允许的视频编码器
ALLOWED_CODECS = {"mp4": ("h264",), "mov": ("h264",), "webm": ("vp9",)}

_SCENE_PRESETS_DIR = Path(__file__).resolve().parent.parent / "templates" / "scene"

ProgressCallback = Callable[[int, int], None]


class ExportError(RuntimeError):
    """导出失败。"""


@dataclass(frozen=True, slots=True)
class ExportSettings:
    """导出选项（全部可选择）。"""

    format: str = "mp4"  # mp4 / mov / webm
    codec: str = "auto"  # auto / h264 / vp9
    resolution: str = "1080p"  # 360p / 480p / 720p / 1080p / 1440p
    fps: int = 30  # 24 / 30 / 60
    aspect: str = "16:9"  # 16:9 / 9:16 / 1:1
    bitrate: str = "auto"  # auto（CRF）/ 如 "8M"
    trim: float | None = None  # 只导出前 N 秒（None = 全曲）


@dataclass(frozen=True, slots=True)
class ExportProject:
    """导出输入（最小项目描述，对应规格 35-37 节）。"""

    audio_path: str
    lrc_path: str | None = None
    scenes: list[Scene] | None = None  # None = 自动用预设均分整曲


def resolve_size(settings: ExportSettings) -> tuple[int, int]:
    """按分辨率与宽高比计算输出尺寸（宽取偶数，编码器要求）。"""
    height = RESOLUTIONS[settings.resolution]
    ratio_w, ratio_h = ASPECT_RATIOS[settings.aspect]
    width = round(height * ratio_w / ratio_h)
    if width % 2:
        width += 1
    return width, height


def validate_settings(settings: ExportSettings) -> None:
    """校验导出选项，非法时抛出 ExportError。"""
    if settings.format not in FORMAT_CODECS:
        raise ExportError(
            f"不支持的格式: {settings.format}（可选 {', '.join(FORMAT_CODECS)}）"
        )
    if settings.codec not in ("auto", "h264", "vp9"):
        raise ExportError(f"不支持的编码器: {settings.codec}（可选 auto/h264/vp9）")
    if settings.codec != "auto" and settings.codec not in ALLOWED_CODECS[settings.format]:
        raise ExportError(
            f"格式 {settings.format} 不支持编码器 {settings.codec}"
            f"（可选 {', '.join(ALLOWED_CODECS[settings.format])}）"
        )
    if settings.resolution not in RESOLUTIONS:
        raise ExportError(
            f"不支持的分辨率: {settings.resolution}（可选 {', '.join(RESOLUTIONS)}）"
        )
    if settings.fps not in FPS_OPTIONS:
        raise ExportError(
            f"不支持的帧率: {settings.fps}（可选 {', '.join(str(f) for f in FPS_OPTIONS)}）"
        )
    if settings.aspect not in ASPECT_RATIOS:
        raise ExportError(
            f"不支持的宽高比: {settings.aspect}（可选 {', '.join(ASPECT_RATIOS)}）"
        )
    if settings.trim is not None and settings.trim <= 0:
        raise ExportError(f"裁剪时长必须大于 0: {settings.trim}")


class Exporter:
    """导出器（规格 37 节接口：export(project, settings)）。"""

    def export(
        self,
        project: ExportProject,
        settings: ExportSettings,
        output_path: str,
        on_progress: ProgressCallback | None = None,
    ) -> str:
        """导出视频，返回输出路径。失败抛出 ExportError。"""
        validate_settings(settings)
        if shutil.which("ffmpeg") is None:
            raise ExportError("未找到 FFmpeg（规格 11 节必需组件）")

        width, height = resolve_size(settings)

        try:
            analyzer = AudioAnalyzer()
            analyzer.load(project.audio_path)
        except AudioLoadError as exc:
            raise ExportError(f"音频加载失败: {exc}") from exc
        duration = analyzer.duration
        if settings.trim is not None:
            duration = min(duration, settings.trim)

        scenes = project.scenes
        if scenes is None:
            presets = load_scene_presets(str(_SCENE_PRESETS_DIR))
            scenes = scenes_from_presets(presets, duration)

        ctx = moderngl.create_context(standalone=True)
        renderer = Renderer()
        try:
            renderer.initialize(ctx=ctx)
            renderer.resize(width, height)
            renderer.set_scene_manager(SceneManager(scenes))
            if project.lrc_path:
                renderer.set_lyrics_provider(LRCProvider(project.lrc_path))
            time_box = [0.0]
            renderer.set_waveform_provider(
                lambda n: analyzer.get_waveform(time_box[0], n)
            )
            fbo = ctx.simple_framebuffer((width, height), components=3)

            command = self._build_command(
                settings, width, height, project.audio_path, output_path
            )
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            total = max(1, int(math.ceil(duration * settings.fps)))
            try:
                for index in range(total):
                    t = index / settings.fps
                    time_box[0] = t
                    state = analyzer.get_state(t)
                    renderer.update(t, state)
                    renderer.render(target=fbo)
                    process.stdin.write(fbo.read(components=3))
                    if on_progress is not None and (index % 5 == 0 or index == total - 1):
                        on_progress(index + 1, total)
            finally:
                if process.stdin is not None:
                    process.stdin.close()
            return_code = process.wait(timeout=1800)
            stderr_text = (
                process.stderr.read().decode("utf-8", "replace")
                if process.stderr is not None
                else ""
            )
            if return_code != 0:
                raise ExportError(f"FFmpeg 退出码 {return_code}: {stderr_text[-500:]}")
        finally:
            ctx.release()
        return output_path

    @staticmethod
    def _build_command(
        settings: ExportSettings,
        width: int,
        height: int,
        audio_path: str,
        output_path: str,
    ) -> list[str]:
        default_vcodec, acodec = FORMAT_CODECS[settings.format]
        vcodec = default_vcodec if settings.codec == "auto" else settings.codec

        command = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{width}x{height}", "-r", str(settings.fps), "-i", "-",
            "-i", audio_path,
        ]
        if settings.bitrate == "auto":
            if vcodec == "h264":
                command += ["-c:v", "libx264", "-preset", "medium", "-crf", "18"]
            else:
                command += [
                    "-c:v", "libvpx-vp9", "-crf", "30", "-b:v", "0", "-cpu-used", "5"
                ]
        else:
            encoder = "libx264" if vcodec == "h264" else "libvpx-vp9"
            command += ["-c:v", encoder, "-b:v", settings.bitrate]
        command += [
            "-pix_fmt", "yuv420p",
            "-c:a", acodec,
            "-map", "0:v:0", "-map", "1:a:0",
            "-shortest",
            output_path,
        ]
        return command
