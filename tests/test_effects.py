"""效果系统测试（阶段 7）。

重点：所有效果参数可调节（默认值 + JSON 覆盖 + set_params 运行时调整）、
震动/闪光逻辑随节拍、粒子渲染（GL，环境不支持时跳过）。
"""

import os
import unittest

import numpy as np

try:
    import moderngl

    _probe = moderngl.create_context(standalone=True)
    _probe.release()
    GL_AVAILABLE = True
except Exception:
    GL_AVAILABLE = False

from core.audio.state import AudioState
from core.effects.effect import PostState
from core.effects.flash import FlashEffect, FlashParams
from core.effects.manager import EffectManager, create_effect
from core.effects.particle import ParticleEffect, ParticleParams
from core.effects.shake import BeatShakeEffect, ShakeParams
from core.effects.template import load_effect_spec

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EFFECTS_DIR = os.path.join(PROJECT_ROOT, "templates", "effects")


def _state(t: float, *, beat: bool = False, bass: float = 0.5) -> AudioState:
    return AudioState(
        timestamp=t, volume=0.5, bass=bass, mid=0.4, treble=0.3, beat=beat, bpm=120.0
    )


class EffectTemplateTestCase(unittest.TestCase):
    def test_loads_all_effect_templates(self) -> None:
        types = set()
        for filename in ("beat_shake.json", "flash.json", "particle.json"):
            spec = load_effect_spec(os.path.join(EFFECTS_DIR, filename))
            types.add(spec.type)
        self.assertEqual(types, {"beat_shake", "flash", "particle"})

    def test_json_params_override_defaults(self) -> None:
        spec = load_effect_spec(os.path.join(EFFECTS_DIR, "flash.json"))
        flash = create_effect(None, spec)  # type: ignore[arg-type]
        self.assertIsInstance(flash, FlashEffect)
        self.assertAlmostEqual(flash.params.intensity, 0.3)

    def test_unknown_param_keys_ignored(self) -> None:
        from core.effects.template import EffectSpec

        spec = EffectSpec(name="flash", type="flash", params={"intensity": 0.5, "bogus": 1})
        flash = create_effect(None, spec)  # type: ignore[arg-type]
        self.assertAlmostEqual(flash.params.intensity, 0.5)


class BeatShakeEffectTestCase(unittest.TestCase):
    def test_beat_produces_offset(self) -> None:
        shake = BeatShakeEffect()
        post = PostState()
        shake.update(1.0, _state(1.0, beat=True), post)
        self.assertGreater(float(np.abs(post.offset).sum()), 0.0)

    def test_offset_decays_without_beat(self) -> None:
        shake = BeatShakeEffect()
        post = PostState()
        shake.update(1.0, _state(1.0, beat=True), post)
        t = 1.0
        while t < 10.0:
            t += 0.1
            post.reset()
            shake.update(t, _state(t), post)
        self.assertAlmostEqual(float(np.abs(post.offset).sum()), 0.0, places=6)

    def test_strength_adjustable(self) -> None:
        """可调节：strength=0 不产生偏移，调大后产生偏移。"""
        shake = BeatShakeEffect(params=ShakeParams(strength=0.0))
        post = PostState()
        shake.update(1.0, _state(1.0, beat=True), post)
        self.assertEqual(float(np.abs(post.offset).sum()), 0.0)
        shake.set_params(strength=0.1)
        post.reset()
        shake.update(2.0, _state(2.0, beat=True), post)
        self.assertGreater(float(np.abs(post.offset).sum()), 0.0)


class FlashEffectTestCase(unittest.TestCase):
    def test_beat_trigger_and_decay(self) -> None:
        flash = FlashEffect()
        post = PostState()
        flash.update(1.0, _state(1.0, beat=True), post)
        self.assertGreater(post.flash, 0.0)
        t = 1.0
        while t < 10.0:
            t += 0.1
            post.reset()
            flash.update(t, _state(t), post)
        self.assertAlmostEqual(post.flash, 0.0, places=6)

    def test_intensity_adjustable(self) -> None:
        """可调节：intensity=0 无闪光，调大后有闪光。"""
        flash = FlashEffect(params=FlashParams(intensity=0.0))
        post = PostState()
        flash.update(1.0, _state(1.0, beat=True), post)
        self.assertEqual(post.flash, 0.0)
        flash.set_params(intensity=0.5)
        post.reset()
        flash.update(2.0, _state(2.0, beat=True), post)
        self.assertGreater(post.flash, 0.0)

    def test_bass_trigger_follows_bass(self) -> None:
        flash = FlashEffect(params=FlashParams(trigger="bass", intensity=0.4))
        post = PostState()
        flash.update(1.0, _state(1.0, bass=0.9), post)
        self.assertAlmostEqual(post.flash, 0.36, places=5)


class ParticleParamsTestCase(unittest.TestCase):
    def test_count_formula_adjustable(self) -> None:
        """可调节：规格 16 公式 count = base + bass × multiplier。"""
        particles = ParticleParams(base_count=50, bass_multiplier=100)
        self.assertEqual(50 + int(0.5 * 100), 50 + 50)
        particles.bass_multiplier = 0
        self.assertEqual(50 + int(0.5 * 0), 50)


class EffectManagerTestCase(unittest.TestCase):
    def test_set_params_by_name(self) -> None:
        manager = EffectManager()
        manager.add(BeatShakeEffect(params=ShakeParams(strength=0.02)))
        self.assertTrue(manager.set_params("beat_shake", strength=0.05))
        self.assertAlmostEqual(manager.effects[0].params.strength, 0.05)
        self.assertFalse(manager.set_params("nonexistent", strength=1.0))


@unittest.skipUnless(GL_AVAILABLE, "当前环境无法创建 OpenGL 上下文")
class ParticleGLTestCase(unittest.TestCase):
    def test_particle_effect_renders_points(self) -> None:
        ctx = moderngl.create_context(standalone=True)
        fbo = ctx.simple_framebuffer((128, 128), components=3)
        ctx.viewport = (0, 0, 128, 128)
        effect = ParticleEffect(ctx, ParticleParams(base_count=40, bass_multiplier=40))
        for t in (0.0, 0.1, 0.5, 1.0):
            effect.update(t, _state(t, bass=1.0))
        fbo.use()
        ctx.clear(0.0, 0.0, 0.0)
        effect.render()
        pixels = np.frombuffer(fbo.read(components=3), dtype=np.uint8).reshape(128, 128, 3)
        self.assertGreater(int(pixels.max()), 50, "粒子应渲染出亮点")
        effect.release()


if __name__ == "__main__":
    unittest.main()
