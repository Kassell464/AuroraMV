# AuroraMV 首次提交计划（first commit plan）

> 依据《AuroraMV V0.1 Engineering Specification》阶段 0（环境搭建）、阶段 1（应用程序骨架）与第 46 节 Git 工作流整理。
> 首次提交 = 阶段 0 + 阶段 1：一个干净、可运行的项目骨架。

## 1. 目标

**程序成功启动** —— 出现一个窗口：

```
AuroraMV
[预览区域]
[控件]
```

对应规格原文：阶段 1 目标“The program launches successfully”，预期结果“A window appears: AuroraMV / [Preview Area] / [Controls]”。

## 2. 提交前准备（阶段 0，半天）

### 2.1 安装清单

- Python 3.12
- Git
- FFmpeg
- Visual Studio Build Tools
- （硬件）现代 GPU，推荐 RTX 3060 或更高；Windows 10+

### 2.2 创建

- `venv`（虚拟环境，不入库，由 `.gitignore` 忽略）
- `requirements.txt`
- `.gitignore`

## 3. 初始依赖（requirements.txt）

按规格阶段 0 的“初始依赖”清单：

```
PySide6
moderngl
pygame
numpy
librosa
soundfile
```

> 约束（AI 规则 4）：依赖仅限规格列出的初始依赖，不引入额外库；如需新增库，先说明“为什么需要 / 替代方案 / 维护状态”。

## 4. .gitignore（建议内容，依据阶段 0 要求与 Python 项目惯例）

```gitignore
# 虚拟环境
venv/

# Python 缓存
__pycache__/
*.pyc

# 导出产物
*.mp4

# 项目文件（.amv 为 zip 打包产物，按需入库）
*.amv

# 缓存
cache/
```

## 5. 首次提交范围（文件清单）

| 路径 | 内容 | 来源 |
|------|------|------|
| `main.py` | 程序入口 | 阶段 1 |
| `app/application.py` | ApplicationController（应用控制器） | 阶段 1 |
| `ui/main_window.py` | MainWindow（主窗口） | 阶段 1 |
| `ui/preview_widget.py` | PreviewWidget（预览控件） | 阶段 1 |
| `ui/panels/` | 面板占位 | 阶段 1 / 目录结构 |
| `requirements.txt` | 初始依赖 | 阶段 0 |
| `.gitignore` | 忽略规则 | 阶段 0 |
| `README.md` | 项目说明（骨架版，阶段 11 再完善） | 阶段 11 提前占位 |
| `LICENSE` | MIT 许可 | 阶段 11 提前占位 |

> 首次提交**不包含**渲染逻辑、音频引擎、场景系统等后续阶段内容——遵守 AI 规则 1“不要一次性生成整个应用程序”，只实现骨架并确保能运行。

## 6. 分支策略与提交信息

- **分支**：`main`（稳定）、`develop`（开发）、`feature/*`（功能分支）。
- 首次提交：先建仓库并推入 `main`，后续开发走 `develop` 与功能分支（如 `feature/renderer`、`feature/audio-engine`、`feature/lyrics`、`feature/export`）。
- **提交信息**（按规格提交格式）：

```
feat: initialize AuroraMV application skeleton
```

> 格式约定：`feat:` 新功能、`fix:` 修复（如 `fix: solve shader loading issue`）、`refactor:` 重构（如 `refactor: cleanup scene manager`）。

## 7. 验收标准

- [ ] `python main.py` 启动成功，窗口标题 AuroraMV
- [ ] 窗口包含 [预览区域] 与 [控件]
- [ ] 依赖按 `requirements.txt` 安装成功（PySide6、moderngl、pygame、numpy、librosa、soundfile）
- [ ] 提交干净：不含 `venv/`、`__pycache__/` 等生成物

## 8. 首次提交禁止事项（AI 编码规则对照）

| 禁止 | 规则 |
|------|------|
| 一次性生成完整 AuroraMV 应用（含渲染/音频/歌词等） | 规则 1 |
| `ui/main_window.py` 直接调用 OpenGL 函数 | 规则 3 |
| 添加规格之外的依赖库 | 规则 4 |
| 修改超出骨架范围的其他模块 | 规则 1 / 规则 6 |

> 写代码前先说明：哪些文件将被修改、为什么修改、架构受到什么影响（规则 2）。每个功能需要：代码 + 最小化测试 + 文档（规则 5）。

## 9. 首次提交后的下一步

按规格的正确开发顺序（先构建引擎）：

```
渲染器核心（阶段 2，feature/renderer）
   ↓
音频响应系统（阶段 3，feature/audio-engine）
   ↓
场景系统（阶段 5）
   ↓
歌词系统（阶段 6，feature/lyrics）
   ↓
UI（阶段 10）
   ↓
导出（阶段 9，feature/export）
```

> 每个后续阶段提交前均需满足里程碑标准：应用可运行、已有功能不被破坏、架构保持模块化、代码提交到 Git。
