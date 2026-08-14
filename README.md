# AuroraMV

An open-source music visualization and music video generation application.

> 将音乐转化为视觉上令人印象深刻的视频，并带有动态歌词、音频响应效果和可自定义的视觉主题。

## What is AuroraMV

AuroraMV 是一个由音乐驱动的视觉引擎，专注于**自动视觉生成**，而非传统的基于时间轴的视频编辑。

- **音乐驱动视觉**：自动响应节拍 / 音量 / 低频 / 节奏
- **模板优先**：选择霓虹风格 + 银河背景 + 赛博歌词，直接得到完整视觉体验
- **实时预览**：所见即所导出（预览与导出共用同一条渲染管线）
- **快速导出**：MP4（H264），支持多种分辨率 / FPS / 宽高比

## Tech Stack

- **语言**：Python 3.12
- **GUI**：PySide6
- **渲染**：ModernGL（GPU 渲染 / 着色器 / 粒子）
- **音频**：librosa / numpy / soundfile
- **导出**：FFmpeg

## Development Status

V0.1 开发中。路线图见 [`task-board.md`](task-board.md)，架构见 [`architecture.md`](architecture.md)。

## License

[MIT](LICENSE)
