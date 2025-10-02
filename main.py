"""
PhotoWatermark Desktop Application
Main entry point for the application
"""
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QIcon
except ImportError:
    print("Error: PyQt5 is required but not installed.")
    print("Please install it using: pip install PyQt5")
    sys.exit(1)

from ui.main_window import MainWindow
from utils.logger import logger, log_exception


class PhotoWatermarkApp(QApplication):
    """Main application class"""
    
    def __init__(self, argv):
        super().__init__(argv)
        
        logger.info("初始化PhotoWatermark应用程序")
        
        # Set application properties
        logger.debug("设置应用程序属性")
        self.setApplicationName("PhotoWatermark")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("PhotoWatermark Team")
        self.setApplicationDisplayName("PhotoWatermark - 专业照片水印工具")
        
        # Set application style
        logger.debug("设置应用程序样式")
        self.setStyle('Fusion')  # Modern cross-platform style
        
        # Apply application-wide stylesheet
        logger.debug("应用样式表")
        self.setStyleSheet(self.get_application_stylesheet())
        
        # Create main window
        self.main_window = None
        logger.info("初始化主窗口")
        self.init_main_window()
    
    @log_exception
    def init_main_window(self):
        """Initialize and show main window"""
        try:
            logger.info("创建主窗口实例")
            self.main_window = MainWindow()
            logger.info("显示主窗口")
            self.main_window.show()
            logger.info("应用程序启动成功")
        except Exception as e:
            logger.error(f"应用程序启动失败: {e}")
            QMessageBox.critical(
                None,
                "启动错误",
                f"应用程序启动失败：\n{str(e)}\n\n请检查依赖是否正确安装。",
                QMessageBox.Ok
            )
            sys.exit(1)
    
    def get_application_stylesheet(self):
        """Get application-wide stylesheet with Chinese font support"""
        return """
        /* Application-wide styles with beautiful Chinese font support */
        
        * {
            font-family: "Microsoft YaHei UI", "Microsoft YaHei", "SimHei", "黑体", "Arial", sans-serif;
        }
        
        QMainWindow {
            background-color: #f5f5f5;
            color: #333;
        }
        
        QMenuBar {
            background-color: #fff;
            border-bottom: 1px solid #ddd;
            padding: 2px;
        }
        
        QMenuBar::item {
            background-color: transparent;
            padding: 5px 8px;
            border-radius: 3px;
        }
        
        QMenuBar::item:selected {
            background-color: #e3f2fd;
        }
        
        QMenu {
            background-color: #fff;
            border: 1px solid #ddd;
            border-radius: 3px;
            padding: 3px;
        }
        
        QMenu::item {
            padding: 5px 20px;
            border-radius: 3px;
        }
        
        QMenu::item:selected {
            background-color: #e3f2fd;
        }
        
        QStatusBar {
            background-color: #fff;
            border-top: 1px solid #ddd;
            padding: 2px;
        }
        
        QPushButton {
            background-color: #fff;
            border: 1px solid #ddd;
            border-radius: 3px;
            padding: 5px 10px;
            min-width: 60px;
        }
        
        QPushButton:hover {
            background-color: #f0f0f0;
            border-color: #bbb;
        }
        
        QPushButton:pressed {
            background-color: #e0e0e0;
        }
        
        QPushButton:disabled {
            background-color: #f8f8f8;
            color: #aaa;
            border-color: #eee;
        }
        
        QLineEdit {
            background-color: #fff;
            border: 1px solid #ddd;
            border-radius: 3px;
            padding: 5px;
        }
        
        QLineEdit:focus {
            border-color: #2196f3;
        }
        
        QComboBox {
            background-color: #fff;
            border: 1px solid #ddd;
            border-radius: 3px;
            padding: 5px;
        }
        
        QComboBox:focus {
            border-color: #2196f3;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #666;
        }
        
        QSpinBox {
            background-color: #fff;
            border: 1px solid #ddd;
            border-radius: 3px;
            padding: 3px;
        }
        
        QSpinBox:focus {
            border-color: #2196f3;
        }
        
        QSlider::groove:horizontal {
            border: 1px solid #ddd;
            height: 6px;
            background: #f0f0f0;
            border-radius: 3px;
        }
        
        QSlider::handle:horizontal {
            background: #2196f3;
            border: 1px solid #1976d2;
            width: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }
        
        QSlider::handle:horizontal:hover {
            background: #1976d2;
        }
        
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #ddd;
            border-radius: 2px;
            background-color: #fff;
        }
        
        QCheckBox::indicator:checked {
            background-color: #2196f3;
            border-color: #1976d2;
        }
        
        QRadioButton::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #ddd;
            border-radius: 8px;
            background-color: #fff;
        }
        
        QRadioButton::indicator:checked {
            background-color: #2196f3;
            border-color: #1976d2;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 1px solid #ddd;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 5px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            background-color: #f5f5f5;
        }
        
        QSplitter::handle {
            background-color: #ddd;
        }
        
        QSplitter::handle:horizontal {
            width: 3px;
        }
        
        QSplitter::handle:vertical {
            height: 3px;
        }
        
        QMessageBox {
            background-color: #fff;
        }
        """


@log_exception
def main():
    """Main function"""
    logger.info("=" * 60)
    logger.info("PhotoWatermark 应用程序启动")
    logger.info("=" * 60)
    
    # Enable high DPI scaling
    logger.debug("启用高DPI缩放")
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create and run application
    logger.info("创建应用程序实例")
    app = PhotoWatermarkApp(sys.argv)
    
    # Set up exception handling
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        import traceback
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.error(f"未捕获异常: {error_msg}")
        
        QMessageBox.critical(
            None,
            "程序错误",
            f"程序遇到未处理的错误：\n\n{str(exc_value)}\n\n程序将退出。",
            QMessageBox.Ok
        )
        sys.exit(1)
    
    logger.debug("设置全局异常处理器")
    sys.excepthook = handle_exception
    
    # Run the application
    try:
        logger.info("启动应用程序主循环")
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        logger.info("用户中断应用程序")
        print("\nApplication interrupted by user")
        sys.exit(0)


if __name__ == '__main__':
    main()