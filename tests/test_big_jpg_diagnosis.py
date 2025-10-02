#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查big.jpg图片信息和预览问题诊断
"""
import sys
import os
from PIL import Image

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from utils.logger import logger

def check_big_jpg():
    """检查big.jpg文件信息"""
    print("=" * 60)
    print("检查big.jpg图片信息")
    print("=" * 60)
    
    big_jpg_path = "tests/big.jpg"
    
    if not os.path.exists(big_jpg_path):
        print("❌ big.jpg文件不存在")
        return False
    
    try:
        # 检查文件基本信息
        file_size = os.path.getsize(big_jpg_path)
        print(f"📁 文件大小: {file_size:,} 字节 ({file_size/1024/1024:.2f} MB)")
        
        # 打开图片检查详细信息
        with Image.open(big_jpg_path) as img:
            print(f"📐 图片尺寸: {img.size[0]} x {img.size[1]} 像素")
            print(f"🎨 颜色模式: {img.mode}")
            print(f"📋 图片格式: {img.format}")
            
            # 计算像素总数
            total_pixels = img.size[0] * img.size[1]
            print(f"🔢 总像素数: {total_pixels:,} ({total_pixels/1e6:.1f}MP)")
            
            # 检查是否可能触发内存保守模式
            if total_pixels > 25 * 1024 * 1024:
                print("⚠️  图片像素数超过25MP，会触发超保守模式")
            elif total_pixels > 15 * 1024 * 1024:
                print("⚠️  图片像素数超过15MP，会触发内存保守模式")
            else:
                print("✅ 图片像素数在正常范围内")
            
            # 检查预览缩放
            max_preview_size = (1920, 1080)
            if img.size[0] > max_preview_size[0] or img.size[1] > max_preview_size[1]:
                scale_x = max_preview_size[0] / img.size[0]
                scale_y = max_preview_size[1] / img.size[1]
                scale = min(scale_x, scale_y)
                new_size = (int(img.size[0] * scale), int(img.size[1] * scale))
                print(f"📏 预览需要缩放: {scale:.3f} -> {new_size[0]} x {new_size[1]}")
            else:
                print("✅ 预览无需缩放")
            
            # 检查是否有特殊属性
            if hasattr(img, 'info') and img.info:
                print(f"📝 图片信息: {len(img.info)} 个属性")
                for key, value in list(img.info.items())[:3]:  # 只显示前3个
                    print(f"   {key}: {str(value)[:50]}...")
            
        return True
        
    except Exception as e:
        print(f"❌ 检查图片时出错: {e}")
        logger.error(f"检查big.jpg时出错: {e}")
        return False

def test_preview_widget():
    """测试预览组件处理big.jpg"""
    print("\n" + "=" * 60)
    print("测试预览组件处理big.jpg")
    print("=" * 60)
    
    try:
        # 导入预览组件
        from ui.widgets.preview_widget import PreviewWidget
        from models.watermark_config import WatermarkConfig, WatermarkType, WatermarkPosition
        
        print("✅ 预览组件导入成功")
        
        # 创建预览组件
        preview_widget = PreviewWidget()
        print("✅ 预览组件创建成功")
        
        # 测试设置图片
        big_jpg_path = os.path.abspath("tests/big.jpg")
        print(f"🖼️  开始设置预览图片: {big_jpg_path}")
        
        logger.info("开始测试big.jpg预览")
        
        # 这里可能会出错
        preview_widget.set_image(big_jpg_path)
        print("✅ 设置预览图片成功")
        
        # 测试水印配置
        config = WatermarkConfig()
        config.watermark_type = WatermarkType.TEXT
        config.position = WatermarkPosition.BOTTOM_RIGHT
        config.text_config.text = "测试水印"
        
        print("🎨 开始设置水印配置")
        preview_widget.set_watermark_config(config)
        print("✅ 设置水印配置成功")
        
        logger.info("big.jpg预览测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 预览组件测试失败: {e}")
        logger.error(f"预览组件测试big.jpg失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    logger.info("开始big.jpg问题诊断")
    
    # 检查图片信息
    img_ok = check_big_jpg()
    
    if not img_ok:
        print("\n❌ 图片检查失败，无法继续测试")
        return False
    
    # 测试预览组件
    preview_ok = test_preview_widget()
    
    print("\n" + "=" * 60)
    print("🔍 诊断结果")
    print("=" * 60)
    
    if preview_ok:
        print("✅ big.jpg预览功能正常")
        print("💡 如果在GUI中仍有问题，可能是PyQt5相关的内存或线程问题")
    else:
        print("❌ big.jpg预览功能异常")
        print("💡 建议检查日志文件获取详细错误信息")
    
    return preview_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)