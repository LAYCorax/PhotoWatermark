"""
Advanced Text Effects Renderer
Implements sophisticated text rendering with various visual effects
"""
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    print("PIL is required for advanced text effects.")
    raise

import math
from typing import Tuple, Optional, List
from models.watermark_config import TextWatermarkConfig
from utils.logger import logger, log_exception
from utils.font_manager import FontManager


class AdvancedTextRenderer:
    """Advanced text renderer with multiple visual effects"""
    
    def __init__(self):
        self.font_cache = {}  # Cache for loaded fonts
        logger.debug("初始化高级文本渲染器")
    
    @log_exception
    def render_text_with_effects(self, image: Image.Image, config: TextWatermarkConfig, 
                               position: Tuple[int, int], text: str, rotation: float = 0.0) -> Image.Image:
        """
        Render text with advanced effects on the given image
        Args:
            image: Base image
            config: Text watermark configuration
            position: (x, y) position for text
            text: Text to render
            rotation: Rotation angle in degrees (default 0.0)
        """
        if not text:
            return image
            
        logger.debug(f"渲染高级文本效果: {text}, 旋转: {rotation}°")
        
        # Load font with style support
        font = self._load_font_with_style(config.font_family, config.font_size, config.font_bold, config.font_italic)
        
        # Get text dimensions without affecting position calculation
        temp_image = Image.new('RGB', (1, 1))
        temp_draw = ImageDraw.Draw(temp_image)
        
        try:
            bbox = temp_draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except (AttributeError, TypeError):
            # Fallback for older Pillow versions
            try:
                text_width, text_height = font.getsize(text)
            except AttributeError:
                text_width = len(text) * config.font_size // 2
                text_height = config.font_size
        
        # Use exact position passed from caller (no adjustment)
        adjusted_position = position
        
        # Create text layer with effects
        text_layer = self._create_text_layer(image.size, text, font, config, adjusted_position)
        
        # Apply rotation if needed
        if rotation != 0.0:
            text_layer = self._rotate_watermark(text_layer, rotation, adjusted_position, text_width, text_height)
        
        # Composite text layer onto original image using paste with alpha mask
        if text_layer.mode == 'RGBA':
            # Convert image to RGBA if needed for proper compositing
            if image.mode != 'RGBA':
                result = image.convert('RGBA')
            else:
                result = image.copy()
            
            # Paste text layer using alpha channel as mask for exact positioning
            result.paste(text_layer, (0, 0), text_layer)
            
            # Keep RGBA mode to preserve transparency (don't convert back)
            # This ensures PNG files maintain their alpha channel
            return result
        else:
            return Image.blend(image, text_layer, alpha=config.opacity)
    
    def _load_font_with_style(self, font_family: str, font_size: int, bold: bool = False, italic: bool = False) -> ImageFont.FreeTypeFont:
        """Load font with proper bold and italic support - uses FontManager for consistency"""
        cache_key = f"{font_family}_{font_size}_{bold}_{italic}"
        
        if cache_key in self.font_cache:
            return self.font_cache[cache_key]
        
        logger.debug(f"高级渲染器: 加载字体 {font_family}, 大小:{font_size}, 粗体:{bold}, 斜体:{italic}")
        
        # First try using FontManager (same as preview and export engine)
        font_path = FontManager.get_font_path(font_family, bold, italic)
        if font_path:
            try:
                font = ImageFont.truetype(font_path, font_size)
                logger.info(f"高级渲染器: 成功使用FontManager加载字体: {font_family} -> {font_path}")
                self.font_cache[cache_key] = font
                return font
            except Exception as e:
                logger.warning(f"高级渲染器: FontManager找到字体文件但加载失败 {font_path}: {e}")
        
        # If FontManager returns None (font doesn't support this style),
        # skip base font fallback and go directly to font substitution logic
        # This ensures we use Arial for unsupported styles (like YaHei italic)
        # rather than falling back to base font without styles
        
        # Fallback: Try hardcoded paths with font substitution logic
        font_paths = []
        
        # Build font paths based on style requirements WITH FONT SUBSTITUTION
        if font_family in ["Microsoft YaHei UI", "Microsoft YaHei", "微软雅黑"]:
            if bold and italic:
                # YaHei doesn't have bold+italic, use Arial bold italic as substitute
                font_paths.extend([
                    "C:/Windows/Fonts/arialbi.ttf", "arialbi.ttf",
                    "C:/Windows/Fonts/msyhbd.ttc", "msyhbd.ttc"
                ])
                logger.info(f"高级渲染器: 微软雅黑无粗斜体，尝试使用Arial粗斜体替代")
            elif bold:
                font_paths.extend(["C:/Windows/Fonts/msyhbd.ttc", "msyhbd.ttc"])
            elif italic:
                # CRITICAL: YaHei doesn't have separate italic, use Arial italic as fallback
                font_paths.extend([
                    "C:/Windows/Fonts/ariali.ttf", "ariali.ttf",  # Primary: Arial italic
                    "C:/Windows/Fonts/msyh.ttc", "msyh.ttc"       # Fallback: Base YaHei
                ])
                logger.info(f"高级渲染器: 微软雅黑无斜体，尝试使用Arial斜体替代")
            else:
                font_paths.extend(["C:/Windows/Fonts/msyh.ttc", "msyh.ttc"])
        elif font_family == "Arial":
            if bold and italic:
                font_paths.extend(["C:/Windows/Fonts/arialbi.ttf", "arialbi.ttf"])
            elif bold:
                font_paths.extend(["C:/Windows/Fonts/arialbd.ttf", "arialbd.ttf"])
            elif italic:
                font_paths.extend(["C:/Windows/Fonts/ariali.ttf", "ariali.ttf"])
            else:
                font_paths.extend(["C:/Windows/Fonts/arial.ttf", "arial.ttf"])
        elif font_family == "Times New Roman":
            if bold and italic:
                font_paths.extend(["C:/Windows/Fonts/timesbi.ttf", "timesbi.ttf"])
            elif bold:
                font_paths.extend(["C:/Windows/Fonts/timesbd.ttf", "timesbd.ttf"])
            elif italic:
                font_paths.extend(["C:/Windows/Fonts/timesi.ttf", "timesi.ttf"])
            else:
                font_paths.extend(["C:/Windows/Fonts/times.ttf", "times.ttf"])
        else:
            # For other fonts, try common patterns
            extensions = [".ttf", ".ttc", ".otf"]
            style_suffixes = []
            
            if bold and italic:
                style_suffixes = ["bi", "bd", "bold-italic", "bolditalic"]
            elif bold:
                style_suffixes = ["bd", "bold", "b"]
            elif italic:
                style_suffixes = ["i", "italic", "o"]
            
            # Font name mapping
            font_name_mapping = {
                "微软雅黑": "msyh",
                "宋体": "simsun",
                "黑体": "simhei",
                "楷体": "simkai",
                "仿宋": "simfang",
            }
            
            font_base = font_name_mapping.get(font_family, font_family.lower().replace(" ", ""))
            
            # Build paths
            for suffix in style_suffixes:
                for ext in extensions:
                    font_paths.append(f"C:/Windows/Fonts/{font_base}{suffix}{ext}")
                    font_paths.append(f"C:/Windows/Fonts/{font_base}_{suffix}{ext}")
            
            # If italic requested for Chinese font, add Arial italic as fallback
            if italic and font_family in ["宋体", "黑体", "楷体", "仿宋", "SimSun", "SimHei", "KaiTi", "FangSong"]:
                font_paths.extend([
                    "C:/Windows/Fonts/ariali.ttf", "ariali.ttf"
                ])
                logger.info(f"高级渲染器: {font_family}无斜体，尝试使用Arial斜体替代")
        
        # Fallback fonts
        font_paths.extend([
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/msyh.ttc",
            "arial.ttf",
            "calibri.ttf",
            "simsun.ttc",
            "msyh.ttc"
        ])
        
        font = None
        loaded_font_path = None
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, font_size)
                loaded_font_path = font_path
                logger.debug(f"高级渲染器: 成功加载字体: {font_path} (粗体:{bold}, 斜体:{italic})")
                break
            except (OSError, IOError):
                continue
        
        if font is None:
            logger.warning(f"高级渲染器: 无法加载字体 {font_family}，使用默认字体")
            font = ImageFont.load_default()
        else:
            # Log if we used a substitute font
            if loaded_font_path and "arial" in loaded_font_path.lower() and font_family not in ["Arial"]:
                logger.info(f"高级渲染器: 使用Arial字体替代 {font_family} 的样式变体")
        
        self.font_cache[cache_key] = font
        return font
    
    def _load_font(self, font_family: str, font_size: int, bold: bool, italic: bool) -> ImageFont.FreeTypeFont:
        """Legacy method - redirects to new implementation"""
        return self._load_font_with_style(font_family, font_size, bold, italic)
    
    def _adjust_position(self, position: Tuple[int, int], text_width: int, 
                        text_height: int, align: str) -> Tuple[int, int]:
        """调整文本位置基于对齐方式"""
        x, y = position
        
        if align == "center":
            x -= text_width // 2
        elif align == "right":
            x -= text_width
        
        return (x, y)
    
    def _create_text_layer(self, image_size: Tuple[int, int], text: str, 
                          font: ImageFont.FreeTypeFont, config: TextWatermarkConfig,
                          position: Tuple[int, int]) -> Image.Image:
        """创建带有效果的文本层"""
        logger.debug(f"高级渲染器: 创建文本层 - 阴影:{config.has_shadow}, 描边:{config.has_outline}")
        
        # Create transparent layer for text rendering
        text_layer = Image.new('RGBA', image_size, (0, 0, 0, 0))
        
        # Apply effects in the correct order
        if config.has_shadow:
            logger.debug(f"高级渲染器: 应用阴影效果")
            text_layer = self._apply_shadow_effect(text_layer, text, font, position, config)
        
        if config.has_outline:
            logger.debug(f"高级渲染器: 应用描边效果")
            text_layer = self._apply_outline_effect(text_layer, text, font, position, config)
        
        # Render main text on top at exact position
        # Create a fresh draw object AFTER effects to ensure correct association
        draw = ImageDraw.Draw(text_layer)
        color_with_alpha = (*config.color, int(255 * config.opacity))
        
        # Debug logging for font rendering
        logger.debug(f"渲染文本: '{text}' 使用字体: {font} 样式信息")
        
        draw.text(position, text, font=font, fill=color_with_alpha)
        
        return text_layer
    
    def _apply_shadow_effect(self, text_layer: Image.Image, text: str, 
                           font: ImageFont.FreeTypeFont, position: Tuple[int, int],
                           config: TextWatermarkConfig) -> Image.Image:
        """应用阴影效果"""
        draw = ImageDraw.Draw(text_layer)
        # Apply shadow at calculated offset position
        shadow_x = position[0] + config.shadow_offset[0]
        shadow_y = position[1] + config.shadow_offset[1]
        shadow_color = (*config.shadow_color, int(255 * config.shadow_opacity))
        
        # Draw shadow
        draw.text((shadow_x, shadow_y), text, font=font, fill=shadow_color)
        
        return text_layer
    
    def _apply_outline_effect(self, text_layer: Image.Image, text: str,
                            font: ImageFont.FreeTypeFont, position: Tuple[int, int],
                            config: TextWatermarkConfig) -> Image.Image:
        """应用描边效果"""
        logger.debug(f"高级渲染器: 开始应用描边效果 - 宽度:{config.outline_width}, 颜色:{config.outline_color}, 不透明度:{config.outline_opacity}")
        draw = ImageDraw.Draw(text_layer)
        outline_color = (*config.outline_color, int(255 * config.outline_opacity))
        
        # Draw outline by rendering text multiple times with slight offsets around exact position
        width = config.outline_width
        offset_count = 0
        for dx in range(-width, width + 1):
            for dy in range(-width, width + 1):
                if dx == 0 and dy == 0:
                    continue  # Skip center (will be drawn as main text)
                
                outline_x = position[0] + dx
                outline_y = position[1] + dy
                draw.text((outline_x, outline_y), text, font=font, fill=outline_color)
                offset_count += 1
        
        logger.debug(f"高级渲染器: 描边效果已应用 - 绘制了{offset_count}个偏移副本")
        return text_layer
    
    def _apply_glow_effect(self, text_layer: Image.Image, text: str,
                         font: ImageFont.FreeTypeFont, position: Tuple[int, int],
                         config: TextWatermarkConfig) -> Image.Image:
        """应用发光效果"""
        # Simple glow implementation
        draw = ImageDraw.Draw(text_layer)
        glow_color = (*config.glow_color, int(255 * config.glow_intensity))
        
        # Draw multiple offset copies for glow effect
        for offset in range(1, config.glow_radius + 1):
            for dx in [-offset, 0, offset]:
                for dy in [-offset, 0, offset]:
                    if dx == 0 and dy == 0:
                        continue
                    glow_x = position[0] + dx
                    glow_y = position[1] + dy
                    draw.text((glow_x, glow_y), text, font=font, fill=glow_color, spacing=config.letter_spacing)
        
        return text_layer
    
    def _apply_gradient_text(self, text_layer: Image.Image, text: str,
                           font: ImageFont.FreeTypeFont, position: Tuple[int, int],
                           config: TextWatermarkConfig) -> Image.Image:
        """应用渐变文本效果"""
        # Simplified gradient text - use solid color for now
        draw = ImageDraw.Draw(text_layer)
        color_with_alpha = (*config.gradient_start_color, int(255 * config.opacity))
        draw.text(position, text, font=font, fill=color_with_alpha, spacing=config.letter_spacing)
        
        return text_layer
    
    def _apply_emboss_effect(self, text_layer: Image.Image, text: str,
                           font: ImageFont.FreeTypeFont, position: Tuple[int, int],
                           config: TextWatermarkConfig) -> Image.Image:
        """应用浮雕效果"""
        draw = ImageDraw.Draw(text_layer)
        depth = config.emboss_depth
        
        # Draw shadow part (bottom-right)
        shadow_pos = (position[0] + depth, position[1] + depth)
        shadow_color = (*config.emboss_shadow_color, int(255 * config.opacity))
        draw.text(shadow_pos, text, font=font, fill=shadow_color, spacing=config.letter_spacing)
        
        # Draw highlight part (top-left)
        highlight_pos = (position[0] - depth, position[1] - depth)
        highlight_color = (*config.emboss_light_color, int(255 * config.opacity))
        draw.text(highlight_pos, text, font=font, fill=highlight_color, spacing=config.letter_spacing)
        
        return text_layer
    
    def _rotate_watermark(self, text_layer: Image.Image, rotation: float, 
                         center_pos: Tuple[int, int], text_width: int, text_height: int) -> Image.Image:
        """
        Rotate watermark around its center point
        Args:
            text_layer: Text layer image
            rotation: Rotation angle in degrees (positive = counter-clockwise)
            center_pos: Center position (x, y) of the watermark
            text_width: Width of the text
            text_height: Height of the text
        """
        if rotation == 0:
            return text_layer
        
        logger.debug(f"旋转水印: {rotation}°, 中心点: {center_pos}")
        
        # Extract the watermark region
        # Calculate the bounding box of the watermark
        x, y = center_pos
        left = max(0, x)
        top = max(0, y)
        right = min(text_layer.size[0], x + text_width)
        bottom = min(text_layer.size[1], y + text_height)
        
        # Extract the watermark region
        watermark_region = text_layer.crop((0, 0, text_layer.size[0], text_layer.size[1]))
        
        # Calculate center for rotation
        center_x = x + text_width // 2
        center_y = y + text_height // 2
        
        # Create a new transparent layer
        rotated_layer = Image.new('RGBA', text_layer.size, (0, 0, 0, 0))
        
        # Rotate the watermark region around its center
        # Note: PIL's rotate is counter-clockwise for positive angles
        rotated_watermark = watermark_region.rotate(
            rotation, 
            resample=Image.BICUBIC,
            expand=False,
            center=(center_x, center_y),
            fillcolor=(0, 0, 0, 0)
        )
        
        return rotated_watermark
    
    def _apply_transformations(self, text_layer: Image.Image, config: TextWatermarkConfig) -> Image.Image:
        """应用旋转和变形效果"""
        if config.text_rotation != 0:
            text_layer = text_layer.rotate(config.text_rotation, expand=True)
        
        return text_layer
    
    def get_text_dimensions(self, text: str, config: TextWatermarkConfig) -> Tuple[int, int]:
        """获取文本尺寸（用于布局计算）"""
        font = self._load_font(config.font_family, config.font_size, config.font_bold, config.font_italic)
        
        # Create temporary draw object for measurement
        temp_image = Image.new('RGB', (1, 1))
        temp_draw = ImageDraw.Draw(temp_image)
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        
        # Account for effects that might expand the text bounds
        if config.has_shadow:
            width += abs(config.shadow_offset[0]) + config.shadow_blur * 2
            height += abs(config.shadow_offset[1]) + config.shadow_blur * 2
        
        if config.has_outline:
            width += config.outline_width * 2
            height += config.outline_width * 2
        
        if config.has_glow:
            width += config.glow_radius * 2
            height += config.glow_radius * 2
        
        return (width, height)