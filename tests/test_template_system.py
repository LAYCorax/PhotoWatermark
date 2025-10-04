"""
测试模板系统功能
"""
import os
import sys
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.template_manager import TemplateManager, Template
from models.watermark_config import WatermarkConfig

def test_template_manager():
    """测试模板管理器基本功能"""
    print("=" * 60)
    print("测试模板管理器")
    print("=" * 60)
    
    # 创建模板管理器实例
    manager = TemplateManager()
    
    # 1. 测试创建默认模板
    print("\n1. 创建默认模板...")
    manager.create_default_templates()
    templates = manager.get_all_templates()
    print(f"   创建完成，共有 {len(templates)} 个模板")
    
    # 2. 列出所有模板
    print("\n2. 模板列表:")
    for i, template in enumerate(templates, 1):
        type_mark = "[默认]" if template.is_default else "[用户]"
        print(f"   {i}. {type_mark} {template.name}")
        print(f"      描述: {template.description or '(无)'}")
        print(f"      创建时间: {template.created_at}")
    
    # 3. 测试保存新模板
    print("\n3. 测试保存新模板...")
    test_config = WatermarkConfig()
    test_config.text_config.text = "测试水印"
    
    test_template = Template(
        name="测试模板",
        config=test_config.to_dict(),
        description="这是一个测试模板"
    )
    
    if manager.save_template(test_template):
        print("   ✓ 模板保存成功")
    else:
        print("   ✗ 模板保存失败")
    
    # 4. 测试获取模板
    print("\n4. 测试获取模板...")
    retrieved_template = manager.get_template("测试模板")
    if retrieved_template:
        print(f"   ✓ 成功获取模板: {retrieved_template.name}")
        print(f"   描述: {retrieved_template.description}")
    else:
        print("   ✗ 获取模板失败")
    
    # 5. 测试导出模板
    print("\n5. 测试导出模板...")
    export_path = "temp_test_template.json"
    if manager.export_template("测试模板", export_path):
        print(f"   ✓ 模板导出成功: {export_path}")
        
        # 验证导出的文件
        if os.path.exists(export_path):
            with open(export_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"   文件内容: {data.get('name')}")
    else:
        print("   ✗ 模板导出失败")
    
    # 6. 测试导入模板
    print("\n6. 测试导入模板...")
    if os.path.exists(export_path):
        imported_template = manager.import_template(export_path)
        if imported_template:
            print(f"   ✓ 模板导入成功: {imported_template.name}")
        else:
            print("   ✗ 模板导入失败")
        
        # 清理临时文件
        os.remove(export_path)
        print("   临时文件已清理")
    
    # 7. 测试删除模板
    print("\n7. 测试删除模板...")
    if manager.delete_template("测试模板"):
        print("   ✓ 模板删除成功")
    else:
        print("   ✗ 模板删除失败")
    
    # 8. 测试获取用户模板和默认模板
    print("\n8. 统计模板数量:")
    all_templates = manager.get_all_templates()
    user_templates = manager.get_user_templates()
    default_templates = manager.get_default_templates()
    
    print(f"   总模板数: {len(all_templates)}")
    print(f"   用户模板: {len(user_templates)}")
    print(f"   默认模板: {len(default_templates)}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

def test_template_config():
    """测试模板配置的序列化和反序列化"""
    print("\n" + "=" * 60)
    print("测试配置序列化")
    print("=" * 60)
    
    # 创建配置
    config = WatermarkConfig()
    config.text_config.text = "序列化测试"
    config.text_config.font_size = 64
    config.text_config.color = (255, 0, 0)
    config.position = "center"
    config.rotation = 45.0
    
    # 转换为字典
    config_dict = config.to_dict()
    print("\n1. 配置已转换为字典")
    print(f"   文本: {config_dict['text_config']['text']}")
    print(f"   字号: {config_dict['text_config']['font_size']}")
    print(f"   颜色: {config_dict['text_config']['color']}")
    print(f"   位置: {config_dict['position']}")
    print(f"   旋转: {config_dict['rotation']}")
    
    # 从字典恢复
    restored_config = WatermarkConfig.from_dict(config_dict)
    print("\n2. 配置已从字典恢复")
    print(f"   文本: {restored_config.text_config.text}")
    print(f"   字号: {restored_config.text_config.font_size}")
    print(f"   颜色: {restored_config.text_config.color}")
    print(f"   位置: {restored_config.position}")
    print(f"   旋转: {restored_config.rotation}")
    
    # 验证
    if restored_config.text_config.text == config.text_config.text:
        print("\n✓ 配置序列化测试通过")
    else:
        print("\n✗ 配置序列化测试失败")

if __name__ == '__main__':
    try:
        test_template_manager()
        test_template_config()
        
        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
