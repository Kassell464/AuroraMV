"""着色器加载（Shader Loader）。

职责：集中管理 GLSL 源码与程序编译。UI 层不得直接使用 OpenGL，
所有着色器编译都经由本模块与 Renderer 完成。
"""

from __future__ import annotations

import moderngl

VERTEX_SHADER = """
#version 330
in vec3 in_position;
in vec2 in_uv;
uniform mat4 u_mvp;
out vec2 v_uv;
void main() {
    gl_Position = u_mvp * vec4(in_position, 1.0);
    v_uv = in_uv;
}
"""

FRAGMENT_SHADER = """
#version 330
in vec2 v_uv;
uniform sampler2D u_texture;
out vec4 fragColor;
void main() {
    fragColor = texture(u_texture, v_uv);
}
"""

# 屏幕空间圆形（阶段 3 音频响应演示：u_radius 由低频驱动）
CIRCLE_VERTEX_SHADER = """
#version 330
in vec3 in_position;
in vec2 in_uv;
out vec2 v_uv;
void main() {
    v_uv = in_uv;
    gl_Position = vec4(in_position, 1.0);
}
"""

CIRCLE_FRAGMENT_SHADER = """
#version 330
in vec2 v_uv;
uniform float u_radius;  // 0.0 .. 0.5
uniform vec3 u_color;
out vec4 fragColor;
void main() {
    float d = distance(v_uv, vec2(0.5, 0.5));
    float edge = fwidth(d) * 1.5 + 0.002;
    float alpha = 1.0 - smoothstep(u_radius - edge, u_radius + edge, d);
    fragColor = vec4(u_color, alpha);
}
"""


class ShaderError(RuntimeError):
    """着色器编译或链接失败。"""


def create_program(
    ctx: moderngl.Context,
    vertex_source: str = VERTEX_SHADER,
    fragment_source: str = FRAGMENT_SHADER,
) -> moderngl.Program:
    """编译并链接着色器程序，失败时抛出 ShaderError。"""
    try:
        return ctx.program(
            vertex_shader=vertex_source,
            fragment_shader=fragment_source,
        )
    except Exception as exc:  # moderngl 编译失败时抛出的具体类型因驱动而异
        raise ShaderError(f"着色器编译失败: {exc}") from exc
