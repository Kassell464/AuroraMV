AuroraMV V0.1 工程规格说明

版本：0.1
许可协议：MIT
平台：Windows 10+
语言：Python 3.12

第一部分 — 产品定义与系统架构
1. 项目概述
项目名称

AuroraMV

项目描述

AuroraMV 是一个开源的、用于音乐可视化和音乐视频生成的应用程序。

AuroraMV 的用途是：

将音乐转化为视觉上令人印象深刻的视频，并带有动态歌词、音频响应效果和可自定义的视觉主题。

AuroraMV 专注于自动视觉生成，而非传统的基于时间轴的视频编辑。

它结合了：

音乐可视化器
动态歌词渲染器
视觉效果引擎
基于场景的合成系统
视频导出器
2. 产品定位

AuroraMV 不是：

Premiere 的替代品
After Effects 的替代品
传统视频编辑器
AI 视频生成器

AuroraMV 是：

一个由音乐驱动的视觉引擎
一个快速制作 MV 的工具
一个基于模板的创意平台
3. 目标用户

主要用户：

音乐创作者

例如：

AI 音乐创作者
独立音乐人
翻唱创作者
视频创作者

例如：

YouTube 创作者
Bilibili 创作者
TikTok 创作者
普通用户

想要如下功能的用户：

“把我最喜欢的歌变成酷炫的视频。”

4. 核心用户体验

主要工作流程：

导入音乐

↓

选择视觉主题

↓

导入歌词（可选）

↓

选择背景

↓

实时预览

↓

调整参数

↓

导出视频


用户应该能够在几分钟内制作出一支音乐视频。

5. 产品设计理念
原则 1

音乐驱动视觉。

系统应自动响应：

节拍
音量
低频
节奏
原则 2

模板优先。

用户不应手动制作所有动画。

而是：

选择：

霓虹风格

银河背景

赛博歌词


并获得完整的视觉体验。

原则 3

实时预览。

用户必须看到：

“所见即所导出。”

预览渲染器与导出渲染器必须共用同一条渲染管线。

6. V0.1 功能范围
必备功能
音频系统

支持：

mp3
wav
flac

功能：

播放
波形分析
BPM 检测
节拍检测
歌词系统

支持：

输入：

LRC 文件
手动文本

可选：

基于 Whisper 的识别接口。

重要：

AI 歌词识别不得阻塞正常的工作流程。

背景系统

V0.1 支持：

用户背景图片

格式：

jpg
png
webp

特性：

缩放
移动
模糊
颜色调整
内置动态背景

例如：

银河粒子
音频波形
霓虹网格
流体着色器
场景系统

AuroraMV 在 V0.1 中不使用复杂的时间轴。

而是：

使用场景合成。

示例：

场景 1

0:00 - 0:30

背景：
image01.jpg

主题：
银河

歌词：
霓虹




场景 2

0:30 - 1:00

背景：
image02.jpg

主题：
赛博朋克

动态歌词

支持：

多种样式
动画
音频响应

示例：

文本：

HELLO WORLD


动画：

入场：
淡入


节拍：

缩放


待机：

发光

导出

输出：

MP4

编解码器：

H264

选项：

分辨率：

360p
480p
720p
1080p
1440p

FPS：

24
30
60

宽高比：

16:9
9:16
1:1

码率：

自动 / 手动

7. 技术栈
编程语言

Python 3.12

理由：

开发速度快
AI 生态
音频处理生态
适合开源
GUI 框架

PySide6

职责：

应用程序窗口
控件
面板
用户交互

PySide6 不得包含渲染逻辑。

渲染引擎

ModernGL

职责：

GPU 渲染
着色器效果
粒子
视觉合成

目标：

RTX 3060

音频处理

库：

librosa

numpy

soundfile


职责：

波形
FFT
BPM
节拍分析
视频编码

FFmpeg

职责：

帧编码
mp4 生成
8. 高层架构
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

9. 架构规则
规则 1

UI 与渲染器必须分离。

不好：

按钮
 |
draw()

好：

按钮

↓

修改渲染器状态

↓

渲染器更新帧

规则 2

所有视觉效果必须模块化。

示例：

不好：

if neon:
    draw neon

if galaxy:
    draw galaxy


好：

EffectManager

    |

    NeonEffect

    GalaxyEffect

规则 3

预览与导出共用渲染器。

架构：

Renderer

   |

   |------ 预览窗口

   |

   |------ 帧导出

10. 项目目录结构
AuroraMV/


main.py


app/

    application.py



ui/

    main_window.py

    preview_widget.py

    panels/



core/


    audio/

        analyzer.py

        beat_detector.py



    renderer/

        engine.py

        scene.py

        camera.py



    lyrics/

        parser.py

        provider.py



    effects/

        manager.py

        particle.py



    templates/

        loader.py



    project/

        project.py

        serializer.py



export/

    ffmpeg.py



templates/


assets/


tests/

11. 开发环境

必需：

Python >=3.12

Git

FFmpeg

现代 GPU


推荐：

RTX 3060 或更高

Windows 10+

第一部分结束

第二部分 — 核心模块设计
12. 核心架构概述

AuroraMV 的核心不是 UI，而是一个实时视觉渲染系统。

核心数据流：

音频文件
    |
    v
音频引擎
    |
    v
音频状态
    |
    |
    +----------------+
                     |
                     v
              场景管理器
                     |
                     v
              渲染器引擎
                     |
      --------------------------------
      |              |               |
      v              v               v

 背景       歌词       效果

 渲染器     渲染器     渲染器


                     |
                     v

              OpenGL 帧

                     |
          ---------------------

          预览       导出

13. 核心模块职责

核心模块：

core/

├── audio/
│
├── renderer/
│
├── lyrics/
│
├── effects/
│
├── templates/
│
└── project/

14. 音频引擎设计
14.1 职责

Audio Engine负责：

音频加载
音频播放同步
音频分析
提供实时Audio State
14.2 音频管线
song.mp3

    |

解码器

    |

PCM 数据

    |

分析器

    |

音频状态

    |

渲染器

15. 音频状态系统

Renderer不应该直接读取音频。

Renderer只读取：

AudioState。

定义：

class AudioState:

    timestamp: float

    volume: float

    bass: float

    mid: float

    treble: float

    beat: bool

    bpm: float


示例：

AudioState(
    timestamp=32.5,

    volume=0.72,

    bass=0.85,

    mid=0.43,

    treble=0.31,

    beat=True,

    bpm=120
)

16. 音频响应系统

所有视觉效果通过 AudioState 响应音乐。

例如：

粒子效果

输入：

bass = 0.8

计算：

particle_count =
base_count + bass * multiplier

摄像机震动

输入：

beat=True

输出：

camera.offset = random()

歌词缩放

输入：

volume

输出：

font_size =
base_size + volume * scale

17. 渲染器引擎设计

Renderer是AuroraMV核心。

职责：

生成每一帧画面。

17.1 渲染器接口
class Renderer:


    def load_scene(self, scene):
        pass


    def update(
        self,
        time,
        audio_state
    ):
        pass


    def render(self):
        pass

17.2 帧渲染管线

每一帧：

例如：

time = 45.23s


Renderer流程：

1. 获取当前场景


2. 更新音频状态


3. 渲染背景


4. 渲染效果


5. 渲染歌词


6. 应用后期处理


7. 输出帧

18. 渲染器图层系统

Renderer采用Layer概念。

类似游戏引擎。

图层：

图层 0：

背景


图层 1：

粒子


图层 2：

效果


图层 3：

歌词


图层 4：

UI 叠加层


渲染顺序：

背景

↓

粒子

↓

效果

↓

歌词

↓

后期处理

19. 背景渲染器
职责

负责：

图片背景
Shader背景

接口：

class BackgroundRenderer:


    def load(source):
        pass


    def update(time):
        pass


    def render():
        pass

20. 图片背景系统

支持：

jpg

png

webp


效果：

缩放
1.0

↓

1.2


模拟镜头推进。

平移

移动：

左

右

上

下

模糊

使用：

shader。

21. 动态背景系统

V0.1内置：

银河

特点：

粒子
星空
波形

特点：

音频波形
霓虹网格

特点：

科幻网格
流体

特点：

Shader流体

动态背景必须：

支持 AudioState。

例如：

低频增强

↓

粒子速度加快

22. 歌词引擎设计

Lyrics Engine负责：

解析歌词
时间同步
动画
23. 歌词提供器架构

统一接口：

class LyricsProvider:


    def load():

        pass


    def get_current_line(time):

        pass


实现：

LyricsProvider

        |

-----------------------

LRCProvider

ManualProvider

WhisperProvider

24. LRC 解析器

输入：

song.lrc


格式：

[00:12.50]

Hello World


输出：

LyricLine(

text="Hello World",

start=12.5,

end=16.0

)

25. 歌词动画引擎

歌词不是文本。

而是：

动画对象。

定义：

class LyricObject:


    text:str


    position:


    opacity:


    scale:


    animation_state:



生命周期：

开始之前

↓

入场动画

↓

激活

↓

退场动画

26. 歌词模板系统

目录：

templates/

lyrics/

    neon.json

    cinema.json

    minimal.json


模板：

{
"name":"Neon",

"font":
"Orbitron",

"color":
"#ffffff",

"animation":

{

"enter":"fade",

"idle":"glow",

"beat":"scale"

}

}

27. 效果引擎

Effect负责：

所有非核心视觉效果。

例如：

闪光
震动
故障
粒子

接口：

class Effect:


    def update(
        self,
        audio_state
    ):
        pass


    def render():

        pass

28. 效果管理器

负责管理多个Effect。

class EffectManager:


    effects=[]


    def update():

        for e in effects:

            e.update()


    def render():

        for e in effects:

            e.render()

29. 场景系统

AuroraMV V0.1 不使用传统Timeline。

使用Scene。

Scene定义：

一个时间范围内的完整视觉状态。

示例：

场景 1

0:00 - 0:30


背景：

galaxy.jpg


歌词：

neon


效果：

beat_shake


30. 场景数据模型

Python：

class Scene:


    id:int


    start_time:float


    end_time:float


    background:


    lyric_template:


    effects:


31. 场景管理器

负责：

根据当前时间返回Scene。

接口：

class SceneManager:


    scenes=[]


    def get_scene(time):

        pass

32. 模板系统架构

Template系统是未来社区生态基础。

目录：

templates/


lyrics/

background/

effects/

scene/

33. 模板类型
歌词模板

控制：

字体
动画
颜色
背景模板

控制：

Shader
参数
效果模板

控制：

特效
场景模板

完整组合：

赛博朋克 MV

=

赛博背景

+

霓虹歌词

+

故障效果

34. 模板加载

接口：

class TemplateLoader:


    def load(path):

        pass


    def validate():

        pass

35. 项目系统

项目文件：

.amv


实际：

zip。

结构：

project.amv


project.json


assets/


audio/


backgrounds/


lyrics/


cache/


36. 项目 JSON 架构

示例：

{

"version":"0.1",


"project":

{

"name":"My MV",

"canvas":

{

"width":1920,

"height":1080

},


"fps":30

},



"audio":

{

"path":"assets/audio/song.mp3"

},



"scenes":

[

{

"id":1,


"start":0,


"end":30,


"background":

{

"type":"image",

"path":"assets/bg/a.jpg"

},


"lyrics":

{

"template":"neon"

},


"effects":

[

"beat_shake"

]


}

]

}

37. 导出管线

Export 不重新实现Renderer。

流程：

项目

↓

渲染器

↓

帧缓冲

↓

FFmpeg

↓

MP4


接口：

class Exporter:


    def export(

        project,

        settings

    ):

        pass

38. 预览管线

实时预览：

渲染器

↓

OpenGL 纹理

↓

PySide6 控件

39. 类关系总览
应用程序


 |

项目管理器
 |

场景管理器
 |

渲染器


 |

---------------------------------

 |              |              |

背景       歌词       效果


渲染器     引擎       引擎


 |

OpenGL

第二部分结束

第三部分 — 开发路线图与 AI 智能体编码规则
40. 开发策略

AuroraMV 是一个复杂的图形应用程序。

最大的风险不是写代码。

最大的风险是：

在架构稳定之前，就让 AI 生成大量无结构的代码。

因此，开发必须遵循增量式里程碑。

每个里程碑必须满足：

应用程序能够运行。
已有功能不能被破坏。
架构保持模块化。
代码必须提交到 Git。
41. 开发理念
先构建引擎。

错误的顺序：

UI
↓
按钮
↓
设置
↓
导出
↓
尝试加入渲染

这会造出一个没有核心的虚假产品。

正确的顺序：

渲染器核心

↓

音频响应系统

↓

场景系统

↓

歌词系统

↓

UI

↓

导出

42. 两周开发路线图
阶段 0 — 环境搭建

时长：

半天

目标：

创建干净的开发环境。

任务：

安装：

Python 3.12

Git

FFmpeg

Visual Studio Build Tools


创建：

venv
requirements.txt
.gitignore

初始依赖：

PySide6

moderngl

pygame

numpy

librosa

soundfile

阶段 1 — 应用程序骨架

时长：

第 1 天

目标：

程序成功启动。

实现：

AuroraMV/
|
main.py


创建：

主窗口

预览控件

应用控制器


预期结果：

出现一个窗口：

AuroraMV

[预览区域]

[控件]

阶段 2 — OpenGL 渲染器核心

时长：

第 2-3 天

目标：

创建视觉引擎基础。

实现：

Renderer 类
class Renderer:


    def initialize():

        pass


    def update():

        pass


    def render():

        pass


创建：

OpenGL 上下文

着色器加载器

纹理管理器

摄像机


演示：

渲染：

背景颜色
图片纹理
简单动画
阶段 3 — 音频引擎

时长：

第 4 天

目标：

将音乐与视觉连接起来。

实现：

音频加载：

mp3/wav

音频分析器：

音量

低频

节拍


创建：

AudioState

演示：

音乐播放时：

↓

圆形大小随低频变化。

阶段 4 — 背景系统

时长：

第 5 天

目标：

创建漂亮的视觉背景。

实现：

图片背景

特性：

加载图片
缩放
平移
着色器背景

实现：

前三个：

银河
波形
霓虹网格

演示：

音乐播放时：

↓

背景产生响应。

阶段 5 — 场景系统

时长：

第 6 天

目标：

创建 AuroraMV 项目逻辑。

实现：

场景：

Scene(
start,
end,
background,
effects
)


场景管理器：

get_current_scene(time)


演示：

在 30 秒时：

背景自动切换。

阶段 6 — 歌词引擎

时长：

第 7-8 天

目标：

动态歌词。

实现：

LRC 解析器：

song.lrc

↓

LyricLine[]


创建：

歌词渲染器

支持：

文本
位置
动画

首批模板：

霓虹
影院
极简

演示：

音乐：

00:10 Hello

00:15 World


显示带动画的歌词。

阶段 7 — 效果系统

时长：

第 9 天

目标：

增加视觉冲击力。

实现：

EffectManager

效果：

节拍震动

输入：

beat=true

输出：

摄像机运动

闪光

输出：

亮度闪烁

粒子

输出：

粒子

阶段 8 — 模板系统

时长：

第 10 天

目标：

让视觉风格可复用。

实现：

TemplateLoader

支持：

.json 模板

示例：

templates/

lyrics/neon.json

background/galaxy.json

effects/shake.json

阶段 9 — 导出系统

时长：

第 11-12 天

目标：

生成 MP4。

管线：

渲染器

↓

帧捕获

↓

FFmpeg

↓

MP4


支持：

分辨率：

360p
480p
720p
1080p
1440p

FPS：

24
30
60
阶段 10 — UI 打磨

时长：

第 13 天

目标：

让应用程序有高级感。

实现：

深色主题
动画
卡片
可视化选择器

灵感来源：

Mineradio。

阶段 11 — 开源准备

时长：

第 14 天

准备：

仓库：

AuroraMV

README.md

LICENSE

docs

examples

templates


创建：

演示视频。
截图。
发布说明。

43. AI 编码智能体规则

这些规则适用于 Claude 和 Codex。

规则 1

不要一次性生成整个应用程序。

禁止：

创建完整的 AuroraMV 应用程序。


允许：

只实现渲染器模块。
确保它能运行。
不要修改其他模块。

规则 2

在编写代码之前：

说明：

哪些文件将被修改。
为什么需要修改它们。
架构会受到什么影响。

规则 3

保持模块独立。

禁止：

ui/main_window.py

直接调用 OpenGL 函数


正确做法：

UI

↓

Renderer API

↓

OpenGL

规则 4

不要引入不必要的依赖。

在添加库之前：

说明：

为什么需要
替代方案
维护状态

规则 5

每个功能都需要：

代码
最小化测试
文档

规则 6

不要重写能正常工作的模块。

优先：

小的增量式修改。

44. Claude 工作流

Claude 应该用于：

架构

示例：

设计渲染器架构。
先只输出设计。
不要写代码。
大型模块

示例：

实现完整的场景系统。
遵循 AuroraMV 架构。
只修改 core/project。
重构

示例：

审查当前架构。
找出耦合问题。
提出改进建议。

45. Codex 工作流

Codex 应该用于：

调试

示例：

OpenGL 预览是黑的。
分析这个错误。
小函数

示例：

实现 LRC 解析器。
不要修改渲染器。
代码审查

示例：

审查这个提交。
找出 bug。

46. Git 工作流

使用：

main

develop

feature/*
分支：

示例：

feature/audio-engine

feature/renderer

feature/lyrics

feature/export


提交格式：

feat:
add renderer initialization


fix:
solve shader loading issue


refactor:
cleanup scene manager

47. 测试策略

V0.1 不要求完整的自动化测试。

但每个模块都需要基本验证。

示例：

音频：

成功加载 mp3


渲染器：

成功绘制帧


歌词：

正确解析 lrc


导出：

生成可播放的 mp4

48. 性能目标

硬件目标：

RTX 3060

预览：

目标：

1080p
30 FPS

导出：

目标：

1080p
30 FPS

优化优先级：

避免不必要的 CPU 渲染。
使用 GPU 着色器。
缓存资源。

49. 未来路线图
V0.2

功能：

视频背景

支持：

mp4

webm

mov

更好的 AI 歌词

添加：

faster-whisper

更多模板

社区包。
V0.3
时间轴编辑器

添加：

拖动场景
关键帧
转场
插件系统

支持：

Python 插件

Shader 插件

V1.0

AuroraMV 成为一个完整的开源生态。

功能：

模板市场
社区分享
插件 API
跨平台构建
50. 最终开发目标

首个版本不需要与专业视频编辑器竞争。

AuroraMV V0.1 的目标是：

用户能够导入一首歌、选择一种视觉风格、实时预览漂亮的音乐可视化效果，并导出一支高质量的音乐视频。

如果能做到这一点：

AuroraMV 就已经拥有了独特的身份。

AuroraMV V0.1 工程规格说明 全文结束
