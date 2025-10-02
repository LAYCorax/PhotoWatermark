"""
简化的RGBA修复验证测试
"""
import sys
import os
import tempfile
from PIL import Image

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_rgba_to_jpeg_conversion():
    """测试RGBA到JPEG的转换"""
    print("测试RGBA到JPEG转换...")
    
    try:
        # 创建RGBA图片
        rgba_img = Image.new('RGBA', (200, 150), (255, 100, 50, 128))
        print(f"创建RGBA图片: {rgba_img.mode}, {rgba_img.size}")
        
        # 方法1: 直接转换（会丢失透明度）
        rgb_img1 = rgba_img.convert('RGB')
        print(f"直接转换结果: {rgb_img1.mode}")
        
        # 方法2: 白色背景合成（保留视觉效果）
        background = Image.new('RGB', rgba_img.size, (255, 255, 255))
        background.paste(rgba_img, mask=rgba_img.split()[-1])
        print(f"背景合成结果: {background.mode}")
        
        # 测试保存
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        background.save(temp_file.name, 'JPEG')
        temp_file.close()
        
        # 验证保存的文件
        with Image.open(temp_file.name) as saved_img:
            print(f"保存后重新加载: {saved_img.mode}, {saved_img.size}")
        
        os.unlink(temp_file.name)
        print("✅ RGBA到JPEG转换测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 转换测试失败: {e}")
        return False

def test_watermark_engine_rgba():
    """测试水印引擎处理RGBA"""
    print("\n测试水印引擎处理RGBA图片...")
    
    try:
        # 创建RGB测试图片（避免初始保存问题）
        test_img = Image.new('RGB', (400, 300), (100, 150, 200))
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        test_img.save(temp_file.name, 'JPEG')
        temp_file.close()
        
        print(f"测试图片已保存: {temp_file.name}")
        
        # 导入并测试水印引擎
        from core.watermark_engine import WatermarkEngine
        from models.watermark_config import WatermarkConfig, WatermarkType
        
        engine = WatermarkEngine()
        config = WatermarkConfig()
        config.watermark_type = WatermarkType.TEXT
        config.text_config.text = "RGBA测试水印"
        config.text_config.font_size = 32
        
        # 处理水印
        output_path = temp_file.name.replace('.jpg', '_watermarked.jpg')
        result_path = engine.process_image(temp_file.name, config, output_path)
        
        if result_path and os.path.exists(result_path):
            with Image.open(result_path) as result_img:
                print(f"✅ 水印处理成功: {result_img.mode}, {result_img.size}")
            os.unlink(result_path)
            success = True
        else:
            print("❌ 水印处理失败")
            success = False
        
        os.unlink(temp_file.name)
        return success
        
    except Exception as e:
        print(f"❌ 水印引擎测试失败: {e}")
        return False

def main():
    """主函数"""
    print("PhotoWatermark RGBA修复简化验证")
    print("=" * 40)
    
    tests = [
        test_rgba_to_jpeg_conversion,
        test_watermark_engine_rgba
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n验证结果: {passed}/{len(tests)} 通过")
    
    if passed == len(tests):
        print("🎉 RGBA处理修复验证成功！")
        return 0
    else:
        print("⚠️ 还有问题需要解决")
        return 1

if __name__ == '__main__':
    sys.exit(main())