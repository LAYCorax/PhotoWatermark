#!/usr/bin/env python3
"""
完整应用日志功能测试
测试应用程序的所有组件是否都正确记录日志
"""
import sys
import os
import tempfile
from PIL import Image
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from utils.logger import logger
from ui.main_window import MainWindow
from models.watermark_config import WatermarkConfig, WatermarkType, WatermarkPosition

def create_test_image(size=(800, 600), color=(255, 255, 255)):
    """创建测试图片"""
    image = Image.new('RGB', size, color)
    temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
    image.save(temp_file.name, 'JPEG')
    return temp_file.name

def test_complete_logging():
    """测试完整的应用日志功能"""
    print("PhotoWatermark 完整日志功能测试")
    print("=" * 50)
    
    # 初始化日志
    logger.info("=" * 60)
    logger.info("开始完整应用日志功能测试")
    logger.info("=" * 60)
    
    # 创建QApplication
    app = QApplication(sys.argv)
    
    try:
        # 测试主窗口创建
        logger.info("创建主窗口...")
        main_window = MainWindow()
        
        # 创建测试图片
        test_image_path = create_test_image()
        logger.info(f"创建测试图片: {test_image_path}")
        
        # 测试添加图片到列表
        logger.info("测试添加图片到列表...")
        main_window.image_list_model.add_images([test_image_path])
        
        # 测试水印配置
        logger.info("测试水印配置...")
        config = WatermarkConfig()
        config.watermark_type = WatermarkType.TEXT
        config.text = "测试水印"
        config.position = WatermarkPosition.BOTTOM_RIGHT
        config.opacity = 0.8
        
        # 测试水印引擎处理
        logger.info("测试水印引擎处理...")
        output_path = test_image_path.replace('.jpg', '_watermarked.jpg')
        result = main_window.watermark_engine.process_image(
            test_image_path, config, output_path
        )
        
        if result and os.path.exists(result):
            logger.info(f"水印处理成功: {result}")
            print("✓ 水印处理测试通过")
        else:
            logger.error("水印处理失败")
            print("✗ 水印处理测试失败")
        
        # 测试预览功能
        logger.info("测试预览功能...")
        main_window.preview_widget.set_image(test_image_path)
        main_window.preview_widget.update_watermark_preview()
        logger.info("预览功能测试完成")
        print("✓ 预览功能测试通过")
        
        # 清理测试文件
        try:
            os.unlink(test_image_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
            logger.info("测试文件清理完成")
        except Exception as e:
            logger.warning(f"清理测试文件时出现警告: {e}")
        
        logger.info("=" * 60)
        logger.info("完整应用日志功能测试完成")
        logger.info("=" * 60)
        
        print("✅ 完整应用日志功能测试通过!")
        print("\n日志信息:")
        print("-" * 30)
        
        # 显示日志文件信息
        log_dir = "logs"
        if os.path.exists(log_dir):
            log_files = sorted([f for f in os.listdir(log_dir) if f.endswith('.log')])
            if log_files:
                latest_log = log_files[-1]
                log_path = os.path.join(log_dir, latest_log)
                print(f"最新日志文件: {latest_log}")
                print(f"日志文件大小: {os.path.getsize(log_path)} 字节")
                print(f"完整路径: {log_path}")
                
                # 显示最后几行日志
                try:
                    with open(log_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        print(f"\n最后5行日志内容:")
                        for line in lines[-5:]:
                            print(f"  {line.strip()}")
                except Exception as e:
                    print(f"读取日志文件失败: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"完整应用测试失败: {e}")
        print(f"✗ 测试失败: {e}")
        return False
    finally:
        # 安全退出
        try:
            app.quit()
        except:
            pass

if __name__ == "__main__":
    success = test_complete_logging()
    sys.exit(0 if success else 1)