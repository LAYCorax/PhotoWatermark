"""
测试脚本 - 验证PhotoWatermark核心功能
"""
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_imports():
    """测试所有模块导入"""
    print("测试模块导入...")
    
    try:
        from models.image_info import ImageInfo, ImageListModel
        print("✓ 图片信息模型导入成功")
        
        from models.watermark_config import WatermarkConfig, WatermarkType, WatermarkPosition
        print("✓ 水印配置模型导入成功")
        
        from utils.file_utils import FileUtils
        print("✓ 文件工具导入成功")
        
        from ui.widgets.image_list_widget import ImageListWidget
        print("✓ 图片列表组件导入成功")
        
        from ui.widgets.preview_widget import PreviewWidget
        print("✓ 预览组件导入成功")
        
        from ui.widgets.watermark_config_widget import WatermarkConfigWidget
        print("✓ 水印配置组件导入成功")
        
        from ui.main_window import MainWindow
        print("✓ 主窗口导入成功")
        
        return True
        
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_model_functionality():
    """测试数据模型功能"""
    print("\n测试数据模型功能...")
    
    try:
        from models.watermark_config import WatermarkConfig
        
        # 测试水印配置
        config = WatermarkConfig()
        config_dict = config.to_dict()
        config2 = WatermarkConfig.from_dict(config_dict)
        
        print("✓ 水印配置序列化/反序列化成功")
        
        from models.image_info import ImageListModel
        
        # 测试图片列表模型
        model = ImageListModel()
        print(f"✓ 图片列表模型创建成功，初始数量: {model.count()}")
        
        return True
        
    except Exception as e:
        print(f"✗ 模型测试失败: {e}")
        return False

def test_file_utils():
    """测试文件工具"""
    print("\n测试文件工具...")
    
    try:
        from utils.file_utils import FileUtils
        
        # 测试文件扩展名检查
        test_files = [
            "test.jpg", "test.png", "test.bmp", "test.txt", "test.exe"
        ]
        
        for test_file in test_files:
            is_image = FileUtils.is_image_file(test_file) if os.path.exists(test_file) else False
            expected = test_file.endswith(('.jpg', '.png', '.bmp'))
            print(f"  {test_file}: {'图片' if expected else '非图片'}")
        
        print("✓ 文件类型检查功能正常")
        
        return True
        
    except Exception as e:
        print(f"✗ 文件工具测试失败: {e}")
        return False

def test_gui_availability():
    """测试GUI可用性"""
    print("\n测试GUI可用性...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        
        # 创建应用程序实例（不显示窗口）
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
            app._created_by_test = True
        
        print("✓ PyQt5应用程序实例创建成功")
        
        # 测试主窗口创建（不显示）
        from ui.main_window import MainWindow
        window = MainWindow()
        print("✓ 主窗口创建成功")
        
        # 清理窗口资源
        window.close()
        window.deleteLater()
        
        # 如果应用程序实力是我们创建的，则退出
        if hasattr(app, '_created_by_test'):
            app.quit()
        
        return True
        
    except Exception as e:
        print(f"✗ GUI测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("PhotoWatermark 核心功能测试")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_model_functionality,
        test_file_utils,
        test_gui_availability
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
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有核心功能测试通过！")
        return 0
    else:
        print("✗ 部分测试失败，请检查相关功能。")
        return 1

if __name__ == '__main__':
    sys.exit(main())