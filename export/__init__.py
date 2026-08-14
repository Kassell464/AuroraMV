"""AuroraMV 导出系统包（规格 37 节）。

管线：项目 → 渲染器 → 帧缓冲 → FFmpeg → 视频文件。
"""

from export.ffmpeg import (
    ExportError,
    ExportProject,
    ExportSettings,
    Exporter,
    resolve_size,
    validate_settings,
)

__all__ = [
    "ExportError",
    "ExportProject",
    "ExportSettings",
    "Exporter",
    "resolve_size",
    "validate_settings",
]
