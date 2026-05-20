"""
Main application entry point for the Human Pose Editor.
Builds the PySide6 main window with a premium dark/neon tech UI,
attaches event handlers, manages skeleton state, and coordinates modular subfunctions.
"""
import sys
import os
from typing import List, Dict, Tuple
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGroupBox, QPushButton, QSlider, QComboBox, QLabel, QFileDialog, 
    QMessageBox, QFrame, QSplitter, QScrollArea, QCheckBox
)
from PySide6.QtGui import QIcon, QColor, QFont
from PySide6.QtCore import Qt, QSize

import i18n
import pose_math
import pose_presets
import pose_io
from pose_canvas import PoseCanvas

# QSS Custom Modern Dark/Neon Style Sheet
DARK_QSS = """
QMainWindow {
    background-color: #121316;
}

QWidget {
    color: #e0e0e6;
    font-family: "Segoe UI", "Microsoft JhengHei", "PingFang TC", sans-serif;
    font-size: 13px;
}

QFrame#sidebar_left, QFrame#sidebar_right {
    background-color: #18191d;
    border: 1px solid #282a30;
    border-radius: 8px;
}

QGroupBox {
    font-weight: bold;
    border: 1px solid #282a30;
    border-radius: 6px;
    margin-top: 15px;
    padding-top: 15px;
    color: #00e5ff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 5px;
}

QPushButton {
    background-color: #2a2d35;
    border: 1px solid #3e424d;
    border-radius: 5px;
    padding: 5px 10px;
    min-height: 22px;
    color: #ffffff;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #353943;
    border: 1px solid #00e5ff;
}

QPushButton:pressed {
    background-color: #1e2025;
}

QPushButton#btn_primary {
    background-color: #0088cc;
    border: 1px solid #00aaff;
    font-size: 14px;
    font-weight: bold;
}

QPushButton#btn_primary:hover {
    background-color: #00aaff;
}

QPushButton#btn_primary:pressed {
    background-color: #006699;
}

QPushButton#btn_lang_switch {
    background-color: #b026ff;
    border: 1px solid #d283ff;
    font-size: 11px;
    font-weight: bold;
}

QPushButton#btn_lang_switch:hover {
    background-color: #c45eff;
}

QPushButton#btn_char_active {
    background-color: #1e3a47;
    border: 1px solid #00e5ff;
    color: #00e5ff;
}

QSlider::groove:horizontal {
    border: 1px solid #2a2d35;
    height: 6px;
    background: #202227;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #00e5ff;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    border: 1px solid #00e5ff;
    width: 14px;
    height: 14px;
    margin-top: -4px;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background: #00e5ff;
}

QComboBox {
    background-color: #202227;
    border: 1px solid #3e424d;
    border-radius: 4px;
    padding: 4px;
    min-width: 6em;
    color: #ffffff;
}

QComboBox:hover {
    border: 1px solid #00e5ff;
}

QComboBox QAbstractItemView {
    background-color: #1e1f24;
    border: 1px solid #3e424d;
    selection-background-color: #00e5ff;
    selection-color: #121316;
}

QLabel {
    color: #a5a6b0;
}

QLabel#lbl_title {
    color: #ffffff;
    font-size: 16px;
    font-weight: bold;
}

QLabel#lbl_char_active {
    color: #00e5ff;
    font-weight: bold;
}

QFrame#status_bar {
    background-color: #15161a;
    border-top: 1px solid #202227;
    padding: 6px;
}

QScrollBar:vertical {
    background-color: #121316;
    width: 10px;
    margin: 0px 0px 0px 0px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #2a2d35;
    min-height: 20px;
    border-radius: 5px;
    border: 1px solid #3e424d;
}

QScrollBar::handle:vertical:hover {
    background-color: #00e5ff;
    border: 1px solid #00e5ff;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}

QCheckBox {
    color: #e0e0e6;
    spacing: 6px;
    padding-top: 4px;
    padding-bottom: 4px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #3e424d;
    border-radius: 3px;
    background-color: #202227;
}
QCheckBox::indicator:unchecked:hover {
    border: 1px solid #00e5ff;
}
QCheckBox::indicator:checked {
    background-color: #00e5ff;
    border: 1px solid #00e5ff;
}
QCheckBox::indicator:checked:hover {
    background-color: #33ebff;
    border: 1px solid #33ebff;
}
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # State settings
        self.lang = "zh_TW"  # Default Language
        self.skeletons: List[Dict] = []
        
        # Canvas Size Default: 512x512
        self.canvas_width = 512
        self.canvas_height = 512
        self.canvas_bg_color = "black"

        # Initialize Default Character
        self.init_default_character()
        
        # Setup UI
        self.init_ui()
        self.retranslate_ui()
        
        # Load Stylesheet
        self.setStyleSheet(DARK_QSS)
        
        # Select first character initially
        self.select_character(0)

    def init_default_character(self):
        """Initializes a single default standing character in the center."""
        stand_pts = pose_presets.get_preset_pose("single_stand", 0, 0)
        self.skeletons = [
            {
                "points": stand_pts,
                "original_points": list(stand_pts),
                "visible": True,
                "locked": False,
                "height_scale": 1.0,
                "limb_scale": 1.0,
                "pose_name": "single_stand"
            }
        ]

    def select_character(self, idx: int):
        """Changes the currently active character index and updates sliders."""
        if 0 <= idx < len(self.skeletons):
            self.canvas.selected_char_idx = idx
            
            # Sync sliders
            sk = self.skeletons[idx]
            self.slider_height.blockSignals(True)
            self.slider_limb.blockSignals(True)
            
            self.slider_height.setValue(int(sk["height_scale"] * 100))
            self.slider_limb.setValue(int(sk["limb_scale"] * 100))
            
            self.slider_height.blockSignals(False)
            self.slider_limb.blockSignals(False)
            
            # Update labels
            self.update_character_ui_list()
        else:
            self.canvas.selected_char_idx = -1
            
        self.canvas.update()

    def update_character_ui_list(self):
        """Updates character status indicators on the sidebar buttons."""
        active_idx = self.canvas.selected_char_idx
        
        # Retranslate labels & states dynamically
        self.lbl_selected_status.setText("")
        
        # Check Character 1 Button
        if len(self.skeletons) > 0:
            self.btn_char1.setVisible(True)
            self.btn_char1.setEnabled(True)
            sk = self.skeletons[0]
            
            # Determine suffix based on state
            status = []
            if sk["locked"]:
                status.append(i18n.get_translation("lock", self.lang))
            if not sk["visible"]:
                status.append(i18n.get_translation("hidden", self.lang))
            
            status_str = f" ({', '.join(status)})" if status else ""
            self.btn_char1.setText(f"{i18n.get_translation('char_label', self.lang).format(1)}{status_str}")
            
            if active_idx == 0:
                self.btn_char1.setObjectName("btn_char_active")
                self.lbl_selected_status.setText(f"{i18n.get_translation('char_label', self.lang).format(1)}")
            else:
                self.btn_char1.setObjectName("")
        else:
            self.btn_char1.setVisible(False)
            
        # Check Character 2 Button
        if len(self.skeletons) > 1:
            self.btn_char2.setVisible(True)
            self.btn_char2.setEnabled(True)
            sk = self.skeletons[1]
            
            status = []
            if sk["locked"]:
                status.append(i18n.get_translation("lock", self.lang))
            if not sk["visible"]:
                status.append(i18n.get_translation("hidden", self.lang))
            
            status_str = f" ({', '.join(status)})" if status else ""
            self.btn_char2.setText(f"{i18n.get_translation('char_label', self.lang).format(2)}{status_str}")
            
            if active_idx == 1:
                self.btn_char2.setObjectName("btn_char_active")
                self.lbl_selected_status.setText(f"{i18n.get_translation('char_label', self.lang).format(2)}")
            else:
                self.btn_char2.setObjectName("")
        else:
            self.btn_char2.setVisible(False)
            
        # Re-apply stylesheet to render active buttons correctly
        self.btn_char1.style().unpolish(self.btn_char1)
        self.btn_char1.style().polish(self.btn_char1)
        if len(self.skeletons) > 1:
            self.btn_char2.style().unpolish(self.btn_char2)
            self.btn_char2.style().polish(self.btn_char2)

    def init_ui(self):
        """Constructs widgets, layouts, sidebars, and binds events."""
        self.setWindowTitle(i18n.get_translation("title", self.lang))
        self.setMinimumSize(QSize(1150, 720))
        
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 5)
        main_layout.setSpacing(10)
        
        # 1. Header Toolbar
        header_layout = QHBoxLayout()
        self.lbl_app_title = QLabel(i18n.get_translation("title", self.lang), self)
        self.lbl_app_title.setObjectName("lbl_title")
        
        self.btn_lang = QPushButton(i18n.get_translation("switch_lang", self.lang), self)
        self.btn_lang.setObjectName("btn_lang_switch")
        self.btn_lang.clicked.connect(self.toggle_language)
        
        header_layout.addWidget(self.lbl_app_title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_lang)
        main_layout.addLayout(header_layout)
        
        # 2. Main Work Area (Left Sidebar + Canvas + Right Sidebar)
        work_layout = QHBoxLayout()
        work_layout.setSpacing(10)
        
        # --- LEFT SIDEBAR (Character Control Panel) ---
        scroll_left = QScrollArea(self)
        scroll_left.setWidgetResizable(True)
        scroll_left.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_left.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_left.setFixedWidth(295)
        scroll_left.setFrameShape(QFrame.Shape.NoFrame)
        scroll_left.setStyleSheet("background-color: transparent;")

        sidebar_left = QFrame(self)
        sidebar_left.setObjectName("sidebar_left")
        left_layout = QVBoxLayout(sidebar_left)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(15)
        
        # A. Character Selection & List Group
        self.grp_chars = QGroupBox(i18n.get_translation("char_manager", self.lang), self)
        grp_chars_layout = QVBoxLayout(self.grp_chars)
        grp_chars_layout.setSpacing(8)
        
        self.btn_char1 = QPushButton(f"{i18n.get_translation('char_label', self.lang).format(1)}", self)
        self.btn_char1.clicked.connect(lambda: self.select_character(0))
        self.btn_char2 = QPushButton(f"{i18n.get_translation('char_label', self.lang).format(2)}", self)
        self.btn_char2.clicked.connect(lambda: self.select_character(1))
        
        char_buttons_layout = QHBoxLayout()
        self.btn_add_char = QPushButton(i18n.get_translation("add_char", self.lang), self)
        self.btn_add_char.clicked.connect(self.add_character)
        self.btn_del_char = QPushButton(i18n.get_translation("del_char", self.lang), self)
        self.btn_del_char.clicked.connect(self.delete_character)
        
        char_buttons_layout.addWidget(self.btn_add_char)
        char_buttons_layout.addWidget(self.btn_del_char)
        
        grp_chars_layout.addWidget(self.btn_char1)
        grp_chars_layout.addWidget(self.btn_char2)
        grp_chars_layout.addLayout(char_buttons_layout)
        left_layout.addWidget(self.grp_chars)
        
        # B. Selected Character Operations Group
        self.grp_operations = QGroupBox("", self)  # Title updated in retranslate
        ops_layout = QVBoxLayout(self.grp_operations)
        ops_layout.setSpacing(10)
        
        # Active label
        self.lbl_selected_status = QLabel("", self)
        self.lbl_selected_status.setObjectName("lbl_char_active")
        ops_layout.addWidget(self.lbl_selected_status)
        
        # Action toggles layout
        toggle_layout = QHBoxLayout()
        self.btn_lock = QPushButton(i18n.get_translation("lock", self.lang), self)
        self.btn_lock.clicked.connect(self.toggle_active_character_lock)
        self.btn_visible = QPushButton(i18n.get_translation("visible", self.lang), self)
        self.btn_visible.clicked.connect(self.toggle_active_character_visibility)
        
        toggle_layout.addWidget(self.btn_lock)
        toggle_layout.addWidget(self.btn_visible)
        ops_layout.addLayout(toggle_layout)
        
        # Mirror and Reset
        ops_btn_layout = QHBoxLayout()
        self.btn_mirror = QPushButton(i18n.get_translation("mirror_pose", self.lang), self)
        self.btn_mirror.clicked.connect(self.mirror_active_pose)
        self.btn_reset = QPushButton(i18n.get_translation("reset_pose", self.lang), self)
        self.btn_reset.clicked.connect(self.reset_active_pose)
        
        ops_btn_layout.addWidget(self.btn_mirror)
        ops_btn_layout.addWidget(self.btn_reset)
        ops_layout.addLayout(ops_btn_layout)
        
        # Proportions controls (Sliders)
        self.lbl_height_scale = QLabel(i18n.get_translation("height_scale", self.lang) + "100%", self)
        self.slider_height = QSlider(Qt.Orientation.Horizontal, self)
        self.slider_height.setRange(50, 200) # 50% to 200%
        self.slider_height.setValue(100)
        self.slider_height.valueChanged.connect(self.adjust_character_proportions)
        
        self.lbl_limb_scale = QLabel(i18n.get_translation("limb_scale", self.lang) + "100%", self)
        self.slider_limb = QSlider(Qt.Orientation.Horizontal, self)
        self.slider_limb.setRange(50, 200) # 50% to 200%
        self.slider_limb.setValue(100)
        self.slider_limb.valueChanged.connect(self.adjust_character_proportions)
        
        ops_layout.addWidget(self.lbl_height_scale)
        ops_layout.addWidget(self.slider_height)
        ops_layout.addWidget(self.lbl_limb_scale)
        ops_layout.addWidget(self.slider_limb)
        
        left_layout.addWidget(self.grp_operations)
        left_layout.addStretch()
        scroll_left.setWidget(sidebar_left)
        work_layout.addWidget(scroll_left)

        # --- CENTER AREA (Interactive Canvas) ---
        self.canvas = PoseCanvas(self)
        self.canvas.set_skeletons(self.skeletons)
        self.canvas.char_selected.connect(self.select_character)
        self.canvas.pose_changed.connect(self.on_canvas_pose_changed)
        
        # Framed wrapper to give the canvas a sleek container look
        canvas_container = QFrame(self)
        canvas_container.setStyleSheet("background-color: #1a1c22; border-radius: 8px; border: 1px solid #282a30;")
        cc_layout = QVBoxLayout(canvas_container)
        cc_layout.setContentsMargins(4, 4, 4, 4)
        cc_layout.addWidget(self.canvas)
        work_layout.addWidget(canvas_container, stretch=1)

        # --- RIGHT SIDEBAR (Presets & Canvas Settings Panel) ---
        scroll_right = QScrollArea(self)
        scroll_right.setWidgetResizable(True)
        scroll_right.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_right.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_right.setFixedWidth(295)
        scroll_right.setFrameShape(QFrame.Shape.NoFrame)
        scroll_right.setStyleSheet("background-color: transparent;")

        sidebar_right = QFrame(self)
        sidebar_right.setObjectName("sidebar_right")
        right_layout = QVBoxLayout(sidebar_right)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(15)
        
        # A. Pose Presets Library
        self.grp_presets = QGroupBox(i18n.get_translation("presets_panel", self.lang), self)
        grp_presets_layout = QVBoxLayout(self.grp_presets)
        grp_presets_layout.setSpacing(10)
        
        # Category selection
        self.lbl_category = QLabel(i18n.get_translation("presets_panel", self.lang), self)
        self.combo_category = QComboBox(self)
        self.combo_category.currentIndexChanged.connect(self.on_category_changed)
        
        grp_presets_layout.addWidget(self.lbl_category)
        grp_presets_layout.addWidget(self.combo_category)
        
        # Container widget for dynamic buttons
        self.preset_buttons_container = QWidget(self)
        self.preset_buttons_layout = QVBoxLayout(self.preset_buttons_container)
        self.preset_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.preset_buttons_layout.setSpacing(6)
        
        grp_presets_layout.addWidget(self.preset_buttons_container)
        right_layout.addWidget(self.grp_presets)
        
        # B. Canvas & Background Settings Group
        self.grp_settings = QGroupBox(i18n.get_translation("canvas_settings", self.lang), self)
        grp_settings_layout = QVBoxLayout(self.grp_settings)
        grp_settings_layout.setSpacing(8)
        
        # Base Bg dropdown
        self.lbl_bg_color = QLabel(i18n.get_translation("canvas_color", self.lang), self)
        self.combo_bg_color = QComboBox(self)
        self.combo_bg_color.currentIndexChanged.connect(self.change_canvas_bg_color)
        
        # Resolution dropdown
        self.lbl_resolution = QLabel(i18n.get_translation("resolution", self.lang), self)
        self.combo_res = QComboBox(self)
        self.combo_res.currentIndexChanged.connect(self.change_resolution)
        
        # Composition Guidelines dropdown
        self.lbl_guide = QLabel(i18n.get_translation("grid_type", self.lang), self)
        self.combo_guide = QComboBox(self)
        self.combo_guide.currentIndexChanged.connect(self.change_composition_guide)

        # Joint Labels Overlay dropdown
        self.lbl_labels = QLabel(i18n.get_translation("labels_type", self.lang), self)
        self.combo_labels = QComboBox(self)
        self.combo_labels.currentIndexChanged.connect(self.change_labels_mode)
        
        # Scale & XYZ axes checkbox
        self.chk_scale_axes = QCheckBox(i18n.get_translation("show_scale_axes", self.lang), self)
        self.chk_scale_axes.setChecked(True)
        self.chk_scale_axes.toggled.connect(self.change_scale_axes_visibility)
        
        # Pose Name checkbox
        self.chk_pose_name = QCheckBox(i18n.get_translation("show_pose_name", self.lang), self)
        self.chk_pose_name.setChecked(True)
        self.chk_pose_name.toggled.connect(self.change_pose_name_visibility)
        
        # Export background image checkbox
        self.chk_export_bg = QCheckBox(i18n.get_translation("export_bg", self.lang), self)
        self.chk_export_bg.setChecked(True)
        
        grp_settings_layout.addWidget(self.lbl_bg_color)
        grp_settings_layout.addWidget(self.combo_bg_color)
        grp_settings_layout.addWidget(self.lbl_resolution)
        grp_settings_layout.addWidget(self.combo_res)
        grp_settings_layout.addWidget(self.lbl_guide)
        grp_settings_layout.addWidget(self.combo_guide)
        grp_settings_layout.addWidget(self.lbl_labels)
        grp_settings_layout.addWidget(self.combo_labels)
        grp_settings_layout.addWidget(self.chk_scale_axes)
        grp_settings_layout.addWidget(self.chk_pose_name)
        grp_settings_layout.addWidget(self.chk_export_bg)
        
        # Ref Background Trace image load
        self.lbl_bg_trace = QLabel(i18n.get_translation("bg_image", self.lang), self)
        self.btn_load_bg = QPushButton(i18n.get_translation("load_bg", self.lang), self)
        self.btn_load_bg.clicked.connect(self.load_reference_bg)
        
        self.btn_clear_bg = QPushButton(i18n.get_translation("clear_bg", self.lang), self)
        self.btn_clear_bg.clicked.connect(self.clear_reference_bg)
        
        # Opacity slider
        self.lbl_bg_opacity = QLabel(i18n.get_translation("bg_opacity", self.lang) + "50%", self)
        self.slider_opacity = QSlider(Qt.Orientation.Horizontal, self)
        self.slider_opacity.setRange(0, 100)
        self.slider_opacity.setValue(50)
        self.slider_opacity.valueChanged.connect(self.adjust_bg_opacity)
        
        grp_settings_layout.addWidget(self.lbl_bg_trace)
        grp_settings_layout.addWidget(self.btn_load_bg)
        grp_settings_layout.addWidget(self.btn_clear_bg)
        grp_settings_layout.addWidget(self.lbl_bg_opacity)
        grp_settings_layout.addWidget(self.slider_opacity)
        
        right_layout.addWidget(self.grp_settings)
        right_layout.addStretch()
        scroll_right.setWidget(sidebar_right)
        work_layout.addWidget(scroll_right)
        
        main_layout.addLayout(work_layout)
        
        # 3. Bottom Action Bar (Large Export Button & Status)
        bottom_layout = QHBoxLayout()
        self.btn_export = QPushButton(i18n.get_translation("export_btn", self.lang), self)
        self.btn_export.setObjectName("btn_primary")
        self.btn_export.setFixedHeight(45)
        self.btn_export.clicked.connect(self.export_pose_image)
        bottom_layout.addWidget(self.btn_export)
        main_layout.addLayout(bottom_layout)
        
        # 4. Status Bar
        self.status_bar_frame = QFrame(self)
        self.status_bar_frame.setObjectName("status_bar")
        sbf_layout = QHBoxLayout(self.status_bar_frame)
        sbf_layout.setContentsMargins(10, 4, 10, 4)
        
        self.lbl_status = QLabel(i18n.get_translation("status_ready", self.lang), self)
        sbf_layout.addWidget(self.lbl_status)
        main_layout.addWidget(self.status_bar_frame)

    def retranslate_ui(self):
        """Updates text elements, group box titles, dropdowns, and button labels to active language."""
        self.setWindowTitle(i18n.get_translation("title", self.lang))
        self.lbl_app_title.setText(i18n.get_translation("title", self.lang))
        self.btn_lang.setText(i18n.get_translation("switch_lang", self.lang))
        
        # Left Panel
        self.grp_chars.setTitle(i18n.get_translation("char_manager", self.lang))
        self.btn_add_char.setText(i18n.get_translation("add_char", self.lang))
        self.btn_del_char.setText(i18n.get_translation("del_char", self.lang))
        
        # Operations Group Title shows the current active character
        active_idx = self.canvas.selected_char_idx
        if active_idx != -1:
            title_text = i18n.get_translation("char_label", self.lang).format(active_idx + 1)
        else:
            title_text = i18n.get_translation("char_manager", self.lang)
        self.grp_operations.setTitle(title_text)
        
        self.btn_lock.setText(i18n.get_translation("lock", self.lang))
        self.btn_visible.setText(i18n.get_translation("visible", self.lang))
        self.btn_mirror.setText(i18n.get_translation("mirror_pose", self.lang))
        self.btn_reset.setText(i18n.get_translation("reset_pose", self.lang))
        
        # Sliders text
        sk_height_val = self.slider_height.value()
        sk_limb_val = self.slider_limb.value()
        self.lbl_height_scale.setText(i18n.get_translation("height_scale", self.lang) + f"{sk_height_val}%")
        self.lbl_limb_scale.setText(i18n.get_translation("limb_scale", self.lang) + f"{sk_limb_val}%")
        
        # Right Panel - Presets
        self.grp_presets.setTitle(i18n.get_translation("presets_panel", self.lang))
        self.lbl_category.setText(i18n.get_translation("presets_panel", self.lang))
        
        # Populate Category dropdown dynamically without losing selection
        curr_cat_idx = max(0, self.combo_category.currentIndex())
        self.combo_category.blockSignals(True)
        self.combo_category.clear()
        for cat_key, names in pose_presets.CATEGORY_DISPLAY_NAMES.items():
            disp = names.get(self.lang, cat_key)
            self.combo_category.addItem(disp, cat_key)
        self.combo_category.setCurrentIndex(curr_cat_idx)
        self.combo_category.blockSignals(False)
        
        # Regenerate buttons
        self.on_category_changed()
        
        # Canvas Settings Panel
        self.grp_settings.setTitle(i18n.get_translation("canvas_settings", self.lang))
        self.lbl_bg_color.setText(i18n.get_translation("canvas_color", self.lang))
        self.lbl_resolution.setText(i18n.get_translation("resolution", self.lang))
        self.lbl_guide.setText(i18n.get_translation("grid_type", self.lang))
        
        # Populate Comboboxes without losing selection indexes
        # 1. Canvas Base Colors
        curr_bg_idx = max(0, self.combo_bg_color.currentIndex())
        self.combo_bg_color.blockSignals(True)
        self.combo_bg_color.clear()
        self.combo_bg_color.addItem(i18n.get_translation("bg_black", self.lang), "black")
        self.combo_bg_color.addItem(i18n.get_translation("bg_white", self.lang), "white")
        self.combo_bg_color.addItem(i18n.get_translation("bg_transparent", self.lang), "transparent")
        self.combo_bg_color.setCurrentIndex(curr_bg_idx)
        self.combo_bg_color.blockSignals(False)
        
        # 2. Canvas Resolution Preset Choices
        curr_res_idx = max(0, self.combo_res.currentIndex())
        self.combo_res.blockSignals(True)
        self.combo_res.clear()
        self.combo_res.addItem("512 x 512 (1:1 Square)", (512, 512))
        self.combo_res.addItem("512 x 768 (2:3 Portrait)", (512, 768))
        self.combo_res.addItem("768 x 512 (3:2 Landscape)", (768, 512))
        self.combo_res.addItem("768 x 768", (768, 768))
        self.combo_res.addItem("1024 x 1024", (1024, 1024))
        self.combo_res.setCurrentIndex(curr_res_idx)
        self.combo_res.blockSignals(False)
        
        # 3. Composition Grid lines
        curr_guide_idx = max(0, self.combo_guide.currentIndex())
        self.combo_guide.blockSignals(True)
        self.combo_guide.clear()
        self.combo_guide.addItem(i18n.get_translation("grid_none", self.lang), "none")
        self.combo_guide.addItem(i18n.get_translation("grid_thirds", self.lang), "thirds")
        self.combo_guide.addItem(i18n.get_translation("grid_golden", self.lang), "golden")
        self.combo_guide.setCurrentIndex(curr_guide_idx)
        self.combo_guide.blockSignals(False)
        
        # 4. Joint labels
        self.lbl_labels.setText(i18n.get_translation("labels_type", self.lang))
        curr_labels_idx = max(0, self.combo_labels.currentIndex())
        self.combo_labels.blockSignals(True)
        self.combo_labels.clear()
        self.combo_labels.addItem(i18n.get_translation("labels_none", self.lang), "none")
        self.combo_labels.addItem(i18n.get_translation("labels_indices", self.lang), "indices")
        self.combo_labels.addItem(i18n.get_translation("labels_names", self.lang), "names")
        self.combo_labels.setCurrentIndex(curr_labels_idx)
        self.combo_labels.blockSignals(False)
        
        # Scale & XYZ axes checkbox
        self.chk_scale_axes.setText(i18n.get_translation("show_scale_axes", self.lang))
        
        # Pose Name checkbox
        self.chk_pose_name.setText(i18n.get_translation("show_pose_name", self.lang))
        
        # Export background image checkbox
        self.chk_export_bg.setText(i18n.get_translation("export_bg", self.lang))
        
        # Load background reference block
        self.lbl_bg_trace.setText(i18n.get_translation("bg_image", self.lang))
        self.btn_load_bg.setText(i18n.get_translation("load_bg", self.lang))
        self.btn_clear_bg.setText(i18n.get_translation("clear_bg", self.lang))
        
        opacity_val = self.slider_opacity.value()
        self.lbl_bg_opacity.setText(i18n.get_translation("bg_opacity", self.lang) + f"{opacity_val}%")
        
        # Bottom Actions
        self.btn_export.setText(i18n.get_translation("export_btn", self.lang))
        self.lbl_status.setText(i18n.get_translation("status_ready", self.lang))
        
        self.update_character_ui_list()

    # --- BUTTON / INTERACTION EVENT HANDLERS ---

    def toggle_language(self):
        """Switches languages between zh_TW and en_US."""
        self.lang = "en_US" if self.lang == "zh_TW" else "zh_TW"
        self.canvas.set_language(self.lang)
        self.retranslate_ui()

    def add_character(self):
        """Adds a new default character pose to the screen (Max 2)."""
        if len(self.skeletons) >= 2:
            self.lbl_status.setText(f"⚠️ {i18n.get_translation('limit_reached', self.lang)}")
            return
            
        # Spawn new character slightly offset to the right so they don't overlap perfectly
        new_stand_pts = pose_presets.get_preset_pose("single_stand", 80, 20)
        self.skeletons.append({
            "points": new_stand_pts,
            "original_points": list(new_stand_pts),
            "visible": True,
            "locked": False,
            "height_scale": 1.0,
            "limb_scale": 1.0,
            "pose_name": "single_stand"
        })
        
        self.canvas.set_skeletons(self.skeletons)
        self.select_character(len(self.skeletons) - 1)
        self.update_character_ui_list()
        
    def delete_character(self):
        """Deletes the active selected character."""
        active_idx = self.canvas.selected_char_idx
        if active_idx == -1 or len(self.skeletons) <= 0:
            self.lbl_status.setText(f"⚠️ {i18n.get_translation('no_char_selected', self.lang)}")
            return
            
        self.skeletons.pop(active_idx)
        self.canvas.set_skeletons(self.skeletons)
        
        # Change selection index
        new_idx = 0 if len(self.skeletons) > 0 else -1
        self.select_character(new_idx)
        self.update_character_ui_list()

    def toggle_active_character_lock(self):
        """Locks/unlocks editing constraints for the current active character."""
        active_idx = self.canvas.selected_char_idx
        if active_idx == -1:
            return
            
        self.skeletons[active_idx]["locked"] = not self.skeletons[active_idx]["locked"]
        self.update_character_ui_list()
        self.canvas.update()

    def toggle_active_character_visibility(self):
        """Shows/hides active character skeleton."""
        active_idx = self.canvas.selected_char_idx
        if active_idx == -1:
            return
            
        self.skeletons[active_idx]["visible"] = not self.skeletons[active_idx]["visible"]
        self.update_character_ui_list()
        self.canvas.update()

    def mirror_active_pose(self):
        """Mirrors the active character pose horizontally around its neck Y axis."""
        active_idx = self.canvas.selected_char_idx
        if active_idx == -1:
            return
            
        sk = self.skeletons[active_idx]
        if sk["locked"]:
            return
            
        # Standard mirror around Neck (index 1) X coordinate
        points = sk["points"]
        neck_x = points[1][0]
        
        sk["points"] = pose_math.mirror_pose(points, neck_x)
        sk["original_points"] = pose_math.mirror_pose(sk["original_points"], neck_x)
        self.canvas.update()

    def reset_active_pose(self):
        """Resets active character back to standing preset posture."""
        active_idx = self.canvas.selected_char_idx
        if active_idx == -1:
            return
            
        sk = self.skeletons[active_idx]
        if sk["locked"]:
            return
            
        # Re-initialize to standard standing pose centered around current Neck position
        curr_neck = sk["points"][1]
        
        # Standard stand initially neck is at (256, 150)
        # So offset is dx = curr_neck[0] - 256, dy = curr_neck[1] - 150
        dx = curr_neck[0] - 256.0
        dy = curr_neck[1] - 150.0
        
        new_stand = pose_presets.get_preset_pose("single_stand", dx, dy)
        sk["points"] = new_stand
        sk["original_points"] = list(new_stand)
        
        # Reset sliders to 100%
        sk["height_scale"] = 1.0
        sk["limb_scale"] = 1.0
        
        self.slider_height.blockSignals(True)
        self.slider_limb.blockSignals(True)
        self.slider_height.setValue(100)
        self.slider_limb.setValue(100)
        self.slider_height.blockSignals(False)
        self.slider_limb.blockSignals(False)
        
        self.lbl_height_scale.setText(i18n.get_translation("height_scale", self.lang) + "100%")
        self.lbl_limb_scale.setText(i18n.get_translation("limb_scale", self.lang) + "100%")
        
        self.canvas.update()

    def adjust_character_proportions(self):
        """Updates active character proportions dynamically based on sidebar slider values."""
        active_idx = self.canvas.selected_char_idx
        if active_idx == -1:
            return
            
        sk = self.skeletons[active_idx]
        if sk["locked"]:
            return
            
        height_val = self.slider_height.value()
        limb_val = self.slider_limb.value()
        
        self.lbl_height_scale.setText(i18n.get_translation("height_scale", self.lang) + f"{height_val}%")
        self.lbl_limb_scale.setText(i18n.get_translation("limb_scale", self.lang) + f"{limb_val}%")
        
        sk["height_scale"] = height_val / 100.0
        sk["limb_scale"] = limb_val / 100.0
        
        # Re-apply proportions dynamically on the baseline original pose coordinates
        sk["points"] = pose_math.adjust_proportions(
            sk["original_points"],
            sk["height_scale"],
            sk["limb_scale"]
        )
        self.canvas.update()

    def on_canvas_pose_changed(self):
        """Called when user manually drags a joint in the canvas. Resets sliders baseline."""
        active_idx = self.canvas.selected_char_idx
        if active_idx == -1:
            return
            
        sk = self.skeletons[active_idx]
        # Copy modified points to original points establishing a new baseline pose
        sk["original_points"] = list(sk["points"])
        
        # Mark as modified pose
        if not sk.get("pose_name", "").endswith("_modified"):
            if sk.get("pose_name", "") and sk.get("pose_name", "") != "custom":
                sk["pose_name"] = sk["pose_name"] + "_modified"
            else:
                sk["pose_name"] = "custom"
        
        # Reset sliders block signals
        sk["height_scale"] = 1.0
        sk["limb_scale"] = 1.0
        
        self.slider_height.blockSignals(True)
        self.slider_limb.blockSignals(True)
        self.slider_height.setValue(100)
        self.slider_limb.setValue(100)
        self.slider_height.blockSignals(False)
        self.slider_limb.blockSignals(False)
        
        self.lbl_height_scale.setText(i18n.get_translation("height_scale", self.lang) + "100%")
        self.lbl_limb_scale.setText(i18n.get_translation("limb_scale", self.lang) + "100%")

    # --- SIDEBAR PRESET TRIGGERS ---

    def on_category_changed(self):
        """Clears old buttons and dynamically creates buttons for the selected category."""
        # Clear layout
        while self.preset_buttons_layout.count():
            item = self.preset_buttons_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        # Get active category
        cat_key = self.combo_category.currentData()
        if not cat_key:
            return
            
        # Fetch poses
        pose_keys = pose_presets.POSE_CATEGORIES.get(cat_key, [])
        for pk in pose_keys:
            names = pose_presets.POSE_DISPLAY_NAMES.get(pk, {})
            display_name = names.get(self.lang, pk)
            
            btn = QPushButton(display_name, self)
            if cat_key == "double":
                btn.clicked.connect(lambda checked=False, k=pk: self.apply_double_preset(k))
            else:
                btn.clicked.connect(lambda checked=False, k=pk: self.apply_preset(k))
                
            self.preset_buttons_layout.addWidget(btn)

    def apply_preset(self, name: str):
        """Applies a single person preset to the active character."""
        active_idx = self.canvas.selected_char_idx
        if active_idx == -1:
            self.lbl_status.setText(f"⚠️ {i18n.get_translation('no_char_selected', self.lang)}")
            return
            
        sk = self.skeletons[active_idx]
        if sk["locked"]:
            return
            
        # Get active neck position to preserve characters layout location
        curr_neck = sk["points"][1]
        dx = curr_neck[0] - 256.0
        dy = curr_neck[1] - 150.0
        
        preset_pts = pose_presets.get_preset_pose(name, dx, dy)
        sk["points"] = preset_pts
        sk["original_points"] = list(preset_pts)
        sk["pose_name"] = name
        
        # Reset sliders
        sk["height_scale"] = 1.0
        sk["limb_scale"] = 1.0
        self.slider_height.setValue(100)
        self.slider_limb.setValue(100)
        
        self.canvas.update()

    def apply_double_preset(self, name: str):
        """Applies dual-character interactive preset (Hug, fight, handshake). Adds character if only one exists."""
        # Ensure we have exactly 2 characters initialized
        if len(self.skeletons) < 2:
            self.add_character()
            
        # Get presets coordinates
        p1_pts, p2_pts = pose_presets.get_double_preset_pose(name)
        
        # Assign to character 1 & 2
        self.skeletons[0]["points"] = p1_pts
        self.skeletons[0]["original_points"] = list(p1_pts)
        self.skeletons[0]["height_scale"] = 1.0
        self.skeletons[0]["limb_scale"] = 1.0
        self.skeletons[0]["pose_name"] = name
        
        self.skeletons[1]["points"] = p2_pts
        self.skeletons[1]["original_points"] = list(p2_pts)
        self.skeletons[1]["height_scale"] = 1.0
        self.skeletons[1]["limb_scale"] = 1.0
        self.skeletons[1]["pose_name"] = name
        
        # Reset sliders on screen
        self.slider_height.setValue(100)
        self.slider_limb.setValue(100)
        
        self.select_character(0)
        self.update_character_ui_list()
        self.canvas.update()

    # --- CANVAS & BACKGROUND CONFIGURATIONS ---

    def change_canvas_bg_color(self):
        """Changes the solid base color behind the skeleton canvas."""
        bg_mode = self.combo_bg_color.currentData()
        if bg_mode:
            self.canvas_bg_color = bg_mode
            self.canvas.set_canvas_bg_color(bg_mode)

    def change_resolution(self):
        """Modifies virtual canvas pixel boundary proportions (e.g. 512x768)."""
        size_data = self.combo_res.currentData()
        if size_data:
            w, h = size_data
            self.canvas_width = w
            self.canvas_height = h
            self.canvas.set_canvas_size(w, h)

    def change_composition_guide(self):
        """Changes composition layout dividing line overlays."""
        guide_mode = self.combo_guide.currentData()
        if guide_mode:
            self.canvas.set_grid_type(guide_mode)

    def change_labels_mode(self):
        """Updates the skeleton labels overlay mode on the canvas."""
        labels_mode = self.combo_labels.currentData()
        if labels_mode:
            self.canvas.set_labels_mode(labels_mode)

    def change_scale_axes_visibility(self):
        """Toggles drawing of scale bar and XYZ axes overlay on the canvas."""
        self.canvas.set_show_scale_axes(self.chk_scale_axes.isChecked())

    def change_pose_name_visibility(self):
        """Toggles drawing of floating pose name label on the canvas."""
        self.canvas.set_show_pose_name(self.chk_pose_name.isChecked())

    def load_reference_bg(self):
        """Prompts user to select a tracing reference photo loaded underneath skeletons."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            i18n.get_translation("load_bg_title", self.lang),
            "",
            f"{i18n.get_translation('image_files', self.lang)};;{i18n.get_translation('all_files', self.lang)}"
        )
        if file_path:
            self.canvas.set_background_image(file_path)
            self.lbl_status.setText(f"📂 Loaded: {os.path.basename(file_path)}")

    def clear_reference_bg(self):
        """Removes background tracing image template."""
        self.canvas.set_background_image("")
        self.lbl_status.setText(i18n.get_translation("status_ready", self.lang))

    def adjust_bg_opacity(self):
        """Adjusts blending transparency of the reference image."""
        val = self.slider_opacity.value()
        self.lbl_bg_opacity.setText(i18n.get_translation("bg_opacity", self.lang) + f"{val}%")
        self.canvas.set_background_opacity(val / 100.0)

    # --- EXPORT ---

    def export_pose_image(self):
        """Renders vector skeletons headlessly and saves to an image file."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"pose_{timestamp}.png"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            i18n.get_translation("save_image_title", self.lang),
            default_name,
            f"{i18n.get_translation('image_files', self.lang)};;{i18n.get_translation('all_files', self.lang)}"
        )
        
        if not file_path:
            return  # Cancelled
            
        # Determine format extension to set transparency defaults
        bg_mode = self.canvas_bg_color
        if bg_mode == "transparent" and not file_path.lower().endswith(".png"):
            # Transparent needs PNG, fallback to black base for JPG
            bg_mode = "black"
            
        labels_mode = self.combo_labels.currentData() or "none"
        
        # Check if reference background image should be exported
        export_bg_path = ""
        export_bg_opacity = 1.0
        if self.chk_export_bg.isChecked() and self.canvas.bg_image_path:
            export_bg_path = self.canvas.bg_image_path
            export_bg_opacity = self.canvas.bg_opacity

        success = pose_io.export_to_image(
            canvas_size=(self.canvas_width, self.canvas_height),
            skeletons=self.skeletons,
            background_mode=bg_mode,
            file_path=file_path,
            labels_mode=labels_mode,
            lang=self.lang,
            show_scale_axes=self.chk_scale_axes.isChecked(),
            show_pose_name=self.chk_pose_name.isChecked(),
            bg_image_path=export_bg_path,
            bg_opacity=export_bg_opacity
        )
        
        if success:
            # Generate Gemini sidecar prompt file
            txt_path = pose_io.generate_sidecar_prompt(
                canvas_size=(self.canvas_width, self.canvas_height),
                skeletons=self.skeletons,
                file_path=file_path,
                lang=self.lang
            )
            
            success_msg = i18n.get_translation("export_success_sidecar_msg", self.lang).format(
                os.path.basename(file_path),
                os.path.basename(txt_path)
            )
            
            QMessageBox.information(
                self,
                i18n.get_translation("export_success", self.lang),
                success_msg
            )
            self.lbl_status.setText(f"✔️ Saved image & Gemini sidecar prompt.")
        else:
            QMessageBox.critical(
                self,
                i18n.get_translation("export_error", self.lang),
                i18n.get_translation("export_error_msg", self.lang).format("Could not write file to path.")
            )


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
