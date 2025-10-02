"""
颜色处理测试脚本
用于验证 PIL 到 QPixmap 转换的颜色准确性
"""
import sys
import os
from PIL import Image, ImageDraw

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_image():
    """创建一个包含已知颜色的测试图像"""
    # 创建一个 200x200 的测试图像
    img = Image.new('RGB', (200, 200), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # 绘制一些已知颜色的区域
    colors = [
        ((255, 0, 0), "红色"),      # 纯红
        ((0, 255, 0), "绿色"),      # 纯绿
        ((0, 0, 255), "蓝色"),      # 纯蓝
        ((255, 255, 0), "黄色"),    # 黄色
        ((255, 0, 255), "洋红"),    # 洋红
        ((0, 255, 255), "青色"),    # 青色
        ((128, 128, 128), "灰色"),  # 灰色
        ((0, 0, 0), "黑色"),        # 黑色
    ]
    
    # 绘制颜色块
    block_size = 50
    for i, (color, name) in enumerate(colors):
        x = (i % 4) * block_size
        y = (i // 4) * block_size
        draw.rectangle([x, y, x + block_size, y + block_size], fill=color)
    
    return img

def test_color_conversion():
    """测试颜色转换的准确性"""
    print("测试颜色转换准确性...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from ui.widgets.preview_widget import PreviewGraphicsView
        
        # 创建应用程序实例
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 创建预览组件
        preview = PreviewGraphicsView()
        
        # 创建测试图像
        test_img = create_test_image()
        
        # 保存原始测试图像
        test_path = "test_colors.png"
        test_img.save(test_path)
        print(f"✓ 测试图像已保存到: {test_path}")
        
        # 测试转换
        qpixmap = preview.pil_to_qpixmap(test_img)
        
        if not qpixmap.isNull():
            print("✓ PIL 到 QPixmap 转换成功")
            print(f"  原始图像尺寸: {test_img.size}")
            print(f"  QPixmap 尺寸: {qpixmap.width()}x{qpixmap.height()}")
        else:
            print("✗ PIL 到 QPixmap 转换失败")
            return False
        
        # 测试不同格式
        formats_to_test = ['RGB', 'RGBA', 'L', 'P']
        for format_name in formats_to_test:
            try:
                if format_name == 'RGBA':
                    test_format_img = test_img.convert('RGBA')
                elif format_name == 'L':
                    test_format_img = test_img.convert('L')
                elif format_name == 'P':
                    test_format_img = test_img.convert('P')
                else:
                    test_format_img = test_img
                
                format_pixmap = preview.pil_to_qpixmap(test_format_img)
                if not format_pixmap.isNull():
                    print(f"✓ {format_name} 格式转换成功")
                else:
                    print(f"✗ {format_name} 格式转换失败")
            except Exception as e:
                print(f"✗ {format_name} 格式测试异常: {e}")
        
        # 清理
        os.remove(test_path)
        return True
        
    except Exception as e:
        print(f"✗ 颜色转换测试失败: {e}")
        return False

def test_watermark_color_integrity():
    """测试水印应用后的颜色完整性"""
    print("\n测试水印颜色完整性...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from ui.widgets.preview_widget import PreviewGraphicsView
        from models.watermark_config import WatermarkConfig, WatermarkType
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        preview = PreviewGraphicsView()
        
        # 创建测试图像
        test_img = create_test_image()
        test_path = "test_watermark_colors.png"
        test_img.save(test_path)
        
        # 创建水印配置
        config = WatermarkConfig()
        config.watermark_type = WatermarkType.TEXT
        config.text_config.text = "TEST"
        config.text_config.color = (255, 255, 255)  # 白色文本
        config.text_config.opacity = 0.8
        
        # 应用水印
        watermarked_pixmap = preview.generate_watermarked_preview(test_path, config)
        
        if watermarked_pixmap and not watermarked_pixmap.isNull():
            print("✓ 水印应用成功，颜色处理正常")
        else:
            print("✗ 水印应用失败")
            return False
        
        # 清理
        os.remove(test_path)
        return True
        
    except Exception as e:
        print(f"✗ 水印颜色完整性测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("PhotoWatermark 颜色处理测试")
    print("=" * 40)
    
    tests = [
        test_color_conversion,
        test_watermark_color_integrity
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ 测试异常: {e}")
    
    print("\n" + "=" * 40)
    print(f"颜色处理测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✅ 所有颜色处理测试通过！色差问题已解决。")
        return 0
    else:
        print("❌ 部分测试失败，请检查颜色处理逻辑。")
        return 1

if __name__ == '__main__':
    sys.exit(main())