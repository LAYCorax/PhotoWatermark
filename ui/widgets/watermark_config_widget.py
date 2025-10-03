"""
Watermark Configuration Widget
Provides controls for configuring watermark settings
"""
from typing import Optional

try:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QLineEdit, QComboBox, QSlider, QSpinBox, QCheckBox,
        QGroupBox, QColorDialog, QFileDialog, QTabWidget,
        QFrame, QSizePolicy, QButtonGroup, QRadioButton,
        QGridLayout
    )
    from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
    from PyQt5.QtGui import QFont, QColor, QPalette, QFontDatabase
except ImportError:
    print("PyQt5 is required but not installed.")
    raise

from utils.logger import logger, log_exception
from models.watermark_config import (
    WatermarkConfig, WatermarkType, WatermarkPosition,
    TextWatermarkConfig, ImageWatermarkConfig
)


class ColorButton(QPushButton):
    """Custom button for color selection"""
    
    color_changed = pyqtSignal(tuple)  # RGB tuple
    
    def __init__(self, initial_color=(255, 255, 255)):
        super().__init__()
        self.current_color = initial_color
        self.setFixedSize(40, 25)
        self.update_color_display()
        self.clicked.connect(self.select_color)
    
    def update_color_display(self):
        """Update button appearance to show current color"""
        r, g, b = self.current_color
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgb({r}, {g}, {b});
                border: 1px solid #999;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                border: 2px solid #666;
            }}
        """)
    
    @pyqtSlot()
    def select_color(self):
        """Open color selection dialog"""
        color = QColorDialog.getColor(
            QColor(*self.current_color),
            self,
            "选择颜色"
        )
        
        if color.isValid():
            self.current_color = (color.red(), color.green(), color.blue())
            self.update_color_display()
            self.color_changed.emit(self.current_color)
    
    def set_color(self, color: tuple):
        """Set color programmatically"""
        self.current_color = color
        self.update_color_display()


class TextWatermarkWidget(QWidget):
    """Widget for text watermark configuration"""
    
    config_changed = pyqtSignal()
    
    def __init__(self, config: TextWatermarkConfig):
        super().__init__()
        self.config = config
        self.init_ui()
        self.setup_connections()
        self.update_ui_from_config()
    
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Text input
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("文本:"))
        self.text_edit = QLineEdit()
        self.text_edit.setPlaceholderText("输入水印文本...")
        text_layout.addWidget(self.text_edit)
        layout.addLayout(text_layout)
        
        # Font settings
        font_group = QGroupBox("字体设置")
        font_layout = QGridLayout(font_group)
        
        # Font family
        font_layout.addWidget(QLabel("字体:"), 0, 0)
        self.font_combo = QComboBox()
        self.font_combo.setEditable(False)  # 设置为不可编辑，只能选择
        self.font_combo.setMaxVisibleItems(20)  # 设置下拉列表最多显示20项
        
        # 设置下拉框样式，增强选中状态的可见性，移除hover白色效果
        self.font_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background: white;
            }
            QComboBox:hover {
                border: 1px solid #3498db;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #ccc;
                selection-color: black;
                background: white;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 6px 10px;
                min-height: 25px;
            }
            QComboBox QAbstractItemView::item:selected {
                background: #3498db;
                color: black;
            }
            QComboBox QAbstractItemView::item:hover:!selected {
                background: #e8f4f8;
                color: black;
            }
        """)
        
        # 获取系统所有可用字体，按字母顺序排序
        font_db = QFontDatabase()
        system_fonts = sorted(font_db.families())
        
        # 添加所有系统字体（支持滚动）
        for font in system_fonts:
            self.font_combo.addItem(font)

        font_layout.addWidget(self.font_combo, 0, 1)
        
        # Font size
        font_layout.addWidget(QLabel("大小:"), 1, 0)
        size_layout = QHBoxLayout()
        self.size_spinbox = QSpinBox()
        self.size_spinbox.setRange(8, 200)
        self.size_spinbox.setSuffix(" px")
        size_layout.addWidget(self.size_spinbox)
        
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(8, 200)
        size_layout.addWidget(self.size_slider)
        font_layout.addLayout(size_layout, 1, 1)
        
        # Font style
        style_layout = QHBoxLayout()
        self.bold_checkbox = QCheckBox("粗体")
        self.italic_checkbox = QCheckBox("斜体")
        style_layout.addWidget(self.bold_checkbox)
        style_layout.addWidget(self.italic_checkbox)
        font_layout.addLayout(style_layout, 2, 0, 1, 2)
        
        layout.addWidget(font_group)
        
        # Color and opacity
        appearance_group = QGroupBox("外观设置")
        appearance_layout = QGridLayout(appearance_group)
        
        # Text color
        appearance_layout.addWidget(QLabel("颜色:"), 0, 0)
        self.color_button = ColorButton()
        appearance_layout.addWidget(self.color_button, 0, 1)
        
        # Opacity
        appearance_layout.addWidget(QLabel("不透明度:"), 1, 0)
        opacity_layout = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_label = QLabel("80%")
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_label)
        appearance_layout.addLayout(opacity_layout, 1, 1)
        
        layout.addWidget(appearance_group)
        
        # Text effects
        effects_group = QGroupBox("文字特效")
        effects_layout = QGridLayout(effects_group)
        
        # Shadow effect
        self.shadow_checkbox = QCheckBox("阴影")
        effects_layout.addWidget(self.shadow_checkbox, 0, 0, 1, 2)  # Span 2 columns
        
        # Shadow settings with each property on separate lines
        shadow_settings_widget = QWidget()
        shadow_settings_layout = QVBoxLayout(shadow_settings_widget)
        shadow_settings_layout.setContentsMargins(20, 5, 5, 5)  # Add left margin for indentation
        shadow_settings_layout.setSpacing(5)
        
        # Color line
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("颜色:"))
        self.shadow_color_button = ColorButton((0, 0, 0))
        color_layout.addWidget(self.shadow_color_button)
        color_layout.addStretch()
        shadow_settings_layout.addLayout(color_layout)
        
        # Offset line
        offset_layout = QHBoxLayout()
        offset_layout.addWidget(QLabel("偏移 X:"))
        self.shadow_x_spinbox = QSpinBox()
        self.shadow_x_spinbox.setRange(-20, 20)
        self.shadow_x_spinbox.setValue(3)
        self.shadow_x_spinbox.setMaximumWidth(60)
        offset_layout.addWidget(self.shadow_x_spinbox)
        offset_layout.addWidget(QLabel("Y:"))
        self.shadow_y_spinbox = QSpinBox()
        self.shadow_y_spinbox.setRange(-20, 20)
        self.shadow_y_spinbox.setValue(3)
        self.shadow_y_spinbox.setMaximumWidth(60)
        offset_layout.addWidget(self.shadow_y_spinbox)
        offset_layout.addStretch()
        shadow_settings_layout.addLayout(offset_layout)
        
        # Opacity line with slider
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("不透明度:"))
        
        # Add slider for shadow opacity
        self.shadow_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.shadow_opacity_slider.setRange(0, 100)
        self.shadow_opacity_slider.setValue(60)
        self.shadow_opacity_slider.setMinimumWidth(120)
        opacity_layout.addWidget(self.shadow_opacity_slider)
        
        # Keep spinbox for precise control
        self.shadow_opacity_spinbox = QSpinBox()
        self.shadow_opacity_spinbox.setRange(0, 100)
        self.shadow_opacity_spinbox.setValue(60)
        self.shadow_opacity_spinbox.setSuffix("%")
        self.shadow_opacity_spinbox.setMaximumWidth(80)
        opacity_layout.addWidget(self.shadow_opacity_spinbox)
        opacity_layout.addStretch()
        shadow_settings_layout.addLayout(opacity_layout)
        
        effects_layout.addWidget(shadow_settings_widget, 1, 0, 1, 2)  # Span 2 columns
        
        # Outline effect
        self.outline_checkbox = QCheckBox("描边")
        effects_layout.addWidget(self.outline_checkbox, 2, 0, 1, 2)  # Span 2 columns
        
        # Outline settings with each property on separate lines
        outline_settings_widget = QWidget()
        outline_settings_layout = QVBoxLayout(outline_settings_widget)
        outline_settings_layout.setContentsMargins(20, 5, 5, 5)  # Add left margin for indentation
        outline_settings_layout.setSpacing(5)
        
        # Color line
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("颜色:"))
        self.outline_color_button = ColorButton((0, 0, 0))
        color_layout.addWidget(self.outline_color_button)
        color_layout.addStretch()
        outline_settings_layout.addLayout(color_layout)
        
        # Width line
        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("宽度:"))
        self.outline_width_spinbox = QSpinBox()
        self.outline_width_spinbox.setRange(1, 10)
        self.outline_width_spinbox.setValue(2)
        self.outline_width_spinbox.setMaximumWidth(60)
        width_layout.addWidget(self.outline_width_spinbox)
        width_layout.addStretch()
        outline_settings_layout.addLayout(width_layout)
        
        # Opacity line with slider
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("不透明度:"))
        
        # Add slider for outline opacity
        self.outline_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.outline_opacity_slider.setRange(0, 100)
        self.outline_opacity_slider.setValue(100)
        self.outline_opacity_slider.setMinimumWidth(120)
        opacity_layout.addWidget(self.outline_opacity_slider)
        
        # Keep spinbox for precise control
        self.outline_opacity_spinbox = QSpinBox()
        self.outline_opacity_spinbox.setRange(0, 100)
        self.outline_opacity_spinbox.setValue(100)
        self.outline_opacity_spinbox.setSuffix("%")
        self.outline_opacity_spinbox.setMaximumWidth(80)
        opacity_layout.addWidget(self.outline_opacity_spinbox)
        opacity_layout.addStretch()
        outline_settings_layout.addLayout(opacity_layout)
        
        effects_layout.addWidget(outline_settings_widget, 3, 0, 1, 2)  # Span 2 columns
        
        # Initially disable effect controls
        self._toggle_shadow_controls(False)
        self._toggle_outline_controls(False)
        
        layout.addWidget(effects_group)
        layout.addStretch()
    
    def setup_connections(self):
        """Setup signal connections"""
        self.text_edit.textChanged.connect(self.on_text_changed)
        self.font_combo.currentTextChanged.connect(self.on_font_changed)
        self.size_spinbox.valueChanged.connect(self.on_size_changed)
        self.size_slider.valueChanged.connect(self.on_size_slider_changed)
        self.bold_checkbox.toggled.connect(self.on_bold_changed)
        self.italic_checkbox.toggled.connect(self.on_italic_changed)
        self.color_button.color_changed.connect(self.on_color_changed)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        
        # Shadow and outline connections
        self.shadow_checkbox.toggled.connect(self.on_shadow_toggled)
        self.shadow_color_button.color_changed.connect(self.on_shadow_color_changed)
        self.shadow_x_spinbox.valueChanged.connect(self.on_shadow_offset_changed)
        self.shadow_y_spinbox.valueChanged.connect(self.on_shadow_offset_changed)
        
        self.outline_checkbox.toggled.connect(self.on_outline_toggled)
        self.outline_color_button.color_changed.connect(self.on_outline_color_changed)
        self.outline_width_spinbox.valueChanged.connect(self.on_outline_width_changed)
        self.outline_opacity_spinbox.valueChanged.connect(self.on_outline_opacity_changed)
        self.outline_opacity_slider.valueChanged.connect(self.on_outline_opacity_slider_changed)
        
        self.shadow_opacity_spinbox.valueChanged.connect(self.on_shadow_opacity_changed)
        self.shadow_opacity_slider.valueChanged.connect(self.on_shadow_opacity_slider_changed)
    
    def update_ui_from_config(self):
        """Update UI controls from configuration"""
        self.text_edit.setText(self.config.text)
        
        # Find and set font
        index = self.font_combo.findText(self.config.font_family)
        if index >= 0:
            self.font_combo.setCurrentIndex(index)
        
        self.size_spinbox.setValue(self.config.font_size)
        self.size_slider.setValue(self.config.font_size)
        self.bold_checkbox.setChecked(self.config.font_bold)
        self.italic_checkbox.setChecked(self.config.font_italic)
        self.color_button.set_color(self.config.color)
        
        opacity_percent = int(self.config.opacity * 100)
        self.opacity_slider.setValue(opacity_percent)
        self.opacity_label.setText(f"{opacity_percent}%")
        
        # Update shadow settings
        self.shadow_checkbox.setChecked(self.config.has_shadow)
        self.shadow_color_button.set_color(self.config.shadow_color)
        self.shadow_x_spinbox.setValue(self.config.shadow_offset[0])
        self.shadow_y_spinbox.setValue(self.config.shadow_offset[1])
        shadow_opacity_percent = int(self.config.shadow_opacity * 100)
        self.shadow_opacity_spinbox.setValue(shadow_opacity_percent)
        self.shadow_opacity_slider.setValue(shadow_opacity_percent)
        self._toggle_shadow_controls(self.config.has_shadow)
        
        # Update outline settings
        self.outline_checkbox.setChecked(self.config.has_outline)
        self.outline_color_button.set_color(self.config.outline_color)
        self.outline_width_spinbox.setValue(self.config.outline_width)
        outline_opacity_percent = int(self.config.outline_opacity * 100)
        self.outline_opacity_spinbox.setValue(outline_opacity_percent)
        self.outline_opacity_slider.setValue(outline_opacity_percent)
        self._toggle_outline_controls(self.config.has_outline)
    
    @pyqtSlot(str)
    def on_text_changed(self, text: str):
        """Handle text change"""
        self.config.text = text
        self.config_changed.emit()
    
    @pyqtSlot(str)
    def on_font_changed(self, font: str):
        """Handle font change"""
        self.config.font_family = font
        self.config_changed.emit()
    
    @pyqtSlot(int)
    def on_size_changed(self, size: int):
        """Handle size change from spinbox"""
        self.config.font_size = size
        self.size_slider.blockSignals(True)
        self.size_slider.setValue(size)
        self.size_slider.blockSignals(False)
        self.config_changed.emit()
    
    @pyqtSlot(int)
    def on_size_slider_changed(self, size: int):
        """Handle size change from slider"""
        self.config.font_size = size
        self.size_spinbox.blockSignals(True)
        self.size_spinbox.setValue(size)
        self.size_spinbox.blockSignals(False)
        self.config_changed.emit()
    
    @pyqtSlot(bool)
    def on_bold_changed(self, bold: bool):
        """Handle bold change"""
        self.config.font_bold = bold
        self.config_changed.emit()
    
    @pyqtSlot(bool)
    def on_italic_changed(self, italic: bool):
        """Handle italic change"""
        self.config.font_italic = italic
        self.config_changed.emit()
    
    @pyqtSlot(tuple)
    def on_color_changed(self, color: tuple):
        """Handle color change"""
        self.config.color = color
        self.config_changed.emit()
    
    @pyqtSlot(int)
    def on_opacity_changed(self, value: int):
        """Handle opacity change"""
        self.config.opacity = value / 100.0
        self.opacity_label.setText(f"{value}%")
        self.config_changed.emit()
    
    @pyqtSlot(bool)
    def on_shadow_toggled(self, enabled: bool):
        """Handle shadow toggle"""
        self.config.has_shadow = enabled
        self._toggle_shadow_controls(enabled)
        self.config_changed.emit()
    
    def on_shadow_color_changed(self, color: tuple):
        """Handle shadow color change"""
        self.config.shadow_color = color
        self.config_changed.emit()
    
    @pyqtSlot(int)
    def on_shadow_offset_changed(self, value: int):
        """Handle shadow offset change"""
        self.config.shadow_offset = (self.shadow_x_spinbox.value(), self.shadow_y_spinbox.value())
        self.config_changed.emit()
    
    @pyqtSlot(bool)
    def on_outline_toggled(self, enabled: bool):
        """Handle outline toggle"""
        self.config.has_outline = enabled
        self._toggle_outline_controls(enabled)
        self.config_changed.emit()
    
    def on_outline_color_changed(self, color: tuple):
        """Handle outline color change"""
        self.config.outline_color = color
        self.config_changed.emit()
    
    @pyqtSlot(int)
    def on_outline_width_changed(self, value: int):
        """Handle outline width change"""
        self.config.outline_width = value
        self.config_changed.emit()
    
    @pyqtSlot(int)
    def on_shadow_opacity_changed(self, value: int):
        """Handle shadow opacity spinbox change"""
        self.config.shadow_opacity = value / 100.0
        # Sync slider without triggering signal
        self.shadow_opacity_slider.blockSignals(True)
        self.shadow_opacity_slider.setValue(value)
        self.shadow_opacity_slider.blockSignals(False)
        self.config_changed.emit()
    
    @pyqtSlot(int)
    def on_shadow_opacity_slider_changed(self, value: int):
        """Handle shadow opacity slider change"""
        self.config.shadow_opacity = value / 100.0
        # Sync spinbox without triggering signal
        self.shadow_opacity_spinbox.blockSignals(True)
        self.shadow_opacity_spinbox.setValue(value)
        self.shadow_opacity_spinbox.blockSignals(False)
        self.config_changed.emit()
    
    @pyqtSlot(int)
    def on_outline_opacity_changed(self, value: int):
        """Handle outline opacity spinbox change"""
        self.config.outline_opacity = value / 100.0
        # Sync slider without triggering signal
        self.outline_opacity_slider.blockSignals(True)
        self.outline_opacity_slider.setValue(value)
        self.outline_opacity_slider.blockSignals(False)
        self.config_changed.emit()
    
    @pyqtSlot(int)
    def on_outline_opacity_slider_changed(self, value: int):
        """Handle outline opacity slider change"""
        self.config.outline_opacity = value / 100.0
        # Sync spinbox without triggering signal
        self.outline_opacity_spinbox.blockSignals(True)
        self.outline_opacity_spinbox.setValue(value)
        self.outline_opacity_spinbox.blockSignals(False)
        self.config_changed.emit()
    
    def _toggle_shadow_controls(self, enabled: bool):
        """Enable/disable shadow controls"""
        self.shadow_color_button.setEnabled(enabled)
        self.shadow_x_spinbox.setEnabled(enabled)
        self.shadow_y_spinbox.setEnabled(enabled)
        self.shadow_opacity_spinbox.setEnabled(enabled)
        self.shadow_opacity_slider.setEnabled(enabled)
    
    def _toggle_outline_controls(self, enabled: bool):
        """Enable/disable outline controls"""
        self.outline_color_button.setEnabled(enabled)
        self.outline_width_spinbox.setEnabled(enabled)
        self.outline_opacity_spinbox.setEnabled(enabled)
        self.outline_opacity_slider.setEnabled(enabled)


class ImageWatermarkWidget(QWidget):
    """Widget for image watermark configuration"""
    
    config_changed = pyqtSignal()
    
    def __init__(self, config: ImageWatermarkConfig):
        super().__init__()
        self.config = config
        self.init_ui()
        self.setup_connections()
        self.update_ui_from_config()
    
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Image selection
        image_group = QGroupBox("水印图片")
        image_layout = QVBoxLayout(image_group)
        
        # File path
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择水印图片...")
        self.path_edit.setReadOnly(True)
        path_layout.addWidget(self.path_edit)
        
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.setFixedWidth(60)
        path_layout.addWidget(self.browse_btn)
        
        image_layout.addLayout(path_layout)
        
        # Image info
        self.info_label = QLabel("支持 PNG (推荐透明背景)、JPG、BMP 等格式")
        self.info_label.setStyleSheet("color: #666; font-size: 11px;")
        image_layout.addWidget(self.info_label)
        
        layout.addWidget(image_group)
        
        # Scale settings
        scale_group = QGroupBox("缩放设置")
        scale_layout = QGridLayout(scale_group)
        
        # Scale slider
        scale_layout.addWidget(QLabel("缩放:"), 0, 0)
        scale_control_layout = QHBoxLayout()
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(10, 300)  # 10% to 300%
        self.scale_label = QLabel("100%")
        scale_control_layout.addWidget(self.scale_slider)
        scale_control_layout.addWidget(self.scale_label)
        scale_layout.addLayout(scale_control_layout, 0, 1)
        
        # Maintain aspect ratio
        self.aspect_checkbox = QCheckBox("保持宽高比")
        scale_layout.addWidget(self.aspect_checkbox, 1, 0, 1, 2)
        
        layout.addWidget(scale_group)
        
        # Opacity
        opacity_group = QGroupBox("不透明度")
        opacity_layout = QHBoxLayout(opacity_group)
        
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_label = QLabel("80%")
        
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_label)
        
        layout.addWidget(opacity_group)
        
        # Note
        note_label = QLabel("提示：PNG 格式图片的透明背景将被保留")
        note_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        layout.addWidget(note_label)
        
        layout.addStretch()
    
    def setup_connections(self):
        """Setup signal connections"""
        self.browse_btn.clicked.connect(self.browse_image)
        self.path_edit.textChanged.connect(self.on_path_changed)
        self.scale_slider.valueChanged.connect(self.on_scale_changed)
        self.aspect_checkbox.toggled.connect(self.on_aspect_changed)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
    
    def update_ui_from_config(self):
        """Update UI controls from configuration"""
        self.path_edit.setText(self.config.image_path)
        
        scale_percent = int(self.config.scale * 100)
        self.scale_slider.setValue(scale_percent)
        self.scale_label.setText(f"{scale_percent}%")
        
        self.aspect_checkbox.setChecked(self.config.maintain_aspect_ratio)
        
        opacity_percent = int(self.config.opacity * 100)
        self.opacity_slider.setValue(opacity_percent)
        self.opacity_label.setText(f"{opacity_percent}%")
    
    @pyqtSlot()
    def browse_image(self):
        """Browse for watermark image"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择水印图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff);;PNG 文件 (*.png);;JPEG 文件 (*.jpg *.jpeg);;所有文件 (*)"
        )
        
        if file_path:
            self.path_edit.setText(file_path)
    
    @pyqtSlot(str)
    def on_path_changed(self, path: str):
        """Handle path change"""
        self.config.image_path = path
        self.config_changed.emit()
    
    @pyqtSlot(int)
    def on_scale_changed(self, value: int):
        """Handle scale change"""
        self.config.scale = value / 100.0
        self.scale_label.setText(f"{value}%")
        self.config_changed.emit()
    
    @pyqtSlot(bool)
    def on_aspect_changed(self, maintain: bool):
        """Handle aspect ratio change"""
        self.config.maintain_aspect_ratio = maintain
        self.config_changed.emit()
    
    @pyqtSlot(int)
    def on_opacity_changed(self, value: int):
        """Handle opacity change"""
        self.config.opacity = value / 100.0
        self.opacity_label.setText(f"{value}%")
        self.config_changed.emit()


class PositionWidget(QWidget):
    """Widget for watermark position configuration"""
    
    position_changed = pyqtSignal()
    
    def __init__(self, config: WatermarkConfig):
        super().__init__()
        self.config = config
        self.init_ui()
        self.setup_connections()
        self.update_ui_from_config()
    
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        
        # Position presets
        preset_group = QGroupBox("预设位置")
        preset_layout = QGridLayout(preset_group)
        
        # Create position buttons in 3x3 grid
        self.position_buttons = QButtonGroup()
        positions = [
            ("左上", WatermarkPosition.TOP_LEFT),
            ("上中", WatermarkPosition.TOP_CENTER),
            ("右上", WatermarkPosition.TOP_RIGHT),
            ("左中", WatermarkPosition.CENTER_LEFT),
            ("居中", WatermarkPosition.CENTER),
            ("右中", WatermarkPosition.CENTER_RIGHT),
            ("左下", WatermarkPosition.BOTTOM_LEFT),
            ("下中", WatermarkPosition.BOTTOM_CENTER),
            ("右下", WatermarkPosition.BOTTOM_RIGHT),
        ]
        
        for i, (text, position) in enumerate(positions):
            button = QRadioButton(text)
            button.setProperty("position", position)
            self.position_buttons.addButton(button, i)
            preset_layout.addWidget(button, i // 3, i % 3)
            # set center as default checked
            if position == WatermarkPosition.CENTER:
                button.setChecked(True)
                self.config.position = WatermarkPosition.CENTER
            else:
                button.setChecked(False)
        
        layout.addWidget(preset_group)
        
        # Margins
        margin_group = QGroupBox("边距")
        margin_layout = QGridLayout(margin_group)
        
        margin_layout.addWidget(QLabel("水平:"), 0, 0)
        self.margin_x_spinbox = QSpinBox()
        self.margin_x_spinbox.setRange(0, 500)
        self.margin_x_spinbox.setSuffix(" px")
        margin_layout.addWidget(self.margin_x_spinbox, 0, 1)
        
        margin_layout.addWidget(QLabel("垂直:"), 1, 0)
        self.margin_y_spinbox = QSpinBox()
        self.margin_y_spinbox.setRange(0, 500)
        self.margin_y_spinbox.setSuffix(" px")
        margin_layout.addWidget(self.margin_y_spinbox, 1, 1)
        
        layout.addWidget(margin_group)
        
        # Rotation control
        rotation_group = QGroupBox("旋转")
        rotation_layout = QVBoxLayout(rotation_group)
        
        rotation_control_layout = QHBoxLayout()
        self.rotation_slider = QSlider(Qt.Horizontal)
        self.rotation_slider.setRange(-180, 180)
        self.rotation_slider.setValue(0)
        self.rotation_slider.setTickPosition(QSlider.TicksBelow)
        self.rotation_slider.setTickInterval(45)
        rotation_control_layout.addWidget(self.rotation_slider)
        
        self.rotation_spinbox = QSpinBox()
        self.rotation_spinbox.setRange(-180, 180)
        self.rotation_spinbox.setSuffix("°")
        self.rotation_spinbox.setValue(0)
        self.rotation_spinbox.setFixedWidth(80)
        rotation_control_layout.addWidget(self.rotation_spinbox)
        
        rotation_layout.addLayout(rotation_control_layout)
        
        rotation_note = QLabel("提示：以水印中心点旋转")
        rotation_note.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
        rotation_layout.addWidget(rotation_note)
        
        layout.addWidget(rotation_group)
        
        # Drag position hint
        drag_hint_group = QGroupBox("自定义位置")
        drag_hint_layout = QVBoxLayout(drag_hint_group)
        
        drag_hint_label = QLabel("💡 在预览区域按住 Ctrl + 拖拽水印可自定义位置")
        drag_hint_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 12px;
                padding: 8px;
                background-color: #e8f4f8;
                border-radius: 4px;
                border-left: 3px solid #3498db;
            }
        """)
        drag_hint_label.setWordWrap(True)
        drag_hint_layout.addWidget(drag_hint_label)
        
        layout.addWidget(drag_hint_group)
        layout.addStretch()
    
    def setup_connections(self):
        """Setup signal connections"""
        self.position_buttons.buttonClicked.connect(self.on_position_changed)
        self.margin_x_spinbox.valueChanged.connect(self.on_margin_x_changed)
        self.margin_y_spinbox.valueChanged.connect(self.on_margin_y_changed)
        self.rotation_slider.valueChanged.connect(self.on_rotation_slider_changed)
        self.rotation_spinbox.valueChanged.connect(self.on_rotation_spinbox_changed)
    
    def update_ui_from_config(self):
        """Update UI from configuration"""
        # Set position button
        for button in self.position_buttons.buttons():
            if button.property("position") == self.config.position:
                button.setChecked(True)
                break
        
        self.margin_x_spinbox.setValue(self.config.margin_x)
        self.margin_y_spinbox.setValue(self.config.margin_y)
        
        # Set rotation
        rotation_degrees = int(self.config.rotation)
        self.rotation_slider.blockSignals(True)
        self.rotation_spinbox.blockSignals(True)
        self.rotation_slider.setValue(rotation_degrees)
        self.rotation_spinbox.setValue(rotation_degrees)
        self.rotation_slider.blockSignals(False)
        self.rotation_spinbox.blockSignals(False)
    
    @pyqtSlot()
    def on_position_changed(self):
        """Handle position change"""
        button = self.position_buttons.checkedButton()
        if button:
            self.config.position = button.property("position")
            self.position_changed.emit()
    
    @pyqtSlot(int)
    def on_margin_x_changed(self, value: int):
        """Handle horizontal margin change"""
        self.config.margin_x = value
        self.position_changed.emit()
    
    @pyqtSlot(int)
    def on_margin_y_changed(self, value: int):
        """Handle vertical margin change"""
        self.config.margin_y = value
        self.position_changed.emit()
    
    @pyqtSlot(int)
    def on_rotation_slider_changed(self, value: int):
        """Handle rotation slider change"""
        self.rotation_spinbox.blockSignals(True)
        self.rotation_spinbox.setValue(value)
        self.rotation_spinbox.blockSignals(False)
        self.config.rotation = float(value)
        self.position_changed.emit()
    
    @pyqtSlot(int)
    def on_rotation_spinbox_changed(self, value: int):
        """Handle rotation spinbox change"""
        self.rotation_slider.blockSignals(True)
        self.rotation_slider.setValue(value)
        self.rotation_slider.blockSignals(False)
        self.config.rotation = float(value)
        self.position_changed.emit()
    
    @pyqtSlot(int, int)
    def on_drag_position_changed(self, x: int, y: int):
        """Handle drag position change from preview"""
        # Update config to custom position
        self.config.position = WatermarkPosition.CUSTOM
        self.config.custom_x = x
        self.config.custom_y = y
        
        # Emit signal to update preview
        self.position_changed.emit()


class WatermarkConfigWidget(QWidget):
    """Main watermark configuration widget"""
    
    config_changed = pyqtSignal()
    
    def __init__(self, config: WatermarkConfig):
        super().__init__()
        self.config = config
        self.init_ui()
        self.setup_connections()
        self.update_ui_from_config()
    
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("水印设置")
        header_label.setStyleSheet("""
            QLabel {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC", "SimHei", "黑体", sans-serif;
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 8px;
                border-bottom: 2px solid #e74c3c;
                margin-bottom: 4px;
            }
        """)
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        # Type selection
        self.text_radio = QRadioButton("文本")
        self.image_radio = QRadioButton("图片")
        header_layout.addWidget(self.text_radio)
        header_layout.addWidget(self.image_radio)
        
        layout.addLayout(header_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("color: #ddd;")
        layout.addWidget(separator)
        
        # Tab widget for different settings
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 3px;
            }
            QTabBar::tab {
                padding: 5px 10px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #e3f2fd;
            }
        """)
        
        # Text watermark tab
        self.text_widget = TextWatermarkWidget(self.config.text_config)
        self.tab_widget.addTab(self.text_widget, "文本设置")

        # Image watermark tab
        self.image_widget = ImageWatermarkWidget(self.config.image_config)
        self.tab_widget.addTab(self.image_widget, "图片设置")        # Position tab
        self.position_widget = PositionWidget(self.config)
        self.tab_widget.addTab(self.position_widget, "位置设置")
        
        layout.addWidget(self.tab_widget)
        
    def setup_connections(self):
        """Setup signal connections"""
        self.text_radio.toggled.connect(self.on_type_changed)
        self.image_radio.toggled.connect(self.on_type_changed)
        self.text_widget.config_changed.connect(self.config_changed)
        self.image_widget.config_changed.connect(self.config_changed)
        self.position_widget.position_changed.connect(self.config_changed)
    
    def update_ui_from_config(self):
        """Update UI from configuration"""
        if self.config.watermark_type == WatermarkType.TEXT:
            self.text_radio.setChecked(True)
            self.tab_widget.setCurrentIndex(0)
        else:
            self.image_radio.setChecked(True)
            self.tab_widget.setCurrentIndex(1)
        
        self.update_tab_visibility()
    
    def update_tab_visibility(self):
        """Update tab visibility based on watermark type"""
        if self.config.watermark_type == WatermarkType.TEXT:
            self.tab_widget.setTabEnabled(0, True)   # Text settings
            self.tab_widget.setTabEnabled(1, False)  # Image settings
        else:
            self.tab_widget.setTabEnabled(0, False)  # Text settings
            self.tab_widget.setTabEnabled(1, True)   # Image settings
    
    @pyqtSlot()
    def on_type_changed(self):
        """Handle watermark type change"""
        if self.text_radio.isChecked():
            self.config.watermark_type = WatermarkType.TEXT
            self.tab_widget.setCurrentIndex(0)
        else:
            self.config.watermark_type = WatermarkType.IMAGE
            self.tab_widget.setCurrentIndex(1)
        
        self.update_tab_visibility()
        self.config_changed.emit()
    
    def set_config(self, config: WatermarkConfig):
        """Set new configuration"""
        self.config = config
        self.text_widget.config = config.text_config
        self.image_widget.config = config.image_config
        self.position_widget.config = config
        self.update_ui_from_config()
        self.text_widget.update_ui_from_config()
        self.image_widget.update_ui_from_config()
        self.position_widget.update_ui_from_config()
    
    def update_config(self):
        """Update UI when config is changed externally"""
        self.update_ui_from_config()
