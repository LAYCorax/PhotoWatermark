"""
初始化默认模板
运行此脚本以创建默认的水印模板
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.template_manager import TemplateManager

def main():
    print("正在创建默认模板...")
    
    manager = TemplateManager()
    manager.create_default_templates()
    
    print(f"\n默认模板创建完成！")
    print(f"共有 {len(manager.get_all_templates())} 个模板：")
    
    for template in manager.get_all_templates():
        type_mark = "[默认]" if template.is_default else "[用户]"
        print(f"  {type_mark} {template.name}")
        if template.description:
            print(f"      {template.description}")

if __name__ == '__main__':
    main()
