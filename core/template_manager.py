"""
模板管理器
负责水印配置模板的保存、加载、管理
"""
import os
import json
from datetime import datetime
from typing import List, Optional, Dict
from utils.logger import logger, log_exception


class Template:
    """水印配置模板"""
    
    def __init__(self, name: str, config: dict, description: str = "", 
                 created_at: str = None, is_default: bool = False):
        self.name = name
        self.config = config
        self.description = description
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.is_default = is_default
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'name': self.name,
            'config': self.config,
            'description': self.description,
            'created_at': self.created_at,
            'is_default': self.is_default
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Template':
        """从字典创建"""
        return cls(
            name=data.get('name', '未命名模板'),
            config=data.get('config', {}),
            description=data.get('description', ''),
            created_at=data.get('created_at'),
            is_default=data.get('is_default', False)
        )


class TemplateManager:
    """模板管理器（单例模式）"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.templates: List[Template] = []
        self.template_dir = os.path.join('config', 'user_templates')
        self.default_template_dir = os.path.join('resources', 'templates')
        
        # 确保目录存在
        os.makedirs(self.template_dir, exist_ok=True)
        os.makedirs(self.default_template_dir, exist_ok=True)
        
        # 加载模板
        self.load_all_templates()
        logger.info(f"模板管理器初始化完成，共加载 {len(self.templates)} 个模板")
    
    @log_exception
    def save_template(self, template: Template) -> bool:
        """保存模板"""
        try:
            # 检查是否已存在同名模板
            existing = self.get_template(template.name)
            if existing:
                # 更新现有模板
                self.templates.remove(existing)
            
            self.templates.append(template)
            
            # 保存到文件
            filename = self._get_safe_filename(template.name) + '.json'
            filepath = os.path.join(self.template_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)
            
            logger.info(f"模板保存成功: {template.name} -> {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"保存模板失败: {e}")
            return False
    
    @log_exception
    def load_template(self, filepath: str) -> Optional[Template]:
        """从文件加载单个模板"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            template = Template.from_dict(data)
            logger.debug(f"加载模板: {template.name} from {filepath}")
            return template
            
        except Exception as e:
            logger.error(f"加载模板失败 {filepath}: {e}")
            return None
    
    @log_exception
    def load_all_templates(self):
        """加载所有模板"""
        self.templates.clear()
        
        # 加载默认模板
        if os.path.exists(self.default_template_dir):
            for filename in os.listdir(self.default_template_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.default_template_dir, filename)
                    template = self.load_template(filepath)
                    if template:
                        template.is_default = True
                        self.templates.append(template)
        
        # 加载用户模板
        if os.path.exists(self.template_dir):
            for filename in os.listdir(self.template_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.template_dir, filename)
                    template = self.load_template(filepath)
                    if template:
                        self.templates.append(template)
        
        logger.info(f"加载了 {len(self.templates)} 个模板")
    
    def get_template(self, name: str) -> Optional[Template]:
        """根据名称获取模板"""
        for template in self.templates:
            if template.name == name:
                return template
        return None
    
    def get_all_templates(self) -> List[Template]:
        """获取所有模板"""
        return self.templates.copy()
    
    def get_user_templates(self) -> List[Template]:
        """获取用户模板（不包括默认模板）"""
        return [t for t in self.templates if not t.is_default]
    
    def get_default_templates(self) -> List[Template]:
        """获取默认模板"""
        return [t for t in self.templates if t.is_default]
    
    @log_exception
    def delete_template(self, name: str) -> bool:
        """删除模板"""
        template = self.get_template(name)
        if not template:
            logger.warning(f"模板不存在: {name}")
            return False
        
        if template.is_default:
            logger.warning(f"不能删除默认模板: {name}")
            return False
        
        try:
            # 从列表中移除
            self.templates.remove(template)
            
            # 删除文件
            filename = self._get_safe_filename(name) + '.json'
            filepath = os.path.join(self.template_dir, filename)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"删除模板: {name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"删除模板失败: {e}")
            return False
    
    @log_exception
    def export_template(self, name: str, export_path: str) -> bool:
        """导出模板到指定路径"""
        template = self.get_template(name)
        if not template:
            return False
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)
            
            logger.info(f"导出模板: {name} -> {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出模板失败: {e}")
            return False
    
    @log_exception
    def import_template(self, import_path: str) -> Optional[Template]:
        """从文件导入模板"""
        template = self.load_template(import_path)
        if template:
            # 确保模板名称唯一
            original_name = template.name
            counter = 1
            while self.get_template(template.name):
                template.name = f"{original_name} ({counter})"
                counter += 1
            
            template.is_default = False
            if self.save_template(template):
                logger.info(f"导入模板成功: {template.name}")
                return template
        
        return None
    
    def _get_safe_filename(self, name: str) -> str:
        """获取安全的文件名"""
        # 移除不安全的字符
        unsafe_chars = '<>:"/\\|?*'
        safe_name = name
        for char in unsafe_chars:
            safe_name = safe_name.replace(char, '_')
        return safe_name
    
    @log_exception
    def create_default_templates(self):
        """创建默认模板"""
        default_templates = [
            {
                'name': '简单文字水印',
                'description': '右下角白色文字水印，适合深色背景图片',
                'config': {
                    'watermark_type': 'text',
                    'text_config': {
                        'text': '版权所有',
                        'font_family': 'Microsoft YaHei',
                        'font_size': 48,
                        'font_bold': False,
                        'font_italic': False,
                        'color': (255, 255, 255),
                        'opacity': 0.8,
                        'has_shadow': False,
                        'has_outline': False
                    },
                    'position': 'bottom_right',
                    'margin_x': 20,
                    'margin_y': 20,
                    'rotation': 0.0
                }
            },
            {
                'name': '带描边文字水印',
                'description': '居中大号文字，带黑色描边效果',
                'config': {
                    'watermark_type': 'text',
                    'text_config': {
                        'text': 'SAMPLE',
                        'font_family': 'Arial',
                        'font_size': 120,
                        'font_bold': True,
                        'font_italic': False,
                        'color': (255, 255, 255),
                        'opacity': 0.6,
                        'has_shadow': False,
                        'has_outline': True,
                        'outline_color': (0, 0, 0),
                        'outline_width': 3,
                        'outline_opacity': 0.8
                    },
                    'position': 'center',
                    'margin_x': 0,
                    'margin_y': 0,
                    'rotation': -45.0
                }
            },
            {
                'name': '带阴影文字水印',
                'description': '左上角文字，带阴影效果增强可读性',
                'config': {
                    'watermark_type': 'text',
                    'text_config': {
                        'text': '© 2025',
                        'font_family': 'Microsoft YaHei',
                        'font_size': 36,
                        'font_bold': False,
                        'font_italic': False,
                        'color': (255, 255, 255),
                        'opacity': 0.9,
                        'has_shadow': True,
                        'shadow_color': (0, 0, 0),
                        'shadow_offset_x': 3,
                        'shadow_offset_y': 3,
                        'shadow_blur': 5,
                        'shadow_opacity': 0.6,
                        'has_outline': False
                    },
                    'position': 'top_left',
                    'margin_x': 20,
                    'margin_y': 20,
                    'rotation': 0.0
                }
            }
        ]
        
        for template_data in default_templates:
            template = Template(
                name=template_data['name'],
                config=template_data['config'],
                description=template_data['description'],
                is_default=True
            )
            
            # 保存到默认模板目录
            filename = self._get_safe_filename(template.name) + '.json'
            filepath = os.path.join(self.default_template_dir, filename)
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)
                logger.info(f"创建默认模板: {template.name}")
            except Exception as e:
                logger.error(f"创建默认模板失败: {e}")
        
        # 重新加载所有模板
        self.load_all_templates()
