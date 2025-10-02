"""
内存管理工具
用于监控和管理应用程序内存使用
"""
import gc
import os
import sys
from typing import Optional
from utils.logger import logger, log_exception


class MemoryManager:
    """内存管理器"""
    
    def __init__(self):
        logger.info("初始化内存管理器")
        self.memory_warning_threshold = 500 * 1024 * 1024  # 500MB warning threshold
        self.memory_critical_threshold = 1024 * 1024 * 1024  # 1GB critical threshold
        self._last_memory_check = 0
        logger.debug(f"内存阈值设置: 警告={self.memory_warning_threshold//1024//1024}MB, 严重={self.memory_critical_threshold//1024//1024}MB")
    
    @log_exception
    def get_memory_usage(self) -> int:
        """获取当前内存使用量（字节）- 简化版本"""
        try:
            # 尝试使用tracemalloc获取内存信息
            import tracemalloc
            if tracemalloc.is_tracing():
                current, peak = tracemalloc.get_traced_memory()
                logger.debug(f"使用tracemalloc获取内存: {current//1024//1024}MB (peak: {peak//1024//1024}MB)")
                return current
            else:
                # 回退到简单的估算
                estimated = len(gc.get_objects()) * 1000  # 粗略估算
                logger.debug(f"使用估算方法获取内存: {estimated//1024//1024}MB")
                return estimated
        except Exception as e:
            logger.error(f"获取内存使用量失败: {e}")
            return 0
    
    def get_memory_usage_mb(self) -> float:
        """获取当前内存使用量（MB）"""
        return self.get_memory_usage() / (1024 * 1024)
    
    def is_memory_warning(self) -> bool:
        """检查是否达到内存警告阈值"""
        usage = self.get_memory_usage()
        is_warning = usage > self.memory_warning_threshold
        if is_warning:
            logger.warning(f"内存使用达到警告级别: {usage//1024//1024}MB > {self.memory_warning_threshold//1024//1024}MB")
        return is_warning
    
    def is_memory_critical(self) -> bool:
        """检查是否达到内存临界阈值"""
        usage = self.get_memory_usage()
        is_critical = usage > self.memory_critical_threshold
        if is_critical:
            logger.error(f"内存使用达到严重级别: {usage//1024//1024}MB > {self.memory_critical_threshold//1024//1024}MB")
        return is_critical
    
    def force_garbage_collection(self):
        """强制垃圾回收"""
        logger.debug("执行强制垃圾回收")
        collected = gc.collect()
        logger.debug(f"垃圾回收完成, 清理了 {collected} 个对象")
    
    @log_exception
    def cleanup_memory(self):
        """清理内存"""
        logger.info("开始清理内存")
        before_usage = self.get_memory_usage_mb()
        
        try:
            # 强制垃圾回收
            logger.debug("执行垃圾回收")
            self.force_garbage_collection()
            
            # 清理临时文件
            temp_dir = "temp_thumbnails"
            if os.path.exists(temp_dir):
                logger.debug(f"清理临时目录: {temp_dir}")
                self.cleanup_old_thumbnails(temp_dir)
            
            after_usage = self.get_memory_usage_mb()
            logger.info(f"内存清理完成: {before_usage:.1f}MB -> {after_usage:.1f}MB (释放 {before_usage-after_usage:.1f}MB)")
                
        except Exception as e:
            logger.error(f"内存清理错误: {e}")
    
    def cleanup_old_thumbnails(self, temp_dir: str, max_age_hours: int = 24):
        """清理旧的缩略图文件"""
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        try:
                            os.remove(file_path)
                        except OSError:
                            pass  # Ignore if can't delete
                            
        except Exception as e:
            print(f"Thumbnail cleanup error: {e}")
    
    def get_memory_status(self) -> dict:
        """获取内存状态信息"""
        try:
            memory_info = self.process.memory_info()
            return {
                'rss': memory_info.rss,
                'vms': memory_info.vms,
                'rss_mb': memory_info.rss / (1024 * 1024),
                'vms_mb': memory_info.vms / (1024 * 1024),
                'is_warning': self.is_memory_warning(),
                'is_critical': self.is_memory_critical()
            }
        except Exception:
            return {}


# 全局内存管理器实例
memory_manager = MemoryManager()