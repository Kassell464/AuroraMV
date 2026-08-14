"""摄像机（Camera）。

职责：提供视图矩阵与投影矩阵，并支持简单动画（缓慢摆动）。
纯数学模块，不依赖 OpenGL，便于单独测试。

后续阶段（如节拍震动）将在本模块扩展 offset 等能力。
"""

from __future__ import annotations

import math

import numpy as np
import numpy.typing as npt

Mat4 = npt.NDArray[np.float32]
Vec3 = npt.NDArray[np.float32]


def look_at(eye: Vec3, target: Vec3, up: Vec3) -> Mat4:
    """构建右手系 LookAt 视图矩阵。"""
    forward = target - eye
    forward = forward / np.linalg.norm(forward)
    side = np.cross(forward, up)
    side = side / np.linalg.norm(side)
    real_up = np.cross(side, forward)

    mat = np.eye(4, dtype=np.float32)
    mat[0, :3] = side
    mat[1, :3] = real_up
    mat[2, :3] = -forward
    mat[0, 3] = -float(np.dot(side, eye))
    mat[1, 3] = -float(np.dot(real_up, eye))
    mat[2, 3] = float(np.dot(forward, eye))
    return mat


def perspective(fov_y: float, aspect: float, near: float, far: float) -> Mat4:
    """构建透视投影矩阵（fov_y 为竖直视场角，单位度）。"""
    f = 1.0 / math.tan(math.radians(fov_y) / 2.0)
    mat = np.zeros((4, 4), dtype=np.float32)
    mat[0, 0] = f / aspect
    mat[1, 1] = f
    mat[2, 2] = (far + near) / (near - far)
    mat[2, 3] = (2.0 * far * near) / (near - far)
    mat[3, 2] = -1.0
    return mat


class Camera:
    """透视摄像机：位置、朝向、视场角与投影。"""

    def __init__(
        self,
        position: tuple[float, float, float] = (0.0, 0.0, 3.0),
        target: tuple[float, float, float] = (0.0, 0.0, 0.0),
        up: tuple[float, float, float] = (0.0, 1.0, 0.0),
        fov_y: float = 60.0,
        aspect: float = 16.0 / 9.0,
        near: float = 0.1,
        far: float = 100.0,
    ) -> None:
        self.position = np.array(position, dtype=np.float32)
        self.target = np.array(target, dtype=np.float32)
        self.up = np.array(up, dtype=np.float32)
        self.fov_y = fov_y
        self.aspect = aspect
        self.near = near
        self.far = far

    def set_aspect(self, aspect: float) -> None:
        """更新投影宽高比（窗口尺寸变化时调用）。"""
        self.aspect = aspect

    def view_matrix(self) -> Mat4:
        """当前视图矩阵。"""
        return look_at(self.position, self.target, self.up)

    def projection_matrix(self) -> Mat4:
        """当前投影矩阵。"""
        return perspective(self.fov_y, self.aspect, self.near, self.far)

    def update(self, time: float) -> None:
        """简单动画：摄像机随音乐缓慢左右摆动（阶段 2 演示用）。"""
        self.position[0] = math.sin(time * 0.6) * 0.4
