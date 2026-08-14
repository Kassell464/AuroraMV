# 示例（examples）

| 脚本 | 说明 |
|------|------|
| [`export_video.py`](export_video.py) | 程序化导出三种典型输出：横屏 MP4 / 竖屏 WebM / 方形 MOV |
| [`capture_screenshot.py`](capture_screenshot.py) | 离屏渲染一帧保存为 PNG（截图 / 宣传图） |

运行示例（在项目根目录）：

```bash
venv\Scripts\python examples\export_video.py
venv\Scripts\python examples\capture_screenshot.py
```

两个脚本都不需要打开窗口（standalone OpenGL 上下文 + 离屏帧缓冲）。
