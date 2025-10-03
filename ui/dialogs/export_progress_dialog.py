"""
导出进度对话框
显示批量导出的实时进度
"""
try:
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
        QPushButton, QProgressBar, QTextEdit, QGroupBox,
        QFrame, QMessageBox
    )
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal
    from PyQt5.QtGui import QFont, QPixmap, QIcon
except ImportError:
    print("PyQt5 is required but not installed.")
    raise

import os
from datetime import datetime, timedelta
from utils.logger import logger, log_exception


class ExportProgressDialog(QDialog):
    """导出进度对话框"""
    
    # 信号
    cancel_requested = pyqtSignal()  # 取消请求信号
    
    def __init__(self, total_files, parent=None):
        super().__init__(parent)
        self.total_files = total_files
        self.processed_files = 0
        self.start_time = None
        self.is_completed = False
        self.is_cancelled = False
        
        self.setWindowTitle("批量导出进度")
        self.setFixedSize(600, 500)
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        
        logger.debug(f"创建导出进度对话框，总文件数: {total_files}")
        
        self.init_ui()
        self.setup_timer()
        self.start_export()
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("批量导出进行中...")
        title_label.setStyleSheet("""
            QLabel {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", "SimHei", "黑体", sans-serif;
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                text-align: center;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 进度区域
        progress_group = self.create_progress_group()
        layout.addWidget(progress_group)
        
        # 状态信息区域
        status_group = self.create_status_group()
        layout.addWidget(status_group)
        
        # 详细日志区域
        log_group = self.create_log_group()
        layout.addWidget(log_group)
        
        # 按钮区域
        button_layout = self.create_button_layout()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def create_progress_group(self):
        """创建进度显示组"""
        group = QGroupBox("导出进度")
        group.setStyleSheet("""
            QGroupBox {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                font-size: 12px;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout()
        
        # 总体进度条
        self.main_progress = QProgressBar()
        self.main_progress.setRange(0, 100)
        self.main_progress.setValue(0)
        self.main_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                font-size: 12px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.main_progress)
        
        # 进度文本
        self.progress_label = QLabel("准备开始...")
        self.progress_label.setStyleSheet("""
            QLabel {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                font-size: 11px;
                color: #7f8c8d;
                padding: 5px;
            }
        """)
        layout.addWidget(self.progress_label)
        
        # 当前处理文件
        self.current_file_label = QLabel("")
        self.current_file_label.setStyleSheet("""
            QLabel {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                font-size: 10px;
                color: #95a5a6;
                padding: 2px;
                background-color: #ecf0f1;
                border-radius: 3px;
            }
        """)
        self.current_file_label.setWordWrap(True)
        layout.addWidget(self.current_file_label)
        
        group.setLayout(layout)
        return group
    
    def create_status_group(self):
        """创建状态信息组"""
        group = QGroupBox("状态信息")
        
        layout = QVBoxLayout()
        
        # 创建状态信息网格
        status_layout = QHBoxLayout()
        
        # 左列状态
        left_status = QVBoxLayout()
        
        self.processed_label = QLabel("已处理: 0/0")
        self.processed_label.setStyleSheet("""
            QLabel {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                font-size: 12px;
                color: #27ae60;
                font-weight: bold;
                padding: 3px;
            }
        """)
        left_status.addWidget(self.processed_label)
        
        self.failed_label = QLabel("失败: 0")
        self.failed_label.setStyleSheet("""
            QLabel {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                font-size: 12px;
                color: #e74c3c;
                font-weight: bold;
                padding: 3px;
            }
        """)
        left_status.addWidget(self.failed_label)
        
        # 右列状态
        right_status = QVBoxLayout()
        
        self.elapsed_label = QLabel("已用时间: 00:00:00")
        self.elapsed_label.setStyleSheet("""
            QLabel {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                font-size: 12px;
                color: #3498db;
                padding: 3px;
            }
        """)
        right_status.addWidget(self.elapsed_label)
        
        self.eta_label = QLabel("预计剩余: 计算中...")
        self.eta_label.setStyleSheet("""
            QLabel {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                font-size: 12px;
                color: #f39c12;
                padding: 3px;
            }
        """)
        right_status.addWidget(self.eta_label)
        
        status_layout.addLayout(left_status)
        status_layout.addLayout(right_status)
        layout.addLayout(status_layout)
        
        group.setLayout(layout)
        return group
    
    def create_log_group(self):
        """创建日志显示组"""
        group = QGroupBox("处理日志")
        
        layout = QVBoxLayout()
        
        # 日志文本区域
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("""
            QTextEdit {
                font-family: "Microsoft YaHei UI", "Consolas", monospace;
                font-size: 9px;
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        group.setLayout(layout)
        return group
    
    def create_button_layout(self):
        """创建按钮布局"""
        layout = QHBoxLayout()
        layout.addStretch()
        
        # 取消/关闭按钮
        self.action_button = QPushButton("取消导出")
        self.action_button.setStyleSheet("""
            QPushButton {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.action_button.clicked.connect(lambda: self.on_action_button_clicked())
        
        layout.addWidget(self.action_button)
        return layout
    
    def setup_timer(self):
        """设置定时器"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_time_info)
        self.update_timer.start(1000)  # 每秒更新一次时间信息
    
    def start_export(self):
        """开始导出"""
        self.start_time = datetime.now()
        self.add_log("开始批量导出...")
        logger.info("导出进度对话框已启动")
    
    @log_exception
    def update_progress(self, progress, current_file=""):
        """更新进度"""
        # 更新进度条
        self.main_progress.setValue(progress)
        
        # 更新进度文本
        self.progress_label.setText(f"进度: {progress}% ({self.processed_files}/{self.total_files})")
        
        # 更新当前文件
        if current_file:
            self.current_file_label.setText(f"正在处理: {current_file}")
            self.add_log(f"处理文件: {current_file}")
        
        # 更新处理计数
        if progress > 0:
            self.processed_files = int((progress / 100) * self.total_files)
            self.processed_label.setText(f"已处理: {self.processed_files}/{self.total_files}")
        
        logger.debug(f"更新导出进度: {progress}%, 当前文件: {current_file}")
    
    @log_exception
    def update_error(self, filename, error_message):
        """更新错误信息"""
        error_log = f"错误: {filename} - {error_message}"
        self.add_log(error_log, is_error=True)
        
        # 更新失败计数（这里需要从外部传入）
        # self.failed_label.setText(f"失败: {failed_count}")
        
        logger.warning(f"导出错误: {filename} - {error_message}")
    
    def update_time_info(self):
        """更新时间信息"""
        if not self.start_time:
            return
        
        # 计算已用时间
        elapsed = datetime.now() - self.start_time
        elapsed_str = self.format_timedelta(elapsed)
        self.elapsed_label.setText(f"已用时间: {elapsed_str}")
        
        # 计算预计剩余时间
        if self.processed_files > 0 and not self.is_completed:
            avg_time_per_file = elapsed.total_seconds() / self.processed_files
            remaining_files = self.total_files - self.processed_files
            eta_seconds = avg_time_per_file * remaining_files
            eta_str = self.format_timedelta(timedelta(seconds=eta_seconds))
            self.eta_label.setText(f"预计剩余: {eta_str}")
        elif self.is_completed:
            self.eta_label.setText("已完成")
    
    def format_timedelta(self, td):
        """格式化时间差"""
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    @log_exception
    def export_completed(self, stats):
        """导出完成"""
        self.is_completed = True
        
        # 更新界面
        self.main_progress.setValue(100)
        self.progress_label.setText("导出完成!")
        self.current_file_label.setText("")
        
        # 更新统计信息
        self.processed_label.setText(f"已处理: {stats['processed']}/{stats['total']}")
        self.failed_label.setText(f"失败: {stats['failed']}")
        
        # 更新按钮
        self.action_button.setText("关闭")
        self.action_button.setStyleSheet("""
            QPushButton {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        # 添加完成日志
        success_rate = (stats['processed'] / stats['total']) * 100
        completion_msg = f"导出完成! 成功率: {success_rate:.1f}% ({stats['processed']}/{stats['total']})"
        self.add_log(completion_msg)
        
        # 如果有错误，显示错误总结
        if stats['failed'] > 0:
            error_summary = f"共有 {stats['failed']} 个文件处理失败"
            self.add_log(error_summary, is_error=True)
        
        logger.info(f"批量导出完成: {completion_msg}")
        
        # 显示完成通知
        if stats['failed'] == 0:
            QMessageBox.information(self, "导出完成", 
                                  f"所有 {stats['total']} 个文件已成功导出!")
        else:
            QMessageBox.warning(self, "导出完成", 
                              f"导出完成，但有 {stats['failed']} 个文件处理失败。\n"
                              f"成功: {stats['processed']} 个文件")
    
    def add_log(self, message, is_error=False):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if is_error:
            log_entry = f"<span style='color: #e74c3c;'>[{timestamp}] {message}</span>"
        else:
            log_entry = f"<span style='color: #ecf0f1;'>[{timestamp}] {message}</span>"
        
        self.log_text.append(log_entry)
        
        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)
    
    @log_exception
    def on_action_button_clicked(self):
        """处理按钮点击"""
        if self.is_completed:
            # 如果已完成，关闭对话框
            self.accept()
        else:
            # 如果未完成，询问是否取消
            reply = QMessageBox.question(
                self, "确认取消", 
                "确定要取消导出吗？已处理的文件不会回滚。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.is_cancelled = True
                self.cancel_requested.emit()
                self.add_log("用户请求取消导出...")
                self.action_button.setText("取消中...")
                self.action_button.setEnabled(False)
                logger.info("用户请求取消批量导出")
    
    def closeEvent(self, event):
        """关闭事件"""
        if not self.is_completed and not self.is_cancelled:
            reply = QMessageBox.question(
                self, "确认关闭", 
                "导出尚未完成，确定要关闭吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
            else:
                self.cancel_requested.emit()
        
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        
        event.accept()
        logger.debug("导出进度对话框已关闭")