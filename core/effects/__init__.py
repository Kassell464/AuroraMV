"""AuroraMV 效果引擎包（规格 27-28 节）。

Effect 负责所有非核心视觉效果（闪光/震动/粒子…）。
所有效果参数可调节：JSON 模板（templates/effects/）+ set_params 运行时调整。
"""

from core.effects.effect import Effect, PostState
from core.effects.manager import EffectManager, create_effect

__all__ = ["Effect", "EffectManager", "PostState", "create_effect"]
