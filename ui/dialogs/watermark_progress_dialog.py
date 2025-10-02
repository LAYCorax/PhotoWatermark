"""
进度提示对话框
提供用户友好的处理进度提示
"""
try:
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
        QPushButton, QProgressBar, QTextEdit, QFrame
    )
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal
    from PyQt5.QtGui import QFont, QMovie, QPixmap
except ImportError:
    print("PyQt5 is required but not installed.")
    raise

from utils.logger import logger, log_exception


class WatermarkProgressDialog(QDialog):
    """水印处理进度对话框"""
    
    # 信号
    cancel_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("正在处理水印...")
        self.setFixedSize(450, 320)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint)
        self.setModal(True)
        
        self.cancelled = False
        self.current_file = ""
        self.total_files = 0
        self.processed_files = 0
        
        logger.debug("创建水印处理进度对话框")
        
        self.init_ui()
        self.setup_timer()
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("正在处理水印，请稍候...")
        title_label.setStyleSheet("""
            QLabel {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", "SimHei", "黑体", sans-serif;
                font-size: 15px;
                font-weight: bold;
                color: #2c3e50;
                padding: 8px;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # 当前处理文件
        self.current_file_label = QLabel("准备开始...")
        self.current_file_label.setWordWrap(True)
        self.current_file_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #ddd;
            }
        """)
        layout.addWidget(self.current_file_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ccc;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # 详细信息
        self.detail_label = QLabel("初始化中...")
        self.detail_label.setAlignment(Qt.AlignCenter)
        self.detail_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.detail_label)
        
        # 日志输出区域
        log_label = QLabel("处理日志:")
        log_label.setFont(QFont("", 9))
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(100)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-family: "Consolas", "Microsoft YaHei UI", "Courier New", "微软雅黑", monospace;
                font-size: 10px;
                color: #495057;
                line-height: 1.4;
                padding: 4px;
            }
        """)
        layout.addWidget(self.log_text)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setMinimumWidth(80)
        self.cancel_button.clicked.connect(self.cancel_processing)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def setup_timer(self):
        """设置定时器用于动画效果"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.animation_dots = 0
    
    def start_processing(self, total_files: int):
        """开始处理"""
        logger.info(f"开始水印处理进度显示，总文件数: {total_files}")
        self.total_files = total_files
        self.processed_files = 0
        self.progress_bar.setMaximum(total_files)
        self.progress_bar.setValue(0)
        self.cancelled = False
        
        self.detail_label.setText(f"总共 {total_files} 个文件待处理")
        self.add_log(f"开始处理 {total_files} 个文件")
        
        # 启动动画
        self.timer.start(500)  # 500ms间隔
        
        self.show()
    
    def update_progress(self, current_file: str, file_index: int):
        """更新进度"""
        self.current_file = current_file
        self.processed_files = file_index
        
        logger.debug(f"更新进度: {file_index}/{self.total_files}, 当前文件: {current_file}")
        
        # 更新进度条
        self.progress_bar.setValue(file_index)
        
        # 更新当前文件显示
        self.current_file_label.setText(f"正在处理: {current_file}")
        
        # 更新详细信息
        percentage = (file_index / self.total_files * 100) if self.total_files > 0 else 0
        self.detail_label.setText(f"进度: {file_index}/{self.total_files} ({percentage:.1f}%)")
        
        # 添加日志
        self.add_log(f"[{file_index}/{self.total_files}] {current_file}")
        
        # 处理事件，保持界面响应
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()
    
    def add_log(self, message: str):
        """添加日志信息"""
        self.log_text.append(message)
        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)
    
    def update_animation(self):
        """更新动画效果"""
        if not self.cancelled:
            self.animation_dots = (self.animation_dots + 1) % 4
            dots = "." * self.animation_dots
            self.setWindowTitle(f"正在处理水印{dots}")
    
    def set_current_file(self, filename: str):
        """设置当前处理的文件"""
        self.current_file_label.setText(f"正在处理: {filename}")
        logger.debug(f"设置当前处理文件: {filename}")
    
    def finish_processing(self, success_count: int, failed_count: int):
        """完成处理"""
        logger.info(f"水印处理完成: 成功 {success_count}, 失败 {failed_count}")
        
        self.timer.stop()
        self.setWindowTitle("处理完成")
        
        if failed_count == 0:
            self.current_file_label.setText(f"✅ 全部完成！成功处理 {success_count} 个文件")
            self.current_file_label.setStyleSheet("""
                QLabel {
                    background-color: #e8f5e8;
                    color: #2e7d32;
                    padding: 8px;
                    border-radius: 4px;
                    border: 1px solid #4caf50;
                    font-weight: bold;
                }
            """)
        else:
            self.current_file_label.setText(f"⚠️ 处理完成：成功 {success_count}，失败 {failed_count}")
            self.current_file_label.setStyleSheet("""
                QLabel {
                    background-color: #fff3e0;
                    color: #f57c00;
                    padding: 8px;
                    border-radius: 4px;
                    border: 1px solid #ff9800;
                    font-weight: bold;
                }
            """)
        
        self.detail_label.setText("处理完成，可以关闭此窗口")
        self.add_log(f"处理完成：成功 {success_count}，失败 {failed_count}")
        
        # 更改按钮
        self.cancel_button.setText("关闭")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
    
    @log_exception
    def cancel_processing(self, checked=False):
        """取消处理
        
        Args:
            checked (bool): Qt clicked signal 参数，表示按钮是否被选中（ignored）
        """
        if self.cancel_button.text() == "关闭":
            logger.debug("用户关闭进度对话框")
            self.accept()
        else:
            logger.info("用户请求取消水印处理")
            self.cancelled = True
            self.cancel_requested.emit()
            self.current_file_label.setText("正在取消...")
            self.detail_label.setText("请稍候，正在安全停止处理...")
            self.cancel_button.setEnabled(False)
    
    def closeEvent(self, event):
        """处理关闭事件"""
        if not self.cancelled and self.cancel_button.text() != "关闭":
            # 如果还在处理中，先取消
            self.cancel_processing()
            event.ignore()
        else:
            logger.debug("进度对话框关闭")
            self.timer.stop()
            event.accept()