"""AuroraMV 渲染器引擎包。

Renderer 是 AuroraMV 核心，负责生成每一帧画面。
"""

from core.renderer.camera import Camera
from core.renderer.engine import Renderer

__all__ = ["Camera", "Renderer"]
