"""
字体管理器
用于查找和加载系统字体文件
"""
import os
import winreg
from typing import Optional, Dict
from utils.logger import logger

class FontManager:
    """字体管理器，用于在Windows上查找字体文件路径"""
    
    _font_cache: Dict[str, str] = {}
    _initialized = False
    
    @classmethod
    def _initialize_font_cache(cls):
        """初始化字体缓存"""
        if cls._initialized:
            return
        
        cls._initialized = True
        fonts_dir = "C:/Windows/Fonts/"
        
        try:
            # 从注册表读取字体映射
            registry_key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
            )
            
            i = 0
            while True:
                try:
                    name, path, _ = winreg.EnumValue(registry_key, i)
                    i += 1
                    
                    # 如果路径不是绝对路径，添加Fonts目录
                    if not os.path.isabs(path):
                        path = os.path.join(fonts_dir, path)
                    
                    # 去除字体名称后的样式信息（如 (TrueType)）
                    font_name = name.split('(')[0].strip()
                    
                    # 存储字体名称到路径的映射
                    cls._font_cache[font_name.lower()] = path
                    
                    # 同时存储不带样式的版本
                    if ' ' in font_name:
                        base_name = font_name.split()[0]
                        if base_name.lower() not in cls._font_cache:
                            cls._font_cache[base_name.lower()] = path
                    
                except OSError:
                    break
            
            winreg.CloseKey(registry_key)
            logger.info(f"字体缓存初始化完成，共 {len(cls._font_cache)} 个字体")
            
        except Exception as e:
            logger.error(f"初始化字体缓存失败: {e}")
    
    @classmethod
    def get_font_path(cls, font_name: str, bold: bool = False, italic: bool = False) -> Optional[str]:
        """
        根据字体名称获取字体文件路径
        
        Args:
            font_name: 字体名称（如 "微软雅黑" 或 "Microsoft YaHei"）
            bold: 是否粗体
            italic: 是否斜体
            
        Returns:
            字体文件的完整路径，如果未找到则返回None
        """
        cls._initialize_font_cache()
        
        # 特殊处理：对于已知不支持特定样式组合的字体，直接返回None
        # 这样可以触发AdvancedTextRenderer中的字体替代逻辑
        font_key_lower = font_name.lower()
        
        # 微软雅黑不支持斜体和粗斜体
        if font_key_lower in ["microsoft yahei", "microsoft yahei ui", "微软雅黑", "msyh"]:
            if italic:  # 无论是否粗体，只要有斜体就不支持
                logger.info(f"FontManager: {font_name} 不原生支持斜体，返回None以触发字体替代")
                return None
        
        # 其他中文字体也通常不支持斜体
        chinese_fonts = ["宋体", "黑体", "楷体", "仿宋", "simsun", "simhei", "simkai", "simfang", "kaiti", "fangsong"]
        if italic and any(cf in font_key_lower for cf in chinese_fonts):
            logger.info(f"FontManager: {font_name} 为中文字体，不原生支持斜体，返回None以触发字体替代")
            return None
        
        # 字体名称别名映射（处理常见的中英文名称变体）
        font_aliases = {
            "微软雅黑": ["microsoft yahei", "msyh"],
            "microsoft yahei": ["microsoft yahei", "msyh", "微软雅黑"],
            "microsoft yahei ui": ["microsoft yahei", "msyh", "微软雅黑"],
            "宋体": ["simsun", "nsimsun"],
            "simsun": ["simsun", "nsimsun", "宋体"],
            "黑体": ["simhei"],
            "simhei": ["simhei", "黑体"],
            "楷体": ["kaiti", "simkai"],
            "kaiti": ["kaiti", "simkai", "楷体"],
            "simkai": ["kaiti", "simkai", "楷体"],
            "仿宋": ["fangsong", "simfang"],
            "fangsong": ["fangsong", "simfang", "仿宋"],
            "simfang": ["fangsong", "simfang", "仿宋"],
        }
        
        # 获取可能的字体名称
        search_names = [font_name]
        font_key = font_name.lower()
        if font_key in font_aliases:
            search_names.extend(font_aliases[font_key])
        
        # 添加带样式的名称变体
        style_variants = []
        if bold and italic:
            style_variants = ["bold italic", "bold & italic", "bolditalic", "bold"]
        elif bold:
            style_variants = ["bold"]
        elif italic:
            style_variants = ["italic"]
        
        # 构建搜索候选列表
        search_candidates = []
        for name in search_names:
            if style_variants:
                for style in style_variants:
                    search_candidates.append(f"{name} {style}")
                    search_candidates.append(f"{name} & {name} {style}")
            search_candidates.append(name)
        
        # 搜索字体（精确匹配）
        for candidate in search_candidates:
            path = cls._font_cache.get(candidate.lower())
            if path and os.path.exists(path):
                logger.debug(f"找到字体文件（精确匹配）: {candidate} -> {path}")
                return path
        
        # 如果精确匹配失败，尝试模糊匹配
        for name in search_names:
            name_lower = name.lower()
            for font_key, font_path in cls._font_cache.items():
                # 检查字体键是否包含搜索名称
                if name_lower in font_key:
                    # 如果需要样式，检查字体键是否包含样式
                    if style_variants:
                        for style in style_variants:
                            if style.lower() in font_key:
                                if os.path.exists(font_path):
                                    logger.debug(f"找到字体文件（模糊匹配+样式）: {font_key} -> {font_path}")
                                    return font_path
                    else:
                        # 不需要样式，直接返回第一个匹配项
                        if os.path.exists(font_path):
                            logger.debug(f"找到字体文件（模糊匹配）: {font_key} -> {font_path}")
                            return font_path
        
        # 如果仍然没找到，尝试只匹配字体文件名的一部分（处理注册表中的特殊格式）
        # 例如："宋体" 可能在注册表中是 "simsun & nsimsun"
        for name in search_names:
            name_part = name.lower().replace(" ", "")
            # 移除可能的连字符和下划线
            name_normalized = name_part.replace("-", "").replace("_", "")
            
            for font_key, font_path in cls._font_cache.items():
                # 规范化字体键
                key_normalized = font_key.lower().replace(" ", "").replace("-", "").replace("_", "").replace("&", "")
                
                # 检查是否包含规范化后的名称
                if name_normalized in key_normalized or name_part in font_key.lower():
                    if os.path.exists(font_path):
                        logger.debug(f"找到字体文件（宽松匹配）: {name} -> {font_key} -> {font_path}")
                        return font_path
        
        logger.warning(f"未找到字体: {font_name} (bold={bold}, italic={italic})")
        return None
    
    @classmethod
    def check_font_style_support(cls, font_name: str, bold: bool = False, italic: bool = False) -> bool:
        """
        检查字体是否支持指定的样式（粗体/斜体）
        
        Args:
            font_name: 字体名称
            bold: 是否检查粗体支持
            italic: 是否检查斜体支持
            
        Returns:
            True if the font has native support for the style, False otherwise
        """
        if not bold and not italic:
            # 基础字体始终支持
            return True
        
        # 特殊处理：已知不支持的字体样式组合
        font_key_lower = font_name.lower()
        
        # 微软雅黑不支持斜体（无论是否粗体）
        if font_key_lower in ["microsoft yahei", "microsoft yahei ui", "微软雅黑", "msyh"]:
            if italic:
                return False
        
        # 其他中文字体通常不支持斜体
        chinese_fonts = ["宋体", "黑体", "楷体", "仿宋", "simsun", "simhei", "simkai", "simfang", "kaiti", "fangsong"]
        if italic and any(cf in font_key_lower for cf in chinese_fonts):
            return False
        
        # 尝试获取带样式的字体路径
        styled_font_path = cls.get_font_path(font_name, bold, italic)
        base_font_path = cls.get_font_path(font_name, False, False)
        
        # 如果找到了带样式的字体，且与基础字体路径不同，说明有原生支持
        if styled_font_path and base_font_path:
            # 如果路径不同，说明有独立的样式字体文件
            return styled_font_path != base_font_path
        
        # 如果没找到带样式的字体，说明不支持该样式
        return False
    
    @classmethod
    def list_available_fonts(cls) -> list:
        """列出所有可用的字体名称"""
        cls._initialize_font_cache()
        return sorted(set(cls._font_cache.keys()))
