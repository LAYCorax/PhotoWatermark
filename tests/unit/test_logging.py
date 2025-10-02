"""
日志功能测试脚本
验证应用程序的日志记录功能
"""
import sys
import os
import tempfile
from PIL import Image

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_logging_functionality():
    """测试日志功能"""
    print("PhotoWatermark 日志功能测试")
    print("=" * 50)
    
    try:
        # 导入日志模块
        from utils.logger import logger
        
        logger.info("开始日志功能测试")
        logger.debug("这是调试信息")
        logger.warning("这是警告信息")
        
        # 测试水印引擎日志
        print("\n测试水印引擎日志...")
        from core.watermark_engine import WatermarkEngine
        from models.watermark_config import WatermarkConfig, WatermarkType
        
        # 创建测试图片
        test_img = Image.new('RGB', (500, 400), (100, 150, 200))
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        test_img.save(temp_file.name, 'JPEG')
        temp_file.close()
        
        logger.info(f"创建测试图片: {temp_file.name}")
        
        # 创建水印引擎和配置
        engine = WatermarkEngine()
        config = WatermarkConfig()
        config.watermark_type = WatermarkType.TEXT
        config.text_config.text = "日志测试水印"
        
        # 处理图片（这会生成详细日志）
        output_path = temp_file.name.replace('.jpg', '_logged.jpg')
        result = engine.process_image(temp_file.name, config, output_path)
        
        if result:
            logger.info("水印处理成功，日志记录正常")
            os.unlink(result)
        else:
            logger.error("水印处理失败")
        
        # 清理
        os.unlink(temp_file.name)
        
        print("✅ 日志功能测试完成")
        print("请查看 logs/ 目录下的日志文件获取详细信息")
        
        return True
        
    except Exception as e:
        print(f"❌ 日志功能测试失败: {e}")
        return False

def test_main_app_logging():
    """测试主应用程序日志"""
    print("\n测试主应用程序日志功能...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from utils.logger import logger
        
        # 创建应用程序实例
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        logger.info("测试主应用程序日志功能")
        
        # 测试主窗口创建（会生成初始化日志）
        from ui.main_window import MainWindow
        
        logger.info("创建主窗口进行日志测试...")
        window = MainWindow()
        
        logger.info("主窗口创建成功，日志记录正常")
        
        # 清理
        window.close()
        window.deleteLater()
        
        print("✅ 主应用程序日志测试完成")
        return True
        
    except Exception as e:
        logger.error(f"主应用程序日志测试失败: {e}")
        print(f"❌ 主应用程序日志测试失败: {e}")
        return False

def show_log_info():
    """显示日志信息"""
    print("\n日志文件信息:")
    print("-" * 30)
    
    log_dir = "logs"
    if os.path.exists(log_dir):
        log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
        if log_files:
            latest_log = max(log_files)
            log_path = os.path.join(log_dir, latest_log)
            log_size = os.path.getsize(log_path)
            
            print(f"最新日志文件: {latest_log}")
            print(f"日志文件大小: {log_size} 字节")
            print(f"完整路径: {log_path}")
            
            # 显示最后几行日志
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        print(f"\n最后5行日志内容:")
                        for line in lines[-5:]:
                            print(f"  {line.strip()}")
            except Exception as e:
                print(f"读取日志文件失败: {e}")
        else:
            print("未找到日志文件")
    else:
        print("日志目录不存在")

def main():
    """主函数"""
    print("PhotoWatermark 日志功能综合测试")
    print("=" * 60)
    
    tests = [
        test_logging_functionality,
        test_main_app_logging
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"测试异常: {e}")
    
    show_log_info()
    
    print(f"\n测试结果: {passed}/{len(tests)} 通过")
    
    if passed == len(tests):
        print("🎉 所有日志功能测试通过！")
        print("应用程序现在具备完善的日志记录能力。")
        return 0
    else:
        print("⚠️ 部分日志功能测试失败。")
        return 1

if __name__ == '__main__':
    sys.exit(main())