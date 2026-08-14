# 背景模板（templates/background）

背景模板（规格 33 节）：控制 Shader 类型与参数。所有参数可调节。

| 模板 | 类型 | 参数 | 预设包 |
|------|------|------|--------|
| `cinema` | image | 缩放速度/幅度、暖色 tint、**节拍切镜（beat_cuts/cut_speed）** | cinema |
| `aurora` | galaxy | 旋速、星亮度、星密度、旋臂色（紫） | aurora |
| `cyberpunk` | neon_grid | 品红、快速流动 | cyberpunk |
| `stage` | neon_grid | 青色、标准速度 | stage |
| `synthwave` | neon_grid | 橙红、慢速流动 | synthwave |
| `dj` | waveform | 亮青波形 | dj |
| `vinyl` | vinyl | 转速、唱片盘面色 | vinyl |
| `planet` | planet | 星球双色、自转速度 | planet |
| `tunnel` | tunnel | 隧道色、速度 | tunnel |
| `spectrum` | spectrum | 频谱线色 | spectrum |
| `emily` | cover_particles | 粒子色、浮动速度 | emily |

场景预设通过 `"background": {"template": "<名称>"}` 引用本目录模板，
也可用 `{"type": ..., "params": ...}` 内联定义。
