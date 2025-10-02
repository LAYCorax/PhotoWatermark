"""
Test launcher for PhotoWatermark application
This script helps test the application without full PyQt5 installation
"""
import sys
import os
from utils.logger import logger, log_exception

@log_exception
def check_dependencies():
    """Check if required dependencies are available"""
    logger.info("检查应用程序依赖")
    missing_deps = []
    
    try:
        import PIL
        logger.debug("PIL/Pillow 已安装")
    except ImportError:
        logger.warning("PIL/Pillow 未安装")
        missing_deps.append("Pillow")
    
    try:
        import PyQt5
        logger.debug("PyQt5 已安装")
    except ImportError:
        logger.warning("PyQt5 未安装")
        missing_deps.append("PyQt5")
    
    logger.info(f"依赖检查完成, 缺少: {missing_deps}")
    return missing_deps

def install_dependencies():
    """Print instructions for installing dependencies"""
    print("PhotoWatermark 依赖安装指南")
    print("=" * 40)
    print()
    print("请在命令行中运行以下命令安装所需依赖：")
    print()
    print("1. 安装 Pillow (图像处理库):")
    print("   pip install Pillow")
    print()
    print("2. 安装 PyQt5 (GUI框架):")
    print("   pip install PyQt5")
    print()
    print("3. 安装其他依赖:")
    print("   pip install piexif")
    print()
    print("或者一次性安装所有依赖：")
    print("   pip install -r requirements.txt")
    print()

@log_exception
def main():
    """Main launcher function"""
    logger.info("启动PhotoWatermark应用程序启动器")
    print("PhotoWatermark 应用程序启动器")
    print("版本: 1.0.0")
    print()
    
    # Check dependencies
    logger.info("检查依赖包")
    missing = check_dependencies()
    if missing:
        logger.error(f"缺少依赖包: {', '.join(missing)}")
        print(f"错误: 缺少以下依赖包: {', '.join(missing)}")
        print()
        install_dependencies()
        return 1
    
    # Try to launch the application
    try:
        # Change to the PhotoWatermark directory
        app_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(app_dir)
        
        # Import and run the main application
        from main import main as app_main
        print("正在启动 PhotoWatermark...")
        app_main()
        
    except Exception as e:
        print(f"启动失败: {e}")
        print()
        print("请确保所有依赖都已正确安装，然后重试。")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())