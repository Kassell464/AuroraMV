"""深色主题（阶段 10：让应用程序有高级感）。

通过 QSS 定义深色主题、卡片、按钮、滑杆等样式。
"""

DARK_QSS = """
/* 注意：不给通用 QWidget 设背景色——QOpenGLWidget 不支持样式表背景，
   会导致预览区渲染内容被纯色背景覆盖（Qt 已知限制）。 */
QWidget {
    color: #d5d7e0;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}
QMainWindow, QDialog {
    background-color: #101014;
}

/* 控制面板 */
QFrame#controlPanel {
    background-color: #16161d;
    border-right: 1px solid #23232c;
}
QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }

/* 标题与文字 */
QLabel[appTitle="true"] {
    font-size: 22px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: 1px;
}
QLabel[muted="true"] { color: #70737f; font-size: 12px; }
QLabel[sectionLabel="true"] {
    color: #8b8e9c;
    font-size: 12px;
    font-weight: 600;
    margin-top: 6px;
}
QLabel[cardTitle="true"] { color: #e8eaf2; font-size: 13px; font-weight: 600; }
QLabel[cardSub="true"] { color: #70737f; font-size: 11px; }

/* 卡片（可视化选择器） */
QFrame[card="true"] {
    background-color: #1b1c25;
    border: 1px solid #26272f;
    border-radius: 10px;
}
QFrame[card="true"]:hover { border-color: #3f81ff; background-color: #20222e; }
QFrame[card="true"][selected="true"] {
    border-color: #2f6fed;
    background-color: #22293f;
}

/* 按钮 */
QPushButton {
    background-color: #1f2029;
    border: 1px solid #2c2e3a;
    border-radius: 8px;
    padding: 8px 14px;
    color: #d5d7e0;
}
QPushButton:hover { background-color: #282a36; border-color: #3a3d4d; }
QPushButton:pressed { background-color: #1a1b23; }
QPushButton#accent {
    background-color: #2f6fed;
    border: none;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#accent:hover { background-color: #3f7dff; }
QPushButton#accent:pressed { background-color: #275fc8; }
QPushButton#accent[pulse="true"] { background-color: #4a8aff; }
QPushButton#accent:disabled { background-color: #232530; color: #6d7080; }

/* 输入框与下拉 */
QLineEdit {
    background-color: #1b1c25;
    border: 1px solid #2c2e3a;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e8eaf2;
}
QLineEdit:focus { border-color: #2f6fed; }
QComboBox {
    background-color: #1f2029;
    border: 1px solid #2c2e3a;
    border-radius: 6px;
    padding: 6px 10px;
}
QComboBox:hover { border-color: #3a3d4d; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background-color: #1f2029;
    border: 1px solid #2c2e3a;
    selection-background-color: #2f6fed;
    color: #d5d7e0;
}

/* 滑杆 */
QSlider::groove:horizontal {
    height: 4px;
    background: #2c2e3a;
    border-radius: 2px;
}
QSlider::sub-page:horizontal { background: #2f6fed; border-radius: 2px; }
QSlider::handle:horizontal {
    width: 14px;
    height: 14px;
    margin: -5px 0;
    background: #7fb2ff;
    border-radius: 7px;
}
QSlider::handle:horizontal:hover { background: #a5c9ff; }

/* 进度条 */
QProgressBar {
    background: #1f2029;
    border: 1px solid #2c2e3a;
    border-radius: 6px;
    height: 16px;
    text-align: center;
    color: #d5d7e0;
    font-size: 11px;
}
QProgressBar::chunk { background: #2f6fed; border-radius: 5px; }

/* 播放底栏 */
QFrame#playerBar {
    background-color: #16161d;
    border-top: 1px solid #23232c;
}
QLabel[barTitle="true"] {
    font-size: 14px;
    font-weight: 600;
    color: #e8eaf2;
}
QPushButton:checked {
    background-color: #232c45;
    border-color: #2f6fed;
    color: #ffffff;
}
"""
