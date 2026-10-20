# -*- coding: utf-8 -*-
"""桌边备忘录 14 - 第二轮精修版（Windows 11 / PySide6）"""
import sys
import os
import json
import re
from pathlib import Path
from datetime import date, datetime, timedelta

from PySide6.QtCore import Qt, QTimer, QPoint, QSize, QObject, QEvent
from PySide6.QtGui import (
    QAction, QIcon, QPixmap, QPainter, QColor, QPen, QFont,
    QTextCharFormat, QTextListFormat, QTextCursor, QTextImageFormat, QBrush, QImage
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton,
    QTextEdit, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QToolButton, QSystemTrayIcon, QMenu, QMessageBox, QGraphicsDropShadowEffect,
    QColorDialog, QFontComboBox, QComboBox, QFileDialog, QFontDialog, QInputDialog,
    QCalendarWidget, QDialog
)

APP_NAME = "桌边备忘录"
APP_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "DeskMemo14"
DATA_FILE = APP_DIR / "notes.json"
CONFIG_FILE = APP_DIR / "config.json"

C = {
    "bg": "#F4F6F9",
    "surface": "#FFFFFF",
    "surface_soft": "#F8FAFC",
    "text": "#202938",
    "muted": "#8A94A5",
    "line": "#E6EAF0",
    "line_soft": "#EEF1F5",
    "blue": "#4B86F7",
    "blue_hover": "#3675EB",
    "blue_pale": "#EDF4FF",
    "green": "#159A67",
    "green_pale": "#ECF9F2",
    "amber": "#B7791F",
}

def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    APP_DIR.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    with open(temp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.flush()
        try:
            os.fsync(f.fileno())
        except OSError:
            pass
    os.replace(temp, path)

def key_for(d):
    return d.isoformat()

def date_text(d):
    if d == date.today():
        return f"今天  {d.month}月{d.day}日"
    if d == date.today() - timedelta(days=1):
        return f"昨天  {d.month}月{d.day}日"
    week = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][d.weekday()]
    return f"{d.month}月{d.day}日  {week}"

APP_STYLE = """
QMainWindow { background: transparent; }
QWidget#canvas { background: transparent; font-family: "Microsoft YaHei UI"; color: #202938; }
QFrame#windowSurface {
    background: #F8FAFC;
    border: 1px solid #E5E9F0;
    border-radius: 24px;
}
QFrame#header {
    background: #FFFFFF;
    border: 0;
    border-top-left-radius: 23px;
    border-top-right-radius: 23px;
}
QLabel#appTitle { color: #1F2937; font-size: 18pt; font-weight: 700; }
QLabel#appSubtitle { color: #8A94A5; font-size: 9pt; }
QFrame#divider { background: #E9EDF3; border: 0; max-height: 1px; min-height: 1px; }
QFrame#card {
    background: #FFFFFF;
    border: 1px solid #E5E9F0;
    border-radius: 17px;
}
QLabel#sectionTitle { color: #202938; font-size: 11pt; font-weight: 700; }
QLabel#muted { color: #8A94A5; font-size: 9pt; }
QLabel#status { color: #159A67; font-size: 9pt; font-weight: 600; }
QFrame#toolbar {
    background: #FFFFFF;
    border: 1px solid #E7EBF1;
    border-radius: 12px;
}
QToolButton {
    background: #F6F8FB;
    color: #455166;
    border: 1px solid #F0F2F6;
    border-radius: 8px;
    padding: 7px 11px;
    font-size: 9pt;
}
QToolButton:hover { background: #EDF3FC; border-color: #DCE8FC; color: #3478F6; }
QTextEdit {
    background: #FFFFFF;
    color: #2E394B;
    border: 0;
    padding: 16px;
    font-size: 11pt;
    selection-background-color: #DCE9FF;
}
QPushButton#primary {
    background: #4B86F7;
    color: #FFFFFF;
    border: 0;
    border-radius: 11px;
    padding: 10px 18px;
    font-size: 10pt;
    font-weight: 700;
}
QPushButton#primary:hover { background: #3675EB; }
QPushButton#windowButton {
    background: #FFFFFF;
    color: #5F6B7D;
    border: 1px solid #E6EAF0;
    border-radius: 10px;
    padding: 8px 12px;
    font-size: 9pt;
    font-weight: 600;
}
QPushButton#windowButton:hover { background: #F6F8FB; color: #263246; }
QPushButton#closeButton {
    background: #FFFFFF;
    color: #687386;
    border: 1px solid #E6EAF0;
    border-radius: 10px;
    padding: 7px 12px;
    font-size: 12pt;
}
QPushButton#closeButton:hover { background: #FFF1F1; color: #C83D3D; border-color: #F8DADA; }
QPushButton#soft {
    background: #FFFFFF;
    color: #4B5563;
    border: 1px solid #E6EAF0;
    border-radius: 10px;
    padding: 8px 12px;
}
QPushButton#soft:hover { background: #F6F8FB; }
QListWidget { background: transparent; border: 0; outline: 0; }
QListWidget::item {
    color: #435066;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 11px;
    padding: 8px 9px;
    margin: 2px 0;
}
QListWidget::item:hover { background: #F7F9FC; }
QListWidget::item:selected {
    color: #2F6FD8;
    background: #EDF4FF;
    border: 1px solid #DDEAFF;
}
"""

class RoundGlyph(QLabel):
    """Small circular icon badge."""
    def __init__(self, glyph, size=42, bg="#EDF4FF", fg="#4B86F7", font_size=15):
        super().__init__(glyph)
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            f"background:{bg};color:{fg};border:1px solid {bg};"
            f"border-radius:{size//2}px;font-size:{font_size}pt;font-weight:700;"
        )

class RichTextEdit(QTextEdit):
    """Rich text editor that saves pasted clipboard images into the app data folder."""
    def __init__(self, owner):
        super().__init__()
        self.owner = owner

    def insertFromMimeData(self, source):
        try:
            if source.hasImage():
                image = source.imageData()
                if isinstance(image, QImage) and not image.isNull():
                    saved_path = self.owner.store_image(image)
                    cursor = self.textCursor()
                    image_format = QTextImageFormat()
                    image_format.setName(str(saved_path))
                    image_format.setWidth(min(image.width(), 680))
                    image_format.setHeight(min(image.height(), 900))
                    if image.width() > 680:
                        image_format.setHeight(image.height() * 680 / image.width())
                    cursor.insertImage(image_format)
                    self.setTextCursor(cursor)
                    self.owner.status.setText("图片已插入，正在自动保存…")
                    return
        except Exception:
            pass
        super().insertFromMimeData(source)


class EdgeBadge(QWidget):
    """Short click opens; long press starts free dragging."""
    def __init__(self, owner):
        super().__init__(None, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint |
                         Qt.WindowType.WindowStaysOnTopHint)
        self.owner = owner
        self.setFixedSize(54, 54)
        self.setStyleSheet("background:#FFFFFF;border:1px solid #E3E8F0;border-radius:17px;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        icon = RoundGlyph("✎", 36, "#EAF2FF", "#4B86F7", 16)
        layout.addWidget(icon, 0, Qt.AlignmentFlag.AlignCenter)
        self.setToolTip("短按打开；长按拖动位置")
        self._press_global = None
        self._press_local = None
        self._dragging = False
        self._long_press = QTimer(self)
        self._long_press.setSingleShot(True)
        self._long_press.timeout.connect(self._begin_drag)

    def enterEvent(self, event):
        # Deliberately do not open on hover; short click opens.
        super().enterEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_global = event.globalPosition().toPoint()
            self._press_local = event.position().toPoint()
            self._dragging = False
            self._long_press.start(350)
            event.accept()
            return
        super().mousePressEvent(event)

    def _begin_drag(self):
        if self._press_global is not None:
            self._dragging = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self._press_global is not None and (self._dragging or
            (event.globalPosition().toPoint() - self._press_global).manhattanLength() >= 8):
            if not self._dragging:
                self._long_press.stop()
                self._begin_drag()
            delta = event.globalPosition().toPoint() - self._press_global
            self.move(self.pos() + delta)
            self._press_global = event.globalPosition().toPoint()
            self._press_local = event.position().toPoint()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._long_press.stop()
            if self._dragging:
                self._dragging = False
                self.setCursor(Qt.CursorShape.ArrowCursor)
                self.owner.save_badge_position(self.pos())
            else:
                self.owner.restore_from_edge()
            self._press_global = None
            self._press_local = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

class WindowResizeFilter(QObject):
    """Resize frameless main window by dragging its edges or corners."""
    BORDER = 8
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.mode = None
        self.start_pos = None
        self.start_rect = None

    def edge_at(self, pos):
        r = self.window.frameGeometry()
        left, right = abs(pos.x()-r.left()) <= self.BORDER, abs(pos.x()-r.right()) <= self.BORDER
        top, bottom = abs(pos.y()-r.top()) <= self.BORDER, abs(pos.y()-r.bottom()) <= self.BORDER
        if top and left: return "top_left"
        if top and right: return "top_right"
        if bottom and left: return "bottom_left"
        if bottom and right: return "bottom_right"
        if left: return "left"
        if right: return "right"
        if top: return "top"
        if bottom: return "bottom"
        return None

    def eventFilter(self, watched, event):
        typ = event.type()
        if typ not in (QEvent.Type.MouseMove, QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease):
            return False
        try:
            pos = event.globalPosition().toPoint()
        except Exception:
            return False
        if typ == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            mode = self.edge_at(pos)
            if mode:
                self.mode = mode
                self.start_pos = pos
                self.start_rect = self.window.geometry()
                return True
        elif typ == QEvent.Type.MouseMove:
            if self.mode and self.start_pos is not None and self.start_rect is not None:
                dx, dy = pos.x()-self.start_pos.x(), pos.y()-self.start_pos.y()
                r = self.start_rect
                x, y, w, h = r.x(), r.y(), r.width(), r.height()
                minw, minh = self.window.minimumWidth(), self.window.minimumHeight()
                if "left" in self.mode:
                    nw = max(minw, w-dx); x = r.x() + w - nw; w = nw
                if "right" in self.mode:
                    w = max(minw, w+dx)
                if "top" in self.mode:
                    nh = max(minh, h-dy); y = r.y() + h - nh; h = nh
                if "bottom" in self.mode:
                    h = max(minh, h+dy)
                self.window.setGeometry(x, y, w, h)
                return True
            edge = self.edge_at(pos)
            cursors = {
                "left": Qt.CursorShape.SizeHorCursor, "right": Qt.CursorShape.SizeHorCursor,
                "top": Qt.CursorShape.SizeVerCursor, "bottom": Qt.CursorShape.SizeVerCursor,
                "top_left": Qt.CursorShape.SizeFDiagCursor, "bottom_right": Qt.CursorShape.SizeFDiagCursor,
                "top_right": Qt.CursorShape.SizeBDiagCursor, "bottom_left": Qt.CursorShape.SizeBDiagCursor
            }
            self.window.setCursor(cursors.get(edge, Qt.CursorShape.ArrowCursor))
        elif typ == QEvent.Type.MouseButtonRelease and self.mode:
            self.mode = None
            self.start_pos = None
            self.start_rect = None
            self.window.unsetCursor()
            return True
        return False


class MemoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        APP_DIR.mkdir(parents=True, exist_ok=True)
        self.notes = load_json(DATA_FILE, {})
        self.config = load_json(CONFIG_FILE, {"edge": "right"})
        self.edge = self.config.get("edge", "right")
        if self.edge not in ("left", "right", "top", "bottom"):
            self.edge = "right"
        self.selected = key_for(date.today())
        self.drag_offset = None
        self.loading = False
        self.tray = None
        self.edge_badge = EdgeBadge(self)

        self.setWindowTitle(APP_NAME)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(1120, 800)
        self.setMinimumSize(1120, 700)
        self.setStyleSheet(APP_STYLE)

        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self.save_now)

        self._build()
        self.resize_filter = WindowResizeFilter(self)
        for widget in self.findChildren(QWidget):
            widget.installEventFilter(self.resize_filter)
        self.installEventFilter(self.resize_filter)
        self._make_tray()
        self._load_selected()
        self._refresh_dates()
        self._place_initial()

    def _build(self):
        canvas = QWidget()
        canvas.setObjectName("canvas")
        self.setCentralWidget(canvas)
        canvas_layout = QVBoxLayout(canvas)
        canvas_layout.setContentsMargins(9, 9, 9, 9)
        canvas_layout.setSpacing(0)

        surface = QFrame()
        surface.setObjectName("windowSurface")
        # Shadow lives outside the rounded surface, without creating white corner artefacts.
        shadow = QGraphicsDropShadowEffect(surface)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 7)
        shadow.setColor(QColor(36, 52, 78, 28))
        surface.setGraphicsEffect(shadow)
        canvas_layout.addWidget(surface)
        self.surface = surface

        surface_l = QVBoxLayout(surface)
        surface_l.setContentsMargins(0, 0, 0, 0)
        surface_l.setSpacing(0)

        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(100)
        header.mousePressEvent = self._drag_start
        header.mouseMoveEvent = self._drag_move
        header.mouseReleaseEvent = self._drag_end
        hl = QHBoxLayout(header)
        hl.setContentsMargins(25, 19, 20, 18)
        hl.setSpacing(14)

        app_icon = RoundGlyph("✎", 52, "#EAF2FF", "#3478F6", 20)
        hl.addWidget(app_icon, 0, Qt.AlignmentFlag.AlignVCenter)
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("桌边备忘录")
        title.setObjectName("appTitle")
        subtitle = QLabel("本地保存  ·  最近 14 天")
        subtitle.setObjectName("appSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        hl.addLayout(title_col)
        hl.addStretch()
        self._header_btn(hl, "吸附", self.dock_nearest, "windowButton", 70)
        self._header_btn(hl, "—", self.minimize_to_tray, "windowButton", 44)
        self._header_btn(hl, "×", self.minimize_to_tray, "closeButton", 44)
        surface_l.addWidget(header)

        divider = QFrame()
        divider.setObjectName("divider")
        surface_l.addWidget(divider)

        body = QWidget()
        body_l = QVBoxLayout(body)
        body_l.setContentsMargins(18, 15, 18, 15)
        body_l.setSpacing(13)

        top = QHBoxLayout()
        top.setSpacing(9)
        self.date_icon = QPushButton("▦")
        self.date_icon.setToolTip("打开日历，选择最近14天的记录")
        self.date_icon.setFixedSize(34, 34)
        self.date_icon.setCursor(Qt.CursorShape.PointingHandCursor)
        self.date_icon.setStyleSheet(
            "QPushButton { background:#F5F7FA; color:#4B5563; border:1px solid #E6EAF0; "
            "border-radius:17px; font-size:13pt; font-weight:600; }"
            "QPushButton:hover { background:#EDF4FF; color:#3478F6; }"
        )
        self.date_icon.clicked.connect(self.open_calendar)
        top.addWidget(self.date_icon, 0, Qt.AlignmentFlag.AlignVCenter)
        self.date_label = QLabel("")
        self.date_label.setObjectName("sectionTitle")
        top.addWidget(self.date_label, 0, Qt.AlignmentFlag.AlignVCenter)
        top.addStretch()
        self.status_icon = RoundGlyph("✓", 22, "#ECF9F2", "#159A67", 9)
        top.addWidget(self.status_icon, 0, Qt.AlignmentFlag.AlignVCenter)
        self.status = QLabel("自动保存已开启")
        self.status.setObjectName("status")
        top.addWidget(self.status, 0, Qt.AlignmentFlag.AlignVCenter)
        body_l.addLayout(top)

        columns = QHBoxLayout()
        columns.setSpacing(14)

        editor_card = QFrame()
        editor_card.setObjectName("card")
        editor_l = QVBoxLayout(editor_card)
        editor_l.setContentsMargins(14, 13, 14, 13)
        editor_l.setSpacing(10)

        toolbar = QFrame()
        toolbar.setObjectName("toolbar")
        tool_l = QHBoxLayout(toolbar)
        tool_l.setContentsMargins(10, 8, 10, 8)
        tool_l.setSpacing(7)
        for label, callback, tip in [
            ("粗体", self.bold, "加粗选中文字"),
            ("斜体", self.italic, "斜体选中文字"),
            ("下划线", self.underline, "为选中文字添加下划线"),
            ("插入图片", self.insert_image, "从电脑选择图片"),
        ]:
            button = QToolButton()
            button.setText(label)
            button.setToolTip(tip)
            button.setMinimumHeight(34)
            button.setStyleSheet("QToolButton { color:#202938; background:#F6F8FB; border:1px solid #E8ECF2; border-radius:8px; padding:7px 10px; font-size:9pt; } QToolButton:hover { background:#EDF4FF; border-color:#D7E5FC; }")
            button.clicked.connect(callback)
            tool_l.addWidget(button)

        size_label = QLabel("字号")
        size_label.setStyleSheet("color:#202938; font-size:9pt; font-weight:600;")
        tool_l.addWidget(size_label)
        self.font_size_combo = QComboBox()
        self.font_size_combo.addItems(["9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "32"])
        self.font_size_combo.setCurrentText("11")
        self.font_size_combo.setToolTip("选择文字字号")
        self.font_size_combo.setFixedWidth(68)
        self.font_size_combo.setMinimumHeight(34)
        self.font_size_combo.setStyleSheet(
            "QComboBox { color:#202938; background:#FFFFFF; border:1px solid #DDE3EC; "
            "border-radius:8px; padding:5px 8px; }"
            "QComboBox QAbstractItemView { color:#202938; background:#FFFFFF; selection-background-color:#EDF4FF; }"
        )
        self.font_size_combo.currentTextChanged.connect(self.apply_font_size_from_combo)
        tool_l.addWidget(self.font_size_combo)

        self.more_button = QToolButton()
        self.more_button.setText("更多功能")
        self.more_button.setToolTip("字体、颜色、对齐、撤销等更多编辑功能")
        self.more_button.setMinimumHeight(34)
        self.more_button.setStyleSheet("QToolButton { color:#202938; background:#F6F8FB; border:1px solid #E8ECF2; border-radius:8px; padding:7px 12px; font-size:9pt; } QToolButton:hover { background:#EDF4FF; border-color:#D7E5FC; }")
        self.more_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.more_menu = QMenu(self.more_button)

        font_action = QAction("字体…", self)
        font_action.triggered.connect(self.choose_font)
        color_action = QAction("文字颜色…", self)
        color_action.triggered.connect(self.choose_text_color)
        highlight_action = QAction("文字高亮颜色…", self)
        highlight_action.triggered.connect(self.choose_highlight)
        strike_action = QAction("删除线", self)
        strike_action.triggered.connect(self.strike)
        bullet_action = QAction("项目符号列表", self)
        bullet_action.triggered.connect(self.bullet_list)
        number_action = QAction("编号列表", self)
        number_action.triggered.connect(self.number_list)
        self.more_menu.addAction(font_action)
        self.more_menu.addAction(strike_action)
        self.more_menu.addSeparator()
        self.more_menu.addAction(bullet_action)
        self.more_menu.addAction(number_action)
        self.more_menu.addSeparator()
        self.more_menu.addAction(color_action)
        self.more_menu.addAction(highlight_action)

        align_menu = self.more_menu.addMenu("段落对齐")
        align_left = QAction("左对齐", self)
        align_left.triggered.connect(lambda: self.align_text(Qt.AlignmentFlag.AlignLeft))
        align_center = QAction("居中对齐", self)
        align_center.triggered.connect(lambda: self.align_text(Qt.AlignmentFlag.AlignHCenter))
        align_right = QAction("右对齐", self)
        align_right.triggered.connect(lambda: self.align_text(Qt.AlignmentFlag.AlignRight))
        align_menu.addAction(align_left)
        align_menu.addAction(align_center)
        align_menu.addAction(align_right)

        self.more_menu.addSeparator()
        undo_action = QAction("撤销", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.editor_undo)
        redo_action = QAction("重做", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.editor_redo)
        self.more_menu.addAction(undo_action)
        self.more_menu.addAction(redo_action)
        self.more_button.setMenu(self.more_menu)
        tool_l.addWidget(self.more_button)
        tool_l.addStretch()
        editor_l.addWidget(toolbar)

        line = QFrame()
        line.setObjectName("divider")
        editor_l.addWidget(line)

        self.editor = RichTextEdit(self)
        self.editor.setPlaceholderText("记录今天的工作、灵感和待办事项……")
        self.editor.textChanged.connect(self._text_changed)
        editor_l.addWidget(self.editor, 1)

        foot = QHBoxLayout()
        self.word_count = QLabel("0 字")
        self.word_count.setObjectName("muted")
        foot.addWidget(self.word_count)
        foot.addStretch()
        save_btn = QPushButton("✎  立即保存")
        save_btn.setObjectName("primary")
        save_btn.clicked.connect(self.save_now)
        foot.addWidget(save_btn)
        editor_l.addLayout(foot)
        columns.addWidget(editor_card, 7)

        history = QFrame()
        history.setObjectName("card")
        history.setMinimumWidth(285)
        history_l = QVBoxLayout(history)
        history_l.setContentsMargins(15, 15, 15, 12)
        history_l.setSpacing(8)
        hist_head = QHBoxLayout()
        hist_icon = RoundGlyph("◷", 34, "#F5F7FA", "#667085", 13)
        hist_head.addWidget(hist_icon, 0, Qt.AlignmentFlag.AlignVCenter)
        hist_title = QLabel("最近 14 天")
        hist_title.setObjectName("sectionTitle")
        hist_head.addWidget(hist_title, 0, Qt.AlignmentFlag.AlignVCenter)
        hist_head.addStretch()
        history_l.addLayout(hist_head)
        hint = QLabel("选择日期查看或修改")
        hint.setObjectName("muted")
        history_l.addWidget(hint)
        self.date_list = QListWidget()
        self.date_list.currentRowChanged.connect(self._date_changed)
        history_l.addWidget(self.date_list, 1)
        columns.addWidget(history, 3)
        body_l.addLayout(columns, 1)

        bottom = QHBoxLayout()
        bottom.setSpacing(8)
        local_icon = RoundGlyph("▣", 28, "#F5F7FA", "#7B8494", 10)
        bottom.addWidget(local_icon, 0, Qt.AlignmentFlag.AlignVCenter)
        local_text = QLabel("仅保存在本机，不上传云端")
        local_text.setObjectName("muted")
        bottom.addWidget(local_text, 0, Qt.AlignmentFlag.AlignVCenter)
        bottom.addStretch()
        settings_icon = RoundGlyph("⚙", 28, "#F5F7FA", "#667085", 10)
        bottom.addWidget(settings_icon, 0, Qt.AlignmentFlag.AlignVCenter)
        settings = QPushButton("设置  ▾")
        settings.setObjectName("soft")
        settings.clicked.connect(self._settings_menu)
        bottom.addWidget(settings)
        body_l.addLayout(bottom)
        surface_l.addWidget(body, 1)

    def _header_btn(self, layout, text, callback, style_name, width):
        btn = QPushButton(text)
        btn.setObjectName(style_name)
        btn.setFixedWidth(width)
        btn.clicked.connect(callback)
        layout.addWidget(btn)

    def _make_tray(self):
        self.tray = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(self._make_icon(), self)
        menu = QMenu()
        a_open = QAction("打开桌边备忘录", self)
        a_open.triggered.connect(self.restore_from_tray)
        a_save = QAction("立即保存", self)
        a_save.triggered.connect(self.save_now)
        a_quit = QAction("退出程序", self)
        a_quit.triggered.connect(self.quit_app)
        menu.addAction(a_open)
        menu.addAction(a_save)
        menu.addSeparator()
        menu.addAction(a_quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda reason: self.restore_from_tray()
                                    if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
        self.tray.setToolTip(APP_NAME)
        self.tray.show()

    def _make_icon(self):
        pix = QPixmap(64, 64)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#EAF2FF"))
        p.drawEllipse(4, 4, 56, 56)
        p.setBrush(QColor("#4B86F7"))
        p.drawEllipse(14, 14, 36, 36)
        p.setPen(QPen(QColor("white"), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(25, 40, 41, 24)
        p.drawLine(24, 29, 35, 29)
        p.end()
        return QIcon(pix)

    def _place_initial(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 20, screen.top() + 30)

    def _drag_start(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    def _drag_move(self, event):
        if self.drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_offset)
            event.accept()
    def _drag_end(self, event):
        self.drag_offset = None
        self._snap_if_near_edge()

    def _snap_if_near_edge(self):
        screen = QApplication.primaryScreen().availableGeometry()
        g = self.frameGeometry()
        d = {
            "left": abs(g.left() - screen.left()),
            "right": abs(screen.right() - g.right()),
            "top": abs(g.top() - screen.top()),
            "bottom": abs(screen.bottom() - g.bottom()),
        }
        edge, distance = min(d.items(), key=lambda x: x[1])
        if distance <= 26:
            self.edge = edge
            self.config["edge"] = edge
            save_json(CONFIG_FILE, self.config)
            self.collapse_to_edge()

    def dock_nearest(self):
        screen = QApplication.primaryScreen().availableGeometry()
        g = self.frameGeometry()
        d = {
            "left": abs(g.left() - screen.left()),
            "right": abs(screen.right() - g.right()),
            "top": abs(g.top() - screen.top()),
            "bottom": abs(screen.bottom() - g.bottom()),
        }
        self.edge = min(d.items(), key=lambda x: x[1])[0]
        self.config["edge"] = self.edge
        save_json(CONFIG_FILE, self.config)
        self.collapse_to_edge()

    def collapse_to_edge(self):
        self.save_now()
        screen = QApplication.primaryScreen().availableGeometry()
        w = self.edge_badge.width()
        h = self.edge_badge.height()
        if self.edge == "left":
            pos = QPoint(screen.left(), screen.center().y() - h // 2)
        elif self.edge == "right":
            pos = QPoint(screen.right() - w + 1, screen.center().y() - h // 2)
        elif self.edge == "top":
            pos = QPoint(screen.center().x() - w // 2, screen.top())
        else:
            pos = QPoint(screen.center().x() - w // 2, screen.bottom() - h + 1)
        saved_x = self.config.get("badge_x")
        saved_y = self.config.get("badge_y")
        if isinstance(saved_x, int) and isinstance(saved_y, int):
            pos = QPoint(
                max(screen.left(), min(saved_x, screen.right() - w + 1)),
                max(screen.top(), min(saved_y, screen.bottom() - h + 1))
            )
        self.hide()
        self.edge_badge.move(pos)
        self.edge_badge.show()
        self.edge_badge.raise_()

    def restore_from_edge(self):
        self.edge_badge.hide()
        screen = QApplication.primaryScreen().availableGeometry()
        if self.edge == "left":
            pos = QPoint(screen.left(), max(screen.top(), screen.center().y() - self.height() // 2))
        elif self.edge == "right":
            pos = QPoint(screen.right() - self.width() + 1, max(screen.top(), screen.center().y() - self.height() // 2))
        elif self.edge == "top":
            pos = QPoint(max(screen.left(), screen.center().x() - self.width() // 2), screen.top())
        else:
            pos = QPoint(max(screen.left(), screen.center().x() - self.width() // 2), screen.bottom() - self.height() + 1)
        self.move(pos)
        self.show()
        self.raise_()
        self.activateWindow()

    def _text_changed(self):
        if self.loading:
            return
        self.status.setText("正在自动保存…")
        self.status.setStyleSheet("color:#B7791F;font-size:9pt;font-weight:600;")
        self.word_count.setText(f"{len(self.editor.toPlainText())} 字")
        self.save_timer.start(500)

    def _load_selected(self):
        self.loading = True
        content = self.notes.get(self.selected, "")
        # Backward compatible: old notes were plain text, new notes are HTML rich text.
        if isinstance(content, str) and content.lstrip().startswith("<"):
            self.editor.setHtml(content)
        else:
            self.editor.setPlainText(content if isinstance(content, str) else "")
        self.loading = False
        self.date_label.setText(date_text(date.fromisoformat(self.selected)))
        self.word_count.setText(f"{len(self.editor.toPlainText())} 字")
        self.status.setText("自动保存已开启")
        self.status.setStyleSheet("color:#159A67;font-size:9pt;font-weight:600;")

    def _refresh_dates(self):
        self.date_list.blockSignals(True)
        self.date_list.clear()
        for i in range(14):
            d = date.today() - timedelta(days=i)
            k = key_for(d)
            raw = self.notes.get(k, "")
            plain = re.sub(r"<[^>]+>", "", raw).replace("&nbsp;", " ").strip() if isinstance(raw, str) else str(raw).strip()
            has = bool(plain)
            status = "已记录" if has else "暂无记录"
            marker = "●" if has else "○"
            item = QListWidgetItem(f"{marker}  {date_text(d)}\n     {status}")
            item.setData(Qt.ItemDataRole.UserRole, k)
            item.setSizeHint(QSize(230, 56))
            self.date_list.addItem(item)
            if k == self.selected:
                self.date_list.setCurrentItem(item)
        self.date_list.blockSignals(False)

    def open_calendar(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("选择日期")
        dialog.setModal(True)
        dialog.setMinimumWidth(330)
        layout = QVBoxLayout(dialog)
        hint = QLabel("只能选择最近 14 天（含今天）")
        hint.setStyleSheet("color:#667085; font-size:9pt;")
        layout.addWidget(hint)

        calendar = QCalendarWidget(dialog)
        today = date.today()
        earliest = today - timedelta(days=13)
        calendar.setMinimumDate(__import__("PySide6.QtCore", fromlist=["QDate"]).QDate(earliest.year, earliest.month, earliest.day))
        calendar.setMaximumDate(__import__("PySide6.QtCore", fromlist=["QDate"]).QDate(today.year, today.month, today.day))
        selected_date = date.fromisoformat(self.selected)
        calendar.setSelectedDate(__import__("PySide6.QtCore", fromlist=["QDate"]).QDate(selected_date.year, selected_date.month, selected_date.day))
        calendar.setGridVisible(True)
        calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        # Highlight the currently selected day with a visible blue background.
        from PySide6.QtGui import QTextCharFormat
        from PySide6.QtCore import QDate
        selected_format = QTextCharFormat()
        selected_format.setBackground(QColor("#3478F6"))
        selected_format.setForeground(QColor("#FFFFFF"))
        calendar.setDateTextFormat(QDate(selected_date.year, selected_date.month, selected_date.day), selected_format)
        calendar.setStyleSheet("""
            QCalendarWidget QWidget { background:#FFFFFF; color:#202938; }
            QCalendarWidget QToolButton { color:#202938; background:#F6F8FB; border:1px solid #E6EAF0; border-radius:6px; padding:5px; }
            QCalendarWidget QMenu { background:#FFFFFF; color:#202938; }
            QCalendarWidget QAbstractItemView { color:#202938; background:#FFFFFF; selection-background-color:#3478F6; selection-color:#FFFFFF; outline:0; }
            QCalendarWidget QAbstractItemView:enabled { color:#202938; selection-background-color:#3478F6; selection-color:#FFFFFF; }
            QCalendarWidget QAbstractItemView:disabled { color:#C9CED7; background:#FAFBFC; }
        """)
        layout.addWidget(calendar)
        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("取消")
        cancel.setObjectName("soft")
        confirm = QPushButton("查看这一天")
        confirm.setObjectName("primary")
        buttons.addWidget(cancel)
        buttons.addWidget(confirm)
        layout.addLayout(buttons)
        cancel.clicked.connect(dialog.reject)
        confirm.clicked.connect(dialog.accept)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            qd = calendar.selectedDate()
            chosen = date(qd.year(), qd.month(), qd.day())
            # Guard against calendar dates outside the permitted range.
            if chosen < earliest or chosen > today:
                QMessageBox.information(self, APP_NAME, "只能查看最近14天的记录。")
                return
            target_key = key_for(chosen)
            for i in range(self.date_list.count()):
                item = self.date_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == target_key:
                    self.date_list.setCurrentRow(i)
                    return

    def apply_font_size_from_combo(self, value):
        if not hasattr(self, "editor") or self.loading:
            return
        try:
            size = float(value)
        except (ValueError, TypeError):
            return
        fmt = QTextCharFormat()
        fmt.setFontPointSize(size)
        self.editor.mergeCurrentCharFormat(fmt)
        self.editor.setFocus()

    def _date_changed(self, row):
        item = self.date_list.item(row)
        if item is None:
            return
        k = item.data(Qt.ItemDataRole.UserRole)
        if not k or k == self.selected:
            return
        self.save_now()
        self.selected = k
        self._load_selected()

    def save_now(self):
        if hasattr(self, "save_timer") and self.save_timer.isActive():
            self.save_timer.stop()
        if not hasattr(self, "editor"):
            return
        plain_text = self.editor.toPlainText()
        rich_html = self.editor.toHtml()
        if plain_text.strip():
            self.notes[self.selected] = rich_html
        else:
            self.notes.pop(self.selected, None)
        try:
            save_json(DATA_FILE, self.notes)
            self.status.setText(f"已保存 {datetime.now():%H:%M:%S}")
            self.status.setStyleSheet("color:#159A67;font-size:9pt;font-weight:600;")
            self._refresh_dates()
        except Exception as e:
            QMessageBox.critical(self, APP_NAME, f"保存失败：{e}")

    def insert(self, text):
        self.editor.insertPlainText(text)
        self.editor.setFocus()
    def bold(self):
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Bold if self.editor.fontWeight() != QFont.Weight.Bold else QFont.Weight.Normal)
        self.editor.mergeCurrentCharFormat(fmt)
    def italic(self):
        fmt = QTextCharFormat()
        fmt.setFontItalic(not self.editor.fontItalic())
        self.editor.mergeCurrentCharFormat(fmt)
    def underline(self):
        fmt = QTextCharFormat()
        fmt.setFontUnderline(not self.editor.fontUnderline())
        self.editor.mergeCurrentCharFormat(fmt)

    def store_image(self, image):
        """Copy an image into the app's local image folder so notes keep working."""
        image_dir = APP_DIR / "images"
        image_dir.mkdir(parents=True, exist_ok=True)
        filename = f"memo_image_{datetime.now():%Y%m%d_%H%M%S_%f}.png"
        path = image_dir / filename
        if not image.save(str(path), "PNG"):
            raise OSError("无法保存粘贴的图片")
        return path

    def insert_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择要插入的图片", str(Path.home()),
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if not path:
            return
        image = QImage(path)
        if image.isNull():
            QMessageBox.warning(self, APP_NAME, "无法读取这张图片。")
            return
        try:
            stored_path = self.store_image(image)
            cursor = self.editor.textCursor()
            image_format = QTextImageFormat()
            image_format.setName(str(stored_path))
            max_width = 680
            display_width = min(image.width(), max_width)
            display_height = image.height() * display_width / image.width()
            image_format.setWidth(display_width)
            image_format.setHeight(display_height)
            cursor.insertImage(image_format)
            self.editor.setTextCursor(cursor)
            self.editor.setFocus()
            self.status.setText("图片已插入，正在自动保存…")
            self.save_timer.start(250)
        except Exception as exc:
            QMessageBox.critical(self, APP_NAME, f"插入图片失败：\\n{exc}")

    def strike(self):
        fmt = QTextCharFormat()
        fmt.setFontStrikeOut(not self.editor.currentCharFormat().fontStrikeOut())
        self.editor.mergeCurrentCharFormat(fmt)

    def choose_font(self):
        current = self.editor.currentFont()
        font, ok = QFontDialog.getFont(current, self, "选择字体")
        if ok:
            self.editor.setCurrentFont(font)
            self.editor.setFocus()

    def choose_font_size(self):
        current_size = self.editor.fontPointSize()
        if not current_size or current_size < 1:
            current_size = 11
        size, ok = QInputDialog.getInt(
            self, "设置字号", "字号（磅）：", int(current_size), 6, 72, 1
        )
        if ok:
            fmt = QTextCharFormat()
            fmt.setFontPointSize(float(size))
            self.editor.mergeCurrentCharFormat(fmt)
            self.editor.setFocus()

    def set_font_family(self, font):
        fmt = QTextCharFormat()
        fmt.setFontFamily(font.family())
        self.editor.mergeCurrentCharFormat(fmt)
        self.editor.setFocus()

    def set_font_size(self, value):
        try:
            size = float(value)
        except (ValueError, TypeError):
            return
        fmt = QTextCharFormat()
        fmt.setFontPointSize(size)
        self.editor.mergeCurrentCharFormat(fmt)
        self.editor.setFocus()

    def choose_text_color(self):
        color = QColorDialog.getColor(parent=self, title="选择文字颜色")
        if color.isValid():
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            self.editor.mergeCurrentCharFormat(fmt)
            self.editor.setFocus()

    def choose_highlight(self):
        color = QColorDialog.getColor(QColor("#FFF1A8"), self, "选择高亮颜色")
        if color.isValid():
            fmt = QTextCharFormat()
            fmt.setBackground(color)
            self.editor.mergeCurrentCharFormat(fmt)
            self.editor.setFocus()

    def align_text(self, alignment):
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        block_fmt = cursor.blockFormat()
        block_fmt.setAlignment(alignment)
        cursor.mergeBlockFormat(block_fmt)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def bullet_list(self):
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        list_fmt = QTextListFormat()
        list_fmt.setStyle(QTextListFormat.Style.ListDisc)
        list_fmt.setIndent(1)
        cursor.createList(list_fmt)
        cursor.endEditBlock()
        self.editor.setFocus()

    def number_list(self):
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        list_fmt = QTextListFormat()
        list_fmt.setStyle(QTextListFormat.Style.ListDecimal)
        list_fmt.setIndent(1)
        cursor.createList(list_fmt)
        cursor.endEditBlock()
        self.editor.setFocus()

    def editor_undo(self):
        self.editor.undo()

    def editor_redo(self):
        self.editor.redo()

    def save_badge_position(self, pos):
        screen = QApplication.primaryScreen().availableGeometry()
        x = max(screen.left(), min(pos.x(), screen.right() - self.edge_badge.width() + 1))
        y = max(screen.top(), min(pos.y(), screen.bottom() - self.edge_badge.height() + 1))
        self.edge_badge.move(x, y)
        self.config["badge_x"] = x
        self.config["badge_y"] = y
        # Keep the nearest edge as the restore direction, but allow the badge to sit anywhere.
        g = self.edge_badge.geometry()
        distances = {
            "left": abs(g.left() - screen.left()),
            "right": abs(screen.right() - g.right()),
            "top": abs(g.top() - screen.top()),
            "bottom": abs(screen.bottom() - g.bottom()),
        }
        self.edge = min(distances.items(), key=lambda item: item[1])[0]
        self.config["edge"] = self.edge
        save_json(CONFIG_FILE, self.config)

    def _settings_menu(self):
        menu = QMenu(self)
        today = QAction("回到今天", self)
        today.triggered.connect(self.go_today)
        dock = QAction("吸附到最近边缘", self)
        dock.triggered.connect(self.dock_nearest)
        folder = QAction("打开本地数据文件夹", self)
        folder.triggered.connect(self.open_data_folder)
        quit_action = QAction("退出程序", self)
        quit_action.triggered.connect(self.quit_app)
        for action in (today, dock, folder, quit_action):
            menu.addAction(action)
        menu.exec(self.mapToGlobal(self.rect().bottomRight()))

    def go_today(self):
        self.save_now()
        self.selected = key_for(date.today())
        self._load_selected()
        self._refresh_dates()

    def open_data_folder(self):
        if os.name == "nt":
            os.startfile(str(APP_DIR))

    def minimize_to_tray(self):
        self.save_now()
        if self.tray is not None:
            self.hide()
        else:
            self.showMinimized()

    def restore_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        self.save_now()
        if self.tray is not None:
            event.ignore()
            self.hide()
        else:
            event.accept()

    def quit_app(self):
        self.save_now()
        if self.tray is not None:
            self.tray.hide()
        QApplication.quit()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)
    window = MemoWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
