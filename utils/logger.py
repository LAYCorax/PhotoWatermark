"""
日志配置模块
提供统一的日志记录功能
"""
import logging
import os
import sys
from datetime import datetime


class PhotoWatermarkLogger:
    """PhotoWatermark应用程序日志器"""
    
    def __init__(self):
        self.logger = None
        self.setup_logger()
    
    def setup_logger(self):
        """设置日志配置"""
        # 创建日志目录
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # 创建日志文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"photowater_{timestamp}.log")
        
        # 配置日志器
        self.logger = logging.getLogger('PhotoWatermark')
        self.logger.setLevel(logging.DEBUG)
        
        # 清除已有的处理器
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # 创建文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # 创建格式器
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        console_formatter = logging.Formatter(
            '[%(levelname)s] %(name)s: %(message)s'
        )
        
        # 设置格式器
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # 记录启动信息
        self.logger.info("="*60)
        self.logger.info("PhotoWatermark 应用程序启动")
        self.logger.info(f"日志文件: {log_file}")
        self.logger.info("="*60)
    
    def get_logger(self):
        """获取日志器实例"""
        return self.logger


# 全局日志器实例
_photo_logger = PhotoWatermarkLogger()
logger = _photo_logger.get_logger()


def log_exception(func):
    """装饰器：自动记录异常"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"异常发生在 {func.__name__}: {str(e)}")
            raise
    return wrapper


def log_performance(func):
    """装饰器：记录性能信息"""
    def wrapper(*args, **kwargs):
        import time
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            logger.debug(f"性能统计 {func.__name__}: {duration:.3f}秒")
            return result
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            logger.error(f"异常发生在 {func.__name__} (耗时 {duration:.3f}秒): {str(e)}")
            raise
    return wrapper