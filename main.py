"""AuroraMV 程序入口。

阶段 1（应用程序骨架）：启动主窗口，暂不包含任何渲染逻辑。
"""

import sys

from PySide6.QtWidgets import QApplication

from app.application import ApplicationController


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("AuroraMV")

    controller = ApplicationController()
    controller.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
