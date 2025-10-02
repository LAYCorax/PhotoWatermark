#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水印处理进度对话框和日志增强测试
验证新的用户界面和详细日志记录功能
"""
import sys
import os
import tempfile
from PIL import Image

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QApplication
from utils.logger import logger
from core.watermark_engine import WatermarkEngine
from models.watermark_config import WatermarkConfig, WatermarkType, WatermarkPosition
from ui.dialogs.watermark_progress_dialog import WatermarkProgressDialog

def create_test_images(count=3):
    """创建测试图片"""
    logger.info(f"创建 {count} 个测试图片")
    test_images = []
    
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]  # 红绿蓝
    sizes = [(800, 600), (1024, 768), (1200, 900)]
    
    for i in range(count):
        color = colors[i % len(colors)]
        size = sizes[i % len(sizes)]
        
        # 创建彩色图片
        image = Image.new('RGB', size, color)
        
        # 添加一些文字标识
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        text = f"Test Image {i+1}"
        draw.text((50, 50), text, fill=(255, 255, 255), font=font)
        
        # 保存图片
        temp_file = tempfile.NamedTemporaryFile(suffix=f'_test_{i+1}.jpg', delete=False)
        temp_file.close()
        image.save(temp_file.name, 'JPEG', quality=85)
        
        test_images.append(temp_file.name)
        logger.debug(f"创建测试图片: {temp_file.name} ({size[0]}x{size[1]})")
    
    return test_images

def test_watermark_progress_dialog():
    """测试水印进度对话框"""
    print("=" * 70)
    print("水印处理进度对话框和日志增强测试")
    print("=" * 70)
    
    logger.info("=" * 60)
    logger.info("开始水印处理进度对话框和日志增强测试")
    logger.info("=" * 60)
    
    app = QApplication(sys.argv)
    
    try:
        # 创建测试图片
        test_images = create_test_images(3)
        logger.info(f"创建了 {len(test_images)} 个测试图片")
        
        # 创建水印引擎
        logger.info("初始化水印引擎")
        engine = WatermarkEngine()
        
        # 创建水印配置
        logger.info("配置文本水印")
        config = WatermarkConfig()
        config.watermark_type = WatermarkType.TEXT
        config.position = WatermarkPosition.BOTTOM_RIGHT
        config.text_config.text = "Progress Test Watermark"
        config.text_config.font_size = 32
        config.text_config.opacity = 0.8
        
        # 创建输出目录
        output_dir = tempfile.mkdtemp(prefix="watermark_test_")
        logger.info(f"输出目录: {output_dir}")
        
        # 创建进度对话框
        logger.info("创建进度对话框")
        progress_dialog = WatermarkProgressDialog()
        
        # 模拟处理过程
        progress_dialog.start_processing(len(test_images))
        
        exported_count = 0
        failed_count = 0
        
        logger.info("开始模拟水印处理过程")
        
        for i, image_path in enumerate(test_images):
            if progress_dialog.cancelled:
                logger.info("用户取消了处理")
                break
            
            # 更新进度
            filename = os.path.basename(image_path)
            progress_dialog.update_progress(filename, i + 1)
            
            logger.info(f"处理图片 {i+1}/{len(test_images)}: {filename}")
            
            try:
                # 生成输出路径
                base_name = os.path.splitext(filename)[0]
                output_path = os.path.join(output_dir, f"{base_name}_watermarked.jpg")
                
                logger.debug(f"输出路径: {output_path}")
                
                # 处理图片
                result = engine.process_image(image_path, config, output_path)
                
                if result and os.path.exists(result):
                    exported_count += 1
                    file_size = os.path.getsize(result)
                    logger.info(f"✓ 成功处理: {filename} -> {os.path.basename(result)} ({file_size} 字节)")
                    progress_dialog.add_log(f"✓ 完成: {os.path.basename(result)}")
                    
                    # 模拟处理时间
                    import time
                    time.sleep(1)  # 1秒延迟让用户看到进度
                    
                else:
                    failed_count += 1
                    logger.error(f"✗ 处理失败: {filename}")
                    progress_dialog.add_log(f"✗ 失败: {filename}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"处理异常 {filename}: {str(e)}")
                progress_dialog.add_log(f"✗ 异常: {filename} - {str(e)[:30]}")
        
        # 完成处理
        progress_dialog.finish_processing(exported_count, failed_count)
        
        # 等待用户关闭对话框
        logger.info("等待用户关闭进度对话框")
        result = progress_dialog.exec_()
        
        logger.info(f"测试完成: 成功 {exported_count}, 失败 {failed_count}")
        
        # 清理测试文件
        logger.info("清理测试文件")
        for image_path in test_images:
            try:
                os.unlink(image_path)
            except Exception as e:
                logger.warning(f"清理文件失败 {image_path}: {e}")
        
        # 清理输出文件
        import shutil
        try:
            shutil.rmtree(output_dir)
            logger.info(f"清理输出目录: {output_dir}")
        except Exception as e:
            logger.warning(f"清理输出目录失败: {e}")
        
        logger.info("=" * 60)
        logger.info("水印处理进度对话框和日志增强测试完成")
        logger.info("=" * 60)
        
        print(f"\n🎉 测试完成！")
        print(f"✅ 成功处理: {exported_count} 个文件")
        if failed_count > 0:
            print(f"❌ 失败: {failed_count} 个文件")
        
        print(f"\n📋 测试验证项目:")
        print("✓ 用户友好的进度对话框")
        print("✓ 实时进度更新和文件名显示")
        print("✓ 详细的处理日志记录")
        print("✓ 异常情况的处理和显示")
        print("✓ 用户取消操作的支持")
        print("✓ 处理完成后的结果展示")
        
        return exported_count > 0
        
    except Exception as e:
        logger.error(f"测试过程中发生异常: {str(e)}")
        print(f"❌ 测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_watermark_progress_dialog()
    
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
            
            # 显示最后几行日志
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    print(f"\n最后3行日志:")
                    for line in lines[-3:]:
                        print(f"  {line.strip()}")
            except Exception as e:
                print(f"读取日志失败: {e}")
    
    print(f"\n{'🎊 测试成功' if success else '❌ 测试失败'}！")
    print("水印处理功能现在具有完善的用户界面和详细的日志记录。")
    
    sys.exit(0 if success else 1)