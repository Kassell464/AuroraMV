# AuroraMV 架构文档（architecture.md）

> 依据《AuroraMV V0.1 Engineering Specification》第一部分（产品定义与系统架构）与第二部分（核心模块设计）整理。
> 版本：0.1 ｜ 许可协议：MIT ｜ 平台：Windows 10+ ｜ 语言：Python 3.12

## 1. 架构总览

AuroraMV 的核心不是 UI，而是一个实时视觉渲染系统。

```
                    AuroraMV
                       |
                 应用核心
                       |
 ------------------------------------------------
 |                    |                         |
UI 层          项目系统                模板系统
                       |
                 渲染器引擎
                       |
 ------------------------------------------------
背景       歌词       效果       摄像机
渲染器     渲染器     渲染器     系统
                       |
                OpenGL 管线
                       |
              预览 / 导出
                       |
                    FFmpeg
```

- **UI 层**：PySide6 负责应用程序窗口、控件、面板、用户交互；**不得包含渲染逻辑**。
- **项目系统**：管理 `.amv` 项目（本质是 zip），内含 `project.json` 与资源目录。
- **模板系统**：歌词 / 背景 / 效果 / 场景四类模板，是未来社区生态基础。
- **渲染器引擎**：ModernGL，负责 GPU 渲染、着色器效果、粒子、视觉合成。
- **预览 / 导出共用同一条渲染管线**（“所见即所导出”），导出经 FFmpeg 生成 MP4。

## 2. 核心数据流

```
音频文件 → 音频引擎 → 音频状态 → 场景管理器 → 渲染器引擎
                                            ↓
                    背景渲染器 / 歌词渲染器 / 效果渲染器
                                            ↓
                                      OpenGL 帧
                                            ↓
                                      预览 / 导出
```

- 渲染器不应该直接读取音频，只读取 `AudioState`。
- 所有视觉效果通过 `AudioState` 响应音乐（节拍、音量、低频、节奏）。

## 3. 核心模块职责

```
core/
├── audio/       音频加载、播放同步、分析、提供实时 AudioState
├── renderer/    生成每一帧画面（Renderer 是 AuroraMV 核心）
├── lyrics/      解析歌词、时间同步、动画
├── effects/     所有非核心视觉效果
├── templates/   模板加载与校验
└── project/     项目文件与序列化
```

## 4. 渲染器引擎（Renderer）

### 4.1 渲染器接口

```python
class Renderer:
    def load_scene(self, scene):
        pass

    def update(self, time, audio_state):
        pass

    def render(self):
        pass
```

### 4.2 帧渲染管线（每一帧）

1. 获取当前场景
2. 更新音频状态
3. 渲染背景
4. 渲染效果
5. 渲染歌词
6. 应用后期处理
7. 输出帧

### 4.3 图层系统

类似游戏引擎，渲染顺序固定：

| 图层 | 内容 | 渲染顺序 |
|------|------|----------|
| Layer 0 | 背景 | 1 |
| Layer 1 | 粒子 | 2 |
| Layer 2 | 效果 | 3 |
| Layer 3 | 歌词 | 4 |
| Layer 4 | UI 叠加层 | — |
| — | 后期处理 | 5 |

## 5. 音频系统

### 5.1 音频管线

```
song.mp3 → 解码器 → PCM 数据 → 分析器 → 音频状态 → 渲染器
```

### 5.2 音频状态（AudioState）

渲染器只读取 `AudioState`，不直接读取音频。

```python
class AudioState:
    timestamp: float
    volume: float
    bass: float
    mid: float
    treble: float
    beat: bool
    bpm: float
```

### 5.3 音频响应示例

| 效果 | 输入 | 计算 / 输出 |
|------|------|-------------|
| 粒子效果 | bass = 0.8 | `particle_count = base_count + bass * multiplier` |
| 摄像机震动 | beat = True | `camera.offset = random()` |
| 歌词缩放 | volume | `font_size = base_size + volume * scale` |

## 6. 背景渲染器

### 6.1 图片背景

- 支持格式：jpg、png、webp
- 效果：缩放（如 1.0 → 1.2 模拟镜头推进）、平移（左/右/上/下）、模糊（使用 shader）、颜色调整

### 6.2 动态背景（V0.1 内置）

| 类型 | 特点 |
|------|------|
| 银河（Galaxy） | 粒子、星空 |
| 波形（Waveform） | 音频波形 |
| 霓虹网格（Neon Grid） | 科幻网格 |
| 流体（Fluid） | Shader 流体 |

动态背景**必须支持 AudioState**。例如：低频增强 → 粒子速度加快。

## 7. 歌词引擎

### 7.1 歌词提供器（LyricsProvider）统一接口

```python
class LyricsProvider:
    def load():
        pass

    def get_current_line(time):
        pass
```

实现：`LRCProvider`（LRC 文件）、`ManualProvider`（手动文本）、`WhisperProvider`（AI 识别，可选，**不得阻塞正常流程**）。

### 7.2 LRC 解析

输入 `[00:12.50] Hello World` → 输出 `LyricLine(text="Hello World", start=12.5, end=16.0)`。

### 7.3 歌词动画引擎

歌词不是文本，而是动画对象（`LyricObject`：text / position / opacity / scale / animation_state）。

生命周期：开始之前 → 入场动画 → 激活 → 退场动画。

### 7.4 歌词模板

`templates/lyrics/neon.json`、`cinema.json`、`minimal.json`（字体、颜色、动画：enter / idle / beat）。

## 8. 效果引擎

- `Effect` 接口：`update(audio_state)` + `render()`，负责所有非核心视觉效果（闪光、震动、故障、粒子）。
- `EffectManager`：管理多个 Effect，统一 `update()` / `render()`。

## 9. 场景系统

- V0.1 **不使用传统 Timeline**，使用 Scene（一个时间范围内的完整视觉状态）。
- `Scene` 数据模型：`id` / `start_time` / `end_time` / `background` / `lyric_template` / `effects`。
- `SceneManager`：`get_scene(time)` 根据当前时间返回场景。

## 10. 模板系统

- 目录：`templates/lyrics`、`templates/background`、`templates/effects`、`templates/scene`。
- 模板类型：歌词模板（字体/动画/颜色）、背景模板（Shader/参数）、效果模板（特效）、场景模板（完整组合，如“赛博朋克 MV = 赛博背景 + 霓虹歌词 + 故障效果”）。
- `TemplateLoader`：`load(path)` + `validate()`。

## 11. 项目系统

- 项目文件：`.amv`，实际是 zip，结构：

```
project.amv
├── project.json
├── assets/
│   ├── audio/
│   ├── backgrounds/
│   └── lyrics/
└── cache/
```

- `project.json` 架构：`version` / `project`（name、canvas、fps）/ `audio`（path）/ `scenes[]`（id、start、end、background、lyrics、effects）。

## 12. 预览与导出管线

**导出管线（Export 不重新实现 Renderer）：**

```
项目 → 渲染器 → 帧缓冲 → FFmpeg → MP4
```

**预览管线（实时预览）：**

```
渲染器 → OpenGL 纹理 → PySide6 控件
```

- 导出输出：MP4 / H264；分辨率 360p–1440p；FPS 24/30/60；宽高比 16:9、9:16、1:1；码率自动 / 手动。

## 13. 类关系总览

```
应用程序 → 项目管理器 → 场景管理器 → 渲染器
                                      ↓
                    背景渲染器 / 歌词引擎 / 效果引擎
                                      ↓
                                   OpenGL
```

## 14. 架构规则（必须遵守）

1. **UI 与渲染器必须分离**：按钮 → 修改渲染器状态 → 渲染器更新帧；UI 不直接调用 `draw()`。
2. **所有视觉效果必须模块化**：使用 EffectManager + NeonEffect / GalaxyEffect，禁止 `if neon: draw neon` 式散落代码。
3. **预览与导出共用渲染器**：Renderer 同时输出到预览窗口与帧导出。

## 15. 技术栈

| 层 | 技术 | 职责 |
|----|------|------|
| 编程语言 | Python 3.12 | 开发快、AI 生态、音频生态、适合开源 |
| GUI | PySide6 | 窗口、控件、面板、用户交互（不含渲染逻辑） |
| 渲染 | ModernGL | GPU 渲染、着色器、粒子、视觉合成 |
| 音频 | librosa / numpy / soundfile | 波形、FFT、BPM、节拍分析 |
| 视频编码 | FFmpeg | 帧编码、MP4 生成 |

## 16. 性能目标

- 目标硬件：RTX 3060（开发环境要求现代 GPU，推荐 RTX 3060 或更高）。
- 预览目标：1080p、30 FPS；导出目标：1080p、30 FPS。
- 优化优先级：避免不必要的 CPU 渲染 → 使用 GPU 着色器 → 缓存资源。

## 17. 扩展预留（未来路线图）

- **V0.2**：视频背景（mp4/webm/mov）、更好的 AI 歌词（faster-whisper）、更多模板（社区包）。
- **V0.3**：时间轴编辑器（拖动场景、关键帧、转场）、插件系统（Python 插件、Shader 插件）。
- **V1.0**：完整开源生态（模板市场、社区分享、插件 API、跨平台构建）。
