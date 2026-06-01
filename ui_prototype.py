"""
BF6 Team Balancer - UI v2 (PyQt5)
Page flow: Import -> Game Mode -> Custom Squad -> Result
"""

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QTableWidget, QTableWidgetItem,
    QStackedWidget, QDoubleSpinBox, QGroupBox, QComboBox,
    QHeaderView, QMessageBox, QFrame, QGridLayout, QSizePolicy,
    QAbstractItemView
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract import extract_players
from core.algorithm import load_players, allocate_teams, random_allocate, compute_balance_report, GAME_MODES
from history import save_record, load_history, load_config, save_config

# -- Global Styles ------------------------------------------------

FONT_FAMILY = "Microsoft YaHei UI, Microsoft YaHei, PingFang SC, sans-serif"

# Mode name mappings (shared across display, copy, history)
ALLOC_MODE_NAMES = {"balanced": "均衡", "random": "随机"}
GAME_MODE_NAMES = {"conquest": "征服", "breakthrough": "突破"}

# -- Theme Config -------------------------------------------------

THEMES = {
    "dark_gray": {
        "name": "🌙 暗夜灰",
        "bg": "#2b2b3a", "card": "#333346", "card_alt": "#3a3a50",
        "btn": "#3d3d50", "btn_hover": "#4a4a60", "btn_disabled": "#333344",
        "text": "#e0dfe6", "text_disabled": "#666680", "text_sub": "#9998aa",
        "text_hint": "#777790", "border": "#44445a", "border_header": "#4a4a60",
        "accent": "#7b8db8", "accent_hover": "#8a9cc8",
        "exit": "#b87b7b", "exit_hover": "#c88a8a",
        "balance": "#a8c8a8", "warning": "#d4a574",
        "squads": ["#363648", "#3e3e52", "#363648", "#42425a"],
        "step_active": "#7b8db8", "step_done": "#8aaa8a", "step_pending": "#3d3d50",
        "step_skipped": "#2d2d3a", "step_connector": "#44445a",
    },
    "deep_blue": {
        "name": "🌊 深海蓝",
        "bg": "#1a2332", "card": "#1e2a3a", "card_alt": "#223344",
        "btn": "#253545", "btn_hover": "#2d4050", "btn_disabled": "#1e2830",
        "text": "#d0dfe6", "text_disabled": "#556677", "text_sub": "#8899aa",
        "text_hint": "#667788", "border": "#2a3a4a", "border_header": "#344455",
        "accent": "#5b8db8", "accent_hover": "#6a9cc8",
        "exit": "#b87b5b", "exit_hover": "#c88a6a",
        "balance": "#8ac8a8", "warning": "#d4a574",
        "squads": ["#1e2e3e", "#253545", "#1e2e3e", "#2a3a4a"],
        "step_active": "#5b8db8", "step_done": "#6a9c6a", "step_pending": "#253545",
        "step_skipped": "#1a2830", "step_connector": "#2a3a4a",
    },
    "dark_green": {
        "name": "🌲 墨绿",
        "bg": "#1a2b1a", "card": "#1e331e", "card_alt": "#223a22",
        "btn": "#253d25", "btn_hover": "#2d4a2d", "btn_disabled": "#1e2e1e",
        "text": "#d0e6d0", "text_disabled": "#557755", "text_sub": "#88aa88",
        "text_hint": "#668866", "border": "#2a4a2a", "border_header": "#345534",
        "accent": "#7ba87b", "accent_hover": "#8ab88a",
        "exit": "#b87b7b", "exit_hover": "#c88a8a",
        "balance": "#a8c8a8", "warning": "#d4b874",
        "squads": ["#1e2e1e", "#253525", "#1e2e1e", "#2a3a2a"],
        "step_active": "#7ba87b", "step_done": "#6a9c6a", "step_pending": "#253d25",
        "step_skipped": "#1a2e1a", "step_connector": "#2a4a2a",
    },
    "dark_red": {
        "name": "🔥 暗红",
        "bg": "#2b1a1a", "card": "#331e1e", "card_alt": "#3a2222",
        "btn": "#3d2525", "btn_hover": "#4a2d2d", "btn_disabled": "#2e1e1e",
        "text": "#e6d0d0", "text_disabled": "#775555", "text_sub": "#aa8888",
        "text_hint": "#886666", "border": "#4a2a2a", "border_header": "#553434",
        "accent": "#b87b7b", "accent_hover": "#c88a8a",
        "exit": "#b87b5b", "exit_hover": "#c88a6a",
        "balance": "#c8a8a8", "warning": "#d4a574",
        "squads": ["#2e1e1e", "#352525", "#2e1e1e", "#3a2a2a"],
        "step_active": "#b87b7b", "step_done": "#8a6a6a", "step_pending": "#3d2525",
        "step_skipped": "#2e1a1a", "step_connector": "#4a2a2a",
    },
    "mono_bw": {
        "name": "⬛ 黑白纯色",
        "bg": "#0a0a0a", "card": "#141414", "card_alt": "#1a1a1a",
        "btn": "#1e1e1e", "btn_hover": "#2a2a2a", "btn_disabled": "#111111",
        "text": "#f0f0f0", "text_disabled": "#555555", "text_sub": "#999999",
        "text_hint": "#666666", "border": "#2a2a2a", "border_header": "#333333",
        "accent": "#ffffff", "accent_hover": "#cccccc",
        "exit": "#888888", "exit_hover": "#aaaaaa",
        "balance": "#cccccc", "warning": "#dddddd",
        "squads": ["#111111", "#1a1a1a", "#111111", "#222222"],
        "step_active": "#ffffff", "step_done": "#999999", "step_pending": "#1e1e1e",
        "step_skipped": "#111111", "step_connector": "#2a2a2a",
    },
}

DEFAULT_THEME = "dark_gray"


def build_stylesheet(t):
    """Generate global stylesheet from theme dict."""
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
QGroupBox {{
    border: 1px solid {t["border"]};
    border-radius: 10px;
    margin-top: 12px;
    padding-top: 20px;
    font-weight: bold;
    font-size: 16px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 10px;
}}
QComboBox {{
    background: {t["btn"]};
    border: 1px solid {t["border"]};
    border-radius: 8px;
    padding: 10px;
    min-width: 160px;
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
    """Get squad color list for the given theme."""
    return THEMES.get(theme_id, THEMES[DEFAULT_THEME])["squads"]


class ModeCard(QPushButton):
    """Game mode selection card."""
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
        if hasattr(self, '_desc_label') and hasattr(self, '_theme'):
            self._desc_label.setStyleSheet(
                f"background: transparent; border: none; color: {self._theme['text_sub']}; font-size: 15px;"
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BF6 Team Balancer")
        self.setMinimumSize(1100, 750)

        # Load saved theme
        config = load_config()
        self.current_theme = config.get("theme", DEFAULT_THEME)
        if self.current_theme not in THEMES:
            self.current_theme = DEFAULT_THEME
        self.setStyleSheet(build_stylesheet(THEMES[self.current_theme]))

        self.players_data = None
        self.players = None
        self.report = None
        self.alloc_mode = "balanced"  # "balanced" | "random"
        self._visited_history = False  # Whether user has visited history page

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 16, 20, 16)

        # Top navigation bar
        nav = QHBoxLayout()
        nav.setSpacing(8)
        self.btn_prev = QPushButton("< 上一步")
        self.btn_prev.setFixedWidth(100)
        self.btn_next = QPushButton("下一步 >")
        self.btn_next.setObjectName("primary")
        self.btn_next.setFixedWidth(120)
        self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(False)

        self.step_indicators = []
        self.step_connectors = []
        indicator_row = QHBoxLayout()
        indicator_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        indicator_row.setSpacing(4)
        t = THEMES[self.current_theme]
        for i in range(6):
            dot = QLabel(f" {i+1} ")
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dot.setFixedSize(42, 42)
            dot.setStyleSheet(
                f"background: {t['step_pending']}; border-radius: 21px; font-weight: bold; color: {t['text_disabled']}; font-size: 17px;"
            )
            self.step_indicators.append(dot)
            indicator_row.addWidget(dot)
            if i < 5:
                line = QLabel("---")
                line.setStyleSheet(f"color: {t['step_connector']}; background: transparent;")
                self.step_connectors.append(line)
                indicator_row.addWidget(line)

        nav.addWidget(self.btn_prev)
        nav.addStretch()
        nav.addLayout(indicator_row)
        nav.addStretch()
        nav.addWidget(self.btn_next)
        main_layout.addLayout(nav)

        # Page stack
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, stretch=1)

        self.page_import = self._build_page_import()
        self.page_alloc = self._build_page_alloc_mode()
        self.page_mode = self._build_page_mode()
        self.page_custom = self._build_page_custom()
        self.page_result = self._build_page_result()
        self.page_history = self._build_page_history()
        self.page_ops = self._build_page_ops()

        self.stack.addWidget(self.page_import)       # index 0
        self.stack.addWidget(self.page_alloc)        # index 1
        self.stack.addWidget(self.page_mode)         # index 2
        self.stack.addWidget(self.page_custom)       # index 3
        self.stack.addWidget(self.page_result)       # index 4
        self.stack.addWidget(self.page_history)      # index 5
        self.stack.addWidget(self.page_ops)          # index 6

        self.btn_prev.clicked.connect(self._go_prev)

        self.current_page = 0
        self._next_handler = self._go_next
        self.btn_next.clicked.connect(lambda: self._next_handler())
        self._update_nav()

    # -- Page 1: Import ---------------------------------------------

    def _build_page_import(self):
        """Build the file import page with theme selector, file picker, and player table."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)

        # Top: title + theme selector
        top_row = QHBoxLayout()
        title = QLabel("导入玩家数据")
        title.setObjectName("title")
        top_row.addWidget(title)
        top_row.addStretch()

        theme_label = QLabel("主题:")
        theme_label.setStyleSheet("color: #9998aa; font-size: 14px;")
        top_row.addWidget(theme_label)
        self.theme_combo = QComboBox()
        self.theme_combo.setFixedWidth(150)
        for tid, t in THEMES.items():
            self.theme_combo.addItem(t["name"], tid)
        # Set current selection
        idx = list(THEMES.keys()).index(self.current_theme)
        self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        top_row.addWidget(self.theme_combo)

        layout.addLayout(top_row)

        subtitle = QLabel("选择 Excel 文件（列1=昵称, 列2=KD, 列3=KPM）")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        # File selection area
        file_frame = QFrame()
        file_frame.setStyleSheet("QFrame { background: #333346; border-radius: 10px; padding: 14px; }")
        file_layout = QHBoxLayout(file_frame)

        self.file_icon = QLabel("📄")
        self.file_icon.setFont(QFont("", 24))
        self.file_icon.setStyleSheet("background: transparent;")
        file_layout.addWidget(self.file_icon)

        file_info = QVBoxLayout()
        self.file_name_label = QLabel("未选择文件")
        self.file_name_label.setStyleSheet("font-weight: bold; background: transparent;")
        self.file_hint_label = QLabel("支持 .xlsx / .xls 格式")
        self.file_hint_label.setStyleSheet("color: #6c7086; background: transparent;")
        file_info.addWidget(self.file_name_label)
        file_info.addWidget(self.file_hint_label)
        file_layout.addLayout(file_info, stretch=1)

        btn_file = QPushButton("选择文件")
        btn_file.setFixedWidth(100)
        btn_file.clicked.connect(self._select_file)
        file_layout.addWidget(btn_file)
        layout.addWidget(file_frame)

        # Offset coefficient
        offset_frame = QFrame()
        offset_frame.setStyleSheet("QFrame { background: #333346; border-radius: 10px; padding: 12px; }")
        offset_layout = QHBoxLayout(offset_frame)
        offset_layout.addWidget(QLabel("KPM 偏移系数:"))
        self.offset_spin = QDoubleSpinBox()
        self.offset_spin.setRange(0.1, 5.0)
        self.offset_spin.setValue(1.313)
        self.offset_spin.setSingleStep(0.01)
        self.offset_spin.setDecimals(3)
        self.offset_spin.setFixedWidth(100)
        offset_layout.addWidget(self.offset_spin)
        offset_layout.addWidget(QLabel("推荐值 1.313"))
        self.player_count_label = QLabel("")
        self.player_count_label.setStyleSheet("color: #8aaa8a; font-weight: bold; background: transparent;")
        offset_layout.addStretch()
        offset_layout.addWidget(self.player_count_label)
        layout.addWidget(offset_frame)

        # Player table (fills remaining space)
        self.player_table = QTableWidget()
        self.player_table.setColumnCount(4)
        self.player_table.setHorizontalHeaderLabels(["昵称", "原始KD", "原始KPM", "调整后KPM"])
        self.player_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.player_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.player_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.player_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.player_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.player_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.player_table.setAlternatingRowColors(True)
        self.player_table.verticalHeader().setVisible(False)
        layout.addWidget(self.player_table, stretch=1)

        return page

    # -- Page 2: Alloc Mode -----------------------------------------

    def _build_page_alloc_mode(self):
        """Build the allocation mode selection page (balanced vs random)."""
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

    # -- Page 3: Game Mode ------------------------------------------

    def _build_page_mode(self):
        """Build the game mode selection page (conquest vs breakthrough)."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)

        title = QLabel("选择游戏模式")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("不同模式会影响 KD 和 KPM 的权重分配")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        # Mode cards
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

    # -- Page 3: Custom Squad ---------------------------------------

    def _build_page_custom(self):
        """Build the custom squad binding page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)

        title = QLabel("自定义小队（可选）")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("绑定的两人将被分配到同一阵营的同一个小队。每人最多被选一次。")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        # Add button
        btn_add = QPushButton("+ 添加绑定")
        btn_add.setFixedWidth(120)
        btn_add.clicked.connect(self._add_binding_row)
        layout.addWidget(btn_add)

        # Binding list area
        self.binding_container = QWidget()
        self.binding_layout = QVBoxLayout(self.binding_container)
        self.binding_layout.setSpacing(8)
        layout.addWidget(self.binding_container, stretch=1)

        # Hint
        hint = QLabel("如果不设绑定，直接点「查看结果」即可")
        hint.setObjectName("hint")
        layout.addWidget(hint)

        return page

    # -- Page 4: Result ---------------------------------------------

    def _build_page_result(self):
        """Build the result page with team tables, reserves, and balance summary."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        # Summary bar
        self.balance_label = QLabel("请先完成分队")
        self.balance_label.setObjectName("balance_summary")
        self.balance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.balance_label)

        # Two columns
        columns = QHBoxLayout()
        columns.setSpacing(12)

        # NATO
        left_frame = QFrame()
        left_frame.setStyleSheet("QFrame { background: #333346; border-radius: 10px; }")
        left_layout = QVBoxLayout(left_frame)
        left_layout.setSpacing(6)
        lbl_a = QLabel("北约")
        lbl_a.setFont(QFont("Microsoft YaHei UI", 16, QFont.Weight.Bold))
        lbl_a.setStyleSheet("color: #9aadd4; background: transparent;")
        left_layout.addWidget(lbl_a)

        self.team_a_table = QTableWidget()
        self.team_a_table.setColumnCount(5)
        self.team_a_table.setHorizontalHeaderLabels(["小队", "昵称", "KD", "KPM", "得分"])
        self.team_a_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.team_a_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.team_a_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.team_a_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.team_a_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.team_a_table.setColumnWidth(0, 50)
        self.team_a_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.team_a_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.team_a_table.verticalHeader().setVisible(False)
        left_layout.addWidget(self.team_a_table, stretch=1)
        columns.addWidget(left_frame, stretch=1)

        # PAC
        right_frame = QFrame()
        right_frame.setStyleSheet("QFrame { background: #333346; border-radius: 10px; }")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setSpacing(6)
        lbl_b = QLabel("和平军团")
        lbl_b.setFont(QFont("Microsoft YaHei UI", 16, QFont.Weight.Bold))
        lbl_b.setStyleSheet("color: #d4a0a0; background: transparent;")
        right_layout.addWidget(lbl_b)

        self.team_b_table = QTableWidget()
        self.team_b_table.setColumnCount(5)
        self.team_b_table.setHorizontalHeaderLabels(["小队", "昵称", "KD", "KPM", "得分"])
        self.team_b_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.team_b_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.team_b_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.team_b_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.team_b_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.team_b_table.setColumnWidth(0, 50)
        self.team_b_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.team_b_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.team_b_table.verticalHeader().setVisible(False)
        right_layout.addWidget(self.team_b_table, stretch=1)
        columns.addWidget(right_frame, stretch=1)

        layout.addLayout(columns, stretch=3)

        # Bottom: reserve table + warnings
        bottom = QHBoxLayout()
        bottom.setSpacing(12)

        reserve_frame = QFrame()
        reserve_frame.setStyleSheet("QFrame { background: #333346; border-radius: 10px; }")
        reserve_layout_inner = QVBoxLayout(reserve_frame)
        reserve_layout_inner.setSpacing(4)
        lbl_r = QLabel("候补队伍")
        lbl_r.setFont(QFont("Microsoft YaHei UI", 14, QFont.Weight.Bold))
        lbl_r.setStyleSheet("color: #c8b88a; background: transparent;")
        reserve_layout_inner.addWidget(lbl_r)

        self.reserve_table = QTableWidget()
        self.reserve_table.setColumnCount(4)
        self.reserve_table.setHorizontalHeaderLabels(["#", "昵称", "KD", "KPM"])
        self.reserve_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.reserve_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.reserve_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.reserve_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.reserve_table.setColumnWidth(0, 36)
        self.reserve_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.reserve_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.reserve_table.verticalHeader().setVisible(False)
        self.reserve_table.setMaximumHeight(200)
        reserve_layout_inner.addWidget(self.reserve_table)
        bottom.addWidget(reserve_frame, stretch=1)

        self.warning_label = QLabel("")
        self.warning_label.setObjectName("warning")
        self.warning_label.setFixedWidth(280)
        self.warning_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        bottom.addWidget(self.warning_label)

        layout.addLayout(bottom, stretch=1)

        # Action buttons
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

    # -- Page 5: History --------------------------------------------

    def _build_page_history(self):
        """Build the history page with record list and detail view."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        title = QLabel("历史记录")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("点击记录查看详情，或直接点「下一步」跳过")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        # History list
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["#", "时间", "分配模式", "游戏模式", "人数"])
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

        # Detail area (two columns, same structure as result page)
        detail_columns = QHBoxLayout()
        detail_columns.setSpacing(12)

        # Left: Team A
        left_frame = QFrame()
        left_frame.setStyleSheet("QFrame { background: #333346; border-radius: 10px; }")
        left_layout = QVBoxLayout(left_frame)
        left_layout.setSpacing(6)
        self.hist_lbl_a = QLabel("阵营A")
        self.hist_lbl_a.setFont(QFont("Microsoft YaHei UI", 16, QFont.Weight.Bold))
        self.hist_lbl_a.setStyleSheet("color: #9aadd4; background: transparent;")
        left_layout.addWidget(self.hist_lbl_a)
        self.hist_team_a_table = QTableWidget()
        self.hist_team_a_table.setColumnCount(2)
        self.hist_team_a_table.setHorizontalHeaderLabels(["小队", "昵称"])
        self.hist_team_a_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.hist_team_a_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.hist_team_a_table.setColumnWidth(0, 50)
        self.hist_team_a_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.hist_team_a_table.verticalHeader().setVisible(False)
        left_layout.addWidget(self.hist_team_a_table, stretch=1)
        detail_columns.addWidget(left_frame, stretch=1)

        # Right: Team B
        right_frame = QFrame()
        right_frame.setStyleSheet("QFrame { background: #333346; border-radius: 10px; }")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setSpacing(6)
        self.hist_lbl_b = QLabel("阵营B")
        self.hist_lbl_b.setFont(QFont("Microsoft YaHei UI", 16, QFont.Weight.Bold))
        self.hist_lbl_b.setStyleSheet("color: #d4a0a0; background: transparent;")
        right_layout.addWidget(self.hist_lbl_b)
        self.hist_team_b_table = QTableWidget()
        self.hist_team_b_table.setColumnCount(2)
        self.hist_team_b_table.setHorizontalHeaderLabels(["小队", "昵称"])
        self.hist_team_b_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.hist_team_b_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.hist_team_b_table.setColumnWidth(0, 50)
        self.hist_team_b_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.hist_team_b_table.verticalHeader().setVisible(False)
        right_layout.addWidget(self.hist_team_b_table, stretch=1)
        detail_columns.addWidget(right_frame, stretch=1)

        layout.addLayout(detail_columns, stretch=1)

        # Bottom: reserve + balance info
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

    def _on_history_row_clicked(self, index):
        """Handle click on a history row, show detail."""
        row = index.row()
        history = load_history()
        if row >= len(history):
            return
        rec = history[row]
        self._display_history_detail(rec)

    def _display_history_detail(self, rec):
        """Render a history record to the detail area."""
        self.hist_lbl_a.setText(rec["team_a"]["name"])
        self.hist_lbl_b.setText(rec["team_b"]["name"])
        squad_colors = get_theme_squad_colors(self.current_theme)

        for team_key, table in [("team_a", self.hist_team_a_table), ("team_b", self.hist_team_b_table)]:
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

        # Reserve
        if rec["reserves"]:
            self.hist_reserve_label.setText(f'候补: {"、".join(rec["reserves"])}')
        else:
            self.hist_reserve_label.setText("无候补")

        # Balance
        bl = rec["balance"]
        self.hist_balance_label.setText(f'KD差{bl["kd_diff"]} | KPM差{bl["kpm_diff"]} | 总分差{bl["score_diff"]}')

    def _refresh_history_table(self):
        """Refresh the history list."""
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

    # -- Page 6: Actions --------------------------------------------

    def _build_page_ops(self):
        """Build the operations page (re-import, re-allocate, exit)."""
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

        # Action buttons
        btn_reimport = QPushButton("📄 重新导入")
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

    # -- Navigation ------------------------------------------------

    def _go_prev(self):
        if self.current_page > 0:
            if self.current_page == 6:
                # Action page -> Result page (skip history)
                self.current_page = 4
            elif self.current_page == 5:
                # History page -> Result page
                self.current_page = 4
            elif self.current_page == 3 and self.alloc_mode == "random":
                self.current_page = 1  # Skip game mode
            else:
                self.current_page -= 1
            self.stack.setCurrentIndex(self.current_page)
            self._update_nav()

    def _go_next(self):
        if self.current_page == 0:
            # Import -> Alloc mode
            if self.players is None:
                QMessageBox.warning(self, "提示", "请先选择 Excel 文件")
                return
            self.current_page = 1
        elif self.current_page == 1:
            # Alloc mode -> Game mode (balanced) or Custom squad (random)
            if self.alloc_mode == "random":
                self.current_page = 3  # Skip game mode
            else:
                self.current_page = 2
        elif self.current_page == 2:
            # Game mode -> Custom squad
            self.current_page = 3
        elif self.current_page == 3:
            # Custom squad -> Result
            self._run_algorithm()
            if self.report is None:
                return
            self.current_page = 4
        elif self.current_page == 4:
            # Result -> Action page (skip history)
            self.current_page = 6
        elif self.current_page == 5:
            # History -> Action page
            self.current_page = 6
        self.stack.setCurrentIndex(self.current_page)
        self._update_nav()

    def _update_nav(self):
        self.btn_prev.setEnabled(self.current_page > 0 and self.current_page < 6)

        if self.current_page >= 6:
            # Action page: hide prev/next
            self.btn_prev.setEnabled(False)
            self.btn_next.setEnabled(False)
            self.btn_next.setText("下一步 >")
            self.btn_next.setObjectName("primary")
            self._next_handler = self._go_next
        elif self.current_page == 5:
            # History page: prev -> result, next -> action
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
            self.btn_next.setText("查看结果" if self.current_page == 3 else "下一步 >")
            self.btn_next.setObjectName("primary")
            self._next_handler = self._go_next
            self.btn_next.setEnabled(self.current_page != 0 or self.players is not None)

        # Re-apply style
        self.btn_next.style().unpolish(self.btn_next)
        self.btn_next.style().polish(self.btn_next)

        # Step indicator mapping: page index -> indicator index
        # Pages: 0=Import, 1=AllocMode, 2=GameMode, 3=Squad, 4=Result, 5=History(no indicator), 6=Action
        # Indicators: 0=Import, 1=AllocMode, 2=GameMode, 3=Squad, 4=Result, 5=Action
        page_to_step = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 4, 6: 5}
        current_step = page_to_step.get(self.current_page, 0)

        t = THEMES[self.current_theme]
        for i, dot in enumerate(self.step_indicators):
            is_skipped = (i == 2 and self.alloc_mode == "random")

            if is_skipped:
                dot.setStyleSheet(
                    f"background: {t['step_skipped']}; border-radius: 21px; font-weight: bold; color: {t['text_disabled']}; font-size: 17px; text-decoration: line-through;"
                )
            elif i == current_step:
                dot.setStyleSheet(
                    f"background: {t['step_active']}; border-radius: 21px; font-weight: bold; color: #ffffff; font-size: 17px;"
                )
            elif i < current_step:
                dot.setStyleSheet(
                    f"background: {t['step_done']}; border-radius: 21px; font-weight: bold; color: #ffffff; font-size: 17px;"
                )
            else:
                dot.setStyleSheet(
                    f"background: {t['step_pending']}; border-radius: 21px; font-weight: bold; color: {t['text_disabled']}; font-size: 17px;"
                )

    # -- Theme Switch -----------------------------------------------

    def _on_theme_changed(self, index):
        theme_id = self.theme_combo.currentData()
        if theme_id and theme_id in THEMES:
            self.current_theme = theme_id
            t = THEMES[theme_id]
            self.setStyleSheet(build_stylesheet(t))
            # Sync all ModeCard themes
            for card in [self.card_balanced, self.card_random,
                         self.card_conquest, self.card_breakthrough]:
                card.set_theme(t)
            # Refresh step indicator colors
            for line in self.step_connectors:
                line.setStyleSheet(f"color: {t['step_connector']}; background: transparent;")
            self._update_nav()
            # Save preference
            config = load_config()
            config["theme"] = theme_id
            save_config(config)

    # -- File Import -----------------------------------------------

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 Excel 文件", "", "Excel (*.xlsx *.xls)"
        )
        if not path:
            return
        try:
            offset = self.offset_spin.value()
            self.players_data = extract_players(path, offset)
            self.players = load_players({"players": self.players_data})
            self.file_name_label.setText(os.path.basename(path))
            self.file_hint_label.setText(f"已加载 {len(self.players)} 名玩家")
            self.player_count_label.setText(f"共 {len(self.players)} 人")
            self._refresh_player_table()
            self.btn_next.setEnabled(True)
            self._refresh_binding_combos()
        except (OSError, ValueError) as e:
            QMessageBox.critical(self, "错误", f"读取失败:\n{e}")

    def _refresh_player_table(self):
        self.player_table.setRowCount(len(self.players_data))
        for i, p in enumerate(self.players_data):
            self.player_table.setItem(i, 0, QTableWidgetItem(p["name"]))
            self.player_table.setItem(i, 1, QTableWidgetItem(str(p["kd"] or "-")))
            self.player_table.setItem(i, 2, QTableWidgetItem(str(p["kpm_raw"] or "-")))
            self.player_table.setItem(i, 3, QTableWidgetItem(str(p["kpm_adjusted"] or "-")))

    # -- Custom Squad ----------------------------------------------

    def _add_binding_row(self):
        if self.players is None:
            return

        row_widget = QFrame()
        row_widget.setStyleSheet("QFrame { background: #3d3d50; border-radius: 8px; padding: 10px; }")
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

        row_data = {"widget": row_widget, "cb1": cb1, "cb2": cb2}
        self.binding_rows = getattr(self, "binding_rows", [])
        self.binding_rows.append(row_data)
        self.binding_layout.addWidget(row_widget)

        btn_remove.clicked.connect(lambda: self._remove_binding_row(row_data))

    def _remove_binding_row(self, row_data):
        self.binding_rows.remove(row_data)
        row_data["widget"].deleteLater()

    def _refresh_binding_combos(self):
        names = [p.name for p in self.players]
        for row in getattr(self, "binding_rows", []):
            row["cb1"].clear()
            row["cb2"].clear()
            row["cb1"].addItems(["-- 选择玩家 --"] + names)
            row["cb2"].addItems(["-- 选择玩家 --"] + names)

    # -- Run Algorithm ---------------------------------------------

    def _run_algorithm(self):
        if not self.players:
            QMessageBox.warning(self, "提示", "没有玩家数据，请先导入 Excel 文件")
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
            bindings.append({"player_a": a, "player_b": b})

        # Random mode defaults to conquest cap (64 players), game mode page is skipped
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
        """Render the allocation report to the result page."""
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

        # Reserve table
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
                score = round(kd * cfg["kd_weight"] + kpm * cfg["kpm_weight"], 2)
                rows.append((sq["squad_id"], p["name"], str(kd), str(kpm), str(score)))

        table.setRowCount(len(rows))
        for i, (sid, name, kd, kpm, score) in enumerate(rows):
            item_sid = QTableWidgetItem(str(sid))
            item_name = QTableWidgetItem(name)
            item_kd = QTableWidgetItem(kd)
            item_kpm = QTableWidgetItem(kpm)
            item_score = QTableWidgetItem(score)

            # Different squad -> different background color
            color = QColor(squad_colors[(sid - 1) % len(squad_colors)])
            for item in [item_sid, item_name, item_kd, item_kpm, item_score]:
                item.setBackground(color)

            table.setItem(i, 0, item_sid)
            table.setItem(i, 1, item_name)
            table.setItem(i, 2, item_kd)
            table.setItem(i, 3, item_kpm)
            table.setItem(i, 4, item_score)

    # -- Copy Result -----------------------------------------------

    def _copy_result(self):
        """Copy formatted result text to clipboard."""
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
            lines.append(f'【{t["name"]}】({t["total_players"]}人, {t["num_squads"]}小队)')
            for sq in t["squads"]:
                members = "、".join(p["name"] for p in sq["members"])
                lines.append(f'  小队{sq["squad_id"]}: {members}')
            lines.append("")

        if r["reserves"]["members"]:
            names = "、".join(m["name"] for m in r["reserves"]["members"])
            lines.append(f"【候补】{names}")
            lines.append("")

        lines.append(f'均衡: KD差{bl["kd_diff"]} | KPM差{bl["kpm_diff"]} | 总分差{bl["score_diff"]}')

        text = "\n".join(lines)
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "已复制", "分队结果已复制到剪贴板")

    # -- History ---------------------------------------------------

    def _show_history(self):
        history = load_history()
        if not history:
            QMessageBox.information(self, "历史记录", "暂无历史记录")
            return
        self._refresh_history_table()
        self._visited_history = True
        self.current_page = 5
        self.stack.setCurrentIndex(5)
        self._update_nav()

    # -- Reset -----------------------------------------------------

    def _reset_to_import(self):
        """Reset to import page, clear all data."""
        self.players_data = None
        self.players = None
        self.report = None
        self.alloc_mode = "balanced"
        self._visited_history = False
        self.file_name_label.setText("未选择文件")
        self.file_hint_label.setText("支持 .xlsx / .xls 格式")
        self.player_count_label.setText("")
        self.player_table.setRowCount(0)
        self.balance_label.setText("请先完成分队")
        self.team_a_table.setRowCount(0)
        self.team_b_table.setRowCount(0)
        self.reserve_table.setRowCount(0)
        self.warning_label.setText("")
        # Clear bindings
        for row in getattr(self, "binding_rows", []):
            row["widget"].deleteLater()
        self.binding_rows = []
        # Reset alloc mode cards
        self.card_balanced.setChecked(True)
        self.card_random.setChecked(False)
        self.current_page = 0
        self.stack.setCurrentIndex(0)
        self._update_nav()

    def _reset_to_alloc(self):
        """Reset to alloc mode page, keep player data."""
        self.report = None
        self._visited_history = False
        self.balance_label.setText("请先完成分队")
        self.team_a_table.setRowCount(0)
        self.team_b_table.setRowCount(0)
        self.reserve_table.setRowCount(0)
        self.warning_label.setText("")
        self.current_page = 1
        self.stack.setCurrentIndex(1)
        self._update_nav()


if __name__ == "__main__":
    # High DPI adaptation
    # Windows DPI awareness: let the process handle scaling itself to avoid blurry upscaling
    if sys.platform == "win32":
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # Per-Monitor DPI Aware
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    # Qt high DPI scaling: auto-scale all widgets, fonts, and spacing
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
