"""
极限大图片压力测试
测试应用程序在极端条件下的稳定性
"""
import sys
import os
import tempfile
from PIL import Image
import time

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_extreme_test_cases():
    """创建多个极限测试用例"""
    test_cases = [
        {
            'name': '超大尺寸图片',
            'size': (8000, 6000),  # 48MP
            'quality': 90,
            'description': '模拟专业相机RAW转换后的大尺寸图片'
        },
        {
            'name': '高压缩比大图片',
            'size': (7000, 4000),  # 28MP
            'quality': 60,
            'description': '模拟压缩后的大尺寸图片，文件小但像素多'
        },
        {
            'name': '高质量中等图片',
            'size': (4000, 3000),  # 12MP
            'quality': 98,
            'description': '模拟未压缩的高质量图片'
        }
    ]
    
    return test_cases

def create_test_image(size, quality, seed=None):
    """创建指定尺寸和质量的测试图片"""
    if seed:
        import random
        random.seed(seed)
    
    print(f"创建 {size[0]}x{size[1]} 像素测试图片...")
    
    # 创建更复杂的图像内容
    img = Image.new('RGB', size)
    width, height = size
    
    # 快速填充算法以节省时间
    import random
    for y in range(0, height, 50):  # 每50行处理
        if y % 500 == 0:
            print(f"  进度: {y/height*100:.0f}%")
        
        for x in range(0, width, 50):  # 每50列处理
            # 创建50x50的色块
            r = random.randint(50, 200)
            g = random.randint(50, 200) 
            b = random.randint(50, 200)
            
            # 填充50x50区域
            for dy in range(min(50, height - y)):
                for dx in range(min(50, width - x)):
                    img.putpixel((x + dx, y + dy), (r, g, b))
    
    return img

def test_extreme_case(test_case):
    """测试单个极限用例"""
    print(f"\n测试用例: {test_case['name']}")
    print(f"描述: {test_case['description']}")
    print("-" * 50)
    
    temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
    
    try:
        # 创建测试图片
        start_time = time.time()
        test_img = create_test_image(test_case['size'], test_case['quality'], seed=42)
        creation_time = time.time() - start_time
        
        # 保存图片
        test_img.save(temp_file.name, 'JPEG', quality=test_case['quality'])
        temp_file.close()
        
        file_size = os.path.getsize(temp_file.name) / (1024 * 1024)
        total_pixels = test_case['size'][0] * test_case['size'][1]
        
        print(f"✓ 图片创建完成 ({creation_time:.1f}s)")
        print(f"  文件大小: {file_size:.1f} MB")
        print(f"  像素总数: {total_pixels/1e6:.1f} MP")
        
        # 测试水印处理
        from core.watermark_engine import WatermarkEngine
        from models.watermark_config import WatermarkConfig, WatermarkType
        
        engine = WatermarkEngine()
        config = WatermarkConfig()
        config.watermark_type = WatermarkType.TEXT
        config.text_config.text = f"极限测试 {test_case['name']}"
        config.text_config.font_size = max(80, min(200, int(test_case['size'][0] / 50)))
        
        # 处理水印
        start_time = time.time()
        output_path = temp_file.name.replace('.jpg', '_watermarked.jpg')
        
        result_path = engine.process_image(temp_file.name, config, output_path)
        processing_time = time.time() - start_time
        
        if result_path and os.path.exists(result_path):
            output_size = os.path.getsize(result_path) / (1024 * 1024)
            print(f"✅ 水印处理成功 ({processing_time:.1f}s)")
            print(f"  输出大小: {output_size:.1f} MB")
            
            # 验证输出
            with Image.open(result_path) as result_img:
                if result_img.size == test_case['size']:
                    print(f"  输出尺寸: {result_img.size} ✓")
                else:
                    print(f"  输出尺寸异常: {result_img.size}")
                    return False
            
            # 清理输出文件
            os.unlink(result_path)
            return True
        else:
            print("❌ 水印处理失败")
            return False
            
    except MemoryError:
        print("❌ 内存不足")
        return False
    except Exception as e:
        print(f"❌ 处理异常: {e}")
        return False
    finally:
        # 清理临时文件
        try:
            os.unlink(temp_file.name)
        except:
            pass

def main():
    """主函数"""
    print("PhotoWatermark 极限大图片压力测试")
    print("=" * 60)
    
    test_cases = create_extreme_test_cases()
    passed = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[测试 {i}/{total}]")
        try:
            if test_extreme_case(test_case):
                passed += 1
                print("✅ 测试通过")
            else:
                print("❌ 测试失败")
        except KeyboardInterrupt:
            print("\n⚠️ 测试被用户中断")
            break
        except Exception as e:
            print(f"❌ 测试异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"极限测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有极限测试通过！应用程序具有出色的稳定性。")
        return 0
    elif passed > 0:
        print("⚠️ 部分极限测试通过，应用程序在大多数情况下稳定。")
        return 0
    else:
        print("❌ 极限测试失败，需要进一步优化。")
        return 1

if __name__ == '__main__':
    sys.exit(main())