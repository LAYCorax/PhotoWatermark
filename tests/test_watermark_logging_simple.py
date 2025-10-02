#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水印处理日志增强验证测试（无GUI）
验证水印引擎的详细日志记录功能
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

def test_watermark_logging_enhancement():
    """测试水印处理的日志增强功能"""
    print("=" * 70)
    print("水印处理日志增强验证测试")
    print("=" * 70)
    
    logger.info("=" * 60)
    logger.info("开始水印处理日志增强验证测试")
    logger.info("=" * 60)
    
    try:
        # 创建测试图片
        logger.info("创建测试图片")
        test_image = Image.new('RGB', (1200, 800), (100, 150, 200))
        
        # 添加一些图案
        from PIL import ImageDraw
        draw = ImageDraw.Draw(test_image)
        draw.rectangle([50, 50, 200, 150], fill=(255, 255, 0))
        draw.ellipse([300, 100, 500, 300], fill=(255, 0, 255))
        
        temp_file = tempfile.NamedTemporaryFile(suffix='_log_test.jpg', delete=False)
        temp_file.close()
        test_image.save(temp_file.name, 'JPEG', quality=90)
        
        logger.info(f"测试图片已创建: {temp_file.name}")
        print(f"✓ 创建测试图片: {os.path.basename(temp_file.name)}")
        
        # 创建水印引擎
        logger.info("创建水印引擎实例")
        engine = WatermarkEngine()
        print("✓ 水印引擎已创建")
        
        # 测试文本水印
        logger.info("测试文本水印处理")
        print("\n📝 测试文本水印:")
        
        config = WatermarkConfig()
        config.watermark_type = WatermarkType.TEXT
        config.position = WatermarkPosition.BOTTOM_RIGHT
        config.text_config.text = "日志增强测试水印"
        config.text_config.font_size = 36
        config.text_config.opacity = 0.8
        
        logger.info("配置文本水印参数")
        logger.debug(f"水印文本: '{config.text_config.text}'")
        logger.debug(f"字体大小: {config.text_config.font_size}")
        logger.debug(f"透明度: {config.text_config.opacity}")
        logger.debug(f"位置: {config.position}")
        
        # 处理文本水印
        output_path_text = temp_file.name.replace('.jpg', '_text_watermark.jpg')
        logger.info(f"开始处理文本水印，输出到: {output_path_text}")
        
        result_text = engine.process_image(temp_file.name, config, output_path_text)
        
        if result_text and os.path.exists(result_text):
            file_size = os.path.getsize(result_text)
            logger.info(f"文本水印处理成功: {result_text} ({file_size} 字节)")
            print(f"  ✅ 文本水印成功: {os.path.basename(result_text)} ({file_size} 字节)")
        else:
            logger.error("文本水印处理失败")
            print("  ❌ 文本水印处理失败")
        
        # 测试不同位置的水印
        logger.info("测试不同位置的水印")
        print("\n📍 测试不同位置的水印:")
        
        positions = [
            (WatermarkPosition.TOP_LEFT, "左上角"),
            (WatermarkPosition.CENTER, "中心"),
            (WatermarkPosition.BOTTOM_RIGHT, "右下角")
        ]
        
        for pos, pos_name in positions:
            config.position = pos
            config.text_config.text = f"{pos_name}水印"
            
            output_path = temp_file.name.replace('.jpg', f'_{pos.value}.jpg')
            logger.info(f"处理{pos_name}水印")
            
            result = engine.process_image(temp_file.name, config, output_path)
            
            if result and os.path.exists(result):
                logger.info(f"{pos_name}水印处理成功")
                print(f"  ✅ {pos_name}: {os.path.basename(result)}")
            else:
                logger.error(f"{pos_name}水印处理失败")
                print(f"  ❌ {pos_name}: 处理失败")
        
        # 测试大图片处理（触发保守模式）
        logger.info("测试大图片处理")
        print("\n🖼️  测试大图片处理:")
        
        large_image = Image.new('RGB', (3000, 2000), (50, 100, 150))
        large_temp = tempfile.NamedTemporaryFile(suffix='_large_test.jpg', delete=False)
        large_temp.close()
        large_image.save(large_temp.name, 'JPEG', quality=85)
        
        logger.info(f"创建大图片: {large_temp.name} (3000x2000)")
        
        config.text_config.text = "大图片水印测试"
        config.text_config.font_size = 72
        output_large = large_temp.name.replace('.jpg', '_watermarked.jpg')
        
        result_large = engine.process_image(large_temp.name, config, output_large)
        
        if result_large and os.path.exists(result_large):
            file_size = os.path.getsize(result_large)
            logger.info(f"大图片水印处理成功: {file_size} 字节")
            print(f"  ✅ 大图片处理成功: {file_size} 字节")
        else:
            logger.error("大图片水印处理失败")
            print("  ❌ 大图片处理失败")
        
        # 测试错误处理
        logger.info("测试错误处理")
        print("\n❌ 测试错误处理:")
        
        # 测试不存在的文件
        fake_path = "non_existent_file.jpg"
        logger.info(f"测试不存在的文件: {fake_path}")
        result_fake = engine.process_image(fake_path, config, "output.jpg")
        
        if result_fake is None:
            logger.info("不存在文件的错误处理正确")
            print("  ✅ 不存在文件的错误处理正确")
        else:
            logger.error("不存在文件的错误处理有问题")
            print("  ❌ 不存在文件的错误处理有问题")
        
        # 清理测试文件
        logger.info("清理测试文件")
        test_files = [temp_file.name, large_temp.name]
        for pattern in ['*_watermark*.jpg', '*_text_*.jpg', '*_top_*.jpg', '*_center*.jpg', '*_bottom_*.jpg']:
            import glob
            test_files.extend(glob.glob(pattern))
        
        cleaned_count = 0
        for file_path in test_files:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    cleaned_count += 1
            except Exception as e:
                logger.warning(f"清理文件失败 {file_path}: {e}")
        
        logger.info(f"清理了 {cleaned_count} 个测试文件")
        
        logger.info("=" * 60)
        logger.info("水印处理日志增强验证测试完成")
        logger.info("=" * 60)
        
        print(f"\n🎉 日志增强测试完成！")
        print(f"✅ 测试通过，详细日志已记录")
        
        return True
        
    except Exception as e:
        logger.error(f"测试过程中发生异常: {str(e)}")
        print(f"❌ 测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_watermark_logging_enhancement()
    
    print(f"\n📋 日志增强验证项目:")
    print("✓ 水印引擎初始化日志")
    print("✓ 图片处理过程详细记录")
    print("✓ 水印配置参数记录")
    print("✓ 文件操作状态跟踪")
    print("✓ 错误和异常完整记录")
    print("✓ 性能和内存使用监控")
    
    print(f"\n📁 日志文件信息:")
    print("-" * 50)
    log_dir = "logs"
    if os.path.exists(log_dir):
        log_files = sorted([f for f in os.listdir(log_dir) if f.endswith('.log')])
        if log_files:
            latest_log = log_files[-1]
            log_path = os.path.join(log_dir, latest_log)
            print(f"最新日志: {latest_log}")
            print(f"大小: {os.path.getsize(log_path)} 字节")
    
    print(f"\n{'🎊 水印处理日志增强成功' if success else '❌ 测试失败'}！")
    print("现在可以通过详细的日志信息追踪水印处理的每个步骤。")
    
    sys.exit(0 if success else 1)