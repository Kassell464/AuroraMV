# AuroraMV 用户指南（V0.1）

## 1. 安装

**环境要求**

| 组件 | 要求 |
|------|------|
| 操作系统 | Windows 10+ |
| Python | ≥ 3.12 |
| GPU | 现代 GPU（推荐 RTX 3060 或更高；渲染与导出均为 GPU 离屏渲染） |
| FFmpeg | 需在 PATH 中（mp3 解码与视频导出必需），`ffmpeg -version` 可验证 |

**步骤**

```bash
git clone https://github.com/Kassell464/AuroraMV.git
cd AuroraMV
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

## 2. 启动预览

```bash
venv\Scripts\python main.py                          # 内置演示曲
venv\Scripts\python main.py --audio 你的歌.wav          # 自己的歌
venv\Scripts\python main.py --audio 你的歌.wav --lrc 歌词.lrc
```

启动后自动播放并进入「自动切换」模式：六套视觉预设随音乐时间轮换。

## 3. 界面说明

| 区块 | 功能 |
|------|------|
| 视觉风格 | 「自动切换」+ 六张预设卡片（电影镜头 / 极光星云 / 赛博朋克 / 歌词舞台 / 合成波 / DJ 现场），点击立即切换 |
| 效果调节 | 节拍震动强度、闪光强度、粒子数量三个滑杆——实时生效，切换场景后保持 |
| 导出视频 | 格式 / 分辨率 / 帧率 / 宽高比下拉 + 输出路径 + 导出按钮（后台导出，带进度条） |
| 播放控制 | 播放 / 暂停（呼吸灯指示播放状态） |

## 4. 导出

### GUI

在「导出视频」区块选择选项 → 点「导出视频」→ 等待进度条完成。

### CLI（无窗口）

| 选项 | 取值 |
|------|------|
| `--export <文件>` | 输出路径（必需） |
| `--format` | `mp4` / `webm` / `mov`（默认 mp4） |
| `--resolution` | `360p` / `480p` / `720p` / `1080p` / `1440p`（默认 1080p） |
| `--fps` | `24` / `30` / `60`（默认 30） |
| `--aspect` | `16:9` / `9:16` / `1:1`（默认 16:9） |
| `--bitrate` | `auto`（CRF，默认）或如 `8M` |
| `--trim` | 只导出前 N 秒（默认整曲） |

示例：

```bash
venv\Scripts\python main.py --export out.mp4 --resolution 1080p --fps 60
venv\Scripts\python main.py --export out.webm --format webm --aspect 9:16 --trim 15
```

## 5. 模板自定义（社区生态基础）

四类 JSON 模板位于 `templates/`，改参数即改视觉，无需改代码：

```
templates/
├── lyrics/       歌词模板：字体、颜色、辉光、动画（enter/idle/beat）
├── background/   背景模板：类型 + 参数（银河旋速/星密度、网格颜色/流速…）
├── effects/      效果模板：类型 + 参数（震动强度、闪光强度、粒子数量…）
└── scene/        场景预设：背景模板引用 + 歌词模板 + 效果组合
```

**示例：调暗赛博朋克网格**（`templates/background/cyberpunk.json`）：

```json
{
  "type": "neon_grid",
  "params": {"color": [0.7, 0.1, 0.45], "speed": 0.9}
}
```

**示例：更猛的节拍震动**（`templates/effects/beat_shake.json`）：

```json
{
  "name": "beat_shake",
  "type": "beat_shake",
  "params": {"strength": 0.06, "decay": 8.0, "frequency": 14.0}
}
```

模板由 `TemplateLoader` 校验（必填字段、类型白名单、颜色格式等），非法模板会报错并说明原因。

## 6. 常见问题

| 问题 | 处理 |
|------|------|
| `导出失败: 未找到 FFmpeg` | 安装 FFmpeg 并加入 PATH（如 `winget install Gyan.FFmpeg`） |
| 导出视频没有声音 | 音频文件路径需有效且可被 FFmpeg 解码 |
| 歌词时间整体偏移 | 个别 LRC 可用 `[offset:+毫秒]` 标签整体校正 |
| 预览窗口黑屏 | 确认 GPU 驱动支持 OpenGL 3.3+ Core Profile |
| 节拍相位偏移 | 已知限制：librosa 节拍相位存在整体偏移（约 0.27s），V0.2 计划校准，详见发布说明 |
