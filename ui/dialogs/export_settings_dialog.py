"""
导出设置对话框
提供用户友好的导出配置界面
"""
try:
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
        QPushButton, QGroupBox, QRadioButton, QCheckBox,
        QComboBox, QSpinBox, QSlider, QLineEdit, QFileDialog,
        QButtonGroup, QFormLayout, QTextEdit, QSplitter,
        QWidget, QFrame, QMessageBox
    )
    from PyQt5.QtCore import Qt, pyqtSignal
    from PyQt5.QtGui import QFont, QPixmap, QPainter
except ImportError:
    print("PyQt5 is required but not installed.")
    raise

import os
from models.watermark_config import WatermarkConfig
from utils.logger import logger, log_exception


class ExportSettingsDialog(QDialog):
    """导出设置对话框"""
    
    # 信号
    export_requested = pyqtSignal(dict)  # 导出配置信号
    
    def __init__(self, total_images: int, image_list=None, parent=None):
        super().__init__(parent)
        self.total_images = total_images
        self.image_list = image_list or []  # 保存图片列表用于检查源目录
        self.export_config = {}
        
        self.setWindowTitle("导出设置")
        self.setFixedSize(800, 1000)
        self.setModal(True)
        
        logger.debug(f"创建导出设置对话框，总计 {total_images} 张图片")
        
        self.init_ui()
        self.setup_default_values()
        self.connect_signals()
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("批量导出设置")
        title_label.setStyleSheet("""
            QLabel {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", "SimHei", "黑体", sans-serif;
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 0px;
                border-bottom: 2px solid #3498db;
                margin-bottom: 0px;
            }
        """)
        layout.addWidget(title_label)
        
        # 创建左右分栏
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧配置面板
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        
        # 输出格式设置
        format_group = self.create_format_group()
        left_layout.addWidget(format_group)
        
        # 输出路径设置
        path_group = self.create_path_group()
        left_layout.addWidget(path_group)
        
        # 文件命名设置
        naming_group = self.create_naming_group()
        left_layout.addWidget(naming_group)
        
        left_layout.addStretch()
        left_widget.setLayout(left_layout)
        
        # 右侧预览面板
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        
        # 预览标题
        preview_title = QLabel("导出信息预览")
        preview_title.setStyleSheet("""
            QLabel {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                font-size: 15px;
                font-weight: bold;
                color: #2c3e50;
                padding: 8px;
                border-bottom: 1px solid #bdc3c7;
                margin-bottom: 8px;
            }
        """)
        right_layout.addWidget(preview_title)
        
        # 预览信息
        self.preview_info = QTextEdit()
        self.preview_info.setFixedHeight(650)
        self.preview_info.setStyleSheet("""
            QTextEdit {
                font-family: "Microsoft YaHei UI", "Consolas", monospace;
                font-size: 12px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                color: #495057;
            }
        """)
        right_layout.addWidget(self.preview_info)
        
        # 处理统计
        stats_group = self.create_stats_group()
        right_layout.addWidget(stats_group)
        
        right_layout.addStretch()
        right_widget.setLayout(right_layout)
        
        # 设置分栏比例
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 2)  # 左侧占2/3
        splitter.setStretchFactor(1, 1)  # 右侧占1/3
        
        layout.addWidget(splitter)
        
        # 按钮区域
        button_layout = self.create_button_layout()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def create_format_group(self):
        """创建输出格式设置组"""
        group = QGroupBox("输出格式")
        
        layout = QVBoxLayout()
        
        # 格式选择
        self.format_buttons = QButtonGroup()
        
        self.jpeg_radio = QRadioButton("JPEG - 高兼容性，小文件")
        self.png_radio = QRadioButton("PNG - 支持透明，高质量") 
        self.bmp_radio = QRadioButton("BMP - 无损质量，大文件")
        self.tiff_radio = QRadioButton("TIFF - 专业格式，最高质量")
        
        # 设置radio button样式以确保中文显示正确
        radio_style = """
            QRadioButton {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                font-size: 12px;
                color: #2c3e50;
                padding: 0px;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
        """
        
        for radio in [self.jpeg_radio, self.png_radio, self.bmp_radio, self.tiff_radio]:
            radio.setStyleSheet(radio_style)
        
        self.format_buttons.addButton(self.jpeg_radio, 0)
        self.format_buttons.addButton(self.png_radio, 1)
        self.format_buttons.addButton(self.bmp_radio, 2)
        self.format_buttons.addButton(self.tiff_radio, 3)
        
        # 设置默认选中JPEG
        self.jpeg_radio.setChecked(True)
        
        layout.addWidget(self.jpeg_radio)
        layout.addWidget(self.png_radio)
        layout.addWidget(self.bmp_radio)
        layout.addWidget(self.tiff_radio)
        
        # JPEG质量设置
        quality_layout = QHBoxLayout()
        quality_label = QLabel("JPEG质量:")
        quality_label.setStyleSheet("""
                QLabel {
                    font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                    font-size: 12px;
                    color: #2c3e50;
                    padding: 0px;
                    spacing: 8px;
                }
                QLabel::indicator {
                    width: 16px;
                    height: 16px;
                }
            """)
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(60, 100)
        self.quality_slider.setValue(100)
        self.quality_value = QLabel("100")
        
        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.quality_slider)
        quality_layout.addWidget(self.quality_value)
        
        layout.addLayout(quality_layout)
        
        # 保持原始格式选项
        self.keep_original_format = QCheckBox("保持原始格式（推荐）")
        self.keep_original_format.setStyleSheet("""
            QCheckBox {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                font-size: 12px;
                color: #2c3e50;
                padding: 0px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        layout.addWidget(self.keep_original_format)
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # 图片尺寸缩放设置
        resize_title = QLabel("图片尺寸缩放")
        resize_title.setStyleSheet("""
            QLabel {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                font-size: 13px;
                font-weight: bold;
                color: #2c3e50;
                padding: 5px 0px;
            }
        """)
        layout.addWidget(resize_title)
        
        # 启用缩放选项
        self.enable_resize = QCheckBox("调整图片尺寸")
        self.enable_resize.setStyleSheet("""
            QCheckBox {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                font-size: 12px;
                color: #2c3e50;
                padding: 0px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        layout.addWidget(self.enable_resize)
        
        # 缩放模式选择
        resize_mode_layout = QHBoxLayout()
        resize_mode_label = QLabel("缩放模式:")
        resize_mode_label.setStyleSheet("""
            QLabel {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                font-size: 12px;
                color: #2c3e50;
            }
        """)
        self.resize_mode_combo = QComboBox()
        self.resize_mode_combo.addItems(["按百分比缩放", "指定最长边", "指定宽度", "指定高度"])
        self.resize_mode_combo.setStyleSheet("""
            QComboBox {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                font-size: 12px;
                color: #2c3e50;
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                padding: 3px 5px;
            }
            QComboBox:hover {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                color: #2c3e50;
                background-color: white;
                selection-background-color: #3498db;
                selection-color: white;
            }
            QComboBox QAbstractItemView::item {
                color: #2c3e50;
                padding: 3px 5px;
            }
            QComboBox QAbstractItemView::item:hover {
                color: #2c3e50;
                background-color: #e8f4f8;
            }
        """)
        self.resize_mode_combo.setEnabled(False)                     
        resize_mode_layout.addWidget(resize_mode_label)
        resize_mode_layout.addWidget(self.resize_mode_combo)
        layout.addLayout(resize_mode_layout)
        
        # 缩放值设置
        resize_value_layout = QHBoxLayout()
        self.resize_value_label = QLabel("缩放比例:")
        self.resize_value_label.setStyleSheet("""
            QLabel {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                font-size: 12px;
                color: #2c3e50;
            }
        """)
        self.resize_value_spinbox = QSpinBox()
        self.resize_value_spinbox.setRange(10, 200)
        self.resize_value_spinbox.setValue(100)
        self.resize_value_spinbox.setSuffix("%")
        self.resize_value_spinbox.setEnabled(False)
        resize_value_layout.addWidget(self.resize_value_label)
        resize_value_layout.addWidget(self.resize_value_spinbox)
        resize_value_layout.addStretch()
        layout.addLayout(resize_value_layout)
        
        # 提示信息
        resize_hint = QLabel("💡 调整尺寸可减小文件大小，适合网络分享")
        resize_hint.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #7f8c8d;
                padding: 4px;
                background-color: #ecf0f1;
                border-radius: 3px;
            }
        """)
        resize_hint.setWordWrap(True)
        layout.addWidget(resize_hint)
        
        group.setLayout(layout)
        return group
    
    def create_path_group(self):
        """创建输出路径设置组"""
        group = QGroupBox("输出路径")
        
        layout = QVBoxLayout()
        
        # 路径选择
        path_layout = QHBoxLayout()
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("选择输出文件夹...")
        
        self.browse_button = QPushButton("浏览")
        self.browse_button.setStyleSheet("""
            QPushButton {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        path_layout.addWidget(self.output_path)
        path_layout.addWidget(self.browse_button)
        layout.addLayout(path_layout)
        
        # 子文件夹选项
        self.create_subfolder = QCheckBox("在子文件夹中创建（watermarked_images）")
        self.create_subfolder.setChecked(True)
        
        # 覆盖选项
        self.overwrite_existing = QCheckBox("覆盖已存在的文件")
        
        # 设置checkbox样式
        checkbox_style = """
            QCheckBox {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                font-size: 12px;
                color: #2c3e50;
                padding: 0px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """
        
        self.create_subfolder.setStyleSheet(checkbox_style)
        self.overwrite_existing.setStyleSheet(checkbox_style)
        
        layout.addWidget(self.create_subfolder)
        layout.addWidget(self.overwrite_existing)
        
        group.setLayout(layout)
        return group
    
    def create_naming_group(self):
        """创建文件命名设置组"""
        group = QGroupBox("文件命名")
        
        layout = QVBoxLayout()
        
        # 命名规则选择
        self.naming_buttons = QButtonGroup()
        
        self.original_name = QRadioButton("保持原文件名")
        self.add_prefix = QRadioButton("添加前缀")
        self.add_suffix = QRadioButton("添加后缀")
        self.custom_pattern = QRadioButton("自定义模式")
        
        # 设置命名radio button样式
        naming_radio_style = """
            QRadioButton {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                font-size: 12px;
                color: #2c3e50;
                padding: 0px;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
        """
        
        for radio in [self.original_name, self.add_prefix, self.add_suffix, self.custom_pattern]:
            radio.setStyleSheet(naming_radio_style)
        
        self.naming_buttons.addButton(self.original_name, 0)
        self.naming_buttons.addButton(self.add_prefix, 1)
        self.naming_buttons.addButton(self.add_suffix, 2)
        self.naming_buttons.addButton(self.custom_pattern, 3)
        
        # 默认选中添加后缀
        self.add_suffix.setChecked(True)
        
        layout.addWidget(self.original_name)
        layout.addWidget(self.add_prefix)
        layout.addWidget(self.add_suffix)
        layout.addWidget(self.custom_pattern)
        
        # 输入框样式 - 统一字体和颜色
        input_style = """
            QLineEdit {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                font-size: 12px;
                color: #2c3e50;
                padding: 10px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
                min-height: 15px;
            }
            QLineEdit:disabled {
                background-color: #f8f9fa;
                color: #6c757d;
                border-color: #dee2e6;
            }
            QLineEdit:focus {
                border-color: #3498db;
                border-width: 2px;
            }
            QLineEdit::placeholder {
                color: #95a5a6;
                font-style: italic;
            }
        """
        
        # 统一标签样式
        label_style = """
            QLabel {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                font-size: 12px;
                color: #2c3e50;
                min-width: 40px;
            }
        """
        
        # 前缀/后缀输入
        prefix_layout = QHBoxLayout()
        prefix_label = QLabel("前缀:")
        prefix_label.setStyleSheet(label_style)
        prefix_layout.addWidget(prefix_label)
        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("输入前缀...")
        self.prefix_input.setEnabled(False)
        self.prefix_input.setStyleSheet(input_style)
        prefix_layout.addWidget(self.prefix_input)
        layout.addLayout(prefix_layout)
        
        suffix_layout = QHBoxLayout()
        suffix_label = QLabel("后缀:")
        suffix_label.setStyleSheet(label_style)
        suffix_layout.addWidget(suffix_label)
        self.suffix_input = QLineEdit()
        self.suffix_input.setPlaceholderText("输入后缀...")
        self.suffix_input.setStyleSheet(input_style)
        suffix_layout.addWidget(self.suffix_input)
        layout.addLayout(suffix_layout)
        
    
        # 自定义模式说明
        pattern_help = QLabel("模式说明: {name} - 原文件名, {date} - 日期, {time} - 时间, {index} - 序号")
        pattern_help.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #7f8c8d;
                padding: 4px;
                background-color: #ecf0f1;
                border-radius: 3px;
            }
        """)
        pattern_help.setWordWrap(True)
        layout.addWidget(pattern_help)
        
        self.custom_input = QLineEdit()
        self.custom_input.setPlaceholderText("输入自定义模式...")
        self.custom_input.setEnabled(False)
        self.custom_input.setStyleSheet(input_style)
        layout.addWidget(self.custom_input)
        
        group.setLayout(layout)
        return group
    
    def create_stats_group(self):
        """创建处理统计组"""
        group = QGroupBox("处理统计")
        
        layout = QFormLayout()
        
        self.total_files_label = QLabel(str(self.total_images))
        self.estimated_size_label = QLabel("计算中...")
        self.estimated_time_label = QLabel("计算中...")
        
        layout.addRow("总文件数:", self.total_files_label)
        layout.addRow("预计大小:", self.estimated_size_label)
        layout.addRow("预计时间:", self.estimated_time_label)
        
        group.setLayout(layout)
        return group
    
    def create_button_layout(self):
        """创建按钮布局"""
        layout = QHBoxLayout()
        layout.addStretch()
        
        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        # 开始导出按钮
        self.export_button = QPushButton("开始导出")
        self.export_button.setStyleSheet("""
            QPushButton {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        layout.addWidget(self.cancel_button)
        layout.addWidget(self.export_button)
        
        return layout
    
    def setup_default_values(self):
        """设置默认值"""
        # 设置默认输出路径为桌面
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        self.output_path.setText(desktop_path)
        
        # 更新预览
        self.update_preview()
    
    def connect_signals(self):
        """连接信号"""
        # 按钮信号
        self.browse_button.clicked.connect(self.browse_output_folder)
        self.cancel_button.clicked.connect(self.reject)
        self.export_button.clicked.connect(lambda: self.start_export())
        
        # 格式变化信号
        self.format_buttons.buttonClicked.connect(self.on_format_changed)
        self.quality_slider.valueChanged.connect(self.on_quality_changed)
        
        # 命名变化信号
        self.naming_buttons.buttonClicked.connect(self.on_naming_changed)
        
        # 输入变化信号
        self.prefix_input.textChanged.connect(lambda: self.update_preview())
        self.suffix_input.textChanged.connect(lambda: self.update_preview())
        self.custom_input.textChanged.connect(lambda: self.update_preview())
        self.output_path.textChanged.connect(lambda: self.update_preview())
        
        # 复选框信号
        self.create_subfolder.toggled.connect(lambda: self.update_preview())
        self.keep_original_format.toggled.connect(lambda: self.update_preview())
        
        # 缩放相关信号
        self.enable_resize.toggled.connect(self.on_resize_enabled_changed)
        self.resize_mode_combo.currentIndexChanged.connect(self.on_resize_mode_changed)
        self.resize_value_spinbox.valueChanged.connect(lambda: self.update_preview())
    
    @log_exception
    def browse_output_folder(self, checked=False):
        """浏览输出文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self, 
            "选择输出文件夹",
            self.output_path.text()
        )
        
        if folder:
            self.output_path.setText(folder)
            logger.debug(f"选择输出文件夹: {folder}")
    
    @log_exception 
    def on_format_changed(self, button):
        """格式变化处理"""
        # 启用/禁用质量滑块
        is_jpeg = self.jpeg_radio.isChecked()
        self.quality_slider.setEnabled(is_jpeg)
        self.quality_value.setEnabled(is_jpeg)
        
        self.update_preview()
    
    @log_exception
    def on_quality_changed(self, value):
        """质量变化处理"""
        self.quality_value.setText(str(value))
        self.update_preview()
    
    @log_exception
    def on_naming_changed(self, button):
        """命名方式变化处理"""
        # 启用/禁用相应输入框
        self.prefix_input.setEnabled(self.add_prefix.isChecked())
        self.suffix_input.setEnabled(self.add_suffix.isChecked())
        self.custom_input.setEnabled(self.custom_pattern.isChecked())
        
        self.update_preview()
    
    @log_exception
    def on_resize_enabled_changed(self, enabled):
        """缩放启用状态变化处理"""
        self.resize_mode_combo.setEnabled(enabled)
        self.resize_value_spinbox.setEnabled(enabled)
        self.update_preview()
    
    @log_exception
    def on_resize_mode_changed(self, index):
        """缩放模式变化处理"""
        # 根据模式更新标签和范围
        if index == 0:  # 按百分比
            self.resize_value_label.setText("缩放比例:")
            self.resize_value_spinbox.setRange(10, 200)
            self.resize_value_spinbox.setValue(100)
            self.resize_value_spinbox.setSuffix("%")
        elif index == 1:  # 最长边
            self.resize_value_label.setText("最长边:")
            self.resize_value_spinbox.setRange(100, 8000)
            self.resize_value_spinbox.setValue(1920)
            self.resize_value_spinbox.setSuffix(" px")
        elif index == 2:  # 宽度
            self.resize_value_label.setText("宽度:")
            self.resize_value_spinbox.setRange(100, 8000)
            self.resize_value_spinbox.setValue(1920)
            self.resize_value_spinbox.setSuffix(" px")
        else:  # 高度
            self.resize_value_label.setText("高度:")
            self.resize_value_spinbox.setRange(100, 8000)
            self.resize_value_spinbox.setValue(1080)
            self.resize_value_spinbox.setSuffix(" px")
        
        self.update_preview()
    
    @log_exception
    def update_preview(self):
        """更新预览信息"""
        try:
            # 获取当前配置
            config = self.get_export_config()
            
            # 生成预览文本
            preview_text = self.generate_preview_text(config)
            self.preview_info.setPlainText(preview_text)
            
            # 更新统计信息
            self.update_statistics(config)
            
            logger.debug("导出预览已更新")
            
        except Exception as e:
            logger.error(f"更新预览失败: {e}")
            self.preview_info.setPlainText(f"预览生成失败: {str(e)}")
    
    def generate_preview_text(self, config):
        """生成预览文本"""
        lines = []
        lines.append("=== 导出配置预览 ===")
        lines.append("")
        
        # 输出格式
        format_name = config['format'].upper()
        if config['format'] == 'jpeg':
            format_name += f" (质量: {config['quality']}%)"
        lines.append(f"输出格式: {format_name}")
        
        if config['keep_original_format']:
            lines.append("注意: 将保持原始格式，上述格式仅用于格式转换")
        
        lines.append("")
        
        # 尺寸设置
        if config.get('enable_resize', False):
            resize_mode = config.get('resize_mode', 0)
            resize_value = config.get('resize_value', 100)
            mode_names = ["按百分比", "最长边", "宽度", "高度"]
            if resize_mode == 0:
                lines.append(f"图片缩放: {mode_names[resize_mode]} - {resize_value}%")
            else:
                lines.append(f"图片缩放: {mode_names[resize_mode]} - {resize_value}px")
        else:
            lines.append("图片缩放: 保持原始尺寸")
        
        lines.append("")
        
        # 输出路径
        output_dir = config['output_dir']
        if config['create_subfolder']:
            output_dir = os.path.join(output_dir, "watermarked_images")
        lines.append(f"输出目录: {output_dir}")
        lines.append("")
        
        # 文件命名示例
        lines.append("命名示例:")
        sample_names = self.generate_sample_names(config)
        for original, new in sample_names:
            lines.append(f"  {original} → {new}")
        
        lines.append("")
        lines.append(f"总计处理: {self.total_images} 个文件")
        
        return "\n".join(lines)
    
    def generate_sample_names(self, config, count=3):
        """生成示例文件名"""
        samples = []
        sample_originals = ["photo1.jpg", "IMG_001.png", "picture.bmp"]
        
        for i, original in enumerate(sample_originals[:count]):
            name, ext = os.path.splitext(original)
            
            # 根据配置生成新文件名
            if config['naming_mode'] == 'original':
                new_name = name
            elif config['naming_mode'] == 'prefix':
                new_name = config['prefix'] + name
            elif config['naming_mode'] == 'suffix':
                new_name = name + config['suffix']
            elif config['naming_mode'] == 'custom':
                pattern = config['custom_pattern']
                new_name = pattern.replace('{name}', name)
                new_name = new_name.replace('{index}', str(i+1).zfill(3))
                new_name = new_name.replace('{date}', '20241002')
                new_name = new_name.replace('{time}', '143022')
            
            # 确定输出扩展名
            if config['keep_original_format']:
                new_ext = ext
            else:
                new_ext = f".{config['format']}"
            
            samples.append((original, new_name + new_ext))
        
        return samples
    
    def update_statistics(self, config):
        """更新统计信息"""
        # 简单估算，实际应用可以更精确
        avg_size_mb = 2.5  # 假设平均文件大小
        
        if config['format'] == 'jpeg':
            compression_ratio = config['quality'] / 100.0
            estimated_size = self.total_images * avg_size_mb * compression_ratio
        elif config['format'] == 'png':
            estimated_size = self.total_images * avg_size_mb * 1.2
        else:
            estimated_size = self.total_images * avg_size_mb * 1.5
        
        # 估算处理时间 (每张图片约1-3秒)
        estimated_time_seconds = self.total_images * 2
        estimated_time_str = f"{estimated_time_seconds // 60}分{estimated_time_seconds % 60}秒"
        
        self.estimated_size_label.setText(f"{estimated_size:.1f} MB")
        self.estimated_time_label.setText(estimated_time_str)
    
    def _check_may_overwrite_source(self, config):
        """
        检查是否可能覆盖源图片
        返回：(会被覆盖的文件列表, 是否检测到覆盖风险)
        """
        if not self.image_list:
            return [], False
        
        output_dir = os.path.normpath(config['output_dir'])
        
        # 如果启用了创建子文件夹，不会覆盖
        if config.get('create_subfolder', False):
            return [], False
        
        will_overwrite = []  # 存储会被覆盖的文件信息
        
        # 遍历所有图片，精确判断哪些会被覆盖
        for index, image_info in enumerate(self.image_list):
            if not hasattr(image_info, 'file_path'):
                continue
            
            source_path = image_info.file_path
            source_dir = os.path.normpath(os.path.dirname(source_path))
            
            # 只检查输出目录与源目录相同的文件
            if source_dir != output_dir:
                continue
            
            # 生成输出文件名（复制batch_export_engine的逻辑）
            output_filename = self._generate_output_filename(source_path, index, config)
            output_path = os.path.normpath(os.path.join(output_dir, output_filename))
            source_path_norm = os.path.normpath(source_path)
            
            # 判断输出路径是否与源路径相同
            # 在Windows上不区分大小写
            if os.name == 'nt':  # Windows
                paths_match = output_path.lower() == source_path_norm.lower()
            else:  # Linux/Mac
                paths_match = output_path == source_path_norm
            
            if paths_match:
                will_overwrite.append({
                    'source': os.path.basename(source_path),
                    'output': output_filename
                })
                logger.warning(f"检测到会覆盖原图：{source_path} -> {output_path}")
        
        return will_overwrite, len(will_overwrite) > 0
    
    def _generate_output_filename(self, input_path, index, config):
        """生成输出文件名（与batch_export_engine保持一致）"""
        original_name = os.path.splitext(os.path.basename(input_path))[0]
        original_ext = os.path.splitext(input_path)[1]  # 保持原始大小写
        
        # 确定输出扩展名
        if config.get('keep_original_format', False):
            output_ext = original_ext
        else:
            # 直接使用format，与batch_export_engine一致
            output_ext = f".{config['format']}"
        
        # 根据命名模式生成新文件名
        naming_mode = config['naming_mode']
        
        if naming_mode == 'original':
            new_name = original_name
        elif naming_mode == 'prefix':
            prefix = config.get('prefix', 'watermarked_')
            new_name = prefix + original_name
        elif naming_mode == 'suffix':
            suffix = config.get('suffix', '_watermarked')
            new_name = original_name + suffix
        elif naming_mode == 'custom':
            pattern = config.get('custom_pattern', '{name}_watermarked')
            new_name = self._apply_custom_pattern(pattern, original_name, index)
        else:
            new_name = original_name + '_watermarked'
        
        return new_name + output_ext
    
    def _apply_custom_pattern(self, pattern, original_name, index):
        """应用自定义命名模式"""
        from datetime import datetime
        now = datetime.now()
        
        result = pattern.replace('{name}', original_name)
        result = result.replace('{index}', str(index + 1).zfill(3))
        result = result.replace('{date}', now.strftime('%Y%m%d'))
        result = result.replace('{time}', now.strftime('%H%M%S'))
        result = result.replace('{year}', now.strftime('%Y'))
        result = result.replace('{month}', now.strftime('%m'))
        result = result.replace('{day}', now.strftime('%d'))
        
        return result
    
    def get_export_config(self):
        """获取导出配置"""
        # 确定输出格式
        if self.jpeg_radio.isChecked():
            format_type = 'jpeg'
        elif self.png_radio.isChecked():
            format_type = 'png'
        elif self.bmp_radio.isChecked():
            format_type = 'bmp'
        else:
            format_type = 'tiff'
        
        # 确定命名模式
        if self.original_name.isChecked():
            naming_mode = 'original'
        elif self.add_prefix.isChecked():
            naming_mode = 'prefix'
        elif self.add_suffix.isChecked():
            naming_mode = 'suffix'
        else:
            naming_mode = 'custom'
        
        return {
            'format': format_type,
            'quality': self.quality_slider.value(),
            'keep_original_format': self.keep_original_format.isChecked(),
            'output_dir': self.output_path.text(),
            'create_subfolder': self.create_subfolder.isChecked(),
            'overwrite_existing': self.overwrite_existing.isChecked(),
            'naming_mode': naming_mode,
            'prefix': self.prefix_input.text(),
            'suffix': self.suffix_input.text(),
            'custom_pattern': self.custom_input.text(),
            'enable_resize': self.enable_resize.isChecked(),
            'resize_mode': self.resize_mode_combo.currentIndex(),
            'resize_value': self.resize_value_spinbox.value()
        }
    
    @log_exception
    def start_export(self):
        """开始导出"""
        config = self.get_export_config()
        
        # 验证配置
        if not config['output_dir']:
            QMessageBox.warning(self, "配置错误", "请选择输出文件夹")
            return
        
        if not os.path.exists(config['output_dir']):
            QMessageBox.warning(self, "配置错误", "输出文件夹不存在")
            return
        
        # 检查是否可能覆盖原图
        will_overwrite, has_overwrite = self._check_may_overwrite_source(config)
        
        if has_overwrite:
            # 构建文件列表提示
            file_list = "\n".join([f"  • {item['source']}" for item in will_overwrite[:10]])
            if len(will_overwrite) > 10:
                file_list += f"\n  ... 还有 {len(will_overwrite) - 10} 个文件"
            
            warning_message = (
                f"检测到以下 {len(will_overwrite)} 个文件将被覆盖：\n\n"
                f"{file_list}\n\n"
                "这些文件的输出路径与源文件路径完全相同！\n\n"
                "建议采取以下措施之一：\n"
                "1. 选择其他输出目录\n"
                "2. 启用'创建子文件夹'选项\n"
                "3. 使用'添加前缀'或'添加后缀'命名模式\n"
                "4. 取消'覆盖已存在文件'选项\n\n"
                "是否仍要继续导出？"
            )
            
            reply = QMessageBox.warning(
                self,
                "警告：将覆盖原始文件",
                warning_message,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                logger.info(f"用户取消导出（避免覆盖 {len(will_overwrite)} 个原图）")
                return
            else:
                logger.warning(f"用户确认导出（将覆盖 {len(will_overwrite)} 个原图）")
        
        # 发送导出请求信号
        self.export_config = config
        logger.info(f"开始导出，配置: {config}")
        self.export_requested.emit(config)
        self.accept()