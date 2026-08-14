"""摄像机数学测试（无需 OpenGL 上下文）。"""

import math
import unittest

import numpy as np

from core.renderer.camera import Camera, look_at, perspective


class LookAtTestCase(unittest.TestCase):
    def test_target_maps_to_negative_z_at_eye_distance(self) -> None:
        eye = np.array([0.0, 0.0, 3.0], dtype=np.float32)
        target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        matrix = look_at(eye, target, up)
        view_pos = matrix @ np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
        self.assertAlmostEqual(float(view_pos[2]), -3.0, places=4)


class PerspectiveTestCase(unittest.TestCase):
    def test_wider_aspect_reduces_x_scale(self) -> None:
        wide = perspective(60.0, 16.0 / 9.0, 0.1, 100.0)
        square = perspective(60.0, 1.0, 0.1, 100.0)
        self.assertLess(float(wide[0, 0]), float(square[0, 0]))


class CameraTestCase(unittest.TestCase):
    def test_update_sways_position(self) -> None:
        camera = Camera()
        camera.update(0.0)
        x0 = float(camera.position[0])
        camera.update(math.pi / 1.2)  # sin(0.6t) = sin(pi/2) = 1 → x = 0.4
        self.assertGreater(float(camera.position[0]), x0)

    def test_set_aspect_updates_projection(self) -> None:
        camera = Camera()
        before = camera.projection_matrix()
        camera.set_aspect(1.0)
        after = camera.projection_matrix()
        self.assertNotEqual(float(before[0, 0]), float(after[0, 0]))


if __name__ == "__main__":
    unittest.main()
