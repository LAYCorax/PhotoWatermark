"""
水印处理引擎
专门处理大图片水印，优化内存使用
"""
import os
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
from models.watermark_config import WatermarkConfig, WatermarkType, WatermarkPosition
from core.advanced_text_renderer import AdvancedTextRenderer
from utils.logger import logger, log_exception, log_performance
from utils.font_manager import FontManager


class WatermarkEngine:
    """水印处理引擎，优化大图片处理"""
    
    def __init__(self):
        logger.info("初始化水印引擎...")
        self.max_image_dimension = 8000  # 最大单边尺寸
        self.max_overlay_size = 1000 * 1000  # 降低最大overlay像素数
        self.memory_conservative_mode = False
        self.ultra_conservative_mode = False  # 超保守模式，针对大文件
        self.advanced_text_renderer = AdvancedTextRenderer()  # Advanced text effects renderer
        logger.debug(f"水印引擎参数: max_dimension={self.max_image_dimension}, max_overlay={self.max_overlay_size}")
    
    @log_performance
    def process_image(self, image_path: str, config: WatermarkConfig, 
                     output_path: Optional[str] = None) -> Optional[str]:
        """
        处理图片添加水印
        
        Args:
            image_path: 输入图片路径
            config: 水印配置
            output_path: 输出路径，如果为None则覆盖原文件
            
        Returns:
            处理后的图片路径，失败返回None
        """
        logger.info(f"开始处理图片: {os.path.basename(image_path)}")
        logger.debug(f"输入路径: {image_path}")
        logger.debug(f"输出路径: {output_path}")
        logger.debug(f"水印类型: {config.watermark_type}")
        
        try:
            # 检查文件是否存在
            if not os.path.exists(image_path):
                logger.error(f"输入文件不存在: {image_path}")
                return None
            
            # 打开图片并检查尺寸
            logger.debug("打开图片文件进行处理")
            with Image.open(image_path) as img:
                original_size = img.size
                logger.info(f"图片尺寸: {original_size[0]}x{original_size[1]} 像素")
                print(f"处理图片: {original_size[0]}x{original_size[1]} 像素")
                
                # 检查是否需要启用内存保守模式
                total_pixels = original_size[0] * original_size[1]
                file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
                
                logger.debug(f"图片信息: {total_pixels/1e6:.1f}MP, {file_size_mb:.1f}MB")
                
                if total_pixels > 25 * 1024 * 1024 or file_size_mb > 5.0:  # 25MP以上或5MB以上
                    self.ultra_conservative_mode = True
                    self.memory_conservative_mode = True
                    logger.info(f"启用超保守模式 (像素: {total_pixels/1e6:.1f}MP, 文件: {file_size_mb:.1f}MB)")
                elif total_pixels > 15 * 1024 * 1024:  # 15MP以上
                    self.memory_conservative_mode = True
                    logger.info(f"启用内存保守模式 (像素: {total_pixels/1e6:.1f}MP)")
                else:
                    logger.debug("使用标准处理模式")
                
                # 预处理大图片以节省内存
                if self.ultra_conservative_mode:
                    img = self._preprocess_large_image(img)
                
                # 处理图片
                processed_img = self._apply_watermark(img, config)
                
                if processed_img is None:
                    return None
                
                # 确定输出路径
                if output_path is None:
                    base, ext = os.path.splitext(image_path)
                    output_path = f"{base}_watermarked{ext}"
                
                # 保存图片
                logger.info(f"保存处理后的图片: {output_path}")
                self._save_image(processed_img, output_path, original_size)
                logger.info(f"水印图片已成功保存: {output_path}")
                print(f"✓ 水印图片已保存: {output_path}")
                
                return output_path
                
        except Exception as e:
            logger.error(f"水印处理失败: {e}")
            print(f"水印处理失败: {e}")
            return None
    
    @log_exception
    def _apply_watermark(self, img: Image.Image, config: WatermarkConfig) -> Optional[Image.Image]:
        """应用水印到图片"""
        try:
            logger.debug(f"开始应用水印: {config.watermark_type}")
            
            if config.watermark_type == WatermarkType.TEXT:
                logger.debug(f"应用文本水印: '{config.text_config.text}'")
                return self._apply_text_watermark_optimized(img, config)
            elif config.watermark_type == WatermarkType.IMAGE:
                logger.debug(f"应用图片水印: {config.image_config.image_path}")
                return self._apply_image_watermark_optimized(img, config)
            else:
                logger.warning(f"未知的水印类型: {config.watermark_type}")
                return img
        except Exception as e:
            logger.error(f"应用水印失败: {e}")
            return None
    
    @log_exception
    def _apply_text_watermark_optimized(self, img: Image.Image, config: WatermarkConfig) -> Image.Image:
        """优化的文本水印处理"""
        try:
            logger.info(f"导出: 开始应用文本水印 - 原图尺寸: {img.size[0]}x{img.size[1]}")
            text_config = config.text_config
            text = text_config.text
            logger.info(f"导出: 水印文本: '{text}', 字体: {text_config.font_family}, 大小: {text_config.font_size}, 粗体: {text_config.font_bold}, 斜体: {text_config.font_italic}")
            logger.info(f"导出: 水印位置: {config.position}, custom_x={config.custom_x}, custom_y={config.custom_y}")
            
            # Check if advanced effects are enabled
            has_advanced_effects = (
                text_config.has_shadow or
                text_config.has_outline
            )
            
            # Also use advanced renderer for styled fonts (bold, italic, or both) to ensure proper rendering
            # This is critical: AdvancedTextRenderer has fallback logic for fonts that don't have italic/bold variants
            has_styled_font = (
                text_config.font_bold or 
                text_config.font_italic
            )
            
            # IMPORTANT: Always use advanced renderer for styled fonts OR effects
            # This ensures font fallback logic (e.g., Arial italic for fonts without italic) is applied
            use_advanced_renderer = has_advanced_effects or has_styled_font
            
            if use_advanced_renderer:
                if has_styled_font and not has_advanced_effects:
                    logger.info(f"导出: 使用高级渲染器处理样式字体（含字体回退机制） - 粗体:{text_config.font_bold}, 斜体:{text_config.font_italic}")
                else:
                    logger.info(f"导出: 使用高级文本效果渲染器 - 阴影:{text_config.has_shadow}, 描边:{text_config.has_outline}")
                
                # Load font first to get accurate text dimensions
                font = self._load_font(text_config.font_family, text_config.font_size, text_config.font_bold, text_config.font_italic)
                
                # Get accurate text dimensions
                temp_img = Image.new('RGB', (1, 1))
                temp_draw = ImageDraw.Draw(temp_img)
                try:
                    bbox = temp_draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                except (AttributeError, TypeError):
                    try:
                        text_width, text_height = font.getsize(text)
                    except AttributeError:
                        text_width = len(text) * text_config.font_size // 2
                        text_height = text_config.font_size
                
                # Calculate position using accurate dimensions
                x, y = self._calculate_position(
                    img.size[0], img.size[1], text_width, text_height, config
                )
                logger.info(f"导出: 文本尺寸({text_width}x{text_height}), 最终位置({x},{y})")
                
                # Use advanced renderer - it has proper font fallback logic
                return self.advanced_text_renderer.render_text_with_effects(
                    img, text_config, (x, y), text, config.rotation
                )
            
            # Fallback to original rendering for simple text or conservative mode
            logger.info(f"导出: 使用基础文本渲染 - 粗体:{config.text_config.font_bold}, 斜体:{config.text_config.font_italic}")
            # 加载字体
            logger.debug(f"加载字体: {config.text_config.font_family}, 大小: {config.text_config.font_size}, 粗体: {config.text_config.font_bold}, 斜体: {config.text_config.font_italic}")
            font = self._load_font(config.text_config.font_family, config.text_config.font_size, config.text_config.font_bold, config.text_config.font_italic)
            
            # 获取文本尺寸
            temp_img = Image.new('RGB', (1, 1))
            temp_draw = ImageDraw.Draw(temp_img)
            
            try:
                bbox = temp_draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except (AttributeError, TypeError):
                try:
                    text_width, text_height = font.getsize(text)
                except AttributeError:
                    text_width = len(text) * config.text_config.font_size // 2
                    text_height = config.text_config.font_size
            
            # 计算位置
            x, y = self._calculate_position(
                img.size[0], img.size[1], text_width, text_height, config
            )
            
            logger.info(f"导出: 文本尺寸({text_width}x{text_height}), 最终位置({x},{y})")
            
            # 选择渲染模式
            if self.ultra_conservative_mode:
                logger.info("使用超保守直接绘制模式")
                return self._draw_text_direct(img, text, font, (x, y), config.text_config)
            elif self.memory_conservative_mode:
                logger.info("使用保守绘制模式")
                return self._draw_text_direct(img, text, font, (x, y), config.text_config)
            else:
                logger.debug("使用高质量overlay模式")
                return self._draw_text_with_overlay(img, text, font, (x, y), text_width, text_height, config.text_config)
                
        except Exception as e:
            print(f"文本水印处理失败: {e}")
            logger.error(f"文本水印处理失败: {e}")
            return img
    
    def _draw_text_direct(self, img: Image.Image, text: str, font: ImageFont.FreeTypeFont,
                         position: Tuple[int, int], text_config) -> Image.Image:
        """直接绘制文本（内存保守模式）"""
        try:
            # 确保图片模式适合直接绘制
            original_mode = img.mode
            if img.mode not in ('RGB', 'RGBA'):
                if img.mode in ('L', 'P'):
                    img = img.convert('RGB')
                else:
                    img = img.convert('RGB')
            
            # 创建绘制对象
            draw = ImageDraw.Draw(img)
            
            # 使用RGB颜色（忽略透明度以节省内存）
            color = text_config.color[:3]  # 只取RGB，忽略alpha
            
            # 绘制文本
            draw.text(position, text, font=font, fill=color)
            
            # 如果原始是RGB模式，确保返回RGB（避免意外转换为RGBA）
            if original_mode == 'RGB' and img.mode != 'RGB':
                img = img.convert('RGB')
            
            return img
            
        except Exception as e:
            print(f"直接文本绘制失败: {e}")
            return img
    
    def _draw_text_with_overlay(self, img: Image.Image, text: str, font: ImageFont.FreeTypeFont,
                               position: Tuple[int, int], text_width: int, text_height: int,
                               text_config) -> Image.Image:
        """使用overlay绘制文本（高质量模式）"""
        try:
            x, y = position
            
            # 计算overlay尺寸
            padding = max(10, text_config.font_size // 8)
            overlay_width = min(text_width + padding * 2, img.size[0])
            overlay_height = min(text_height + padding * 2, img.size[1])
            
            # 检查overlay大小
            if overlay_width * overlay_height > self.max_overlay_size:
                print("Overlay太大，使用直接绘制模式")
                return self._draw_text_direct(img, text, font, position, text_config)
            
            # 创建小的overlay
            overlay = Image.new('RGBA', (overlay_width, overlay_height), (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            # 在overlay上绘制文本
            text_x = padding
            text_y = padding
            alpha = int(text_config.opacity * 255)
            text_color = (*text_config.color, alpha)
            overlay_draw.text((text_x, text_y), text, font=font, fill=text_color)
            
            # 合成到主图像
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # 计算粘贴位置
            paste_x = max(0, min(x - padding, img.size[0] - overlay_width))
            paste_y = max(0, min(y - padding, img.size[1] - overlay_height))
            
            img.paste(overlay, (paste_x, paste_y), overlay)
            
            return img
            
        except MemoryError:
            print("内存不足，回退到直接绘制")
            return self._draw_text_direct(img, text, font, position, text_config)
        except Exception as e:
            print(f"Overlay文本绘制失败: {e}")
            return self._draw_text_direct(img, text, font, position, text_config)
    
    def _apply_image_watermark_optimized(self, img: Image.Image, config: WatermarkConfig) -> Image.Image:
        """优化的图片水印处理"""
        try:
            watermark_path = config.image_config.image_path
            if not os.path.exists(watermark_path):
                return img
            
            with Image.open(watermark_path) as watermark_img:
                # 限制水印图片大小
                max_wm_size = min(img.size[0] // 3, img.size[1] // 3, 800)
                
                if watermark_img.size[0] > max_wm_size or watermark_img.size[1] > max_wm_size:
                    watermark_img.thumbnail((max_wm_size, max_wm_size), Image.Resampling.LANCZOS)
                
                # 应用缩放
                scale = config.image_config.scale
                new_size = (
                    int(watermark_img.size[0] * scale),
                    int(watermark_img.size[1] * scale)
                )
                watermark_img = watermark_img.resize(new_size, Image.Resampling.LANCZOS)
                
                # 计算位置
                x, y = self._calculate_position(
                    img.size[0], img.size[1], 
                    watermark_img.size[0], watermark_img.size[1], 
                    config
                )
                
                # 合成图片
                if self.memory_conservative_mode:
                    # 简单粘贴，不使用透明度
                    if watermark_img.mode == 'RGBA':
                        watermark_img = watermark_img.convert('RGB')
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img.paste(watermark_img, (x, y))
                else:
                    # 高质量合成
                    original_img_mode = img.mode
                    
                    if watermark_img.mode != 'RGBA':
                        watermark_img = watermark_img.convert('RGBA')
                    
                    # 应用透明度，保留现有alpha通道
                    opacity = config.image_config.opacity
                    if opacity < 1.0:
                        # 获取现有alpha通道
                        r, g, b, a = watermark_img.split()
                        # 将现有alpha乘以不透明度因子
                        a = a.point(lambda x: int(x * opacity))
                        # 合并回去
                        watermark_img = Image.merge('RGBA', (r, g, b, a))
                    
                    # 应用旋转
                    if config.rotation != 0:
                        watermark_img = watermark_img.rotate(
                            config.rotation,
                            resample=Image.BICUBIC,
                            expand=True,
                            fillcolor=(0, 0, 0, 0)
                        )
                        # 重新计算位置
                        x, y = self._calculate_position(
                            img.size[0], img.size[1],
                            watermark_img.size[0], watermark_img.size[1],
                            config
                        )
                    
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    
                    img.paste(watermark_img, (x, y), watermark_img)
                    
                    # 如果原始图片是RGB，在合成后检查是否需要转回RGB
                    if original_img_mode == 'RGB' and img.mode == 'RGBA':
                        # 检查是否有实际透明度
                        alpha_channel = img.split()[-1]
                        if alpha_channel.getextrema()[0] == 255:  # 完全不透明
                            img = img.convert('RGB')
                
                return img
                
        except Exception as e:
            print(f"图片水印处理失败: {e}")
            return img
    
    def _load_font(self, font_family: str, font_size: int, bold: bool = False, italic: bool = False) -> ImageFont.FreeTypeFont:
        """加载字体，支持粗体和斜体 - 使用FontManager确保与预览一致"""
        logger.debug(f"导出: 加载字体 {font_family}, 大小:{font_size}, 粗体:{bold}, 斜体:{italic}")
        
        # 首先尝试使用FontManager获取字体路径（与预览保持一致）
        font_path = FontManager.get_font_path(font_family, bold, italic)
        if font_path:
            try:
                font = ImageFont.truetype(font_path, font_size)
                logger.info(f"导出: 成功使用FontManager加载字体: {font_family} -> {font_path}")
                return font
            except Exception as e:
                logger.warning(f"导出: FontManager找到字体文件但加载失败 {font_path}: {e}")
        
        # 如果没有样式需求，再次尝试查找基础字体
        if (bold or italic) and font_path is None:
            font_path = FontManager.get_font_path(font_family, False, False)
            if font_path:
                try:
                    font = ImageFont.truetype(font_path, font_size)
                    logger.warning(f"导出: 使用基础字体替代样式字体: {font_family} -> {font_path}")
                    return font
                except Exception as e:
                    logger.warning(f"导出: 基础字体加载失败 {font_path}: {e}")
        
        # Fallback: 尝试常见字体路径（保持原有逻辑作为备用）
        font_paths = []
        
        # Build font paths based on style requirements
        if font_family in ["Microsoft YaHei UI", "Microsoft YaHei", "微软雅黑"]:
            if bold and italic:
                # For bold+italic combination, try Arial bold italic first, then YaHei bold
                font_paths.extend(["C:/Windows/Fonts/arialbi.ttf", "arialbi.ttf", "C:/Windows/Fonts/msyhbd.ttc", "msyhbd.ttc"])
            elif bold:
                font_paths.extend(["C:/Windows/Fonts/msyhbd.ttc", "msyhbd.ttc"])
            elif italic:
                # YaHei doesn't have separate italic, use Arial italic as fallback
                font_paths.extend(["C:/Windows/Fonts/ariali.ttf", "C:/Windows/Fonts/msyh.ttc", "msyh.ttc", "ariali.ttf"])
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
            # 通用字体加载策略
            # 尝试多种可能的文件扩展名和粗体/斜体变体
            extensions = [".ttf", ".ttc", ".otf"]
            style_suffixes = []
            
            if bold and italic:
                style_suffixes = ["bi", "bd", "bold-italic", "bolditalic", "z"]  # z是粗体的另一种命名
            elif bold:
                style_suffixes = ["bd", "bold", "b"]
            elif italic:
                style_suffixes = ["i", "italic", "o"]
            else:
                style_suffixes = [""]
            
            # 字体名称映射表（中文名到文件名）
            font_name_mapping = {
                "微软雅黑": "msyh",
                "宋体": "simsun",
                "黑体": "simhei",
                "楷体": "simkai",
                "仿宋": "simfang",
                "Microsoft YaHei": "msyh",
                "Microsoft YaHei UI": "msyh",
                "SimSun": "simsun",
                "SimHei": "simhei",
                "KaiTi": "simkai",
                "FangSong": "simfang",
            }
            
            font_base = font_name_mapping.get(font_family, font_family.lower().replace(" ", ""))
            
            # 组合字体路径
            for suffix in style_suffixes:
                for ext in extensions:
                    if suffix:
                        font_paths.append(f"C:/Windows/Fonts/{font_base}{suffix}{ext}")
                        font_paths.append(f"C:/Windows/Fonts/{font_base}_{suffix}{ext}")
                        font_paths.append(f"C:/Windows/Fonts/{font_base}-{suffix}{ext}")
                    else:
                        font_paths.append(f"C:/Windows/Fonts/{font_base}{ext}")
            
            # 尝试直接使用字体名称
            for ext in extensions:
                font_paths.append(f"C:/Windows/Fonts/{font_family}{ext}")
                font_paths.append(f"C:/Windows/Fonts/{font_family.replace(' ', '')}{ext}")
        
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
        
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, font_size)
                logger.debug(f"导出: 成功加载字体: {font_path} (粗体:{bold}, 斜体:{italic})")
                return font
            except (OSError, IOError):
                continue
        
        logger.warning(f"导出: 无法加载字体 {font_family}，使用默认字体")
        return ImageFont.load_default()
    
    def _calculate_position(self, img_w: int, img_h: int, wm_w: int, wm_h: int,
                          config: WatermarkConfig) -> Tuple[int, int]:
        """计算水印位置"""
        margin_x = config.margin_x
        margin_y = config.margin_y
        
        position_map = {
            WatermarkPosition.TOP_LEFT: (margin_x, margin_y),
            WatermarkPosition.TOP_CENTER: ((img_w - wm_w) // 2, margin_y),
            WatermarkPosition.TOP_RIGHT: (img_w - wm_w - margin_x, margin_y),
            WatermarkPosition.CENTER_LEFT: (margin_x, (img_h - wm_h) // 2),
            WatermarkPosition.CENTER: ((img_w - wm_w) // 2, (img_h - wm_h) // 2),
            WatermarkPosition.CENTER_RIGHT: (img_w - wm_w - margin_x, (img_h - wm_h) // 2),
            WatermarkPosition.BOTTOM_LEFT: (margin_x, img_h - wm_h - margin_y),
            WatermarkPosition.BOTTOM_CENTER: ((img_w - wm_w) // 2, img_h - wm_h - margin_y),
            WatermarkPosition.BOTTOM_RIGHT: (img_w - wm_w - margin_x, img_h - wm_h - margin_y),
            WatermarkPosition.CUSTOM: (config.custom_x, config.custom_y),
        }
        
        return position_map.get(config.position, (margin_x, img_h - wm_h - margin_y))
    
    def _preprocess_large_image(self, img: Image.Image) -> Image.Image:
        """预处理大图片以优化内存使用"""
        try:
            print("预处理大图片...")
            
            # 如果图片过大，先进行质量优化但保持尺寸
            # 这里主要是优化图片的内部结构而不是尺寸
            if img.mode == 'RGBA':
                # 检查是否真的需要Alpha通道
                alpha_channel = img.split()[-1]
                if alpha_channel.getextrema() == (255, 255):  # 完全不透明
                    print("移除不必要的Alpha通道")
                    img = img.convert('RGB')
            
            # 对于超大图片，使用内存映射模式
            if hasattr(img, '_getexif'):
                # 清除不必要的EXIF数据以节省内存
                img.info.pop('exif', None)
            
            return img
            
        except Exception as e:
            print(f"预处理失败，使用原图: {e}")
            return img
    
    def _save_image(self, img: Image.Image, output_path: str, original_size: Tuple[int, int]):
        """保存图片"""
        try:
            # 确保输出格式与颜色模式兼容
            output_format = self._get_output_format(output_path)
            
            # 根据输出格式调整颜色模式
            if output_format in ('JPEG', 'JPG'):
                # JPEG不支持透明度，必须转换为RGB
                if img.mode in ('RGBA', 'LA', 'P'):
                    if img.mode == 'RGBA':
                        # 创建白色背景合成RGBA
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[-1] if len(img.split()) == 4 else None)
                        img = background
                    else:
                        img = img.convert('RGB')
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
            elif output_format == 'PNG':
                # PNG支持透明度，保持原有模式或转换为RGBA
                if img.mode not in ('RGB', 'RGBA', 'L', 'LA'):
                    img = img.convert('RGBA')
            else:
                # 其他格式，安全转换为RGB
                if img.mode != 'RGB':
                    if img.mode == 'RGBA':
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[-1])
                        img = background
                    else:
                        img = img.convert('RGB')
            
            # 根据原始图片大小调整保存质量
            total_pixels = original_size[0] * original_size[1]
            if total_pixels > 50 * 1024 * 1024:  # 50MP以上
                quality = 85
                optimize = True
            elif total_pixels > 20 * 1024 * 1024:  # 20MP以上
                quality = 90
                optimize = True
            else:
                quality = 95
                optimize = False
            
            # 保存图片
            if output_format in ('JPEG', 'JPG'):
                img.save(output_path, 'JPEG', quality=quality, optimize=optimize)
            elif output_format == 'PNG':
                img.save(output_path, 'PNG', optimize=optimize)
            else:
                # 默认使用JPEG格式
                img.save(output_path, 'JPEG', quality=quality, optimize=optimize)
                
        except Exception as e:
            logger.error(f"保存图片失败: {e}")
            logger.error(f"图片模式: {img.mode}, 输出路径: {output_path}")
            logger.error(f"图片尺寸: {img.size}")
            raise
    
    def _get_output_format(self, output_path: str) -> str:
        """获取输出文件格式"""
        ext = os.path.splitext(output_path.lower())[1]
        format_map = {
            '.jpg': 'JPEG',
            '.jpeg': 'JPEG', 
            '.png': 'PNG',
            '.bmp': 'BMP',
            '.tiff': 'TIFF',
            '.tif': 'TIFF'
        }
        return format_map.get(ext, 'JPEG')  # 默认JPEG