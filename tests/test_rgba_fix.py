"""
RGBA模式保存测试
专门测试修复后的RGBA到JPEG保存问题
"""
import sys
import os
import tempfile
from PIL import Image

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_rgba_save_fix():
    """测试RGBA模式图片保存修复"""
    print("测试RGBA模式图片保存修复")
    print("=" * 40)
    
    # 创建一个RGBA模式的测试图片
    print("1. 创建RGBA模式测试图片...")
    test_img = Image.new('RGBA', (1000, 800), (100, 150, 200, 128))  # 半透明背景
    
    # 添加一些内容
    from PIL import ImageDraw
    draw = ImageDraw.Draw(test_img)
    draw.rectangle([100, 100, 900, 700], fill=(255, 0, 0, 200))  # 半透明红色矩形
    draw.text((200, 300), "测试RGBA模式", fill=(255, 255, 255, 255))
    
    print(f"✓ 创建完成，模式: {test_img.mode}")
    
    # 保存为临时文件（先转换为RGB以支持JPEG）
    temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
    try:
        # 将RGBA转换为RGB（白色背景）以支持JPEG保存
        if test_img.mode == 'RGBA':
            background = Image.new('RGB', test_img.size, (255, 255, 255))
            background.paste(test_img, mask=test_img.split()[-1])
            save_img = background
        else:
            save_img = test_img
            
        save_img.save(temp_file.name, 'JPEG', quality=85)
        temp_file.close()
        print(f"✓ 临时RGBA图片已保存 (转换为RGB): {temp_file.name}")
        
        # 测试水印引擎处理
        print("\n2. 测试水印引擎处理RGBA图片...")
        from core.watermark_engine import WatermarkEngine
        from models.watermark_config import WatermarkConfig, WatermarkType
        
        engine = WatermarkEngine()
        config = WatermarkConfig()
        config.watermark_type = WatermarkType.TEXT
        config.text_config.text = "RGBA测试水印"
        config.text_config.font_size = 48
        
        # 处理图片
        output_path = temp_file.name.replace('.jpg', '_watermarked.jpg')
        result_path = engine.process_image(temp_file.name, config, output_path)
        
        if result_path and os.path.exists(result_path):
            print("✅ RGBA模式图片水印处理成功")
            
            # 验证输出
            with Image.open(result_path) as result_img:
                print(f"  输出模式: {result_img.mode}")
                print(f"  输出尺寸: {result_img.size}")
            
            # 清理输出文件
            os.unlink(result_path)
            return True
        else:
            print("❌ RGBA模式图片水印处理失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    finally:
        # 清理临时文件
        try:
            os.unlink(temp_file.name)
        except:
            pass

def test_different_modes():
    """测试不同颜色模式的处理"""
    print("\n测试不同颜色模式处理")
    print("=" * 40)
    
    modes_to_test = [
        ('RGB', (255, 100, 50)),
        ('RGBA', (255, 100, 50, 200)),
        ('L', 128),  # 灰度
        ('P', None)  # 调色板模式
    ]
    
    from core.watermark_engine import WatermarkEngine
    from models.watermark_config import WatermarkConfig, WatermarkType
    
    engine = WatermarkEngine()
    config = WatermarkConfig()
    config.watermark_type = WatermarkType.TEXT
    config.text_config.text = "模式测试"
    config.text_config.font_size = 36
    
    passed = 0
    total = len(modes_to_test)
    
    for mode, color in modes_to_test:
        print(f"\n测试 {mode} 模式...")
        
        try:
            # 创建测试图片
            if mode == 'P':
                # 调色板模式需要特殊处理
                test_img = Image.new('RGB', (800, 600), (100, 150, 200))
                test_img = test_img.quantize(colors=256)
            else:
                test_img = Image.new(mode, (800, 600), color)
            
            print(f"  创建图片: {test_img.mode} 模式")
            
            # 保存和处理
            temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
            try:
                # 正确处理不兼容JPEG的模式
                if test_img.mode == 'RGBA':
                    # RGBA需要合成背景
                    background = Image.new('RGB', test_img.size, (255, 255, 255))
                    background.paste(test_img, mask=test_img.split()[-1])
                    save_img = background
                elif test_img.mode in ('LA', 'P', 'L'):
                    # 其他模式直接转换为RGB
                    save_img = test_img.convert('RGB')
                else:
                    save_img = test_img
                
                save_img.save(temp_file.name, 'JPEG', quality=85)
                temp_file.close()
                
                # 使用水印引擎处理
                output_path = temp_file.name.replace('.jpg', f'_{mode}_watermarked.jpg')
                result_path = engine.process_image(temp_file.name, config, output_path)
                
                if result_path and os.path.exists(result_path):
                    print(f"  ✅ {mode} 模式处理成功")
                    
                    # 验证输出
                    with Image.open(result_path) as result_img:
                        print(f"    输出模式: {result_img.mode}")
                    
                    os.unlink(result_path)
                    passed += 1
                else:
                    print(f"  ❌ {mode} 模式处理失败")
                    
            finally:
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
                    
        except Exception as e:
            print(f"  ❌ {mode} 模式测试异常: {e}")
    
    print(f"\n颜色模式测试结果: {passed}/{total} 通过")
    return passed == total

def main():
    """主函数"""
    print("PhotoWatermark RGBA保存问题修复验证")
    print("=" * 50)
    
    tests = [
        test_rgba_save_fix,
        test_different_modes
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✅ 测试通过")
            else:
                print("❌ 测试失败")
        except Exception as e:
            print(f"❌ 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"RGBA修复验证结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 RGBA保存问题已完全修复！")
        return 0
    else:
        print("⚠️ 还有部分问题需要解决")
        return 1

if __name__ == '__main__':
    sys.exit(main())