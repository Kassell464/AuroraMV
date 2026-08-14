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
uniform float u_spin_speed;
uniform float u_star_brightness;
uniform float u_star_density;
uniform vec3 u_arm_color;
out vec4 fragColor;

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
}

void main() {
    vec2 uv = (v_uv - 0.5) * 2.0;
    uv.x *= u_aspect;
    float r = length(uv);
    float ang = atan(uv.y, uv.x);

    float spin = u_time * (0.15 + u_bass * 0.6) * u_spin_speed;
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
        if (h > u_star_density) {
            float d = length(f);
            float s = 1.0 - smoothstep(0.0, 0.14, d);
            float tw = 0.5 + 0.5 * sin(u_time * (2.0 + 3.0 * u_bass) + h * 60.0);
            stars += s * tw * (0.35 + u_bass) / scale;
        }
    }

    float core = exp(-r * 4.0) * (0.8 + u_bass * 2.0);

    vec3 col = vec3(0.03, 0.03, 0.09);
    col += arms * u_arm_color * (0.7 + 0.3 * u_bass);
    col += stars * u_star_brightness * vec3(0.90, 0.95, 1.00);
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
    float line = 1.0 - smoothstep(0.0, 0.03, d);
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
uniform float u_speed;
uniform vec3 u_color;
out vec4 fragColor;

void main() {
    vec2 p = (v_uv - 0.5) * 2.0;
    p.x *= u_aspect;

    float horizon = -0.72;
    float speed = (0.6 + u_bass * 2.0) * u_speed;
    float t = u_time * speed;

    float depth = 1.0 / max(0.02, p.y - horizon);
    vec2 g = p * depth * 2.0;
    g.x += t;

    vec2 f = abs(fract(g) - 0.5);
    float line = min(f.x, f.y);
    float grid = (1.0 - smoothstep(0.0, 0.09, line)) * min(1.0, 1.0 / (depth * 0.5));

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


# 粒子（阶段 7）：点精灵，生命周期淡出
PARTICLE_VERTEX_SHADER = """
#version 330
in vec2 in_position;
in float in_life;   // 剩余生命比例 0..1
in float in_size;
out float v_life;
void main() {
    v_life = clamp(in_life, 0.0, 1.0);
    gl_Position = vec4(in_position, 0.0, 1.0);
    gl_PointSize = in_size * (0.4 + v_life * 1.2);
}
"""

PARTICLE_FRAGMENT_SHADER = """
#version 330
in float v_life;
uniform vec3 u_color;
out vec4 fragColor;
void main() {
    vec2 p = gl_PointCoord - 0.5;
    float d = length(p);
    float a = (1.0 - smoothstep(0.15, 0.5, d)) * v_life;
    fragColor = vec4(u_color, a);
}
"""

# 后期处理（阶段 7）：场景纹理 + 震动偏移 + 闪光叠加
POST_FRAGMENT_SHADER = """
#version 330
in vec2 v_uv;
uniform sampler2D u_scene;
uniform vec2 u_offset;
uniform float u_flash;
uniform vec3 u_flash_color;
out vec4 fragColor;
void main() {
    vec2 uv = v_uv + u_offset;
    vec3 col = texture(u_scene, uv).rgb;
    col += u_flash_color * u_flash;
    fragColor = vec4(col, 1.0);
}
"""


# 黑胶唱片（MineRadio 概念灵感）：旋转盘体 + 沟槽 + 圆形专辑封面
VINYL_FRAGMENT_SHADER = """
#version 330
in vec2 v_uv;
uniform float u_time;
uniform float u_bass;
uniform float u_aspect;
uniform sampler2D u_cover;
uniform float u_has_cover;
uniform vec3 u_label_color;
out vec4 fragColor;

void main() {
    vec2 p = (v_uv - 0.5) * 2.0;
    p.x *= u_aspect;
    float r = length(p);
    float ang = atan(p.y, p.x);

    vec3 bg = vec3(0.015, 0.015, 0.03);
    vec3 col = bg;

    // 盘体 + 沟槽（转速随低频）
    float disc = (1.0 - smoothstep(0.90, 0.94, r)) * smoothstep(0.30, 0.34, r);
    float rot = ang + u_time * (0.25 + u_bass * 1.0);
    float grooves = 0.5 + 0.5 * sin(r * 240.0 + sin(rot * 2.0) * 1.5);
    vec3 vinyl_col = vec3(0.05, 0.05, 0.07) + smoothstep(0.55, 1.0, grooves) * vec3(0.055);
    float shine = smoothstep(0.75, 1.0, sin(rot + 1.3)) * (1.0 - smoothstep(0.32, 0.95, r)) * 0.4;
    col += disc * (vinyl_col + shine * vec3(0.85, 0.88, 0.95));

    // 中心封面（随盘旋转；无封面时显示标签色）
    float cover_r = 0.26;
    float inside = 1.0 - smoothstep(cover_r, cover_r + 0.015, r);
    if (inside > 0.0) {
        float cr = cover_r * 2.0;
        vec2 q = vec2(p.x * cos(-rot) - p.y * sin(-rot), p.x * sin(-rot) + p.y * cos(-rot));
        vec2 cuv = q / cr + 0.5;
        vec3 cover = u_has_cover > 0.5 ? texture(u_cover, cuv).rgb : u_label_color;
        col = mix(col, cover, inside);
    }

    // 中心孔
    col = mix(col, bg, 1.0 - smoothstep(0.0, 0.015, r));
    fragColor = vec4(col, 1.0);
}
"""

# 星球（MineRadio 概念灵感）：球体着色器 + 云带 + 边缘光
PLANET_FRAGMENT_SHADER = """
#version 330
in vec2 v_uv;
uniform float u_time;
uniform float u_bass;
uniform float u_aspect;
uniform float u_speed;
uniform vec3 u_color_a;
uniform vec3 u_color_b;
out vec4 fragColor;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

void main() {
    vec2 p = (v_uv - 0.5) * 2.0;
    p.x *= u_aspect;
    vec3 ro = vec3(0.0, 0.0, 2.4);
    vec3 rd = normalize(vec3(p, -1.8));
    float radius = 0.62;
    float b = dot(ro, rd);
    float c = dot(ro, ro) - radius * radius;
    float h = b * b - c;
    if (h < 0.0) {
        vec2 g = p * 5.0;
        float star = step(0.965, hash(floor(g)));
        fragColor = vec4(vec3(0.01, 0.01, 0.035) + star * vec3(0.55, 0.6, 0.75), 1.0);
        return;
    }
    float t = -b - sqrt(h);
    vec3 pos = ro + rd * t;
    vec3 n = normalize(pos);
    float lon = atan(n.z, n.x) + u_time * (0.12 + u_bass * 0.25) * u_speed;
    float lat = asin(clamp(n.y, -1.0, 1.0));
    float bands = 0.5 + 0.5 * sin(lat * 11.0 + sin(lon * 2.0 + lat * 6.0) * 2.5);
    vec3 albedo = mix(u_color_a, u_color_b, bands);
    vec3 light = normalize(vec3(0.6, 0.4, -0.7));
    float diff = max(dot(n, light), 0.0);
    float rim = pow(1.0 - abs(dot(n, normalize(-rd))), 2.2);
    vec3 col = albedo * (0.22 + diff * 0.95) + rim * u_color_b * 0.55;
    fragColor = vec4(col, 1.0);
}
"""

# 滚筒隧道（MineRadio 概念灵感）：沉浸隧道 + 节拍脉冲
TUNNEL_FRAGMENT_SHADER = """
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
    p *= 1.0 + u_flash * 0.1;

    float speed = 0.6 + u_bass * 1.8;
    float t = u_time * speed;
    float depth = 1.0 / max(length(p), 0.015);
    float ang = atan(p.y, p.x) + t * 0.6;

    float rings = abs(fract(depth * 0.5 + t * 0.25) - 0.5);
    float ring = 1.0 - smoothstep(0.0, 0.18, rings);
    float spokes = abs(fract(ang / 0.785) - 0.5);
    float spoke = (1.0 - smoothstep(0.0, 0.16, spokes)) * 0.6;

    float fade = exp(-depth * 0.5);
    vec3 col = vec3(0.01, 0.01, 0.03);
    col += u_color * (ring * 1.4 + spoke * 0.8) * fade * (0.5 + u_bass * 1.2);
    col += u_color * u_flash * 0.12;
    fragColor = vec4(col, 1.0);
}
"""

# 音域回响（MineRadio 概念灵感）：频谱地形高度图（真实 FFT 数据）
SPECTRUM_FRAGMENT_SHADER = """
#version 330
in vec2 v_uv;
uniform sampler2D u_spectrum;
uniform float u_bass;
uniform float u_time;
uniform vec3 u_color;
out vec4 fragColor;

void main() {
    float m = texture(u_spectrum, vec2(v_uv.x, 0.5)).r;
    float y = 0.14 + m * 0.72;
    float line = 1.0 - smoothstep(0.0, 0.012, abs(v_uv.y - y));
    float fill = (1.0 - smoothstep(0.0, 0.03, y - v_uv.y)) * 0.10;
    float glow = exp(-abs(v_uv.y - y) * 22.0) * 0.35;
    float grid = (1.0 - smoothstep(0.0, 0.02, abs(fract(v_uv.x * 16.0) - 0.5))) * 0.05;
    grid += (1.0 - smoothstep(0.0, 0.02, abs(fract(v_uv.y * 8.0) - 0.5))) * 0.05;

    vec3 col = vec3(0.015, 0.02, 0.04);
    col += u_color * (line * 1.5 + fill + glow) * (0.6 + u_bass * 0.8);
    col += u_color * grid * (0.35 + u_bass * 0.6);
    fragColor = vec4(col, 1.0);
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
