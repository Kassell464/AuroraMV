AuroraMV V0.1 Engineering Specification

Version: 0.1
License: MIT
Platform: Windows 10+
Language: Python 3.12

Part 1 — Product Definition & System Architecture
1. Project Overview
Project Name

AuroraMV

Project Description

AuroraMV is an open-source music visualization and music video generation application.

The purpose of AuroraMV is:

Transform music into visually impressive videos with dynamic lyrics, audio-reactive effects, and customizable visual themes.

AuroraMV focuses on automatic visual generation rather than traditional timeline-based video editing.

It combines:

Music visualizer
Dynamic lyric renderer
Visual effects engine
Scene-based composition system
Video exporter
2. Product Positioning

AuroraMV is NOT:

A replacement for Premiere
A replacement for After Effects
A traditional video editor
An AI video generator

AuroraMV IS:

A music-driven visual engine
A fast MV creation tool
A template-based creative platform
3. Target Users

Primary users:

Music creators

Examples:

AI music creators
Independent musicians
Cover creators
Video creators

Examples:

YouTube creators
Bilibili creators
TikTok creators
Ordinary users

Users who want:

"Turn my favorite song into a cool video."

4. Core User Experience

The main workflow:

Import Music

↓

Select Visual Theme

↓

Import Lyrics(optional)

↓

Select Background

↓

Preview in Real Time

↓

Adjust Parameters

↓

Export Video


The user should be able to create a music video within minutes.

5. Product Design Philosophy
Principle 1

Music drives visuals.

The system should automatically react to:

beat
volume
bass
rhythm
Principle 2

Template first.

Users should not manually animate everything.

Instead:

Choose:

Neon Style

Galaxy Background

Cyber Lyrics


and get a complete visual experience.

Principle 3

Realtime preview.

The user must see:

"What you see is what you export."

Preview Renderer and Export Renderer must share the same rendering pipeline.

6. V0.1 Feature Scope
Must Have Features
Audio System

Support:

mp3
wav
flac

Functions:

playback
waveform analysis
BPM detection
beat detection
Lyrics System

Support:

Input:

LRC file
manual text

Optional:

Whisper based recognition interface.

Important:

AI lyrics recognition must not block normal workflow.

Background System

V0.1 supports:

User Background Images

Formats:

jpg
png
webp

Features:

scale
move
blur
color adjustment
Built-in Dynamic Backgrounds

Examples:

Galaxy particles
Audio waveform
Neon grid
Fluid shader
Scene System

AuroraMV does not use a complex timeline in V0.1.

Instead:

Use Scene composition.

Example:

Scene 1

0:00 - 0:30

Background:
image01.jpg

Theme:
Galaxy

Lyrics:
Neon



Scene 2

0:30 - 1:00

Background:
image02.jpg

Theme:
Cyberpunk

Dynamic Lyrics

Support:

multiple styles
animation
audio reaction

Example:

Text:

HELLO WORLD


Animation:

Enter:
Fade


Beat:

Scale


Idle:

Glow

Export

Output:

MP4

Codec:

H264

Options:

Resolution:

360p
480p
720p
1080p
1440p

FPS:

24
30
60

Aspect Ratio:

16:9
9:16
1:1

Bitrate:

Auto / Manual

7. Technology Stack
Programming Language

Python 3.12

Reason:

fast development
AI ecosystem
audio processing ecosystem
suitable for open source
GUI Framework

PySide6

Responsibilities:

application window
controls
panels
user interaction

PySide6 must NOT contain rendering logic.

Rendering Engine

ModernGL

Responsibilities:

GPU rendering
shader effects
particles
visual composition

Target:

RTX 3060

Audio Processing

Libraries:

librosa

numpy

soundfile


Responsibilities:

waveform
FFT
BPM
beat analysis
Video Encoding

FFmpeg

Responsibilities:

frame encoding
mp4 generation
8. High Level Architecture
                    AuroraMV


                       |

                 Application Core


                       |

 ------------------------------------------------

 |                    |                         |

UI Layer        Project System          Template System


                       |

                 Renderer Engine


                       |

 ------------------------------------------------


Background     Lyrics       Effects      Camera


Renderer       Renderer     Renderer     System


                       |

                  OpenGL Pipeline


                       |

             Preview / Export


                       |

                    FFmpeg

9. Architecture Rules
Rule 1

UI and Renderer must be separated.

Bad:

Button
 |
draw()

Good:

Button

↓

Change Renderer State

↓

Renderer Updates Frame

Rule 2

All visual effects must be modular.

Example:

Bad:

if neon:
    draw neon

if galaxy:
    draw galaxy


Good:

EffectManager

    |

    NeonEffect

    GalaxyEffect

Rule 3

Preview and Export share renderer.

Architecture:

Renderer

   |

   |------ Preview Window

   |

   |------ Frame Export

10. Project Directory Structure
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


11. Development Environment

Required:

Python >=3.12

Git

FFmpeg

Modern GPU


Recommended:

RTX 3060 or above

Windows 10+

End of Part 1

Part 2 — Core Module Design
12. Core Architecture Overview

AuroraMV 的核心不是 UI，而是一个实时视觉渲染系统。

核心数据流：

Audio File
    |
    v
Audio Engine
    |
    v
Audio State
    |
    |
    +----------------+
                     |
                     v
              Scene Manager
                     |
                     v
              Renderer Engine
                     |
      --------------------------------
      |              |               |
      v              v               v

 Background     Lyrics        Effects

 Renderer       Renderer      Renderer


                     |
                     v

              OpenGL Frame

                     |
          ---------------------

          Preview       Export

13. Core Module Responsibilities

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

14. Audio Engine Design
14.1 Responsibility

Audio Engine负责：

音频加载
音频播放同步
音频分析
提供实时Audio State
14.2 Audio Pipeline
song.mp3

    |

Decoder

    |

PCM Data

    |

Analyzer

    |

Audio State

    |

Renderer

15. Audio State System

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

16. Audio Reactive System

所有视觉效果通过 AudioState 响应音乐。

例如：

Particle Effect

输入：

bass = 0.8

计算：

particle_count =
base_count + bass * multiplier

Camera Shake

输入：

beat=True

输出：

camera.offset = random()

Lyrics Scale

输入：

volume

输出：

font_size =
base_size + volume * scale

17. Renderer Engine Design

Renderer是AuroraMV核心。

职责：

生成每一帧画面。

17.1 Renderer Interface
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

17.2 Frame Rendering Pipeline

每一帧：

例如：

time = 45.23s


Renderer流程：

1. Get Current Scene


2. Update Audio State


3. Render Background


4. Render Effects


5. Render Lyrics


6. Apply Post Processing


7. Output Frame

18. Renderer Layer System

Renderer采用Layer概念。

类似游戏引擎。

Layers:

Layer 0:

Background


Layer 1:

Particles


Layer 2:

Effects


Layer 3:

Lyrics


Layer 4:

UI Overlay


渲染顺序：

Background

↓

Particles

↓

Effects

↓

Lyrics

↓

Post Processing

19. Background Renderer
Responsibility

负责：

图片背景
Shader背景

Interface:

class BackgroundRenderer:


    def load(source):
        pass


    def update(time):
        pass


    def render():
        pass

20. Image Background System

支持：

jpg

png

webp


效果：

Scale
1.0

↓

1.2


模拟镜头推进。

Pan

移动：

left

right

up

down

Blur

使用：

shader。

21. Dynamic Background System

V0.1内置：

Galaxy

特点：

粒子
星空
Waveform

特点：

音频波形
Neon Grid

特点：

科幻网格
Fluid

特点：

Shader流体

动态背景必须：

支持 AudioState。

例如：

bass increase

↓

particle speed increase

22. Lyrics Engine Design

Lyrics Engine负责：

解析歌词
时间同步
动画
23. Lyrics Provider Architecture

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

24. LRC Parser

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

25. Lyrics Animation Engine

歌词不是文本。

而是：

Animated Object。

定义：

class LyricObject:


    text:str


    position:


    opacity:


    scale:


    animation_state:



生命周期：

Before Start

↓

Enter Animation

↓

Active

↓

Exit Animation

26. Lyric Template System

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

27. Effect Engine

Effect负责：

所有非核心视觉效果。

例如：

flash
shake
glitch
particles

Interface:

class Effect:


    def update(
        self,
        audio_state
    ):
        pass


    def render():

        pass

28. Effect Manager

负责管理多个Effect。

class EffectManager:


    effects=[]


    def update():

        for e in effects:

            e.update()


    def render():

        for e in effects:

            e.render()

29. Scene System

AuroraMV V0.1 不使用传统Timeline。

使用Scene。

Scene定义：

一个时间范围内的完整视觉状态。

Example:

Scene 1

0:00 - 0:30


Background:

galaxy.jpg


Lyrics:

neon


Effects:

beat_shake


30. Scene Data Model

Python:

class Scene:


    id:int


    start_time:float


    end_time:float


    background:


    lyric_template:


    effects:


31. Scene Manager

负责：

根据当前时间返回Scene。

Interface:

class SceneManager:


    scenes=[]


    def get_scene(time):

        pass

32. Template System Architecture

Template系统是未来社区生态基础。

目录：

templates/


lyrics/

background/

effects/

scene/

33. Template Types
Lyric Template

控制：

字体
动画
颜色
Background Template

控制：

Shader
参数
Effect Template

控制：

特效
Scene Template

完整组合：

Cyberpunk MV

=

Cyber background

+

Neon lyrics

+

Glitch effect

34. Template Loading

Interface:

class TemplateLoader:


    def load(path):

        pass


    def validate():

        pass

35. Project System

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


36. Project JSON Schema

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

37. Export Pipeline

Export 不重新实现Renderer。

流程：

Project

↓

Renderer

↓

Frame Buffer

↓

FFmpeg

↓

MP4


Interface:

class Exporter:


    def export(

        project,

        settings

    ):

        pass

38. Preview Pipeline

实时预览：

Renderer

↓

OpenGL Texture

↓

PySide6 Widget

39. Class Relationship Overview
Application


 |

ProjectManager

 |

SceneManager

 |

Renderer


 |
---------------------------------

 |              |              |

Background   Lyrics        Effects


Renderer     Engine        Engine


 |

OpenGL

End of Part 2

Part 3 — Development Roadmap & AI Agent Coding Rules
40. Development Strategy

AuroraMV is a complex graphics application.

The biggest risk is not writing code.

The biggest risk is:

Letting AI generate a large amount of unstructured code before the architecture is stable.

Therefore development must follow incremental milestones.

Each milestone must satisfy:

The application can run.
Existing functions cannot be broken.
The architecture remains modular.
Code must be committed to Git.
41. Development Philosophy
Build the engine first.

Incorrect order:

UI
↓
Buttons
↓
Settings
↓
Export
↓
Try to add rendering

This creates a fake product with no core.

Correct order:

Renderer Core

↓

Audio Reactive System

↓

Scene System

↓

Lyrics System

↓

UI

↓

Export

42. Two Week Development Roadmap
Phase 0 — Environment Setup

Duration:

Half day

Goal:

Create a clean development environment.

Tasks:

Install:

Python 3.12

Git

FFmpeg

Visual Studio Build Tools


Create:

venv
requirements.txt
.gitignore

Initial dependencies:

PySide6

moderngl

pygame

numpy

librosa

soundfile

Phase 1 — Application Skeleton

Duration:

Day 1

Goal:

The program launches successfully.

Implement:

AuroraMV/
|
main.py


Create:

MainWindow

PreviewWidget

ApplicationController


Expected result:

A window appears:

AuroraMV

[Preview Area]

[Controls]

Phase 2 — OpenGL Renderer Core

Duration:

Day 2-3

Goal:

Create the visual engine foundation.

Implement:

Renderer class
class Renderer:


    def initialize():

        pass


    def update():

        pass


    def render():

        pass


Create:

OpenGL Context

Shader Loader

Texture Manager

Camera


Demo:

Render:

background color
image texture
simple animation
Phase 3 — Audio Engine

Duration:

Day 4

Goal:

Connect music with visuals.

Implement:

Audio loading:

mp3/wav

Audio analyzer:

volume

bass

beat


Create:

AudioState

Demo:

Music playing:

↓

Circle size changes with bass.

Phase 4 — Background System

Duration:

Day 5

Goal:

Create beautiful visual background.

Implement:

Image Background

Features:

load image
scale
pan
Shader Background

Implement:

First three:

Galaxy
Waveform
Neon Grid

Demo:

Music playing:

↓

Background reacts.

Phase 5 — Scene System

Duration:

Day 6

Goal:

Create AuroraMV project logic.

Implement:

Scene:

Scene(
start,
end,
background,
effects
)


SceneManager:

get_current_scene(time)


Demo:

At 30 seconds:

Background changes automatically.

Phase 6 — Lyrics Engine

Duration:

Day 7-8

Goal:

Dynamic lyrics.

Implement:

LRC Parser:

song.lrc

↓

LyricLine[]


Create:

Lyric Renderer

Support:

text
position
animation

First templates:

Neon
Cinema
Minimal

Demo:

Music:

00:10 Hello

00:15 World


shows animated lyrics.

Phase 7 — Effect System

Duration:

Day 9

Goal:

Add visual impact.

Implement:

EffectManager

Effects:

Beat Shake

Input:

beat=true

Output:

camera movement

Flash

Output:

brightness flash

Particle

Output:

particles

Phase 8 — Template System

Duration:

Day 10

Goal:

Make visual styles reusable.

Implement:

TemplateLoader

Support:

.json templates

Example:

templates/

lyrics/neon.json

background/galaxy.json

effects/shake.json

Phase 9 — Export System

Duration:

Day 11-12

Goal:

Generate MP4.

Pipeline:

Renderer

↓

Frame Capture

↓

FFmpeg

↓

MP4


Support:

Resolution:

360p
480p
720p
1080p
1440p

FPS:

24
30
60
Phase 10 — UI Polish

Duration:

Day 13

Goal:

Make the application feel premium.

Implement:

dark theme
animations
cards
visual selector

Inspired by:

Mineradio.

Phase 11 — Open Source Preparation

Duration:

Day 14

Prepare:

Repository:

AuroraMV

README.md

LICENSE

docs

examples

templates


Create:

Demo video.

Screenshot.

Release notes.

43. AI Coding Agent Rules

These rules apply to Claude and Codex.

Rule 1

Do not generate the entire application at once.

Forbidden:

Create complete AuroraMV application.


Allowed:

Implement Renderer module only.

Ensure it runs.

Do not modify other modules.

Rule 2

Before writing code:

Explain:

What files will change.
Why they need changing.
How the architecture is affected.
Rule 3

Keep modules independent.

Forbidden:

ui/main_window.py

directly calls OpenGL functions


Correct:

UI

↓

Renderer API

↓

OpenGL

Rule 4

Do not introduce unnecessary dependencies.

Before adding a library:

Explain:

Why needed
Alternative
Maintenance status
Rule 5

Every feature requires:

Code
Minimal test
Documentation
Rule 6

Do not rewrite working modules.

Prefer:

small incremental changes.

44. Claude Workflow

Claude should be used for:

Architecture

Example:

Design the Renderer architecture.

Only output design first.

Do not code.

Large modules

Example:

Implement the complete Scene system.

Follow AuroraMV architecture.

Only modify core/project.

Refactoring

Example:

Review current architecture.

Find coupling problems.

Suggest improvements.

45. Codex Workflow

Codex should be used for:

Debugging

Example:

OpenGL preview is black.

Analyze this error.

Small functions

Example:

Implement LRC parser.

Do not modify renderer.

Code review

Example:

Review this commit.

Find bugs.

46. Git Workflow

Use:

main

develop

feature/*

Branches:

Example:

feature/audio-engine

feature/renderer

feature/lyrics

feature/export


Commit format:

feat:
add renderer initialization


fix:
solve shader loading issue


refactor:
cleanup scene manager

47. Testing Strategy

V0.1 does not require full automated testing.

But every module needs basic validation.

Example:

Audio:

load mp3 successfully


Renderer:

draw frame successfully


Lyrics:

parse lrc correctly


Export:

generate playable mp4

48. Performance Targets

Hardware target:

RTX 3060

Preview:

Target:

1080p
30 FPS

Export:

Target:

1080p
30 FPS

Optimization priority:

Avoid unnecessary CPU rendering.

Use GPU shaders.

Cache resources.

49. Future Roadmap
V0.2

Features:

Video Background

Support:

mp4

webm

mov

Better AI Lyrics

Add:

faster-whisper

More Templates

Community packs.

V0.3
Timeline Editor

Add:

drag scenes
keyframes
transitions
Plugin System

Support:

Python plugins

Shader plugins

V1.0

AuroraMV becomes a complete open-source ecosystem.

Features:

Template marketplace
Community sharing
Plugin API
Cross-platform build
50. Final Development Goal

The first release does not need to compete with professional video editors.

The goal of AuroraMV V0.1 is:

A user can import a song, choose a visual style, preview a beautiful music visualization in real time, and export a high-quality music video.

If this works:

AuroraMV already has a unique identity.

End of AuroraMV V0.1 Engineering Specification