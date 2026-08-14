"""纹理管理（Texture Manager）。

职责：上传纹理数据到 GPU、按名称缓存纹理，
并提供程序化测试纹理（避免阶段 2 依赖外部图片文件）。
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

import moderngl


def make_test_texture(size: int = 256) -> npt.NDArray[np.uint8]:
    """生成程序化测试纹理：彩色渐变 + 棋盘格暗色叠加。"""
    x = np.linspace(0.0, 1.0, size, dtype=np.float32)
    y = np.linspace(0.0, 1.0, size, dtype=np.float32)
    grid_x, grid_y = np.meshgrid(x, y)

    rgba = np.zeros((size, size, 4), dtype=np.uint8)
    rgba[..., 0] = ((1.0 - grid_y) * 255.0).astype(np.uint8)  # R：上红下黑
    rgba[..., 1] = (grid_x * 255.0).astype(np.uint8)  # G：左黑右绿
    rgba[..., 2] = (grid_y * 255.0).astype(np.uint8)  # B：上黑下蓝
    rgba[..., 3] = 255

    checker = ((grid_x * 8).astype(np.int32) + (grid_y * 8).astype(np.int32)) % 2 == 0
    rgba[checker] = rgba[checker] // 2  # 棋盘格暗色叠加

    return rgba


def upload_texture(ctx: moderngl.Context, rgba: npt.NDArray[np.uint8]) -> moderngl.Texture:
    """把 RGBA 数组上传为 GPU 纹理（双线性过滤）。"""
    height, width = rgba.shape[:2]
    texture = ctx.texture((width, height), 4, data=rgba.tobytes())
    texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
    return texture


class TextureManager:
    """管理 GPU 纹理的生命周期（按名称缓存）。"""

    def __init__(self, ctx: moderngl.Context) -> None:
        self._ctx = ctx
        self._textures: dict[str, moderngl.Texture] = {}

    def create(self, name: str, rgba: npt.NDArray[np.uint8]) -> moderngl.Texture:
        """上传并缓存纹理。"""
        texture = upload_texture(self._ctx, rgba)
        self._textures[name] = texture
        return texture

    def get(self, name: str) -> moderngl.Texture | None:
        """按名称获取纹理；不存在时返回 None。"""
        return self._textures.get(name)

    def release(self, name: str | None = None) -> None:
        """释放单个纹理；name 为 None 时释放全部。"""
        if name is None:
            for texture in self._textures.values():
                texture.release()
            self._textures.clear()
            return
        texture = self._textures.pop(name, None)
        if texture is not None:
            texture.release()
