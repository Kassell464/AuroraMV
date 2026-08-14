# 场景预设（templates/scene）

场景预设 = 一个完整视觉组合（规格 33 节：背景 + 歌词模板 + 效果），不含时间；
运行期由 `scenes_from_presets` 按曲目时长均分生成带时间的场景。

## 预设列表

| 预设 | 背景 | 歌词模板（阶段 6） | 效果（阶段 7） | 概念灵感 |
|------|------|-------------------|---------------|----------|
| `cinema` | 星云图片 + 慢速镜头推进 | cinema | — | 电影镜头 |
| `particles` | 银河（粒子/星空，低频加速） | minimal | — | 粒子舞台 |
| `stage` | 霓虹网格（节拍闪光） | neon | beat_flash | 歌词舞台 |
| `dj` | 音频波形（低频增亮） | minimal | beat_shake、flash | DJ 专属模式 |

## 灵感说明

预设的概念与气质参考了开源项目
[Mineradio（XxHuberrr/Mineradio）](https://github.com/XxHuberrr/Mineradio) 的
「电影镜头视觉」「粒子舞台」「歌词舞台」「DJ/播客专属视觉模式」等方向。

**仅借鉴概念方向**：本项目的着色器、预设 JSON 与素材均为原创实现（MIT 许可），
未复制 Mineradio 的任何代码或素材（Mineradio 为 GPL-3.0，其 Logo、名称与界面
视觉设计归原作者所有）。
