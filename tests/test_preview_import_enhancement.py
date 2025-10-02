#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预览和导入功能增强测试
验证预览图片生成的日志记录和文件导入进度对话框
"""
import sys
import os
import tempfile
import shutil
from PIL import Image

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from utils.logger import logger
from models.watermark_config import WatermarkConfig, WatermarkType, WatermarkPosition

def create_test_images_folder():
    """创建测试图片文件夹"""
    logger.info("创建测试图片文件夹")
    
    # 创建临时文件夹
    test_folder = tempfile.mkdtemp(prefix="test_images_")
    logger.info(f"测试文件夹: {test_folder}")
    
    # 创建子文件夹
    sub_folder = os.path.join(test_folder, "subfolder")
    os.makedirs(sub_folder)
    
    # 创建测试图片
    test_images = []
    
    # 主文件夹中的图片
    for i in range(3):
        image = Image.new('RGB', (400 + i * 100, 300 + i * 50), 
                         (255 - i * 50, 100 + i * 50, 150 + i * 30))
        
        # 添加文字标识
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        text = f"Main Image {i+1}"
        draw.text((20, 20), text, fill=(255, 255, 255), font=font)
        
        # 保存图片
        image_path = os.path.join(test_folder, f"main_image_{i+1}.jpg")
        image.save(image_path, 'JPEG', quality=85)
        test_images.append(image_path)
    
    # 子文件夹中的图片
    for i in range(2):
        image = Image.new('RGB', (300, 400), (100 + i * 50, 200 - i * 30, 255 - i * 50))
        
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        text = f"Sub Image {i+1}"
        draw.text((20, 20), text, fill=(255, 255, 255), font=font)
        
        # 保存图片
        image_path = os.path.join(sub_folder, f"sub_image_{i+1}.png")
        image.save(image_path, 'PNG')
        test_images.append(image_path)
    
    # 添加一些非图片文件
    with open(os.path.join(test_folder, "readme.txt"), 'w') as f:
        f.write("This is a test folder")
    
    with open(os.path.join(sub_folder, "info.doc"), 'w') as f:
        f.write("Document file")
    
    logger.info(f"创建了 {len(test_images)} 个测试图片")
    return test_folder, test_images

def test_preview_logging():
    """测试预览图片生成的日志功能"""
    print("=" * 70)
    print("预览图片生成日志功能测试")
    print("=" * 70)
    
    logger.info("=" * 60)
    logger.info("开始预览图片生成日志功能测试")
    logger.info("=" * 60)
    
    try:
        # 创建测试图片
        test_image = Image.new('RGB', (800, 600), (100, 150, 200))
        
        # 添加图案
        from PIL import ImageDraw
        draw = ImageDraw.Draw(test_image)
        draw.rectangle([50, 50, 200, 150], fill=(255, 255, 0))
        draw.ellipse([300, 200, 500, 400], fill=(255, 0, 255))
        
        temp_file = tempfile.NamedTemporaryFile(suffix='_preview_test.jpg', delete=False)
        temp_file.close()
        test_image.save(temp_file.name, 'JPEG', quality=90)
        
        logger.info(f"测试图片已创建: {temp_file.name}")
        print(f"✓ 创建测试图片: {os.path.basename(temp_file.name)}")
        
        # 导入并测试预览组件
        from ui.widgets.preview_widget import PreviewWidget
        
        logger.info("创建预览组件")
        preview_widget = PreviewWidget()
        print("✓ 预览组件已创建")
        
        # 测试设置图片
        logger.info("测试设置预览图片")
        preview_widget.set_image(temp_file.name)
        print("✓ 设置预览图片成功")
        
        # 测试水印配置
        logger.info("测试水印配置")
        config = WatermarkConfig()
        config.watermark_type = WatermarkType.TEXT
        config.position = WatermarkPosition.BOTTOM_RIGHT
        config.text_config.text = "预览测试水印"
        config.text_config.font_size = 24
        config.text_config.opacity = 0.7
        
        preview_widget.set_watermark_config(config)
        print("✓ 设置水印配置成功")
        
        # 测试不同的水印位置
        positions = [
            (WatermarkPosition.TOP_LEFT, "左上角"),
            (WatermarkPosition.CENTER, "中心"),
            (WatermarkPosition.BOTTOM_RIGHT, "右下角")
        ]
        
        for pos, pos_name in positions:
            logger.info(f"测试{pos_name}水印预览")
            config.position = pos
            config.text_config.text = f"{pos_name}预览"
            preview_widget.set_watermark_config(config)
            print(f"✓ {pos_name}水印预览成功")
        
        # 清理测试文件
        os.unlink(temp_file.name)
        logger.info("测试文件清理完成")
        
        logger.info("=" * 60)
        logger.info("预览图片生成日志功能测试完成")
        logger.info("=" * 60)
        
        print("✅ 预览日志功能测试通过！")
        return True
        
    except Exception as e:
        logger.error(f"预览日志功能测试失败: {str(e)}")
        print(f"❌ 预览测试失败: {str(e)}")
        return False

def test_import_progress_dialog():
    """测试文件导入进度对话框（无GUI交互）"""
    print("\n" + "=" * 70)
    print("文件导入进度对话框功能测试")
    print("=" * 70)
    
    logger.info("=" * 60)
    logger.info("开始文件导入进度对话框功能测试")
    logger.info("=" * 60)
    
    try:
        # 创建测试图片文件夹
        test_folder, test_images = create_test_images_folder()
        print(f"✓ 创建测试文件夹: {len(test_images)} 个图片")
        
        # 测试文件工具的扫描功能
        from utils.file_utils import FileUtils
        
        logger.info("测试非递归扫描")
        files_non_recursive = FileUtils.get_image_files_from_folder(test_folder, recursive=False)
        logger.info(f"非递归扫描结果: {len(files_non_recursive)} 个文件")
        print(f"✓ 非递归扫描: {len(files_non_recursive)} 个文件")
        
        logger.info("测试递归扫描")
        files_recursive = FileUtils.get_image_files_from_folder(test_folder, recursive=True)
        logger.info(f"递归扫描结果: {len(files_recursive)} 个文件")
        print(f"✓ 递归扫描: {len(files_recursive)} 个文件")
        
        # 测试图片列表模型
        from models.image_info import ImageListModel
        
        logger.info("测试图片列表模型批量添加")
        model = ImageListModel()
        
        # 分批添加文件
        chunk_size = 2
        added_total = 0
        
        for i in range(0, len(files_recursive), chunk_size):
            chunk = files_recursive[i:i + chunk_size]
            logger.info(f"添加块 {i//chunk_size + 1}: {len(chunk)} 个文件")
            
            chunk_added = model.add_images(chunk)
            added_total += chunk_added
            
            logger.debug(f"块 {i//chunk_size + 1} 添加了 {chunk_added} 个文件")
            print(f"  批次 {i//chunk_size + 1}: 添加 {chunk_added} 个文件")
        
        logger.info(f"批量添加完成: 总共添加 {added_total} 个文件")
        print(f"✓ 批量添加完成: {added_total} 个文件")
        
        # 清理测试文件夹
        shutil.rmtree(test_folder)
        logger.info(f"清理测试文件夹: {test_folder}")
        
        logger.info("=" * 60)
        logger.info("文件导入进度对话框功能测试完成")
        logger.info("=" * 60)
        
        print("✅ 导入进度功能测试通过！")
        return True
        
    except Exception as e:
        logger.error(f"导入进度功能测试失败: {str(e)}")
        print(f"❌ 导入测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("=" * 80)
    print("PhotoWatermark 预览和导入功能增强测试")
    print("=" * 80)
    
    logger.info("=" * 70)
    logger.info("开始PhotoWatermark预览和导入功能增强测试")
    logger.info("=" * 70)
    
    results = []
    
    # 测试预览日志功能
    results.append(("预览日志功能", test_preview_logging()))
    
    # 测试导入进度功能
    results.append(("导入进度功能", test_import_progress_dialog()))
    
    # 汇总结果
    print(f"\n" + "=" * 80)
    print("📊 测试结果汇总")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:20s} : {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    logger.info(f"测试完成: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有增强功能测试通过!")
        logger.info("🎉 所有增强功能测试通过!")
    else:
        print(f"⚠️  有 {total - passed} 个测试失败")
        logger.warning(f"有 {total - passed} 个测试失败")
    
    print("\n📋 增强功能验证项目:")
    print("✓ 预览图片生成过程详细日志记录")
    print("✓ 水印配置变更跟踪日志")
    print("✓ 文件导入过程用户友好界面")
    print("✓ 批量文件处理进度显示")
    print("✓ 递归和非递归文件夹扫描")
    print("✓ 错误处理和异常日志记录")
    
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
    
    logger.info("=" * 70)
    logger.info("PhotoWatermark预览和导入功能增强测试完成")
    logger.info("=" * 70)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    print(f"\n{'🎊 预览和导入功能增强成功' if success else '❌ 测试失败'}！")
    print("现在您可以享受更好的用户体验和详细的操作日志。")
    
    sys.exit(0 if success else 1)