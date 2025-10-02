"""
大图片水印处理测试
专门测试7000x4000等超大尺寸图片的水印处理
"""
import sys
import os
import tempfile
from PIL import Image

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_realistic_large_image(size=(7000, 4000), target_file_size_mb=6.6):
    """创建接近真实情况的大尺寸测试图片"""
    print(f"创建 {size[0]}x{size[1]} 像素的高质量测试图片 (目标: ~{target_file_size_mb}MB)...")
    
    import random
    import math
    
    # 创建基础图片
    img = Image.new('RGB', size)
    pixels = img.load()
    width, height = size
    
    print("生成复杂图像内容...")
    
    # 创建更复杂的图像内容以增加文件大小和内存占用
    for y in range(height):
        if y % 200 == 0:
            print(f"处理进度: {y/height*100:.1f}%")
        
        for x in range(width):
            # 创建复杂的颜色模式
            # 添加噪声和纹理以模拟真实照片
            noise_r = random.randint(-30, 30)
            noise_g = random.randint(-30, 30)
            noise_b = random.randint(-30, 30)
            
            # 基于位置的颜色变化
            base_r = int(128 + 100 * math.sin(x / 500.0) * math.cos(y / 300.0))
            base_g = int(128 + 80 * math.sin(x / 700.0 + 1) * math.cos(y / 400.0))
            base_b = int(128 + 60 * math.sin(x / 600.0 + 2) * math.cos(y / 350.0))
            
            # 添加一些细节纹理
            detail = int(20 * math.sin(x / 50.0) * math.sin(y / 50.0))
            
            r = max(0, min(255, base_r + noise_r + detail))
            g = max(0, min(255, base_g + noise_g + detail))
            b = max(0, min(255, base_b + noise_b + detail))
            
            pixels[x, y] = (r, g, b)
    
    print("图像生成完成")
    return img

def test_large_image_watermark():
    """测试大图片水印处理"""
    print("大图片水印处理测试")
    print("=" * 50)
    
    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
    
    try:
        # 创建7000x4000的大图片（模拟6.6MB真实照片）
        large_img = create_realistic_large_image((7000, 4000), 6.6)
        
        # 使用较高质量保存以达到目标文件大小
        large_img.save(temp_file.name, 'JPEG', quality=95, optimize=False)
        temp_file.close()
        
        print(f"✓ 大图片已保存: {temp_file.name}")
        print(f"文件大小: {os.path.getsize(temp_file.name) / (1024*1024):.1f} MB")
        
        # 测试直接处理原始尺寸（跳过预览缩放）
        print("\n测试原始尺寸水印处理（跳过预览限制）...")
        
        # 直接处理大图片
        with Image.open(temp_file.name) as original_img:
            print(f"原始图片尺寸: {original_img.size}")
            
            # 使用新的水印引擎（不需要QApplication）
            from core.watermark_engine import WatermarkEngine
            from models.watermark_config import WatermarkConfig, WatermarkType
            
            engine = WatermarkEngine()
            config = WatermarkConfig()
            config.watermark_type = WatermarkType.TEXT
            config.text_config.text = "LARGE IMAGE TEST"
            config.text_config.font_size = 150  # 大字体
            
            try:
                # 直接处理原始尺寸
                print("使用WatermarkEngine处理原始尺寸...")
                output_temp = tempfile.NamedTemporaryFile(suffix='_watermarked.jpg', delete=False)
                output_temp.close()
                
                result_path = engine.process_image(temp_file.name, config, output_temp.name)
                
                if result_path:
                    print(f"✓ 原始尺寸水印处理成功")
                    print(f"输出文件大小: {os.path.getsize(result_path) / (1024*1024):.1f} MB")
                    
                    # 验证输出
                    with Image.open(result_path) as result_img:
                        print(f"输出图片尺寸: {result_img.size}")
                    
                    # 清理输出文件
                    os.unlink(result_path)
                else:
                    print("✗ 原始尺寸水印处理失败")
                    return False
                    
            except MemoryError as e:
                print(f"✗ 内存错误: {e}")
                return False
            except Exception as e:
                print(f"✗ 处理异常: {e}")
                return False
        
        # 测试新的水印引擎
        from PyQt5.QtWidgets import QApplication
        from core.watermark_engine import WatermarkEngine
        from models.watermark_config import WatermarkConfig, WatermarkType
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        engine = WatermarkEngine()
        config = WatermarkConfig()
        config.watermark_type = WatermarkType.TEXT
        config.text_config.text = "TEST WATERMARK"
        config.text_config.font_size = 200  # 大字体以适应大图片
        
        print("\n开始水印处理...")
        print("警告：这可能会消耗大量内存！")
        
        # 监控内存使用（简化版本）
        import gc
        initial_objects = len(gc.get_objects())
        print(f"初始对象数量: {initial_objects}")
        initial_memory = None  # 简化版本不监控具体内存
        
        # 执行水印处理 - 测试新引擎
        try:
            # 创建输出文件路径
            output_path = temp_file.name.replace('.jpg', '_watermarked.jpg')
            
            print("使用新的WatermarkEngine处理大图片...")
            result_path = engine.process_image(temp_file.name, config, output_path)
            
            if result_path and os.path.exists(result_path):
                print(f"✓ 水印处理成功！输出文件: {result_path}")
                
                # 检查输出文件
                output_size = os.path.getsize(result_path) / (1024 * 1024)
                print(f"输出文件大小: {output_size:.1f} MB")
                
                # 验证输出图片
                with Image.open(result_path) as result_img:
                    print(f"输出图片尺寸: {result_img.size}")
                
                # 清理输出文件
                os.unlink(result_path)
                
                # 检查对象数量变化
                final_objects = len(gc.get_objects())
                print(f"最终对象数量: {final_objects}")
                print(f"对象增长: {final_objects - initial_objects}")
                
                return True
            else:
                print("✗ 水印处理失败")
                return False
                
        except MemoryError as e:
            print(f"✗ 内存错误: {e}")
            return False
        except Exception as e:
            print(f"✗ 处理异常: {e}")
            return False
    
    finally:
        # 清理临时文件
        try:
            os.unlink(temp_file.name)
            print("✓ 清理临时文件")
        except Exception as e:
            print(f"清理文件失败: {e}")

def main():
    """主函数"""
    print("PhotoWatermark 大图片水印测试")
    print("测试尺寸: 7000x4000 像素 (~28MP)")
    print("=" * 60)
    
    try:
        success = test_large_image_watermark()
        if success:
            print("\n🎉 大图片水印测试通过！")
            return 0
        else:
            print("\n❌ 大图片水印测试失败！")
            return 1
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n💥 测试过程中发生异常: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())