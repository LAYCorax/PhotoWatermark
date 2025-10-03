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
    
    def __init__(self, total_images: int, parent=None):
        super().__init__(parent)
        self.total_images = total_images
        self.export_config = {}
        
        self.setWindowTitle("导出设置")
        self.setFixedSize(800, 780)
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
        self.preview_info.setFixedHeight(460)
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
    
    @log_exception
    def browse_output_folder(self):
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
            'custom_pattern': self.custom_input.text()
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
        
        # 发送导出请求信号
        self.export_config = config
        logger.info(f"开始导出，配置: {config}")
        self.export_requested.emit(config)
        self.accept()