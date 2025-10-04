"""
批量导出引擎
处理图片的批量导出操作
"""
try:
    from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QPixmap, QFontDatabase
except ImportError:
    print("PyQt5 is required but not installed.")
    raise

import os
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from models.watermark_config import WatermarkConfig
from core.advanced_text_renderer import AdvancedTextRenderer
from utils.logger import logger, log_exception
from utils.file_utils import FileUtils
from utils.font_manager import FontManager


class BatchExportEngine(QThread):
    """批量导出引擎"""
    
    # 信号定义
    progress_updated = pyqtSignal(int, str)  # 进度, 当前处理文件
    export_completed = pyqtSignal(dict)  # 完成信息
    error_occurred = pyqtSignal(str, str)  # 错误文件, 错误信息
    
    def __init__(self, image_list, watermark_config, export_config, parent=None):
        super().__init__(parent)
        
        self.image_list = image_list  # 图片列表
        self.watermark_config = watermark_config  # 水印配置
        self.export_config = export_config  # 导出配置
        
        self.is_cancelled = False
        self.mutex = QMutex()
        
        # 初始化高级文本渲染器用于高级效果
        self.advanced_text_renderer = AdvancedTextRenderer()
        
        # 统计信息
        self.stats = {
            'total': len(image_list),
            'processed': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': None,
            'end_time': None,
            'errors': []
        }
        
        logger.info(f"初始化批量导出引擎，共 {len(image_list)} 个文件")
    
    def cancel_export(self):
        """取消导出"""
        with QMutexLocker(self.mutex):
            self.is_cancelled = True
            logger.info("用户取消批量导出")
    
    @log_exception
    def run(self):
        """运行导出任务"""
        try:
            self.stats['start_time'] = datetime.now()
            logger.info("开始批量导出任务")
            
            # 准备输出目录
            output_dir = self.prepare_output_directory()
            if not output_dir:
                return
            
            # 处理每个图片文件
            for index, image_info in enumerate(self.image_list):
                # 检查是否被取消
                with QMutexLocker(self.mutex):
                    if self.is_cancelled:
                        logger.info("导出任务已取消")
                        return
                
                # 更新进度
                progress = int((index / len(self.image_list)) * 100)
                filename = os.path.basename(image_info.file_path)
                self.progress_updated.emit(progress, f"正在处理: {filename}")
                
                # 处理单个文件
                success = self.process_single_image(image_info, output_dir, index)
                
                if success:
                    self.stats['processed'] += 1
                else:
                    self.stats['failed'] += 1
                
                # 短暂延迟以避免界面冻结
                self.msleep(10)
            
            # 完成导出
            self.stats['end_time'] = datetime.now()
            self.progress_updated.emit(100, "导出完成")
            
            logger.info(f"批量导出完成: 成功 {self.stats['processed']}, 失败 {self.stats['failed']}")
            self.export_completed.emit(self.stats)
            
        except Exception as e:
            logger.error(f"批量导出过程中发生错误: {e}")
            self.error_occurred.emit("系统错误", str(e))
    
    @log_exception
    def prepare_output_directory(self):
        """准备输出目录"""
        try:
            output_dir = self.export_config['output_dir']
            
            # 如果需要创建子文件夹
            if self.export_config['create_subfolder']:
                output_dir = os.path.join(output_dir, "watermarked_images")
            
            # 确保目录存在
            FileUtils.ensure_directory_exists(output_dir)
            logger.debug(f"准备输出目录: {output_dir}")
            
            return output_dir
            
        except Exception as e:
            logger.error(f"准备输出目录失败: {e}")
            self.error_occurred.emit("目录错误", f"无法创建输出目录: {str(e)}")
            return None
    
    @log_exception
    def process_single_image(self, image_info, output_dir, index):
        """处理单个图片"""
        try:
            input_path = image_info.file_path
            
            # 生成输出文件名
            output_filename = self.generate_output_filename(input_path, index)
            output_path = os.path.join(output_dir, output_filename)
            
            # 检查文件是否已存在
            if os.path.exists(output_path) and not self.export_config['overwrite_existing']:
                logger.debug(f"跳过已存在文件: {output_path}")
                self.stats['skipped'] += 1
                return True
            
            # 加载并处理图片
            try:
                # 打开原始图片
                with Image.open(input_path) as original_image:
                    # 根据导出格式决定图片模式处理
                    if self.export_config['format'] == 'jpeg':
                        # JPEG不支持透明，统一转换为RGB
                        if original_image.mode in ('RGBA', 'LA', 'P'):
                            # 创建白色背景
                            rgb_image = Image.new('RGB', original_image.size, (255, 255, 255))
                            if original_image.mode == 'P':
                                original_image = original_image.convert('RGBA')
                            rgb_image.paste(original_image, mask=original_image.split()[-1] if original_image.mode in ('RGBA', 'LA') else None)
                            processed_image = rgb_image
                        elif original_image.mode == 'L':
                            # 灰度图转RGB
                            processed_image = original_image.convert('RGB')
                        else:
                            processed_image = original_image.copy()
                    else:
                        # PNG、TIFF等格式，统一转换为RGBA以支持透明通道
                        if original_image.mode != 'RGBA':
                            processed_image = original_image.convert('RGBA')
                        else:
                            processed_image = original_image.copy()
                    
                    # 先应用水印
                    watermarked_image = self.apply_watermark(processed_image, image_info)
                    
                    # 再应用图片尺寸缩放（如果启用），这样水印也会一起缩放
                    if self.export_config.get('enable_resize', False):
                        watermarked_image = self._resize_image(watermarked_image)
                    
                    # 保存图片
                    self.save_image(watermarked_image, output_path)
                    
                    logger.debug(f"成功处理图片: {input_path} -> {output_path}")
                    return True
                    
            except Exception as e:
                error_msg = f"处理图片失败: {str(e)}"
                logger.error(f"{input_path}: {error_msg}")
                self.stats['errors'].append({
                    'file': input_path,
                    'error': error_msg
                })
                self.error_occurred.emit(os.path.basename(input_path), error_msg)
                return False
                
        except Exception as e:
            logger.error(f"处理单个图片时发生未知错误: {e}")
            return False
    
    def generate_output_filename(self, input_path, index):
        """生成输出文件名"""
        original_name = os.path.splitext(os.path.basename(input_path))[0]
        original_ext = os.path.splitext(input_path)[1]
        
        # 确定输出扩展名
        if self.export_config['keep_original_format']:
            output_ext = original_ext
        else:
            output_ext = f".{self.export_config['format']}"
        
        # 根据命名模式生成新文件名
        naming_mode = self.export_config['naming_mode']
        
        if naming_mode == 'original':
            new_name = original_name
        elif naming_mode == 'prefix':
            prefix = self.export_config.get('prefix', 'watermarked_')
            new_name = prefix + original_name
        elif naming_mode == 'suffix':
            suffix = self.export_config.get('suffix', '_watermarked')
            new_name = original_name + suffix
        elif naming_mode == 'custom':
            pattern = self.export_config.get('custom_pattern', '{name}_watermarked')
            new_name = self.apply_custom_pattern(pattern, original_name, index)
        else:
            new_name = original_name + '_watermarked'
        
        # 生成安全的文件名
        safe_filename = FileUtils.get_safe_filename(new_name + output_ext)
        return safe_filename
    
    def apply_custom_pattern(self, pattern, original_name, index):
        """应用自定义命名模式"""
        now = datetime.now()
        
        # 替换模式变量
        result = pattern.replace('{name}', original_name)
        result = result.replace('{index}', str(index + 1).zfill(3))
        result = result.replace('{date}', now.strftime('%Y%m%d'))
        result = result.replace('{time}', now.strftime('%H%M%S'))
        result = result.replace('{year}', now.strftime('%Y'))
        result = result.replace('{month}', now.strftime('%m'))
        result = result.replace('{day}', now.strftime('%d'))
        
        return result
    
    def _resize_image(self, image: Image.Image) -> Image.Image:
        """根据配置缩放图片"""
        try:
            resize_mode = self.export_config.get('resize_mode', 0)
            resize_value = self.export_config.get('resize_value', 100)
            
            original_width, original_height = image.size
            
            if resize_mode == 0:  # 按百分比缩放
                scale = resize_value / 100.0
                new_width = int(original_width * scale)
                new_height = int(original_height * scale)
                logger.info(f"批量导出: 按百分比缩放 {resize_value}% - {original_width}x{original_height} -> {new_width}x{new_height}")
                
            elif resize_mode == 1:  # 指定最长边
                max_side = resize_value
                if original_width >= original_height:
                    scale = max_side / original_width
                else:
                    scale = max_side / original_height
                new_width = int(original_width * scale)
                new_height = int(original_height * scale)
                logger.info(f"批量导出: 按最长边缩放 {max_side}px - {original_width}x{original_height} -> {new_width}x{new_height}")
                
            elif resize_mode == 2:  # 指定宽度
                new_width = resize_value
                scale = new_width / original_width
                new_height = int(original_height * scale)
                logger.info(f"批量导出: 按宽度缩放 {resize_value}px - {original_width}x{original_height} -> {new_width}x{new_height}")
                
            else:  # 指定高度
                new_height = resize_value
                scale = new_height / original_height
                new_width = int(original_width * scale)
                logger.info(f"批量导出: 按高度缩放 {resize_value}px - {original_width}x{original_height} -> {new_width}x{new_height}")
            
            # 确保尺寸至少为1x1
            new_width = max(1, new_width)
            new_height = max(1, new_height)
            
            # 使用高质量的Lanczos重采样算法
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            return resized_image
            
        except Exception as e:
            logger.error(f"缩放图片失败: {e}")
            return image
    
    @log_exception
    def apply_watermark(self, image, image_info):
        """应用水印到图片"""
        try:
            # 确保图片是RGBA模式以支持透明通道
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # 创建画布
            draw = ImageDraw.Draw(image)
            
            # 获取图片尺寸
            img_width, img_height = image.size
            
            # 应用文本水印
            if (self.watermark_config.watermark_type.value == 'text' or 
                self.watermark_config.watermark_type.value == 'both') and self.watermark_config.text_config.text:
                image = self.apply_text_watermark(draw, image, img_width, img_height)
            
            # 应用图片水印
            if (self.watermark_config.watermark_type.value == 'image' or 
                self.watermark_config.watermark_type.value == 'both') and \
                self.watermark_config.image_config.image_path and \
                os.path.exists(self.watermark_config.image_config.image_path):
                image = self.apply_image_watermark(image, img_width, img_height)
            
            return image
            
        except Exception as e:
            logger.error(f"应用水印失败: {e}")
            # 如果水印应用失败，返回原图
            return image
    
    def apply_text_watermark(self, draw, image, img_width, img_height):
        """应用文本水印（支持旋转和自定义位置，使用AdvancedTextRenderer支持高级效果）"""
        try:
            text = self.watermark_config.text_config.text
            text_config = self.watermark_config.text_config
            
            # 计算字体大小
            font_size = max(12, text_config.font_size)
            
            # 获取字体样式配置
            font_family = text_config.font_family
            font_bold = text_config.font_bold
            font_italic = text_config.font_italic
            
            logger.info(f"批量导出: 应用文本水印 - 图片尺寸({img_width}x{img_height}), 文本:'{text}', 字体:{font_family}, 大小:{font_size}, 粗体:{font_bold}, 斜体:{font_italic}")
            logger.info(f"批量导出: 效果设置 - 阴影:{text_config.has_shadow}, 描边:{text_config.has_outline}")
            logger.info(f"批量导出: 位置设置: {self.watermark_config.position}, custom_x={self.watermark_config.custom_x}, custom_y={self.watermark_config.custom_y}")
            
            # 检查是否需要使用高级渲染器（有高级效果或样式字体）
            has_advanced_effects = text_config.has_shadow or text_config.has_outline
            has_styled_font = font_bold or font_italic
            use_advanced_renderer = has_advanced_effects or has_styled_font
            
            if use_advanced_renderer:
                logger.info(f"批量导出: 使用高级渲染器 - 阴影:{text_config.has_shadow}, 描边:{text_config.has_outline}, 样式字体:{has_styled_font}")
                
                # 加载字体获取文本尺寸
                font = self._load_styled_font(font_family, font_size, font_bold, font_italic)
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # 计算位置
                position = self.calculate_text_position(
                    img_width, img_height, text_width, text_height
                )
                
                logger.info(f"批量导出: 文本尺寸({text_width}x{text_height}), 最终位置({position[0]},{position[1]})")
                
                # 使用AdvancedTextRenderer渲染（它会处理所有效果和旋转）
                return self.advanced_text_renderer.render_text_with_effects(
                    image, text_config, position, text, self.watermark_config.rotation
                )
            else:
                # 简单文本，使用基础渲染
                logger.info(f"批量导出: 使用基础渲染器")
                
                font = self._load_styled_font(font_family, font_size, font_bold, font_italic)
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                position = self.calculate_text_position(
                    img_width, img_height, text_width, text_height
                )
                
                logger.info(f"批量导出: 文本尺寸({text_width}x{text_height}), 最终位置({position[0]},{position[1]})")
                
                # 简单绘制（支持旋转）
                rotation = self.watermark_config.rotation
                if rotation != 0.0:
                    text_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
                    text_draw = ImageDraw.Draw(text_layer)
                    
                    color_with_opacity = (*text_config.color, int(255 * text_config.opacity))
                    text_draw.text(position, text, font=font, fill=color_with_opacity)
                    
                    center_x = position[0] + text_width // 2
                    center_y = position[1] + text_height // 2
                    text_layer = text_layer.rotate(rotation, center=(center_x, center_y), expand=False)
                    
                    image.paste(text_layer, (0, 0), text_layer)
                    return image
                else:
                    color_with_opacity = (*text_config.color, int(255 * text_config.opacity))
                    draw.text(position, text, font=font, fill=color_with_opacity)
                    return image
            
        except Exception as e:
            logger.error(f"应用文本水印失败: {e}")
            return image
    
    def calculate_text_position(self, img_width, img_height, text_width, text_height):
        """计算文本位置（支持自定义位置）"""
        # 使用配置中的边距
        margin_x = self.watermark_config.margin_x
        margin_y = self.watermark_config.margin_y
        
        positions = {
            'top_left': (margin_x, margin_y),
            'top_center': ((img_width - text_width) // 2, margin_y),
            'top_right': (img_width - text_width - margin_x, margin_y),
            'center_left': (margin_x, (img_height - text_height) // 2),
            'center': ((img_width - text_width) // 2, (img_height - text_height) // 2),
            'center_right': (img_width - text_width - margin_x, (img_height - text_height) // 2),
            'bottom_left': (margin_x, img_height - text_height - margin_y),
            'bottom_center': ((img_width - text_width) // 2, img_height - text_height - margin_y),
            'bottom_right': (img_width - text_width - margin_x, img_height - text_height - margin_y),
            'custom': (self.watermark_config.custom_x, self.watermark_config.custom_y)
        }
        
        return positions.get(self.watermark_config.position.value, positions['bottom_right'])
    
    def apply_image_watermark(self, base_image, img_width, img_height):
        """应用图片水印（支持旋转和自定义位置）"""
        try:
            # 打开水印图片
            with Image.open(self.watermark_config.image_config.image_path) as watermark:
                # 转换为RGBA模式
                if watermark.mode != 'RGBA':
                    watermark = watermark.convert('RGBA')
                
                # 计算水印尺寸 - 使用配置的缩放
                wm_size = int(min(img_width, img_height) * 0.2)  # 默认20%大小
                
                # 保持宽高比调整水印大小
                wm_ratio = watermark.width / watermark.height
                if wm_ratio > 1:
                    wm_width = int(wm_size * self.watermark_config.image_config.scale)
                    wm_height = int(wm_size / wm_ratio * self.watermark_config.image_config.scale)
                else:
                    wm_width = int(wm_size * wm_ratio * self.watermark_config.image_config.scale)
                    wm_height = int(wm_size * self.watermark_config.image_config.scale)
                
                watermark = watermark.resize((wm_width, wm_height), Image.Resampling.LANCZOS)
                
                # 调整透明度，保留现有alpha通道
                opacity = self.watermark_config.image_config.opacity
                if opacity < 1.0:
                    alpha = watermark.split()[-1]
                    # 将现有alpha乘以不透明度因子（0-1范围）
                    alpha = alpha.point(lambda x: int(x * opacity))
                    watermark.putalpha(alpha)
                
                # 应用旋转
                if self.watermark_config.rotation != 0:
                    watermark = watermark.rotate(
                        self.watermark_config.rotation,
                        resample=Image.BICUBIC,
                        expand=True,
                        fillcolor=(0, 0, 0, 0)
                    )
                    # 更新尺寸
                    wm_width, wm_height = watermark.size
                
                # 计算位置
                wm_position = self.calculate_image_position(
                    img_width, img_height, wm_width, wm_height
                )
                
                # 粘贴水印
                if base_image.mode != 'RGBA':
                    base_image = base_image.convert('RGBA')
                
                base_image.paste(watermark, wm_position, watermark)
                
                return base_image
                
        except Exception as e:
            logger.error(f"应用图片水印失败: {e}")
            return base_image
    
    def calculate_image_position(self, img_width, img_height, wm_width, wm_height):
        """计算图片水印位置（支持自定义位置）"""
        # 使用配置中的边距
        margin_x = self.watermark_config.margin_x
        margin_y = self.watermark_config.margin_y
        
        positions = {
            'top_left': (margin_x, margin_y),
            'top_center': ((img_width - wm_width) // 2, margin_y),
            'top_right': (img_width - wm_width - margin_x, margin_y),
            'center_left': (margin_x, (img_height - wm_height) // 2),
            'center': ((img_width - wm_width) // 2, (img_height - wm_height) // 2),
            'center_right': (img_width - wm_width - margin_x, (img_height - wm_height) // 2),
            'bottom_left': (margin_x, img_height - wm_height - margin_y),
            'bottom_center': ((img_width - wm_width) // 2, img_height - wm_height - margin_y),
            'bottom_right': (img_width - wm_width - margin_x, img_height - wm_height - margin_y),
            'custom': (self.watermark_config.custom_x, self.watermark_config.custom_y)
        }
        
        return positions.get(self.watermark_config.position.value, positions['bottom_right'])
    
    @log_exception
    def save_image(self, image, output_path):
        """保存图片"""
        try:
            # 根据格式保存
            format_type = self.export_config['format']
            
            if format_type == 'jpeg':
                # JPEG不支持透明，转换为RGB
                if image.mode in ('RGBA', 'LA'):
                    rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                    rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                    image = rgb_image
                
                image.save(output_path, 'JPEG', 
                          quality=self.export_config['quality'],
                          optimize=True)
                          
            elif format_type == 'png':
                image.save(output_path, 'PNG', optimize=True)
                
            elif format_type == 'bmp':
                # BMP不支持透明，转换为RGB
                if image.mode in ('RGBA', 'LA'):
                    rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                    rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                    image = rgb_image
                image.save(output_path, 'BMP')
                
            elif format_type == 'tiff':
                image.save(output_path, 'TIFF', compression='lzw')
            
            logger.debug(f"图片保存成功: {output_path}")
            
        except Exception as e:
            logger.error(f"保存图片失败 {output_path}: {e}")
            raise
    
    def _load_styled_font(self, font_family: str, font_size: int, bold: bool = False, italic: bool = False):
        """加载字体，支持粗体和斜体样式"""
        
        # 首先尝试使用FontManager获取字体路径（最可靠的方法）
        font_path = FontManager.get_font_path(font_family, bold, italic)
        if font_path:
            try:
                font = ImageFont.truetype(font_path, font_size)
                logger.debug(f"成功使用FontManager加载字体: {font_family} -> {font_path}")
                return font
            except Exception as e:
                logger.warning(f"FontManager找到字体文件但加载失败 {font_path}: {e}")
        
        # 如果FontManager失败，尝试使用QFontDatabase
        font_paths = []
        try:
            font_db = QFontDatabase()
            # 检查字体是否存在
            if font_family in font_db.families():
                # 尝试直接使用字体名称让PIL加载
                # PIL在Windows上可以直接使用字体名称
                try:
                    # 构建字体样式字符串
                    style_parts = []
                    if bold:
                        style_parts.append("Bold")
                    if italic:
                        style_parts.append("Italic")
                    
                    # 尝试使用完整的字体名称（包含样式）
                    if style_parts:
                        full_font_name = f"{font_family} {' '.join(style_parts)}"
                        font = ImageFont.truetype(full_font_name, font_size)
                        logger.debug(f"成功使用字体名称加载: {full_font_name}")
                        return font
                    else:
                        font = ImageFont.truetype(font_family, font_size)
                        logger.debug(f"成功使用字体名称加载: {font_family}")
                        return font
                except (OSError, IOError):
                    pass
        except Exception as e:
            logger.debug(f"QFontDatabase加载字体失败: {e}")
        
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
        
        # 获取字体文件基础名
        font_base = font_name_mapping.get(font_family, font_family.lower().replace(" ", ""))
        
        # 根据样式构建字体路径
        if font_family in ["Microsoft YaHei UI", "Microsoft YaHei", "微软雅黑"]:
            if bold and italic:
                font_paths.extend(["C:/Windows/Fonts/arialbi.ttf", "C:/Windows/Fonts/msyhbd.ttc", "msyhbd.ttc"])
            elif bold:
                font_paths.extend(["C:/Windows/Fonts/msyhbd.ttc", "msyhbd.ttc"])
            elif italic:
                font_paths.extend(["C:/Windows/Fonts/ariali.ttf", "C:/Windows/Fonts/msyh.ttc", "msyh.ttc"])
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
            extensions = [".ttf", ".ttc", ".otf"]
            style_suffixes = []
            
            if bold and italic:
                style_suffixes = ["bi", "bd", "bold-italic", "bolditalic", "z"]
            elif bold:
                style_suffixes = ["bd", "bold", "b"]
            elif italic:
                style_suffixes = ["i", "italic", "o"]
            else:
                style_suffixes = [""]
            
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
                logger.debug(f"批量导出加载字体: {font_path} (字体:{font_family}, 粗体:{bold}, 斜体:{italic})")
                return font
            except (OSError, IOError):
                continue
        
        logger.warning(f"无法加载字体 {font_family}，使用默认字体")
        return ImageFont.load_default()