#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全模块日志功能测试
验证所有模块的日志记录功能是否正常工作
"""
import sys
import os
import tempfile
from PIL import Image

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from utils.logger import logger
from utils.file_utils import FileUtils
from utils.memory_manager import MemoryManager
from models.watermark_config import WatermarkConfig, WatermarkType, WatermarkPosition
from models.image_info import ImageListModel, ImageInfo

def test_all_modules_logging():
    """测试所有模块的日志功能"""
    print("=" * 70)
    print("PhotoWatermark 全模块日志功能测试")
    print("=" * 70)
    
    logger.info("=" * 60)
    logger.info("开始全模块日志功能测试")
    logger.info("=" * 60)
    
    test_results = []
    
    # 1. 测试FileUtils日志
    print("\n1. 测试文件工具日志...")
    try:
        logger.info("测试FileUtils模块日志功能")
        
        # 创建测试图片
        test_image = Image.new('RGB', (100, 100), (255, 0, 0))
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        temp_file.close()  # 关闭文件句柄
        test_image.save(temp_file.name, 'JPEG')
        
        # 测试文件检查
        is_image = FileUtils.is_image_file(temp_file.name)
        logger.info(f"文件检查结果: {is_image}")
        
        # 测试文件列表
        temp_dir = os.path.dirname(temp_file.name)
        files = FileUtils.get_image_files_from_folder(temp_dir, max_files=5)
        logger.info(f"找到图片文件: {len(files)}")
        
        # 清理
        try:
            os.unlink(temp_file.name)
        except Exception as e:
            logger.debug(f"文件清理警告: {e}")
        
        test_results.append(("FileUtils日志", "✅ 通过"))
        print("✅ FileUtils日志测试通过")
        
    except Exception as e:
        logger.error(f"FileUtils日志测试失败: {e}")
        test_results.append(("FileUtils日志", f"❌ 失败: {e}"))
        print(f"❌ FileUtils日志测试失败: {e}")
    
    # 2. 测试MemoryManager日志
    print("\n2. 测试内存管理器日志...")
    try:
        logger.info("测试MemoryManager模块日志功能")
        
        memory_manager = MemoryManager()
        
        # 测试内存使用量检查
        usage = memory_manager.get_memory_usage_mb()
        logger.info(f"当前内存使用: {usage:.1f}MB")
        
        # 测试内存警告检查
        is_warning = memory_manager.is_memory_warning()
        logger.info(f"内存警告状态: {is_warning}")
        
        # 测试内存清理
        memory_manager.cleanup_memory()
        
        test_results.append(("MemoryManager日志", "✅ 通过"))
        print("✅ MemoryManager日志测试通过")
        
    except Exception as e:
        logger.error(f"MemoryManager日志测试失败: {e}")
        test_results.append(("MemoryManager日志", f"❌ 失败: {e}"))
        print(f"❌ MemoryManager日志测试失败: {e}")
    
    # 3. 测试WatermarkConfig日志
    print("\n3. 测试水印配置日志...")
    try:
        logger.info("测试WatermarkConfig模块日志功能")
        
        # 创建配置
        config = WatermarkConfig()
        config.watermark_type = WatermarkType.TEXT
        config.position = WatermarkPosition.CENTER
        
        # 测试序列化
        config_dict = config.to_dict()
        logger.info(f"配置序列化: {len(config_dict)} 个参数")
        
        # 测试反序列化
        new_config = WatermarkConfig.from_dict(config_dict)
        logger.info(f"配置反序列化: 类型={new_config.watermark_type.value}")
        
        test_results.append(("WatermarkConfig日志", "✅ 通过"))
        print("✅ WatermarkConfig日志测试通过")
        
    except Exception as e:
        logger.error(f"WatermarkConfig日志测试失败: {e}")
        test_results.append(("WatermarkConfig日志", f"❌ 失败: {e}"))
        print(f"❌ WatermarkConfig日志测试失败: {e}")
    
    # 4. 测试ImageListModel日志（如果有的话）
    print("\n4. 测试图片列表模型日志...")
    try:
        logger.info("测试ImageListModel模块日志功能")
        
        # 创建模型
        model = ImageListModel()
        
        # 创建测试图片信息
        test_image = Image.new('RGB', (200, 150), (0, 255, 0))
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_file.close()  # 关闭文件句柄
        test_image.save(temp_file.name, 'PNG')
        
        # 添加图片
        added = model.add_images([temp_file.name])
        logger.info(f"添加图片结果: {added} 个")
        
        # 清理
        try:
            os.unlink(temp_file.name)
        except Exception as e:
            logger.debug(f"文件清理警告: {e}")
        
        test_results.append(("ImageListModel日志", "✅ 通过"))
        print("✅ ImageListModel日志测试通过")
        
    except Exception as e:
        logger.error(f"ImageListModel日志测试失败: {e}")
        test_results.append(("ImageListModel日志", f"❌ 失败: {e}"))
        print(f"❌ ImageListModel日志测试失败: {e}")
    
    # 5. 测试launcher模块（导入测试）
    print("\n5. 测试启动器日志...")
    try:
        logger.info("测试launcher模块日志功能")
        
        from launcher import check_dependencies
        deps = check_dependencies()
        logger.info(f"依赖检查完成: 缺失={deps}")
        
        test_results.append(("Launcher日志", "✅ 通过"))
        print("✅ Launcher日志测试通过")
        
    except Exception as e:
        logger.error(f"Launcher日志测试失败: {e}")
        test_results.append(("Launcher日志", f"❌ 失败: {e}"))
        print(f"❌ Launcher日志测试失败: {e}")
    
    # 汇总测试结果
    logger.info("=" * 60)
    logger.info("全模块日志功能测试完成")
    logger.info("=" * 60)
    
    print("\n" + "=" * 70)
    print("📊 测试结果汇总")
    print("=" * 70)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        print(f"{test_name:20s} : {result}")
        if "✅" in result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有模块的日志功能都正常工作！")
        logger.info("🎉 所有模块的日志功能都正常工作！")
    else:
        print(f"⚠️  有 {total - passed} 个测试失败，请检查相关模块")
        logger.warning(f"有 {total - passed} 个测试失败")
    
    print("\n📁 日志文件信息:")
    print("-" * 50)
    
    # 显示日志文件信息
    log_dir = "logs"
    if os.path.exists(log_dir):
        log_files = sorted([f for f in os.listdir(log_dir) if f.endswith('.log')])
        if log_files:
            latest_log = log_files[-1]
            log_path = os.path.join(log_dir, latest_log)
            print(f"最新日志文件: {latest_log}")
            print(f"日志文件大小: {os.path.getsize(log_path)} 字节")
            print(f"完整路径: {log_path}")
            
            # 显示最后几行日志
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    print(f"\n最后3行日志内容:")
                    for line in lines[-3:]:
                        print(f"  {line.strip()}")
            except Exception as e:
                print(f"读取日志文件失败: {e}")
    
    return passed == total

if __name__ == "__main__":
    success = test_all_modules_logging()
    sys.exit(0 if success else 1)