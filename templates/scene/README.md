# 场景预设（templates/scene）

场景预设 = 一个完整视觉组合（规格 33 节：背景 + 歌词模板 + 效果），不含时间；
运行期由 `scenes_from_presets` 按曲目时长均分生成带时间的场景。

背景通过 `"background": {"template": "<名称>"}` 引用
[`../background`](../background) 目录下的背景模板，也可以内联定义
`{"type": ..., "params": ...}`（内联键覆盖模板键）。

## 六套系统预设包

| # | 预设 | 背景模板 | 歌词模板 | 效果 | 概念灵感 |
|---|------|----------|----------|------|----------|
| 1 | `cinema` | cinema（星云图片 + 慢镜头推进 + 暖色） | cinema | — | 电影镜头 |
| 2 | `aurora` | aurora（紫色旋臂银河，慢旋高星密度） | minimal | particle | 粒子舞台 |
| 3 | `cyberpunk` | cyberpunk（品红霓虹网格，快速流动） | neon | flash、beat_shake | 赛博朋克 |
| 4 | `stage` | stage（青色霓虹网格） | neon | beat_shake、flash | 歌词舞台 |
| 5 | `synthwave` | synthwave（橙红霓虹网格，慢速） | neon | flash | 合成波 |
| 6 | `dj` | dj（亮青波形） | minimal | beat_shake、flash、particle | DJ 专属模式 |

所有背景/歌词/效果参数均可调节：改 `templates/background/*.json`、
`templates/lyrics/*.json`、`templates/effects/*.json` 中的 `params` 即可。

## 灵感说明

预设的概念与气质参考了开源项目
[Mineradio（XxHuberrr/Mineradio）](https://github.com/XxHuberrr/Mineradio) 的
「电影镜头视觉」「粒子舞台」「歌词舞台」「DJ/播客专属视觉模式」等方向。

**仅借鉴概念方向**：本项目的着色器、预设 JSON 与素材均为原创实现（MIT 许可），
未复制 Mineradio 的任何代码或素材（Mineradio 为 GPL-3.0，其 Logo、名称与界面
视觉设计归原作者所有）。
