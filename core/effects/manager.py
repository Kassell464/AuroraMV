"""效果管理器（规格 28 节）：管理多个 Effect，统一 update / render。"""

from __future__ import annotations

from dataclasses import fields

import moderngl

from core.audio.state import AudioState
from core.effects.effect import Effect, PostState
from core.effects.flash import FlashEffect, FlashParams
from core.effects.particle import ParticleEffect, ParticleParams
from core.effects.shake import BeatShakeEffect, ShakeParams
from core.effects.template import EffectSpec


def create_effect(ctx: moderngl.Context, spec: EffectSpec) -> Effect:
    """按规格创建效果实例（JSON 参数覆盖默认值，未知键忽略）。"""
    if spec.type == "beat_shake":
        return BeatShakeEffect(ctx, ShakeParams(**_pick(ShakeParams, spec.params)))
    if spec.type == "flash":
        return FlashEffect(ctx, FlashParams(**_pick(FlashParams, spec.params)))
    if spec.type == "particle":
        return ParticleEffect(ctx, ParticleParams(**_pick(ParticleParams, spec.params)))
    raise ValueError(f"未知效果类型: {spec.type}（可选 beat_shake/flash/particle）")


def _pick(cls: type, params: dict[str, object]) -> dict[str, object]:
    names = {field.name for field in fields(cls)}
    return {key: value for key, value in params.items() if key in names}


class EffectManager:
    """管理多个 Effect：统一 update / render（规格 28 节）。"""

    def __init__(self) -> None:
        self.effects: list[Effect] = []

    def add(self, effect: Effect) -> None:
        self.effects.append(effect)

    def clear(self) -> None:
        for effect in self.effects:
            effect.release()
        self.effects.clear()

    def update(
        self,
        time: float,
        audio_state: AudioState | None = None,
        post_state: PostState | None = None,
    ) -> None:
        for effect in self.effects:
            effect.update(time, audio_state, post_state)

    def render(self) -> None:
        for effect in self.effects:
            effect.render()

    def set_params(self, name: str, **kwargs: object) -> bool:
        """按效果名运行时调参（可调节性）。返回是否命中。"""
        for effect in self.effects:
            if effect.name == name:
                effect.set_params(**kwargs)
                return True
        return False
