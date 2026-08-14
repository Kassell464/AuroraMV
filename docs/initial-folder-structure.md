# AuroraMV 初始目录结构（initial folder structure）

> 依据《AuroraMV V0.1 Engineering Specification》第 10 节“项目目录结构”、第二部分各模块章节（13、23、26、32、35 节）与第三部分阶段 0 / 阶段 11 整理。

## 1. 初始目录树

```
AuroraMV/
├── main.py                        # 程序入口
├── requirements.txt               # 初始依赖（阶段 0）
├── .gitignore                     # Git 忽略规则（阶段 0）
├── README.md                      # 开源说明（阶段 11）
├── LICENSE                        # MIT 许可（阶段 11）
│
├── app/
│   └── application.py             # 应用核心 / ApplicationController
│
├── ui/                            # UI 层（PySide6，不得包含渲染逻辑）
│   ├── main_window.py             # 主窗口 MainWindow
│   ├── preview_widget.py          # 预览控件 PreviewWidget
│   └── panels/                    # 面板
│
├── core/                          # 核心模块
│   ├── audio/                     # 音频引擎（加载、播放同步、分析、AudioState）
│   │   ├── analyzer.py            # 分析器（波形、FFT、BPM、音量/低频/节拍）
│   │   └── beat_detector.py       # 节拍检测
│   │
│   ├── renderer/                  # 渲染器引擎（Renderer 是 AuroraMV 核心）
│   │   ├── engine.py              # Renderer：load_scene / update / render
│   │   ├── scene.py               # Scene / SceneManager
│   │   └── camera.py              # 摄像机系统
│   │
│   ├── lyrics/                    # 歌词引擎（解析、时间同步、动画）
│   │   ├── parser.py              # LRC 解析器
│   │   └── provider.py            # LyricsProvider（LRC / Manual / Whisper）
│   │
│   ├── effects/                   # 效果引擎（非核心视觉效果）
│   │   ├── manager.py             # EffectManager
│   │   └── particle.py            # 粒子效果
│   │
│   ├── templates/                 # 模板系统
│   │   └── loader.py              # TemplateLoader：load / validate
│   │
│   └── project/                   # 项目系统
│       ├── project.py             # 项目数据模型
│       └── serializer.py          # project.json 序列化（.amv = zip）
│
├── export/
│   └── ffmpeg.py                  # 导出管线：帧捕获 → FFmpeg → MP4
│
├── templates/                     # 模板目录（社区生态基础）
│   ├── lyrics/                    # 歌词模板（neon.json / cinema.json / minimal.json）
│   ├── background/                # 背景模板（galaxy.json 等）
│   ├── effects/                   # 效果模板（shake.json 等）
│   └── scene/                     # 场景模板（完整组合）
│
├── assets/                        # 静态资源
│
├── docs/                          # 文档（阶段 11）
├── examples/                      # 示例（阶段 11）
│
└── tests/                         # 测试（每个模块的基本验证）
```

## 2. 各目录 / 文件职责速查

| 路径 | 职责 | 关键规则 |
|------|------|----------|
| `main.py` | 程序入口 | 阶段 1：程序成功启动 |
| `app/application.py` | 应用核心、ApplicationController | — |
| `ui/` | 窗口、控件、面板、用户交互 | **不得包含渲染逻辑**；不直接调用 OpenGL |
| `core/audio/` | 音频加载、播放同步、分析、实时 AudioState | 渲染器只读 AudioState，不直接读音频 |
| `core/renderer/` | 生成每一帧画面；场景；摄像机 | 预览与导出共用渲染器 |
| `core/lyrics/` | 歌词解析、时间同步、动画 | AI 识别（Whisper）不得阻塞正常流程 |
| `core/effects/` | 所有非核心视觉效果 | 必须模块化（EffectManager 统一管理） |
| `core/templates/` | 模板加载与校验 | .json 模板 |
| `core/project/` | 项目模型与序列化 | 项目文件 .amv（zip） |
| `export/` | FFmpeg 帧编码、MP4 生成 | 不重新实现 Renderer |
| `templates/` | 歌词/背景/效果/场景四类模板 | 未来社区生态基础 |
| `assets/` | 静态资源 | — |
| `tests/` | 模块基本验证 | 音频/渲染器/歌词/导出各一项最小测试 |
| `docs/`、`examples/` | 开源准备（阶段 11） | — |

## 3. 模板目录细分

```
templates/
├── lyrics/
│   ├── neon.json      # 字体 Orbitron、颜色 #ffffff、动画 enter=fade / idle=glow / beat=scale
│   ├── cinema.json
│   └── minimal.json
├── background/
│   └── galaxy.json    # 动态背景（银河 / 波形 / 霓虹网格 / 流体）
├── effects/
│   └── shake.json     # 节拍震动等效果模板
└── scene/
    └── *.json         # 场景模板（如：赛博朋克 MV = 赛博背景 + 霓虹歌词 + 故障效果）
```

## 4. 项目文件（.amv）内部结构

项目文件 `.amv` 实际是 zip：

```
project.amv
├── project.json        # 版本 / 项目（name、canvas、fps）/ 音频路径 / scenes[]
├── assets/
│   ├── audio/          # 音频（如 song.mp3）
│   ├── backgrounds/    # 背景图片
│   └── lyrics/         # 歌词（LRC 等）
└── cache/              # 缓存
```

## 5. 各阶段的目录落地节奏

| 阶段 | 新增内容 |
|------|----------|
| 阶段 0 环境搭建 | `venv/`（不入库）、`requirements.txt`、`.gitignore` |
| 阶段 1 应用程序骨架 | `main.py`、`app/`、`ui/`（MainWindow、PreviewWidget、ApplicationController） |
| 阶段 2 渲染器核心 | `core/renderer/`（engine、camera；OpenGL 上下文、着色器加载器、纹理管理器） |
| 阶段 3 音频引擎 | `core/audio/`（analyzer、beat_detector、AudioState） |
| 阶段 4 背景系统 | `core/renderer/` 背景部分、`assets/` |
| 阶段 5 场景系统 | `core/renderer/scene.py`（Scene、SceneManager）、`core/project/` |
| 阶段 6 歌词引擎 | `core/lyrics/`（parser、provider）、`templates/lyrics/` |
| 阶段 7 效果系统 | `core/effects/`（manager、particle） |
| 阶段 8 模板系统 | `core/templates/loader.py`、`templates/` 全部模板 |
| 阶段 9 导出系统 | `export/ffmpeg.py` |
| 阶段 10 UI 打磨 | `ui/panels/`、主题样式 |
| 阶段 11 开源准备 | `README.md`、`LICENSE`、`docs/`、`examples/`、演示视频与截图 |

> 注意：目录按模块边界创建，新增文件只落在所属模块内，禁止跨模块修改（如 UI 直接调用 OpenGL）。
