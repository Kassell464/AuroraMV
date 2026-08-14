"""应用控制器（ApplicationController）。

职责：创建并协调主窗口。此模块不含渲染逻辑，
后续阶段由它连接音频、场景与渲染器引擎。
"""

from ui.main_window import MainWindow


class ApplicationController:
    def __init__(self) -> None:
        self.window = MainWindow()

    def show(self) -> None:
        self.window.show()
