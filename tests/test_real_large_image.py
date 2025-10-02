"""
真实大图片水印应用测试
模拟用户在主应用程序中处理大图片的场景
"""
import sys
import os
import tempfile
from PIL import Image
import random

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_realistic_photo(size=(7000, 4000), target_mb=6.6):
    """创建更接近真实照片的测试图片"""
    print(f"创建真实感照片 {size[0]}x{size[1]} 像素 (目标: {target_mb}MB)...")
    
    # 创建基础风景照片效果
    img = Image.new('RGB', size)
    width, height = size
    
    # 创建天空渐变（上半部分）
    for y in range(height // 3):
        sky_blue = int(135 + (y / (height // 3)) * 50)  # 天空蓝色渐变
        for x in range(width):
            img.putpixel((x, y), (sky_blue, sky_blue + 20, 200))
    
    # 创建地面（下半部分）
    for y in range(height // 3, height):
        ground_green = int(50 + random.randint(-20, 20))
        for x in range(width):
            noise = random.randint(-15, 15)
            r = max(0, min(255, 80 + noise))
            g = max(0, min(255, ground_green + noise))
            b = max(0, min(255, 40 + noise))
            img.putpixel((x, y), (r, g, b))
    
    print("基础图像创建完成")
    return img

def test_main_app_with_large_image():
    """测试主应用程序处理大图片"""
    print("测试主应用程序处理大图片")
    print("=" * 50)
    
    # 创建测试图片
    temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
    
    try:
        # 创建接近真实的大图片
        print("创建测试图片...")
        large_img = create_realistic_photo((7000, 4000), 6.6)
        
        # 保存为中等质量JPEG以控制文件大小
        large_img.save(temp_file.name, 'JPEG', quality=75)
        temp_file.close()
        
        file_size = os.path.getsize(temp_file.name) / (1024 * 1024)
        print(f"✓ 测试图片已保存: {temp_file.name}")
        print(f"文件大小: {file_size:.1f} MB")
        
        # 测试主应用程序的水印处理流程
        from PyQt5.QtWidgets import QApplication
        from models.watermark_config import WatermarkConfig, WatermarkType
        from models.image_info import ImageListModel
        from core.watermark_engine import WatermarkEngine
        
        # 创建应用程序实例
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        print("\n测试完整应用流程...")
        
        # 1. 测试图片导入
        print("1. 测试图片模型导入...")
        image_model = ImageListModel()
        success = image_model.add_image(temp_file.name)
        
        if not success:
            print("✗ 图片导入失败")
            return False
        
        image_info = image_model.get_image(0)
        print(f"✓ 图片导入成功: {image_info.get_dimensions_string()}")
        
        # 2. 测试水印配置
        print("2. 配置水印参数...")
        config = WatermarkConfig()
        config.watermark_type = WatermarkType.TEXT
        config.text_config.text = "大图片测试水印"
        config.text_config.font_size = 120  # 适合大图片的字体
        config.text_config.color = (255, 255, 255)
        config.text_config.opacity = 0.8
        
        # 3. 测试预览生成（应该会自动缩放）
        print("3. 测试预览生成...")
        from ui.widgets.preview_widget import PreviewGraphicsView
        
        preview_widget = PreviewGraphicsView()
        preview_pixmap = preview_widget.generate_watermarked_preview(temp_file.name, config)
        
        if preview_pixmap and not preview_pixmap.isNull():
            print(f"✓ 预览生成成功: {preview_pixmap.width()}x{preview_pixmap.height()}")
        else:
            print("✗ 预览生成失败")
            return False
        
        # 4. 测试实际导出（完整尺寸）
        print("4. 测试完整尺寸导出...")
        engine = WatermarkEngine()
        output_path = temp_file.name.replace('.jpg', '_watermarked_full.jpg')
        
        result_path = engine.process_image(temp_file.name, config, output_path)
        
        if result_path and os.path.exists(result_path):
            output_size = os.path.getsize(result_path) / (1024 * 1024)
            print(f"✓ 完整尺寸导出成功: {output_size:.1f} MB")
            
            # 验证输出
            with Image.open(result_path) as result_img:
                print(f"输出尺寸: {result_img.size}")
            
            # 清理输出文件
            os.unlink(result_path)
        else:
            print("✗ 完整尺寸导出失败")
            return False
        
        print("✅ 所有测试通过！")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理临时文件
        try:
            os.unlink(temp_file.name)
            print("✓ 清理临时文件")
        except Exception as e:
            print(f"清理临时文件失败: {e}")

def main():
    """主函数"""
    print("PhotoWatermark 真实大图片应用测试")
    print("模拟6.6MB的7000×4000像素照片处理")
    print("=" * 60)
    
    try:
        success = test_main_app_with_large_image()
        if success:
            print("\n🎉 真实大图片应用测试通过！")
            print("应用程序可以稳定处理大尺寸图片。")
            return 0
        else:
            print("\n❌ 真实大图片应用测试失败！")
            return 1
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n💥 测试过程中发生异常: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())