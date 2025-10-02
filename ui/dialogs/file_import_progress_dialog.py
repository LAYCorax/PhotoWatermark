"""
文件导入进度对话框
提供用户友好的文件导入进度提示
"""
try:
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
        QPushButton, QProgressBar, QTextEdit, QFrame
    )
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal
    from PyQt5.QtGui import QFont
except ImportError:
    print("PyQt5 is required but not installed.")
    raise

from utils.logger import logger, log_exception


class FileImportProgressDialog(QDialog):
    """文件导入进度对话框"""
    
    # 信号
    cancel_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("正在导入文件...")
        self.setFixedSize(500, 350)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint)
        self.setModal(True)
        
        self.cancelled = False
        self.current_phase = ""
        self.total_files = 0
        self.processed_files = 0
        
        logger.debug("创建文件导入进度对话框")
        
        self.init_ui()
        self.setup_timer()
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("正在导入图片文件，请稍候...")
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
        
        # 当前阶段
        self.phase_label = QLabel("准备开始...")
        self.phase_label.setWordWrap(True)
        self.phase_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #ddd;
            }
        """)
        layout.addWidget(self.phase_label)
        
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
        self.detail_label.setStyleSheet("""
            QLabel {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", "SimSun", "宋体", sans-serif;
                color: #5d6d7e;
                font-size: 12px;
                padding: 6px;
                line-height: 1.4;
            }
        """)
        layout.addWidget(self.detail_label)
        
        # 状态日志区域
        log_label = QLabel("导入日志:")
        log_label.setStyleSheet("""
            QLabel {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", "SimSun", "宋体", sans-serif;
                font-size: 11px;
                color: #5d6d7e;
                font-weight: 500;
                padding: 2px 0;
            }
        """)
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
        self.cancel_button.clicked.connect(self.cancel_import)
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
    
    def start_scanning(self, folder_path: str, recursive: bool):
        """开始文件夹扫描"""
        logger.info(f"开始扫描文件夹: {folder_path}, 递归={recursive}")
        self.current_phase = "扫描文件夹"
        self.cancelled = False
        
        self.phase_label.setText(f"正在扫描: {folder_path}")
        self.detail_label.setText("扫描中，请稍候...")
        self.progress_bar.setRange(0, 0)  # 不确定进度
        
        self.add_log(f"开始扫描文件夹: {folder_path}")
        if recursive:
            self.add_log("包含子文件夹扫描")
        
        # 启动动画
        self.timer.start(500)
        self.show()
    
    def finish_scanning(self, file_count: int):
        """完成文件夹扫描"""
        logger.info(f"文件夹扫描完成，找到 {file_count} 个图片文件")
        self.total_files = file_count
        
        if file_count > 0:
            self.phase_label.setText(f"找到 {file_count} 个图片文件")
            self.detail_label.setText("准备开始导入...")
            self.add_log(f"扫描完成，找到 {file_count} 个文件")
        else:
            self.phase_label.setText("未找到图片文件")
            self.detail_label.setText("请检查文件夹是否包含支持的图片格式")
            self.add_log("未找到图片文件")
    
    def start_importing(self, total_files: int):
        """开始导入文件"""
        logger.info(f"开始导入 {total_files} 个文件")
        self.current_phase = "导入文件"
        self.total_files = total_files
        self.processed_files = 0
        
        self.progress_bar.setRange(0, total_files)
        self.progress_bar.setValue(0)
        
        self.phase_label.setText("正在导入文件...")
        self.detail_label.setText(f"总共 {total_files} 个文件待导入")
        self.add_log(f"开始导入 {total_files} 个文件")
    
    def update_import_progress(self, processed: int, added: int, current_file: str = ""):
        """更新导入进度"""
        self.processed_files = processed
        
        logger.debug(f"导入进度: {processed}/{self.total_files}, 已添加: {added}")
        
        # 更新进度条
        self.progress_bar.setValue(processed)
        
        # 更新显示
        if current_file:
            self.phase_label.setText(f"正在处理: {current_file}")
        
        percentage = (processed / self.total_files * 100) if self.total_files > 0 else 0
        self.detail_label.setText(f"进度: {processed}/{self.total_files} ({percentage:.1f}%) - 已添加: {added}")
        
        # 添加日志
        if current_file:
            self.add_log(f"[{processed}/{self.total_files}] {current_file}")
        
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
            if self.current_phase == "扫描文件夹":
                self.setWindowTitle(f"正在扫描文件夹{dots}")
            elif self.current_phase == "导入文件":
                self.setWindowTitle(f"正在导入文件{dots}")
    
    def finish_importing(self, total_added: int, total_skipped: int):
        """完成导入"""
        logger.info(f"文件导入完成: 添加 {total_added}, 跳过 {total_skipped}")
        
        self.timer.stop()
        self.setWindowTitle("导入完成")
        
        if total_added > 0:
            self.phase_label.setText(f"✅ 导入完成！成功添加 {total_added} 个文件")
            self.phase_label.setStyleSheet("""
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
            self.phase_label.setText("⚠️ 未添加新文件（可能已存在或格式不支持）")
            self.phase_label.setStyleSheet("""
                QLabel {
                    background-color: #fff3e0;
                    color: #f57c00;
                    padding: 8px;
                    border-radius: 4px;
                    border: 1px solid #ff9800;
                    font-weight: bold;
                }
            """)
        
        if total_skipped > 0:
            self.detail_label.setText(f"添加: {total_added}, 跳过: {total_skipped}")
        else:
            self.detail_label.setText("导入完成，可以关闭此窗口")
        
        self.add_log(f"导入完成：添加 {total_added}，跳过 {total_skipped}")
        
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
    def cancel_import(self, checked=False):
        """取消导入
        
        Args:
            checked (bool): Qt clicked signal 参数，表示按钮是否被选中（ignored）
        """
        if self.cancel_button.text() == "关闭":
            logger.debug("用户关闭导入进度对话框")
            self.accept()
        else:
            logger.info("用户请求取消文件导入")
            self.cancelled = True
            self.cancel_requested.emit()
            self.phase_label.setText("正在取消...")
            self.detail_label.setText("请稍候，正在安全停止导入...")
            self.cancel_button.setEnabled(False)
    
    def closeEvent(self, event):
        """处理关闭事件"""
        if not self.cancelled and self.cancel_button.text() != "关闭":
            # 如果还在处理中，先取消
            self.cancel_import()
            event.ignore()
        else:
            logger.debug("导入进度对话框关闭")
            self.timer.stop()
            event.accept()