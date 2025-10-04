"""
模板管理对话框
提供模板的查看、应用、保存、导入、导出、删除等功能
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QLineEdit,
    QMessageBox, QFileDialog, QGroupBox, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

import os
from core.template_manager import TemplateManager, Template
from models.watermark_config import WatermarkConfig
from utils.logger import logger, log_exception


class TemplateDialog(QDialog):
    """模板管理对话框"""
    
    template_applied = pyqtSignal(dict)  # 应用模板信号
    
    def __init__(self, current_config: WatermarkConfig = None, parent=None):
        super().__init__(parent)
        self.current_config = current_config
        self.template_manager = TemplateManager()
        
        self.setWindowTitle("水印模板管理")
        self.setFixedSize(900, 400)
        self.setModal(True)
        
        self.init_ui()
        self.load_templates()
        
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("水印模板管理")
        title_label.setStyleSheet("""
            QLabel {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 5px;
                border-bottom: 2px solid #3498db;
            }
        """)
        layout.addWidget(title_label)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：模板列表
        left_widget = self.create_template_list()
        splitter.addWidget(left_widget)
        
        # 右侧：模板详情和操作
        right_widget = self.create_template_details()
        splitter.addWidget(right_widget)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
        # 底部按钮
        button_layout = self.create_button_bar()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def create_template_list(self):
        """创建模板列表区域"""
        widget = QGroupBox("模板列表")
        widget.setStyleSheet("""
            QGroupBox {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # 搜索框
        search_layout = QHBoxLayout()
        search_label = QLabel("搜索:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入模板名称...")
        self.search_input.textChanged.connect(self.filter_templates)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # 模板列表
        self.template_list = QListWidget()
        self.template_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e8f4f8;
            }
        """)
        self.template_list.currentItemChanged.connect(self.on_template_selected)
        layout.addWidget(self.template_list)
        
        widget.setLayout(layout)
        return widget
        
    def create_template_details(self):
        """创建模板详情区域"""
        widget = QGroupBox("模板详情")
        widget.setStyleSheet("""
            QGroupBox {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # 模板名称
        name_layout = QHBoxLayout()
        name_label = QLabel("名称:")
        name_label.setFixedWidth(60)
        self.name_display = QLabel("(未选择)")
        self.name_display.setStyleSheet("font-weight: bold; color: #2c3e50;")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_display)
        name_layout.addStretch()
        layout.addLayout(name_layout)
        
        # 创建时间
        time_layout = QHBoxLayout()
        time_label = QLabel("创建时间:")
        time_label.setFixedWidth(60)
        self.time_display = QLabel("-")
        time_layout.addWidget(time_label)
        time_layout.addWidget(self.time_display)
        time_layout.addStretch()
        layout.addLayout(time_layout)
        
        # 模板类型
        type_layout = QHBoxLayout()
        type_label = QLabel("类型:")
        type_label.setFixedWidth(60)
        self.type_display = QLabel("-")
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_display)
        type_layout.addStretch()
        layout.addLayout(type_layout)
        
        # 描述
        desc_label = QLabel("描述:")
        layout.addWidget(desc_label)
        
        self.description_display = QTextEdit()
        self.description_display.setReadOnly(True)
        self.description_display.setMaximumHeight(100)
        self.description_display.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                padding: 5px;
                background-color: #f8f9fa;
            }
        """)
        layout.addWidget(self.description_display)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("应用模板")
        self.apply_button.setEnabled(False)
        self.apply_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.apply_button.clicked.connect(self.apply_template)
        
        self.export_button = QPushButton("导出")
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.export_template)
        
        self.delete_button = QPushButton("删除")
        self.delete_button.setEnabled(False)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.delete_button.clicked.connect(self.delete_template)
        
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
        
    def create_button_bar(self):
        """创建底部按钮栏"""
        layout = QHBoxLayout()
        
        # 左侧按钮
        self.save_current_button = QPushButton("保存当前配置为模板")
        self.save_current_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.save_current_button.clicked.connect(self.save_current_config)
        
        self.import_button = QPushButton("导入模板")
        self.import_button.clicked.connect(self.import_template)
        
        self.create_default_button = QPushButton("创建默认模板")
        self.create_default_button.clicked.connect(self.create_default_templates)
        
        layout.addWidget(self.save_current_button)
        layout.addWidget(self.import_button)
        layout.addWidget(self.create_default_button)
        layout.addStretch()
        
        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        return layout
        
    @log_exception
    def load_templates(self):
        """加载模板列表"""
        self.template_list.clear()
        templates = self.template_manager.get_all_templates()
        
        for template in templates:
            item = QListWidgetItem(template.name)
            if template.is_default:
                item.setForeground(Qt.blue)
                item.setText(f"📌 {template.name}")
            item.setData(Qt.UserRole, template)
            self.template_list.addItem(item)
        
        logger.debug(f"加载了 {len(templates)} 个模板")
        
    def filter_templates(self, text):
        """过滤模板列表"""
        for i in range(self.template_list.count()):
            item = self.template_list.item(i)
            template = item.data(Qt.UserRole)
            visible = text.lower() in template.name.lower()
            item.setHidden(not visible)
            
    def on_template_selected(self, current, previous):
        """模板选择变化"""
        if not current:
            self.apply_button.setEnabled(False)
            self.export_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            self.name_display.setText("(未选择)")
            self.time_display.setText("-")
            self.type_display.setText("-")
            self.description_display.clear()
            return
        
        template = current.data(Qt.UserRole)
        
        # 更新显示
        self.name_display.setText(template.name)
        self.time_display.setText(template.created_at)
        
        # 显示类型
        watermark_type = template.config.get('watermark_type', 'unknown')
        type_map = {
            'text': '文字水印',
            'image': '图片水印',
            'both': '文字+图片水印'
        }
        self.type_display.setText(type_map.get(watermark_type, '未知'))
        
        self.description_display.setText(template.description or "(无描述)")
        
        # 启用按钮
        self.apply_button.setEnabled(True)
        self.export_button.setEnabled(True)
        self.delete_button.setEnabled(not template.is_default)
        
    @log_exception
    def apply_template(self, checked=False):
        """应用选中的模板"""
        current_item = self.template_list.currentItem()
        if not current_item:
            return
        
        template = current_item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            "确认应用",
            f"确定要应用模板 '{template.name}' 吗？\n当前的水印设置将被替换。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.template_applied.emit(template.config)
            logger.info(f"应用模板: {template.name}")
            QMessageBox.information(self, "成功", f"模板 '{template.name}' 已应用！")
            
    @log_exception
    def save_current_config(self, checked=False):
        """保存当前配置为模板"""
        if not self.current_config:
            QMessageBox.warning(self, "错误", "没有可用的水印配置")
            return
        
        # 弹出对话框输入模板名称和描述
        from PyQt5.QtWidgets import QDialog, QFormLayout
        
        dialog = QDialog(self)
        dialog.setWindowTitle("保存为模板")
        dialog.setFixedWidth(400)
        
        layout = QFormLayout()
        
        name_input = QLineEdit()
        name_input.setPlaceholderText("输入模板名称...")
        layout.addRow("模板名称:", name_input)
        
        desc_input = QTextEdit()
        desc_input.setPlaceholderText("输入模板描述...")
        desc_input.setMaximumHeight(80)
        layout.addRow("模板描述:", desc_input)
        
        button_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        cancel_btn = QPushButton("取消")
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addRow(button_layout)
        
        save_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            name = name_input.text().strip()
            description = desc_input.toPlainText().strip()
            
            if not name:
                QMessageBox.warning(self, "错误", "请输入模板名称")
                return
            
            # 检查是否存在同名模板
            existing_template = self.template_manager.get_template(name)
            if existing_template:
                # 提示用户是否覆盖
                reply = QMessageBox.question(
                    self,
                    "模板已存在",
                    f"已存在名为 '{name}' 的模板。\n是否覆盖现有模板？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    logger.debug(f"用户取消覆盖模板: {name}")
                    return
            
            # 创建模板
            template = Template(
                name=name,
                config=self.current_config.to_dict(),
                description=description
            )
            
            if self.template_manager.save_template(template):
                action = "更新" if existing_template else "保存"
                QMessageBox.information(self, "成功", f"模板 '{name}' {action}成功！")
                self.load_templates()
                logger.info(f"模板{'覆盖' if existing_template else '创建'}成功: {name}")
            else:
                QMessageBox.critical(self, "错误", "保存模板失败")
                
    @log_exception
    def import_template(self, checked=False):
        """导入模板"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "选择模板文件",
            "",
            "模板文件 (*.json)"
        )
        
        if filepath:
            template = self.template_manager.import_template(filepath)
            if template:
                QMessageBox.information(self, "成功", f"模板 '{template.name}' 导入成功！")
                self.load_templates()
            else:
                QMessageBox.critical(self, "错误", "导入模板失败")
                
    @log_exception
    def export_template(self, checked=False):
        """导出选中的模板"""
        current_item = self.template_list.currentItem()
        if not current_item:
            return
        
        template = current_item.data(Qt.UserRole)
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "导出模板",
            f"{template.name}.json",
            "模板文件 (*.json)"
        )
        
        if filepath:
            if self.template_manager.export_template(template.name, filepath):
                QMessageBox.information(self, "成功", f"模板已导出到:\n{filepath}")
            else:
                QMessageBox.critical(self, "错误", "导出模板失败")
                
    @log_exception
    def delete_template(self, checked=False):
        """删除选中的模板"""
        current_item = self.template_list.currentItem()
        if not current_item:
            return
        
        template = current_item.data(Qt.UserRole)
        
        if template.is_default:
            QMessageBox.warning(self, "错误", "不能删除默认模板")
            return
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除模板 '{template.name}' 吗？\n此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.template_manager.delete_template(template.name):
                QMessageBox.information(self, "成功", f"模板 '{template.name}' 已删除")
                self.load_templates()
            else:
                QMessageBox.critical(self, "错误", "删除模板失败")
                
    @log_exception
    def create_default_templates(self, checked=False):
        """创建默认模板"""
        reply = QMessageBox.question(
            self,
            "确认创建",
            "确定要创建默认模板吗？\n这将添加几个预设的水印模板。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            self.template_manager.create_default_templates()
            QMessageBox.information(self, "成功", "默认模板已创建！")
            self.load_templates()
