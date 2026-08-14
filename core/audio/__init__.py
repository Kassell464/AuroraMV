"""AuroraMV 音频引擎包。

音频管线（规格 14.2 节）：解码 → PCM 数据 → 分析器 → AudioState → 渲染器。

注意：此包只导出轻量类型；AudioAnalyzer / AudioEngine 请按需显式导入，
避免 UI 层引入 librosa 等重依赖。
"""

from core.audio.state import AudioState

__all__ = ["AudioState"]
