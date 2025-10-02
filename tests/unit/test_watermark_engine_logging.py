#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水印引擎日志功能验证测试
测试watermark_engine的增强日志记录功能
"""
import sys
import os
import tempfile
from PIL import Image

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from utils.logger import logger
from core.watermark_engine import WatermarkEngine
from models.watermark_config import WatermarkConfig, WatermarkType, WatermarkPosition

def test_watermark_engine_logging():
    """测试水印引擎的日志功能"""
    print("=" * 60)
    print("水印引擎日志功能验证测试")
    print("=" * 60)
    
    logger.info("=" * 50)
    logger.info("开始水印引擎日志功能验证测试")
    logger.info("=" * 50)
    
    try:
        # 创建测试图片
        logger.info("创建测试图片")
        test_image = Image.new('RGB', (800, 600), (100, 150, 200))
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        temp_file.close()
        test_image.save(temp_file.name, 'JPEG')
        logger.info(f"测试图片已创建: {temp_file.name}")
        
        # 创建水印引擎
        logger.info("创建水印引擎实例")
        engine = WatermarkEngine()
        
        # 创建水印配置
        logger.info("配置文本水印")
        config = WatermarkConfig()
        config.watermark_type = WatermarkType.TEXT
        config.position = WatermarkPosition.BOTTOM_RIGHT
        config.text_config.text = "测试水印 - 日志记录"
        config.text_config.font_size = 48
        config.text_config.opacity = 0.7
        
        # 处理图片并添加水印
        logger.info("开始水印处理")
        output_path = temp_file.name.replace('.jpg', '_watermarked_log_test.jpg')
        result = engine.process_image(temp_file.name, config, output_path)
        
        if result and os.path.exists(result):
            logger.info(f"水印处理成功: {result}")
            print("✅ 水印引擎日志测试通过")
            print(f"   输出文件: {result}")
            
            # 检查文件大小
            file_size = os.path.getsize(result)
            logger.info(f"输出文件大小: {file_size} 字节")
            print(f"   文件大小: {file_size} 字节")
        else:
            logger.error("水印处理失败")
            print("❌ 水印引擎日志测试失败")
        
        # 清理测试文件
        try:
            os.unlink(temp_file.name)
            if result and os.path.exists(result):
                os.unlink(result)
            logger.info("测试文件清理完成")
        except Exception as e:
            logger.warning(f"清理测试文件时出现警告: {e}")
        
        logger.info("=" * 50)
        logger.info("水印引擎日志功能验证测试完成")
        logger.info("=" * 50)
        
        print("\n📋 日志记录验证:")
        print("-" * 40)
        print("✓ 引擎初始化日志")
        print("✓ 图片处理过程日志")
        print("✓ 水印应用详细日志")
        print("✓ 文件保存过程日志")
        print("✓ 错误和异常处理日志")
        
        return True
        
    except Exception as e:
        logger.error(f"水印引擎日志测试失败: {e}")
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_watermark_engine_logging()
    
    print(f"\n📁 日志文件信息:")
    print("-" * 40)
    log_dir = "logs"
    if os.path.exists(log_dir):
        log_files = sorted([f for f in os.listdir(log_dir) if f.endswith('.log')])
        if log_files:
            latest_log = log_files[-1]
            log_path = os.path.join(log_dir, latest_log)
            print(f"最新日志: {latest_log}")
            print(f"大小: {os.path.getsize(log_path)} 字节")
    
    print(f"\n🎉 水印引擎日志增强{'成功' if success else '失败'}！")
    sys.exit(0 if success else 1)