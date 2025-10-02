"""
大规模文件处理测试脚本
用于测试应用程序在处理大量文件时的稳定性
"""
import sys
import os
import tempfile
import shutil
from PIL import Image
import random

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_images(count: int = 100, output_dir: str = None) -> str:
    """创建测试图片文件"""
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="photowater_test_")
    
    print(f"创建 {count} 个测试图片到: {output_dir}")
    
    for i in range(count):
        # 创建不同尺寸的测试图片
        sizes = [(800, 600), (1920, 1080), (3000, 2000), (4000, 3000)]
        size = random.choice(sizes)
        
        # 创建随机颜色的图片
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        img = Image.new('RGB', size, color)
        
        # 添加一些简单的内容
        filename = f"test_image_{i:04d}.jpg"
        filepath = os.path.join(output_dir, filename)
        
        # 随机质量保存
        quality = random.randint(70, 95)
        img.save(filepath, 'JPEG', quality=quality)
        
        if (i + 1) % 10 == 0:
            print(f"已创建 {i + 1}/{count} 个图片")
    
    print(f"✓ 测试图片创建完成: {output_dir}")
    return output_dir

def test_large_folder_import(image_count: int = 100):
    """测试大文件夹导入"""
    print(f"\n测试大文件夹导入 ({image_count} 张图片)")
    print("=" * 50)
    
    # 创建测试图片
    test_dir = create_test_images(image_count)
    
    try:
        from PyQt5.QtWidgets import QApplication
        from utils.file_utils import FileUtils
        from models.image_info import ImageListModel
        
        # 创建应用程序实例
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        print("\n测试文件扫描...")
        image_files = FileUtils.get_image_files_from_folder(test_dir, recursive=False)
        print(f"✓ 扫描到 {len(image_files)} 个图片文件")
        
        print("\n测试批量导入...")
        model = ImageListModel()
        added_count = model.add_images(image_files)
        print(f"✓ 成功导入 {added_count} 张图片")
        
        print(f"✓ 模型中共有 {model.count()} 张图片")
        
        # 测试内存使用
        try:
            from utils.memory_manager import memory_manager
            memory_mb = memory_manager.get_memory_usage_mb()
            print(f"✓ 当前内存使用: {memory_mb:.1f} MB")
            
            if memory_manager.is_memory_warning():
                print("⚠ 内存使用警告")
                memory_manager.cleanup_memory()
                print("✓ 执行内存清理")
        except Exception as e:
            print(f"内存监控测试跳过: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ 大文件夹导入测试失败: {e}")
        return False
    finally:
        # 清理测试文件
        try:
            shutil.rmtree(test_dir)
            print(f"✓ 清理测试文件: {test_dir}")
        except Exception as e:
            print(f"清理测试文件失败: {e}")

def test_large_image_processing():
    """测试大图片处理"""
    print("\n测试大图片处理")
    print("=" * 50)
    
    # 创建一个大图片
    large_size = (6000, 4000)  # 24MP图片
    test_img = Image.new('RGB', large_size, (100, 150, 200))
    
    temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
    test_img.save(temp_file.name, 'JPEG', quality=90)
    temp_file.close()
    
    try:
        from PyQt5.QtWidgets import QApplication
        from ui.widgets.preview_widget import PreviewGraphicsView
        from models.watermark_config import WatermarkConfig
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        print(f"✓ 创建大图片: {large_size[0]}x{large_size[1]} 像素")
        
        # 测试预览组件
        preview = PreviewGraphicsView()
        
        print("测试大图片预览生成...")
        config = WatermarkConfig()
        watermarked_pixmap = preview.generate_watermarked_preview(temp_file.name, config)
        
        if watermarked_pixmap and not watermarked_pixmap.isNull():
            print(f"✓ 大图片预览生成成功: {watermarked_pixmap.width()}x{watermarked_pixmap.height()}")
        else:
            print("✗ 大图片预览生成失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 大图片处理测试失败: {e}")
        return False
    finally:
        # 清理临时文件
        try:
            os.unlink(temp_file.name)
            print("✓ 清理临时大图片")
        except Exception as e:
            print(f"清理临时文件失败: {e}")

def main():
    """主测试函数"""
    print("PhotoWatermark 大规模文件处理测试")
    print("=" * 60)
    
    tests = [
        lambda: test_large_folder_import(50),    # 50张图片
        lambda: test_large_folder_import(200),   # 200张图片
        test_large_image_processing,
    ]
    
    passed = 0
    total = len(tests)
    
    for i, test in enumerate(tests, 1):
        print(f"\n[测试 {i}/{total}]")
        try:
            if test():
                passed += 1
                print("✅ 测试通过")
            else:
                print("❌ 测试失败")
        except Exception as e:
            print(f"❌ 测试异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"大规模处理测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有大规模处理测试通过！应用程序可以稳定处理大量文件。")
        return 0
    else:
        print("⚠️ 部分测试失败，需要进一步优化大规模文件处理。")
        return 1

if __name__ == '__main__':
    sys.exit(main())