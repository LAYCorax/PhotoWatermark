#!/usr/bin/env python3
"""
应用程序启动测试 - 自动退出版本
"""
import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from utils.logger import logger
from ui.main_window import MainWindow

def test_app_startup():
    """测试应用程序启动和日志记录"""
    logger.info("=" * 60)
    logger.info("应用程序启动日志测试")
    logger.info("=" * 60)
    
    # 创建QApplication
    app = QApplication(sys.argv)
    
    try:
        # 创建主窗口
        logger.info("创建应用程序主窗口...")
        main_window = MainWindow()
        main_window.show()
        
        logger.info("应用程序主窗口已显示")
        logger.info("所有组件初始化完成")
        
        # 设置3秒后自动退出
        def auto_exit():
            logger.info("测试完成，3秒后自动退出")
            logger.info("=" * 60)
            logger.info("应用程序启动日志测试完成")
            logger.info("=" * 60)
            app.quit()
        
        timer = QTimer()
        timer.timeout.connect(auto_exit)
        timer.start(3000)  # 3秒
        
        print("✅ 应用程序启动成功，正在记录日志...")
        print("⏱️  3秒后自动退出...")
        
        # 运行应用
        app.exec_()
        
        return True
        
    except Exception as e:
        logger.error(f"应用程序启动失败: {e}")
        print(f"✗ 应用程序启动失败: {e}")
        return False

if __name__ == "__main__":
    success = test_app_startup()
    print("\n日志已记录到 logs/ 目录")