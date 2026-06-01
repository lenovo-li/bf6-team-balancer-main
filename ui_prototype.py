"""
BF6 Team Balancer - UI v2 API Edition (PyQt5)
Page flow: Fetch Stats -> Allocation Mode -> Game Mode -> Custom Squad -> Result

Excel 导入已移除，改为通过 bfstats.dll 查询玩家数据。
"""

import sys
import os
import json
import ctypes
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QStackedWidget, QDoubleSpinBox, QComboBox,
    QHeaderView, QMessageBox, QFrame, QSizePolicy,
    QAbstractItemView, QTextEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.algorithm import (
    load_players,
    allocate_teams,
    random_allocate,
    compute_balance_report,
    GAME_MODES
)
from history import save_record, load_history, load_config, save_config


# ---------------------------------------------------------------------------
# BFStats DLL Config
# ---------------------------------------------------------------------------

BFSTATS_DLL_DIR_NAME = "dll"
BFSTATS_DLL_NAME = "BFStats.dll"

BF6_OK = 0
BF6_PLATFORM_PC = 0
BF6_PLATFORM_EA = 1
BF6_PLATFORM_PSN = 2
BF6_PLATFORM_XBOX = 3

PLATFORM_NAMES = {
    BF6_PLATFORM_PC: "PC",
    BF6_PLATFORM_EA: "EA",
    BF6_PLATFORM_PSN: "PSN",
    BF6_PLATFORM_XBOX: "XBOX",
}

BF6_ERROR_NAMES = {
    0: "成功",
    -1: "参数非法",
    -2: "网络错误",
    -3: "HTTP 错误",
    -4: "玩家不存在 / 无数据",
    -5: "JSON 解析失败",
    -6: "内部错误",
}


# ---------------------------------------------------------------------------
# Global Styles
# ---------------------------------------------------------------------------

FONT_FAMILY = "Microsoft YaHei UI, Microsoft YaHei, PingFang SC, sans-serif"

ALLOC_MODE_NAMES = {
    "balanced": "均衡",
    "random": "随机"
}

GAME_MODE_NAMES = {
    "conquest": "征服",
    "breakthrough": "突破"
}


# ---------------------------------------------------------------------------
# Theme Config
# ---------------------------------------------------------------------------

THEMES = {
    "dark_gray": {
        "name": "🌙 暗夜灰",
        "bg": "#2b2b3a",
        "card": "#333346",
        "card_alt": "#3a3a50",
        "btn": "#3d3d50",
        "btn_hover": "#4a4a60",
        "btn_disabled": "#333344",
        "text": "#e0dfe6",
        "text_disabled": "#666680",
        "text_sub": "#9998aa",
        "text_hint": "#777790",
        "border": "#44445a",
        "border_header": "#4a4a60",
        "accent": "#7b8db8",
        "accent_hover": "#8a9cc8",
        "exit": "#b87b7b",
        "exit_hover": "#c88a8a",
        "balance": "#a8c8a8",
        "warning": "#d4a574",
        "squads": ["#363648", "#3e3e52", "#363648", "#42425a"],
        "step_active": "#7b8db8",
        "step_done": "#8aaa8a",
        "step_pending": "#3d3d50",
        "step_skipped": "#2d2d3a",
        "step_connector": "#44445a",
    },
    "deep_blue": {
        "name": "🌊 深海蓝",
        "bg": "#1a2332",
        "card": "#1e2a3a",
        "card_alt": "#223344",
        "btn": "#253545",
        "btn_hover": "#2d4050",
        "btn_disabled": "#1e2830",
        "text": "#d0dfe6",
        "text_disabled": "#556677",
        "text_sub": "#8899aa",
        "text_hint": "#667788",
        "border": "#2a3a4a",
        "border_header": "#344455",
        "accent": "#5b8db8",
        "accent_hover": "#6a9cc8",
        "exit": "#b87b5b",
        "exit_hover": "#c88a6a",
        "balance": "#8ac8a8",
        "warning": "#d4a574",
        "squads": ["#1e2e3e", "#253545", "#1e2e3e", "#2a3a4a"],
        "step_active": "#5b8db8",
        "step_done": "#6a9c6a",
        "step_pending": "#253545",
        "step_skipped": "#1a2830",
        "step_connector": "#2a3a4a",
    },
    "dark_green": {
        "name": "🌲 墨绿",
        "bg": "#1a2b1a",
        "card": "#1e331e",
        "card_alt": "#223a22",
        "btn": "#253d25",
        "btn_hover": "#2d4a2d",
        "btn_disabled": "#1e2e1e",
        "text": "#d0e6d0",
        "text_disabled": "#557755",
        "text_sub": "#88aa88",
        "text_hint": "#668866",
        "border": "#2a4a2a",
        "border_header": "#345534",
        "accent": "#7ba87b",
        "accent_hover": "#8ab88a",
        "exit": "#b87b7b",
        "exit_hover": "#c88a8a",
        "balance": "#a8c8a8",
        "warning": "#d4b874",
        "squads": ["#1e2e1e", "#253525", "#1e2e1e", "#2a3a2a"],
        "step_active": "#7ba87b",
        "step_done": "#6a9c6a",
        "step_pending": "#253d25",
        "step_skipped": "#1a2e1a",
        "step_connector": "#2a4a2a",
    },
    "dark_red": {
        "name": "🔥 暗红",
        "bg": "#2b1a1a",
        "card": "#331e1e",
        "card_alt": "#3a2222",
        "btn": "#3d2525",
        "btn_hover": "#4a2d2d",
        "btn_disabled": "#2e1e1e",
        "text": "#e6d0d0",
        "text_disabled": "#775555",
        "text_sub": "#aa8888",
        "text_hint": "#886666",
        "border": "#4a2a2a",
        "border_header": "#553434",
        "accent": "#b87b7b",
        "accent_hover": "#c88a8a",
        "exit": "#b87b5b",
        "exit_hover": "#c88a6a",
        "balance": "#c8a8a8",
        "warning": "#d4a574",
        "squads": ["#2e1e1e", "#352525", "#2e1e1e", "#3a2a2a"],
        "step_active": "#b87b7b",
        "step_done": "#8a6a6a",
        "step_pending": "#3d2525",
        "step_skipped": "#2e1a1a",
        "step_connector": "#4a2a2a",
    },
    "mono_bw": {
        "name": "⬛ 黑白纯色",
        "bg": "#0a0a0a",
        "card": "#141414",
        "card_alt": "#1a1a1a",
        "btn": "#1e1e1e",
        "btn_hover": "#2a2a2a",
        "btn_disabled": "#111111",
        "text": "#f0f0f0",
        "text_disabled": "#555555",
        "text_sub": "#999999",
        "text_hint": "#666666",
        "border": "#2a2a2a",
        "border_header": "#333333",
        "accent": "#ffffff",
        "accent_hover": "#cccccc",
        "exit": "#888888",
        "exit_hover": "#aaaaaa",
        "balance": "#cccccc",
        "warning": "#dddddd",
        "squads": ["#111111", "#1a1a1a", "#111111", "#222222"],
        "step_active": "#ffffff",
        "step_done": "#999999",
        "step_pending": "#1e1e1e",
        "step_skipped": "#111111",
        "step_connector": "#2a2a2a",
    },
}

DEFAULT_THEME = "dark_gray"


def build_stylesheet(t):
    return f"""
QMainWindow {{
    background: {t["bg"]};
}}
QWidget {{
    color: {t["text"]};
    font-family: {FONT_FAMILY};
    font-size: 16px;
}}
QPushButton {{
    background: {t["btn"]};
    color: {t["text"]};
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    font-size: 16px;
    font-family: {FONT_FAMILY};
}}
QPushButton:hover {{
    background: {t["btn_hover"]};
}}
QPushButton:disabled {{
    background: {t["btn_disabled"]};
    color: {t["text_disabled"]};
}}
QPushButton#primary {{
    background: {t["accent"]};
    color: #ffffff;
    font-weight: bold;
    font-size: 17px;
}}
QPushButton#primary:hover {{
    background: {t["accent_hover"]};
}}
QPushButton#exit_btn {{
    background: {t["exit"]};
    color: #ffffff;
    font-weight: bold;
    font-size: 17px;
}}
QPushButton#exit_btn:hover {{
    background: {t["exit_hover"]};
}}
QTextEdit {{
    background: {t["card"]};
    color: {t["text"]};
    border: 1px solid {t["border"]};
    border-radius: 8px;
    padding: 10px;
    font-size: 15px;
    font-family: {FONT_FAMILY};
}}
QTableWidget {{
    background: {t["card"]};
    alternate-background-color: {t["card_alt"]};
    border: none;
    border-radius: 8px;
    gridline-color: {t["border"]};
    font-size: 15px;
    font-family: {FONT_FAMILY};
}}
QTableWidget::item {{
    padding: 8px;
}}
QHeaderView::section {{
    background: {t["btn"]};
    color: {t["text"]};
    border: none;
    border-bottom: 2px solid {t["border_header"]};
    padding: 10px;
    font-size: 15px;
    font-weight: bold;
    font-family: {FONT_FAMILY};
}}
QComboBox {{
    background: {t["btn"]};
    border: 1px solid {t["border"]};
    border-radius: 8px;
    padding: 10px;
    min-width: 120px;
    font-size: 15px;
    font-family: {FONT_FAMILY};
}}
QComboBox::drop-down {{
    border: none;
}}
QComboBox QAbstractItemView {{
    background: {t["btn"]};
    border: 1px solid {t["border"]};
    selection-background-color: {t["accent"]};
    selection-color: #ffffff;
    font-size: 15px;
}}
QDoubleSpinBox {{
    background: {t["btn"]};
    border: 1px solid {t["border"]};
    border-radius: 8px;
    padding: 10px;
    font-size: 15px;
}}
QLabel#title {{
    font-size: 26px;
    font-weight: bold;
    color: {t["text"]};
}}
QLabel#subtitle {{
    font-size: 16px;
    color: {t["text_sub"]};
}}
QLabel#balance_summary {{
    font-size: 20px;
    font-weight: bold;
    color: {t["balance"]};
    padding: 16px;
    background: {t["card"]};
    border-radius: 10px;
}}
QLabel#warning {{
    color: {t["warning"]};
    font-weight: bold;
    font-size: 15px;
    padding: 8px;
}}
QLabel#hint {{
    color: {t["text_hint"]};
    font-size: 14px;
}}
QFrame#separator {{
    background: {t["border"]};
    max-height: 1px;
}}
"""


def get_theme_squad_colors(theme_id):
    return THEMES.get(theme_id, THEMES[DEFAULT_THEME])["squads"]


# ---------------------------------------------------------------------------
# BFStats API Wrapper
# ---------------------------------------------------------------------------

class BFStatsClient:
    def __init__(self, dll_path=None):
        if dll_path is None:
            base_dir = get_app_base_dir()
            dll_dir = os.path.join(base_dir, BFSTATS_DLL_DIR_NAME)
            dll_path = os.path.join(dll_dir, BFSTATS_DLL_NAME)
        else:
            dll_dir = os.path.dirname(os.path.abspath(dll_path))

        if not os.path.exists(dll_path):
            raise FileNotFoundError(
                f"找不到 {BFSTATS_DLL_NAME}。\n"
                f"请确认 DLL 位于:\n{dll_path}"
            )

        # Python 3.8+ 在 Windows 上加载 DLL 依赖时，需要把 DLL 所在目录加入搜索路径。
        # 如果 BFStats.dll 还依赖其他 DLL，也建议一起放在 dll 文件夹里。
        if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
            os.add_dll_directory(dll_dir)

        self.dll = ctypes.CDLL(dll_path)

        self.dll.bf6_query_multiple.argtypes = [
            ctypes.POINTER(ctypes.c_char_p),
            ctypes.c_int,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_void_p)
        ]
        self.dll.bf6_query_multiple.restype = ctypes.c_int

        self.dll.bf6_free.argtypes = [ctypes.c_void_p]
        self.dll.bf6_free.restype = None

        self.dll.bf6_version.argtypes = []
        self.dll.bf6_version.restype = ctypes.c_char_p

    def version(self):
        v = self.dll.bf6_version()
        return v.decode("utf-8") if v else "unknown"

    def query_multiple(self, names, platform):
        if not names:
            raise ValueError("玩家列表为空")

        encoded_names = [name.encode("utf-8") for name in names]
        arr = (ctypes.c_char_p * len(encoded_names))(*encoded_names)

        out = ctypes.c_void_p(None)

        ret = self.dll.bf6_query_multiple(
            arr,
            len(encoded_names),
            int(platform),
            ctypes.byref(out)
        )

        if not out.value:
            err = BF6_ERROR_NAMES.get(ret, f"未知错误 {ret}")
            raise RuntimeError(f"接口调用失败: {err}")

        try:
            raw = ctypes.string_at(out.value).decode("utf-8")
        finally:
            self.dll.bf6_free(out)

        data = json.loads(raw)

        # 只要有一个成功，C API 会返回 BF6_OK。
        # 如果全部失败，ret 可能是负数，但 out_json 仍可能有失败列表。
        if ret != BF6_OK and not any(item.get("ok") for item in data):
            err = BF6_ERROR_NAMES.get(ret, f"未知错误 {ret}")
            raise RuntimeError(f"全部玩家查询失败: {err}")

        return data

def get_app_base_dir():
    """
    获取程序基础目录。

    普通运行:
        使用当前 .py 文件所在目录。

    PyInstaller 打包后:
        使用 exe 所在目录。
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)

    return os.path.dirname(os.path.abspath(__file__))

def convert_api_result_to_players(api_result, offset):
    players = []
    failures = []

    for item in api_result:
        name = item.get("name", "")

        if not item.get("ok"):
            err_code = item.get("error")
            err_name = BF6_ERROR_NAMES.get(err_code, f"未知错误 {err_code}")
            failures.append({
                "name": name,
                "error": err_name
            })
            continue

        d = item.get("data", {})

        user_name = d.get("userName") or name
        kd = float(d.get("killDeath") or 0)
        kpm_raw = float(d.get("killsPerMinute") or 0)
        kpm_adjusted = round(kpm_raw * offset, 3)

        players.append({
            "name": user_name,
            "kd": round(kd, 3),
            "kpm_raw": round(kpm_raw, 3),
            "kpm_adjusted": kpm_adjusted
        })

    return players, failures


class StatsFetchWorker(QThread):
    success = pyqtSignal(list, list, str)
    failed = pyqtSignal(str)

    def __init__(self, names, platform, offset, parent=None):
        super().__init__(parent)
        self.names = names
        self.platform = platform
        self.offset = offset

    def run(self):
        try:
            client = BFStatsClient()
            version = client.version()
            api_result = client.query_multiple(self.names, self.platform)
            players, failures = convert_api_result_to_players(api_result, self.offset)

            if not players:
                raise RuntimeError("没有任何玩家查询成功，无法继续分队。")

            self.success.emit(players, failures, version)

        except Exception as e:
            self.failed.emit(str(e))


# ---------------------------------------------------------------------------
# Mode Card
# ---------------------------------------------------------------------------

class ModeCard(QPushButton):
    def __init__(self, title, desc, mode_id):
        super().__init__()
        self.mode_id = mode_id
        self.setCheckable(True)
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._theme = THEMES[DEFAULT_THEME]
        self._update_style()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_title = QLabel(title)
        lbl_title.setFont(QFont("Microsoft YaHei UI", 22, QFont.Weight.Bold))
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet("background: transparent; border: none;")

        lbl_desc = QLabel(desc)
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_desc.setWordWrap(True)
        self._desc_label = lbl_desc

        layout.addWidget(lbl_title)
        layout.addSpacing(10)
        layout.addWidget(lbl_desc)

        self._update_desc_style()

    def _update_desc_style(self):
        self._desc_label.setStyleSheet(
            f"background: transparent; border: none; "
            f"color: {self._theme['text_sub']}; font-size: 15px;"
        )

    def set_theme(self, theme):
        self._theme = theme
        self._update_style()
        self._update_desc_style()

    def _update_style(self):
        t = self._theme
        if self.isChecked():
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {t["card_alt"]};
                    color: #ffffff;
                    border: 2px solid {t["accent"]};
                    border-radius: 14px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {t["card"]};
                    color: {t["text"]};
                    border: 2px solid {t["border"]};
                    border-radius: 14px;
                }}
                QPushButton:hover {{
                    border-color: {t["accent"]};
                    background: {t["btn"]};
                }}
            """)

    def setChecked(self, checked):
        super().setChecked(checked)
        self._update_style()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self._update_style()


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("BF6 Team Balancer")
        self.setMinimumSize(1100, 750)

        config = load_config()
        self.current_theme = config.get("theme", DEFAULT_THEME)
        if self.current_theme not in THEMES:
            self.current_theme = DEFAULT_THEME

        self.setStyleSheet(build_stylesheet(THEMES[self.current_theme]))

        self.players_data = None
        self.players = None
        self.report = None
        self.alloc_mode = "balanced"
        self.fetch_worker = None

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 16, 20, 16)

        nav = QHBoxLayout()
        nav.setSpacing(8)

        self.btn_prev = QPushButton("< 上一步")
        self.btn_prev.setFixedWidth(100)
        self.btn_prev.setEnabled(False)

        self.btn_next = QPushButton("下一步 >")
        self.btn_next.setObjectName("primary")
        self.btn_next.setFixedWidth(120)
        self.btn_next.setEnabled(False)

        self.step_indicators = []
        self.step_connectors = []

        indicator_row = QHBoxLayout()
        indicator_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        indicator_row.setSpacing(4)

        t = THEMES[self.current_theme]
        for i in range(6):
            dot = QLabel(f" {i + 1} ")
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dot.setFixedSize(42, 42)
            dot.setStyleSheet(
                f"background: {t['step_pending']}; "
                f"border-radius: 21px; font-weight: bold; "
                f"color: {t['text_disabled']}; font-size: 17px;"
            )
            self.step_indicators.append(dot)
            indicator_row.addWidget(dot)

            if i < 5:
                line = QLabel("---")
                line.setStyleSheet(
                    f"color: {t['step_connector']}; background: transparent;"
                )
                self.step_connectors.append(line)
                indicator_row.addWidget(line)

        nav.addWidget(self.btn_prev)
        nav.addStretch()
        nav.addLayout(indicator_row)
        nav.addStretch()
        nav.addWidget(self.btn_next)

        main_layout.addLayout(nav)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, stretch=1)

        self.page_import = self._build_page_import()
        self.page_alloc = self._build_page_alloc_mode()
        self.page_mode = self._build_page_mode()
        self.page_custom = self._build_page_custom()
        self.page_result = self._build_page_result()
        self.page_history = self._build_page_history()
        self.page_ops = self._build_page_ops()

        self.stack.addWidget(self.page_import)   # 0
        self.stack.addWidget(self.page_alloc)    # 1
        self.stack.addWidget(self.page_mode)     # 2
        self.stack.addWidget(self.page_custom)   # 3
        self.stack.addWidget(self.page_result)   # 4
        self.stack.addWidget(self.page_history)  # 5
        self.stack.addWidget(self.page_ops)      # 6

        self.btn_prev.clicked.connect(self._go_prev)

        self.current_page = 0
        self._next_handler = self._go_next
        self.btn_next.clicked.connect(lambda: self._next_handler())

        self._update_nav()

    # -----------------------------------------------------------------------
    # Page 1: API Fetch
    # -----------------------------------------------------------------------

    def _build_page_import(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)

        top_row = QHBoxLayout()

        title = QLabel("获取玩家数据")
        title.setObjectName("title")
        top_row.addWidget(title)
        top_row.addStretch()

        theme_label = QLabel("主题:")
        theme_label.setStyleSheet("color: #9998aa; font-size: 14px;")
        top_row.addWidget(theme_label)

        self.theme_combo = QComboBox()
        self.theme_combo.setFixedWidth(150)
        for tid, theme in THEMES.items():
            self.theme_combo.addItem(theme["name"], tid)

        idx = list(THEMES.keys()).index(self.current_theme)
        self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        top_row.addWidget(self.theme_combo)

        layout.addLayout(top_row)

        subtitle = QLabel("输入玩家 ID，每行一个，点击获取后自动查询 KD / KPM")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        input_frame = QFrame()
        input_frame.setStyleSheet(
            f"QFrame {{ background: {THEMES[self.current_theme]['card']}; "
            f"border-radius: 10px; padding: 12px; }}"
        )
        input_layout = QVBoxLayout(input_frame)

        self.names_edit = QTextEdit()
        self.names_edit.setPlaceholderText(
            "例如:\n"
            "PlayerOne\n"
            "PlayerTwo\n"
            "PlayerThree"
        )
        self.names_edit.setMinimumHeight(120)
        input_layout.addWidget(self.names_edit)

        option_row = QHBoxLayout()

        option_row.addWidget(QLabel("平台:"))
        self.platform_combo = QComboBox()
        self.platform_combo.addItem("PC", BF6_PLATFORM_PC)
        self.platform_combo.addItem("EA", BF6_PLATFORM_EA)
        self.platform_combo.addItem("PSN", BF6_PLATFORM_PSN)
        self.platform_combo.addItem("XBOX", BF6_PLATFORM_XBOX)
        self.platform_combo.setCurrentIndex(1)
        self.platform_combo.setFixedWidth(120)
        option_row.addWidget(self.platform_combo)

        option_row.addSpacing(20)

        option_row.addWidget(QLabel("KPM 偏移系数:"))
        self.offset_spin = QDoubleSpinBox()
        self.offset_spin.setRange(0.1, 5.0)
        self.offset_spin.setValue(1.313)
        self.offset_spin.setSingleStep(0.01)
        self.offset_spin.setDecimals(3)
        self.offset_spin.setFixedWidth(100)
        option_row.addWidget(self.offset_spin)

        option_row.addWidget(QLabel("推荐值 1.313"))

        option_row.addStretch()

        self.player_count_label = QLabel("")
        self.player_count_label.setStyleSheet(
            "color: #8aaa8a; font-weight: bold; background: transparent;"
        )
        option_row.addWidget(self.player_count_label)

        self.btn_fetch = QPushButton("获取数据")
        self.btn_fetch.setObjectName("primary")
        self.btn_fetch.setFixedWidth(120)
        self.btn_fetch.clicked.connect(self._fetch_players_from_api)
        option_row.addWidget(self.btn_fetch)

        input_layout.addLayout(option_row)

        self.fetch_status_label = QLabel("等待输入玩家 ID")
        self.fetch_status_label.setObjectName("hint")
        input_layout.addWidget(self.fetch_status_label)

        layout.addWidget(input_frame)

        self.player_table = QTableWidget()
        self.player_table.setColumnCount(4)
        self.player_table.setHorizontalHeaderLabels([
            "昵称",
            "KD",
            "原始KPM",
            "调整后KPM"
        ])
        self.player_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.player_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.player_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.player_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self.player_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.player_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.player_table.setAlternatingRowColors(True)
        self.player_table.verticalHeader().setVisible(False)

        layout.addWidget(self.player_table, stretch=1)

        return page

    def _fetch_players_from_api(self):
        text = self.names_edit.toPlainText().strip()

        if not text:
            QMessageBox.warning(self, "提示", "请先输入玩家 ID，每行一个。")
            return

        raw_names = [line.strip() for line in text.splitlines() if line.strip()]

        names = []
        seen = set()
        for name in raw_names:
            if name not in seen:
                names.append(name)
                seen.add(name)

        if not names:
            QMessageBox.warning(self, "提示", "玩家 ID 列表为空。")
            return

        platform = self.platform_combo.currentData()
        offset = self.offset_spin.value()

        self.btn_fetch.setEnabled(False)
        self.btn_next.setEnabled(False)
        self.fetch_status_label.setText(
            f"正在查询 {len(names)} 名玩家，请稍候..."
        )
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        self.fetch_worker = StatsFetchWorker(names, platform, offset, self)
        self.fetch_worker.success.connect(self._on_fetch_success)
        self.fetch_worker.failed.connect(self._on_fetch_failed)
        self.fetch_worker.finished.connect(self._on_fetch_finished)
        self.fetch_worker.start()

    def _on_fetch_success(self, players_data, failures, dll_version):
        self.players_data = players_data
        self.players = load_players({"players": self.players_data})

        self.player_count_label.setText(f"共 {len(self.players)} 人")
        self._refresh_player_table()
        self._refresh_binding_combos()

        if failures:
            fail_lines = [
                f"{f['name']}: {f['error']}"
                for f in failures[:8]
            ]
            more = ""
            if len(failures) > 8:
                more = f"\n... 还有 {len(failures) - 8} 个失败"

            self.fetch_status_label.setText(
                f"bfstats v{dll_version} | 成功 {len(players_data)} 人，"
                f"失败 {len(failures)} 人。\n"
                + "\n".join(fail_lines)
                + more
            )
        else:
            self.fetch_status_label.setText(
                f"bfstats v{dll_version} | 成功获取 {len(players_data)} 名玩家数据。"
            )

        self.btn_next.setEnabled(True)

    def _on_fetch_failed(self, message):
        QMessageBox.critical(self, "查询失败", message)
        self.fetch_status_label.setText("查询失败，请检查网络、DLL、玩家 ID 或平台。")
        self.btn_next.setEnabled(False)

    def _on_fetch_finished(self):
        self.btn_fetch.setEnabled(True)
        QApplication.restoreOverrideCursor()

    def _refresh_player_table(self):
        self.player_table.setRowCount(len(self.players_data or []))

        for i, p in enumerate(self.players_data or []):
            self.player_table.setItem(i, 0, QTableWidgetItem(str(p["name"])))
            self.player_table.setItem(i, 1, QTableWidgetItem(str(p["kd"])))
            self.player_table.setItem(i, 2, QTableWidgetItem(str(p["kpm_raw"])))
            self.player_table.setItem(i, 3, QTableWidgetItem(str(p["kpm_adjusted"])))

    # -----------------------------------------------------------------------
    # Page 2: Alloc Mode
    # -----------------------------------------------------------------------

    def _build_page_alloc_mode(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)

        title = QLabel("选择分配方式")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("均衡模式按实力分配，随机模式纯随机打乱")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        self.card_balanced = ModeCard(
            "⚖️ 均衡分配",
            "根据 KD / KPM 加权得分\n贪心算法平衡双方实力\n适合正式内战",
            "balanced"
        )
        self.card_random = ModeCard(
            "🎲 随机分配",
            "完全随机打乱玩家\n不考虑实力数据\n适合娱乐局 / 测试",
            "random"
        )

        self.card_balanced.setChecked(True)

        self.card_balanced.clicked.connect(lambda: self._select_alloc_mode("balanced"))
        self.card_random.clicked.connect(lambda: self._select_alloc_mode("random"))

        cards_layout.addWidget(self.card_balanced)
        cards_layout.addWidget(self.card_random)

        layout.addLayout(cards_layout, stretch=1)

        return page

    def _select_alloc_mode(self, mode):
        self.alloc_mode = mode
        self.card_balanced.setChecked(mode == "balanced")
        self.card_random.setChecked(mode == "random")
        self._update_nav()

    # -----------------------------------------------------------------------
    # Page 3: Game Mode
    # -----------------------------------------------------------------------

    def _build_page_mode(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)

        title = QLabel("选择游戏模式")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("不同模式会影响 KD 和 KPM 的权重分配")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        self.card_conquest = ModeCard(
            "征服 Conquest",
            "更看重 KD（生存能力）\n权重: KD 70% / KPM 30%\n最多 64 人 (16 队)",
            0
        )
        self.card_breakthrough = ModeCard(
            "突破 Breakthrough",
            "更看重 KPM（击杀效率）\n权重: KPM 70% / KD 30%\n最多 48 人 (12 队)",
            1
        )

        self.card_conquest.setChecked(True)

        self.card_conquest.clicked.connect(lambda: self._select_mode(0))
        self.card_breakthrough.clicked.connect(lambda: self._select_mode(1))

        cards_layout.addWidget(self.card_conquest)
        cards_layout.addWidget(self.card_breakthrough)

        layout.addLayout(cards_layout, stretch=1)

        return page

    def _select_mode(self, mode_id):
        self.card_conquest.setChecked(mode_id == 0)
        self.card_breakthrough.setChecked(mode_id == 1)

    # -----------------------------------------------------------------------
    # Page 4: Custom Squad
    # -----------------------------------------------------------------------

    def _build_page_custom(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)

        title = QLabel("自定义小队（可选）")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("绑定的两人将被分配到同一阵营的同一个小队。每人最多被选一次。")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        btn_add = QPushButton("+ 添加绑定")
        btn_add.setFixedWidth(120)
        btn_add.clicked.connect(self._add_binding_row)
        layout.addWidget(btn_add)

        self.binding_container = QWidget()
        self.binding_layout = QVBoxLayout(self.binding_container)
        self.binding_layout.setSpacing(8)
        layout.addWidget(self.binding_container, stretch=1)

        hint = QLabel("如果不设绑定，直接点「查看结果」即可")
        hint.setObjectName("hint")
        layout.addWidget(hint)

        return page

    def _add_binding_row(self):
        if self.players is None:
            return

        row_widget = QFrame()
        row_widget.setStyleSheet(
            "QFrame { background: #3d3d50; border-radius: 8px; padding: 10px; }"
        )

        row_layout = QHBoxLayout(row_widget)

        cb1 = QComboBox()
        cb2 = QComboBox()

        names = [p.name for p in self.players]
        cb1.addItems(["-- 选择玩家 --"] + names)
        cb2.addItems(["-- 选择玩家 --"] + names)

        cb1.setMinimumWidth(200)
        cb2.setMinimumWidth(200)

        btn_remove = QPushButton("X")
        btn_remove.setFixedSize(30, 30)

        row_layout.addWidget(QLabel("玩家A:"))
        row_layout.addWidget(cb1, stretch=1)
        row_layout.addWidget(QLabel("+"))
        row_layout.addWidget(QLabel("玩家B:"))
        row_layout.addWidget(cb2, stretch=1)
        row_layout.addWidget(btn_remove)

        row_data = {
            "widget": row_widget,
            "cb1": cb1,
            "cb2": cb2
        }

        self.binding_rows = getattr(self, "binding_rows", [])
        self.binding_rows.append(row_data)
        self.binding_layout.addWidget(row_widget)

        btn_remove.clicked.connect(lambda: self._remove_binding_row(row_data))

    def _remove_binding_row(self, row_data):
        self.binding_rows.remove(row_data)
        row_data["widget"].deleteLater()

    def _refresh_binding_combos(self):
        if not self.players:
            return

        names = [p.name for p in self.players]

        for row in getattr(self, "binding_rows", []):
            row["cb1"].clear()
            row["cb2"].clear()
            row["cb1"].addItems(["-- 选择玩家 --"] + names)
            row["cb2"].addItems(["-- 选择玩家 --"] + names)

    # -----------------------------------------------------------------------
    # Page 5: Result
    # -----------------------------------------------------------------------

    def _build_page_result(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        self.balance_label = QLabel("请先完成分队")
        self.balance_label.setObjectName("balance_summary")
        self.balance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.balance_label)

        columns = QHBoxLayout()
        columns.setSpacing(12)

        left_frame = QFrame()
        left_frame.setStyleSheet("QFrame { background: #333346; border-radius: 10px; }")
        left_layout = QVBoxLayout(left_frame)
        left_layout.setSpacing(6)

        lbl_a = QLabel("北约")
        lbl_a.setFont(QFont("Microsoft YaHei UI", 16, QFont.Weight.Bold))
        lbl_a.setStyleSheet("color: #9aadd4; background: transparent;")
        left_layout.addWidget(lbl_a)

        self.team_a_table = self._create_team_table()
        left_layout.addWidget(self.team_a_table, stretch=1)
        columns.addWidget(left_frame, stretch=1)

        right_frame = QFrame()
        right_frame.setStyleSheet("QFrame { background: #333346; border-radius: 10px; }")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setSpacing(6)

        lbl_b = QLabel("和平军团")
        lbl_b.setFont(QFont("Microsoft YaHei UI", 16, QFont.Weight.Bold))
        lbl_b.setStyleSheet("color: #d4a0a0; background: transparent;")
        right_layout.addWidget(lbl_b)

        self.team_b_table = self._create_team_table()
        right_layout.addWidget(self.team_b_table, stretch=1)
        columns.addWidget(right_frame, stretch=1)

        layout.addLayout(columns, stretch=3)

        bottom = QHBoxLayout()
        bottom.setSpacing(12)

        reserve_frame = QFrame()
        reserve_frame.setStyleSheet(
            "QFrame { background: #333346; border-radius: 10px; }"
        )
        reserve_layout = QVBoxLayout(reserve_frame)
        reserve_layout.setSpacing(4)

        lbl_r = QLabel("候补队伍")
        lbl_r.setFont(QFont("Microsoft YaHei UI", 14, QFont.Weight.Bold))
        lbl_r.setStyleSheet("color: #c8b88a; background: transparent;")
        reserve_layout.addWidget(lbl_r)

        self.reserve_table = QTableWidget()
        self.reserve_table.setColumnCount(4)
        self.reserve_table.setHorizontalHeaderLabels(["#", "昵称", "KD", "KPM"])
        self.reserve_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Fixed
        )
        self.reserve_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.reserve_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.reserve_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self.reserve_table.setColumnWidth(0, 36)
        self.reserve_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.reserve_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.reserve_table.verticalHeader().setVisible(False)
        self.reserve_table.setMaximumHeight(200)

        reserve_layout.addWidget(self.reserve_table)
        bottom.addWidget(reserve_frame, stretch=1)

        self.warning_label = QLabel("")
        self.warning_label.setObjectName("warning")
        self.warning_label.setFixedWidth(280)
        self.warning_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        bottom.addWidget(self.warning_label)

        layout.addLayout(bottom, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_copy = QPushButton("📋 复制结果")
        btn_copy.setFixedWidth(140)
        btn_copy.clicked.connect(self._copy_result)

        btn_history = QPushButton("📜 历史记录")
        btn_history.setFixedWidth(140)
        btn_history.clicked.connect(self._show_history)

        btn_row.addStretch()
        btn_row.addWidget(btn_copy)
        btn_row.addWidget(btn_history)

        layout.addLayout(btn_row)

        return page

    def _create_team_table(self):
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["小队", "昵称", "KD", "KPM", "得分"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        table.setColumnWidth(0, 50)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.verticalHeader().setVisible(False)
        return table

    # -----------------------------------------------------------------------
    # History
    # -----------------------------------------------------------------------

    def _build_page_history(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        title = QLabel("历史记录")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("点击记录查看详情，或直接点「下一步」跳过")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            "#",
            "时间",
            "分配模式",
            "游戏模式",
            "人数"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.setColumnWidth(0, 40)
        self.history_table.setMaximumHeight(200)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.clicked.connect(self._on_history_row_clicked)
        layout.addWidget(self.history_table)

        detail_columns = QHBoxLayout()
        detail_columns.setSpacing(12)

        left_frame = QFrame()
        left_frame.setStyleSheet("QFrame { background: #333346; border-radius: 10px; }")
        left_layout = QVBoxLayout(left_frame)
        left_layout.setSpacing(6)

        self.hist_lbl_a = QLabel("阵营A")
        self.hist_lbl_a.setFont(QFont("Microsoft YaHei UI", 16, QFont.Weight.Bold))
        self.hist_lbl_a.setStyleSheet("color: #9aadd4; background: transparent;")
        left_layout.addWidget(self.hist_lbl_a)

        self.hist_team_a_table = self._create_history_team_table()
        left_layout.addWidget(self.hist_team_a_table, stretch=1)
        detail_columns.addWidget(left_frame, stretch=1)

        right_frame = QFrame()
        right_frame.setStyleSheet("QFrame { background: #333346; border-radius: 10px; }")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setSpacing(6)

        self.hist_lbl_b = QLabel("阵营B")
        self.hist_lbl_b.setFont(QFont("Microsoft YaHei UI", 16, QFont.Weight.Bold))
        self.hist_lbl_b.setStyleSheet("color: #d4a0a0; background: transparent;")
        right_layout.addWidget(self.hist_lbl_b)

        self.hist_team_b_table = self._create_history_team_table()
        right_layout.addWidget(self.hist_team_b_table, stretch=1)
        detail_columns.addWidget(right_frame, stretch=1)

        layout.addLayout(detail_columns, stretch=1)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(12)

        self.hist_reserve_label = QLabel("")
        self.hist_reserve_label.setStyleSheet("color: #c8b88a; font-size: 15px;")

        self.hist_balance_label = QLabel("")
        self.hist_balance_label.setStyleSheet("color: #a8c8a8; font-size: 15px;")

        bottom_row.addWidget(self.hist_reserve_label, stretch=1)
        bottom_row.addWidget(self.hist_balance_label)

        layout.addLayout(bottom_row)

        return page

    def _create_history_team_table(self):
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["小队", "昵称"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.setColumnWidth(0, 50)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        return table

    def _on_history_row_clicked(self, index):
        row = index.row()
        history = load_history()

        if row >= len(history):
            return

        rec = history[row]
        self._display_history_detail(rec)

    def _display_history_detail(self, rec):
        self.hist_lbl_a.setText(rec["team_a"]["name"])
        self.hist_lbl_b.setText(rec["team_b"]["name"])

        squad_colors = get_theme_squad_colors(self.current_theme)

        for team_key, table in [
            ("team_a", self.hist_team_a_table),
            ("team_b", self.hist_team_b_table)
        ]:
            t = rec[team_key]
            rows = []

            for sq in t["squads"]:
                for name in sq["members"]:
                    rows.append((sq["id"], name))

            table.setRowCount(len(rows))

            for i, (sid, name) in enumerate(rows):
                item_sid = QTableWidgetItem(str(sid))
                item_name = QTableWidgetItem(name)

                color = QColor(squad_colors[(sid - 1) % len(squad_colors)])
                item_sid.setBackground(color)
                item_name.setBackground(color)

                table.setItem(i, 0, item_sid)
                table.setItem(i, 1, item_name)

        if rec["reserves"]:
            self.hist_reserve_label.setText(
                f'候补: {"、".join(rec["reserves"])}'
            )
        else:
            self.hist_reserve_label.setText("无候补")

        bl = rec["balance"]
        self.hist_balance_label.setText(
            f'KD差{bl["kd_diff"]} | '
            f'KPM差{bl["kpm_diff"]} | '
            f'总分差{bl["score_diff"]}'
        )

    def _refresh_history_table(self):
        history = load_history()

        self.history_table.setRowCount(len(history))

        for i, rec in enumerate(history):
            alloc = ALLOC_MODE_NAMES.get(rec["alloc_mode"], rec["alloc_mode"])
            game = GAME_MODE_NAMES.get(rec["game_mode"], rec["game_mode"])
            total = rec["team_a"]["total_players"] + rec["team_b"]["total_players"]

            self.history_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.history_table.setItem(i, 1, QTableWidgetItem(rec["timestamp"]))
            self.history_table.setItem(i, 2, QTableWidgetItem(alloc))
            self.history_table.setItem(i, 3, QTableWidgetItem(game))
            self.history_table.setItem(i, 4, QTableWidgetItem(f"{total}人"))

    def _show_history(self):
        history = load_history()

        if not history:
            QMessageBox.information(self, "历史记录", "暂无历史记录")
            return

        self._refresh_history_table()
        self.current_page = 5
        self.stack.setCurrentIndex(5)
        self._update_nav()

    # -----------------------------------------------------------------------
    # Ops
    # -----------------------------------------------------------------------

    def _build_page_ops(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)

        title = QLabel("操作")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("选择下一步操作")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        btn_reimport = QPushButton("🔄 重新获取数据")
        btn_reimport.setMinimumHeight(60)
        btn_reimport.setFont(QFont("Microsoft YaHei UI", 18))
        btn_reimport.clicked.connect(self._reset_to_import)

        btn_realloc = QPushButton("🔀 重新分配")
        btn_realloc.setMinimumHeight(60)
        btn_realloc.setFont(QFont("Microsoft YaHei UI", 18))
        btn_realloc.clicked.connect(self._reset_to_alloc)

        btn_exit = QPushButton("❌ 退出")
        btn_exit.setObjectName("exit_btn")
        btn_exit.setMinimumHeight(60)
        btn_exit.setFont(QFont("Microsoft YaHei UI", 18))
        btn_exit.clicked.connect(self.close)

        layout.addStretch()
        layout.addWidget(btn_reimport)
        layout.addSpacing(12)
        layout.addWidget(btn_realloc)
        layout.addSpacing(12)
        layout.addWidget(btn_exit)
        layout.addStretch()

        return page

    # -----------------------------------------------------------------------
    # Navigation
    # -----------------------------------------------------------------------

    def _go_prev(self):
        if self.current_page > 0:
            if self.current_page == 6:
                self.current_page = 4
            elif self.current_page == 5:
                self.current_page = 4
            elif self.current_page == 3 and self.alloc_mode == "random":
                self.current_page = 1
            else:
                self.current_page -= 1

            self.stack.setCurrentIndex(self.current_page)
            self._update_nav()

    def _go_next(self):
        if self.current_page == 0:
            if self.players is None:
                QMessageBox.warning(self, "提示", "请先获取玩家数据")
                return
            self.current_page = 1

        elif self.current_page == 1:
            if self.alloc_mode == "random":
                self.current_page = 3
            else:
                self.current_page = 2

        elif self.current_page == 2:
            self.current_page = 3

        elif self.current_page == 3:
            self._run_algorithm()
            if self.report is None:
                return
            self.current_page = 4

        elif self.current_page == 4:
            self.current_page = 6

        elif self.current_page == 5:
            self.current_page = 6

        self.stack.setCurrentIndex(self.current_page)
        self._update_nav()

    def _update_nav(self):
        self.btn_prev.setEnabled(self.current_page > 0 and self.current_page < 6)

        if self.current_page >= 6:
            self.btn_prev.setEnabled(False)
            self.btn_next.setEnabled(False)
            self.btn_next.setText("下一步 >")
            self.btn_next.setObjectName("primary")
            self._next_handler = self._go_next

        elif self.current_page == 5:
            self.btn_next.setText("下一步 >")
            self.btn_next.setObjectName("primary")
            self.btn_next.setEnabled(True)
            self._next_handler = self._go_next

        elif self.current_page == 4:
            self.btn_next.setText("下一步 >")
            self.btn_next.setObjectName("primary")
            self.btn_next.setEnabled(True)
            self._next_handler = self._go_next

        else:
            self.btn_next.setText(
                "查看结果" if self.current_page == 3 else "下一步 >"
            )
            self.btn_next.setObjectName("primary")
            self._next_handler = self._go_next
            self.btn_next.setEnabled(
                self.current_page != 0 or self.players is not None
            )

        self.btn_next.style().unpolish(self.btn_next)
        self.btn_next.style().polish(self.btn_next)

        page_to_step = {
            0: 0,
            1: 1,
            2: 2,
            3: 3,
            4: 4,
            5: 4,
            6: 5
        }
        current_step = page_to_step.get(self.current_page, 0)

        t = THEMES[self.current_theme]

        for i, dot in enumerate(self.step_indicators):
            is_skipped = (i == 2 and self.alloc_mode == "random")

            if is_skipped:
                dot.setStyleSheet(
                    f"background: {t['step_skipped']}; "
                    f"border-radius: 21px; font-weight: bold; "
                    f"color: {t['text_disabled']}; font-size: 17px; "
                    f"text-decoration: line-through;"
                )
            elif i == current_step:
                dot.setStyleSheet(
                    f"background: {t['step_active']}; "
                    f"border-radius: 21px; font-weight: bold; "
                    f"color: #ffffff; font-size: 17px;"
                )
            elif i < current_step:
                dot.setStyleSheet(
                    f"background: {t['step_done']}; "
                    f"border-radius: 21px; font-weight: bold; "
                    f"color: #ffffff; font-size: 17px;"
                )
            else:
                dot.setStyleSheet(
                    f"background: {t['step_pending']}; "
                    f"border-radius: 21px; font-weight: bold; "
                    f"color: {t['text_disabled']}; font-size: 17px;"
                )

    # -----------------------------------------------------------------------
    # Theme
    # -----------------------------------------------------------------------

    def _on_theme_changed(self, index):
        theme_id = self.theme_combo.currentData()

        if theme_id and theme_id in THEMES:
            self.current_theme = theme_id
            t = THEMES[theme_id]

            self.setStyleSheet(build_stylesheet(t))

            for card in [
                self.card_balanced,
                self.card_random,
                self.card_conquest,
                self.card_breakthrough
            ]:
                card.set_theme(t)

            for line in self.step_connectors:
                line.setStyleSheet(
                    f"color: {t['step_connector']}; background: transparent;"
                )

            self._update_nav()

            config = load_config()
            config["theme"] = theme_id
            save_config(config)

    # -----------------------------------------------------------------------
    # Algorithm
    # -----------------------------------------------------------------------

    def _run_algorithm(self):
        if not self.players:
            QMessageBox.warning(self, "提示", "没有玩家数据，请先获取玩家数据")
            return

        bindings = []
        used_names = set()

        for row in getattr(self, "binding_rows", []):
            a = row["cb1"].currentText()
            b = row["cb2"].currentText()

            if a.startswith("--") or b.startswith("--"):
                continue

            if a == b:
                QMessageBox.warning(self, "提示", f"不能绑定同一个玩家: {a}")
                return

            if a in used_names or b in used_names:
                QMessageBox.warning(self, "提示", f"玩家已被绑定: {a} 或 {b}")
                return

            used_names.add(a)
            used_names.add(b)

            bindings.append({
                "player_a": a,
                "player_b": b
            })

        if self.alloc_mode == "random":
            game_mode = "conquest"
        else:
            game_mode = "conquest" if self.card_conquest.isChecked() else "breakthrough"

        try:
            if self.alloc_mode == "random":
                ta, tb, rv = random_allocate(self.players, bindings, game_mode)
            else:
                ta, tb, rv = allocate_teams(self.players, bindings, game_mode)

            self.report = compute_balance_report(ta, tb, rv, game_mode)

            save_record(self.report, self.alloc_mode)

            self._display_report()

        except (ValueError, KeyError) as e:
            QMessageBox.critical(self, "错误", f"分队失败:\n{e}")
            self.report = None

    def _display_report(self):
        r = self.report
        bl = r["balance"]
        mode_name = GAME_MODE_NAMES.get(r["game_mode"], r["game_mode"])

        if self.alloc_mode == "random":
            self.balance_label.setText(
                f"[{mode_name} · 随机分配]  "
                f"KD差距: {bl['kd_diff']}  |  "
                f"KPM差距: {bl['kpm_diff']}  |  "
                f"总分差距: {bl['score_diff']}"
            )
        else:
            self.balance_label.setText(
                f"[{mode_name}]  "
                f"KD差距: {bl['kd_diff']}  |  "
                f"KPM差距: {bl['kpm_diff']}  |  "
                f"总分差距: {bl['score_diff']}"
            )

        self._fill_team_table(self.team_a_table, r["team_a"], r["game_mode"])
        self._fill_team_table(self.team_b_table, r["team_b"], r["game_mode"])

        rv = r["reserves"]
        self.reserve_table.setRowCount(len(rv["members"]))

        for i, m in enumerate(rv["members"]):
            self.reserve_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.reserve_table.setItem(i, 1, QTableWidgetItem(m["name"]))
            self.reserve_table.setItem(i, 2, QTableWidgetItem(str(m["kd"])))
            self.reserve_table.setItem(i, 3, QTableWidgetItem(str(m["kpm"])))

        if not rv["members"]:
            self.reserve_table.setRowCount(1)
            self.reserve_table.setItem(0, 0, QTableWidgetItem(""))
            self.reserve_table.setItem(0, 1, QTableWidgetItem("无候补"))
            self.reserve_table.setItem(0, 2, QTableWidgetItem(""))
            self.reserve_table.setItem(0, 3, QTableWidgetItem(""))

        if self.alloc_mode == "random":
            self.warning_label.setText("🎲 随机分配，均衡性仅供参考")
        elif r["warnings"]:
            self.warning_label.setText("⚠ " + "\n".join(r["warnings"]))
        else:
            self.warning_label.setText("")

    def _fill_team_table(self, table, team_data, game_mode):
        cfg = GAME_MODES[game_mode]
        squad_colors = get_theme_squad_colors(self.current_theme)

        rows = []

        for sq in team_data["squads"]:
            for p in sq["members"]:
                kd = p["kd"]
                kpm = p["kpm"]
                score = round(
                    kd * cfg["kd_weight"] +
                    kpm * cfg["kpm_weight"],
                    2
                )
                rows.append((
                    sq["squad_id"],
                    p["name"],
                    str(kd),
                    str(kpm),
                    str(score)
                ))

        table.setRowCount(len(rows))

        for i, (sid, name, kd, kpm, score) in enumerate(rows):
            item_sid = QTableWidgetItem(str(sid))
            item_name = QTableWidgetItem(name)
            item_kd = QTableWidgetItem(kd)
            item_kpm = QTableWidgetItem(kpm)
            item_score = QTableWidgetItem(score)

            color = QColor(squad_colors[(sid - 1) % len(squad_colors)])

            for item in [
                item_sid,
                item_name,
                item_kd,
                item_kpm,
                item_score
            ]:
                item.setBackground(color)

            table.setItem(i, 0, item_sid)
            table.setItem(i, 1, item_name)
            table.setItem(i, 2, item_kd)
            table.setItem(i, 3, item_kpm)
            table.setItem(i, 4, item_score)

    # -----------------------------------------------------------------------
    # Copy Result
    # -----------------------------------------------------------------------

    def _copy_result(self):
        if not self.report:
            return

        r = self.report
        bl = r["balance"]

        mode_name = GAME_MODE_NAMES.get(r["game_mode"], r["game_mode"])
        alloc_name = ALLOC_MODE_NAMES.get(self.alloc_mode, self.alloc_mode)

        from datetime import datetime
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")

        lines = [
            f"=== BF6 分队结果 ({ts}) ===",
            f"模式: {alloc_name} · {mode_name}",
            "",
        ]

        for team_key in ["team_a", "team_b"]:
            t = r[team_key]
            lines.append(
                f'【{t["name"]}】({t["total_players"]}人, {t["num_squads"]}小队)'
            )

            for sq in t["squads"]:
                members = "、".join(p["name"] for p in sq["members"])
                lines.append(f'  小队{sq["squad_id"]}: {members}')

            lines.append("")

        if r["reserves"]["members"]:
            names = "、".join(m["name"] for m in r["reserves"]["members"])
            lines.append(f"【候补】{names}")
            lines.append("")

        lines.append(
            f'均衡: KD差{bl["kd_diff"]} | '
            f'KPM差{bl["kpm_diff"]} | '
            f'总分差{bl["score_diff"]}'
        )

        text = "\n".join(lines)
        QApplication.clipboard().setText(text)

        QMessageBox.information(self, "已复制", "分队结果已复制到剪贴板")

    # -----------------------------------------------------------------------
    # Reset
    # -----------------------------------------------------------------------

    def _reset_to_import(self):
        self.players_data = None
        self.players = None
        self.report = None
        self.alloc_mode = "balanced"

        self.player_count_label.setText("")
        self.fetch_status_label.setText("等待输入玩家 ID")
        self.player_table.setRowCount(0)

        self.balance_label.setText("请先完成分队")
        self.team_a_table.setRowCount(0)
        self.team_b_table.setRowCount(0)
        self.reserve_table.setRowCount(0)
        self.warning_label.setText("")

        for row in getattr(self, "binding_rows", []):
            row["widget"].deleteLater()

        self.binding_rows = []

        self.card_balanced.setChecked(True)
        self.card_random.setChecked(False)

        self.current_page = 0
        self.stack.setCurrentIndex(0)
        self._update_nav()

    def _reset_to_alloc(self):
        self.report = None

        self.balance_label.setText("请先完成分队")
        self.team_a_table.setRowCount(0)
        self.team_b_table.setRowCount(0)
        self.reserve_table.setRowCount(0)
        self.warning_label.setText("")

        self.current_page = 1
        self.stack.setCurrentIndex(1)
        self._update_nav()


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if sys.platform == "win32":
        import ctypes as _ctypes
        try:
            _ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                _ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())