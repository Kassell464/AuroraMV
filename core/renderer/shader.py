"""着色器加载（Shader Loader）。

职责：集中管理 GLSL 源码与程序编译。UI 层不得直接使用 OpenGL，
所有着色器编译都经由本模块与 Renderer / 背景渲染器完成。
"""

from __future__ import annotations

import moderngl

# 全屏四边形顶点着色器（v_uv = 0..1 屏幕坐标）
FULLSCREEN_VERTEX_SHADER = """
#version 330
in vec3 in_position;
in vec2 in_uv;
out vec2 v_uv;
void main() {
    v_uv = in_uv;
    gl_Position = vec4(in_position, 1.0);
}
"""

# 屏幕空间圆形（阶段 3 音频响应演示：半径随低频变化）
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

# 图片背景：cover 裁切 + 缩放（镜头推进）+ 平移 + 颜色调整
IMAGE_FRAGMENT_SHADER = """
#version 330
in vec2 v_uv;
uniform sampler2D u_image;
uniform float u_zoom;         // >= 1.0，越大越推进
uniform vec2 u_offset;        // 平移（uv 单位）
uniform float u_tex_aspect;
uniform float u_screen_aspect;
uniform vec4 u_tint;
out vec4 fragColor;
void main() {
    vec2 crop = vec2(min(1.0, u_tex_aspect / u_screen_aspect),
                     min(1.0, u_screen_aspect / u_tex_aspect));
    vec2 uv = 0.5 + (v_uv - 0.5) * crop / u_zoom + u_offset;
    uv = clamp(uv, 0.0, 1.0);
    fragColor = texture(u_image, uv) * u_tint;
}
"""

# 银河：旋臂 + 恒星 + 核心；低频增强 → 旋转/闪烁加快
GALAXY_FRAGMENT_SHADER = """
#version 330
in vec2 v_uv;
uniform float u_time;
uniform float u_bass;
uniform float u_aspect;
out vec4 fragColor;

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
}

void main() {
    vec2 uv = (v_uv - 0.5) * 2.0;
    uv.x *= u_aspect;
    float r = length(uv);
    float ang = atan(uv.y, uv.x);

    float spin = u_time * (0.15 + u_bass * 0.6);
    float rot_ang = ang + spin * (1.0 + 1.5 * r);

    float arms = 0.5 + 0.5 * sin(rot_ang * 2.0 + 16.0 * r);
    arms = smoothstep(0.45, 1.0, arms) * (1.0 - smoothstep(0.1, 0.95, r));

    float stars = 0.0;
    for (int i = 0; i < 3; i++) {
        float scale = float(i + 1);
        vec2 g = uv * (2.5 * scale);
        vec2 id = floor(g);
        vec2 f = fract(g) - 0.5;
        float h = hash(id);
        if (h > 0.86) {
            float d = length(f);
            float s = smoothstep(0.14, 0.0, d);
            float tw = 0.5 + 0.5 * sin(u_time * (2.0 + 3.0 * u_bass) + h * 60.0);
            stars += s * tw * (0.35 + u_bass) / scale;
        }
    }

    float core = exp(-r * 4.0) * (0.8 + u_bass * 2.0);

    vec3 col = vec3(0.03, 0.03, 0.09);
    col += arms * vec3(0.30, 0.15, 0.60) * (0.7 + 0.3 * u_bass);
    col += stars * vec3(0.90, 0.95, 1.00);
    col += core * vec3(1.00, 0.80, 0.90);
    fragColor = vec4(col, 1.0);
}
"""

# 波形：真实音频波形（u_wave 1D 纹理）；低频增强 → 颜色更亮
WAVEFORM_FRAGMENT_SHADER = """
#version 330
in vec2 v_uv;
uniform sampler2D u_wave;
uniform float u_bass;
uniform float u_time;
uniform vec3 u_color;
out vec4 fragColor;

void main() {
    float s = texture(u_wave, vec2(v_uv.x, 0.5)).r;
    float y = s * 0.4 + 0.5;
    float d = abs(v_uv.y - y);
    float line = smoothstep(0.03, 0.0, d);
    float fill = step(v_uv.y, y);
    float glow = exp(-d * 25.0) * 0.6;
    float pulse = 0.85 + 0.15 * sin(u_time * 3.0);
    vec3 base = vec3(0.02, 0.03, 0.07);
    vec3 col = base + u_color * (0.5 + u_bass * 0.9) * (line * 1.2 + fill * 0.18 + glow) * pulse;
    fragColor = vec4(col, 1.0);
}
"""

# 霓虹网格：科幻透视网格；低频增强 → 流动加快；节拍 → 闪光
NEON_GRID_FRAGMENT_SHADER = """
#version 330
in vec2 v_uv;
uniform float u_time;
uniform float u_bass;
uniform float u_flash;
uniform float u_aspect;
uniform vec3 u_color;
out vec4 fragColor;

void main() {
    vec2 p = (v_uv - 0.5) * 2.0;
    p.x *= u_aspect;

    float horizon = -0.72;
    float speed = 0.6 + u_bass * 2.0;
    float t = u_time * speed;

    float depth = 1.0 / max(0.02, p.y - horizon);
    vec2 g = p * depth * 2.0;
    g.x += t;

    vec2 f = abs(fract(g) - 0.5);
    float line = min(f.x, f.y);
    float grid = smoothstep(0.09, 0.0, line) * min(1.0, 1.0 / (depth * 0.5));

    float glow = exp(-abs(p.y - horizon) * 6.0);
    vec3 col = u_color * (grid * (0.4 + u_bass * 1.5) + glow * (0.25 + u_flash * 0.8));
    col += u_color * u_flash * 0.12;
    fragColor = vec4(col, 1.0);
}
"""


# 歌词文本（阶段 6）：屏幕空间四边形 + 透明度
LYRIC_VERTEX_SHADER = """
#version 330
in vec3 in_position;
in vec2 in_uv;
uniform vec2 u_center;
uniform vec2 u_half_size;
out vec2 v_uv;
void main() {
    v_uv = in_uv;
    gl_Position = vec4(u_center + in_position.xy * u_half_size, 0.0, 1.0);
}
"""

LYRIC_FRAGMENT_SHADER = """
#version 330
in vec2 v_uv;
uniform sampler2D u_text;
uniform float u_alpha;
out vec4 fragColor;
void main() {
    vec4 tex = texture(u_text, v_uv);
    fragColor = vec4(tex.rgb, tex.a * u_alpha);
}
"""


class ShaderError(RuntimeError):
    """着色器编译或链接失败。"""


def create_program(
    ctx: moderngl.Context,
    vertex_source: str = FULLSCREEN_VERTEX_SHADER,
    fragment_source: str = CIRCLE_FRAGMENT_SHADER,
) -> moderngl.Program:
    """编译并链接着色器程序，失败时抛出 ShaderError。"""
    try:
        return ctx.program(
            vertex_shader=vertex_source,
            fragment_shader=fragment_source,
        )
    except Exception as exc:  # moderngl 编译失败时抛出的具体类型因驱动而异
        raise ShaderError(f"着色器编译失败: {exc}") from exc
