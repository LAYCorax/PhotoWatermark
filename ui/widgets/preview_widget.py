"""
Preview Widget
Displays image preview with watermark overlay
"""
import os
from typing import Optional

try:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
        QFrame, QSizePolicy, QSlider, QSpinBox
    )
    from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QRectF
    from PyQt5.QtGui import QPixmap, QFont, QPainter, QColor, QPen, QImage
except ImportError:
    print("PyQt5 is required but not installed.")
    raise

from PIL import Image, ImageDraw, ImageFont
from models.watermark_config import WatermarkConfig, WatermarkType, WatermarkPosition
from utils.logger import logger, log_exception
import os


class PreviewGraphicsView(QGraphicsView):
    """Custom graphics view for image preview with zoom and pan"""
    
    def __init__(self):
        super().__init__()
        
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Configure view
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Image item
        self.image_item = None
        self.watermark_overlay = None
        
        # Zoom settings
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
    
    @log_exception
    def set_image(self, image_path: str):
        """Set image to preview with large image handling"""
        logger.debug(f"PreviewGraphicsView设置图片: {os.path.basename(image_path)}")
        
        self.scene.clear()
        self.image_item = None
        self.watermark_overlay = None
        
        if not os.path.exists(image_path):
            logger.error(f"预览图片文件不存在: {image_path}")
            return
        
        try:
            # 检查文件大小
            file_size = os.path.getsize(image_path)
            logger.debug(f"图片文件大小: {file_size/1024/1024:.2f}MB")
            
            # Load image using PIL with memory-conscious approach
            with Image.open(image_path) as pil_img:
                original_size = pil_img.size
                total_pixels = original_size[0] * original_size[1]
                logger.debug(f"原始图片尺寸: {original_size}, 像素数: {total_pixels/1e6:.1f}MP")
                
                # 对于超大图片，使用更保守的缩放策略
                max_preview_pixels = 1920 * 1080  # 更保守的预览像素数 (2MP)
                if total_pixels > max_preview_pixels:
                    # 计算缩放比例
                    scale = (max_preview_pixels / total_pixels) ** 0.5
                    new_size = (int(original_size[0] * scale), int(original_size[1] * scale))
                    logger.info(f"大图片预览缩放: {original_size} -> {new_size} (缩放比例: {scale:.3f})")
                    
                    # 使用渐进式缩放以避免内存问题
                    try:
                        # 首先尝试高质量缩放
                        pil_img = pil_img.resize(new_size, Image.Resampling.LANCZOS)
                    except (MemoryError, OSError) as e:
                        logger.warning(f"高质量缩放失败: {e}, 使用快速缩放")
                        pil_img = pil_img.resize(new_size, Image.Resampling.BILINEAR)
                
                # 转换为QPixmap
                pixmap = self.pil_to_qpixmap(pil_img)
                
            if not pixmap.isNull():
                logger.debug(f"QPixmap创建成功: {pixmap.width()}x{pixmap.height()}")
                self.image_item = self.scene.addPixmap(pixmap)
                self.scene.setSceneRect(QRectF(pixmap.rect()))
                self.fit_in_view()
                logger.debug("预览图片设置成功")
            else:
                logger.error("QPixmap创建失败")
                raise Exception("QPixmap创建失败")
                
        except Exception as e:
            logger.error(f"PIL加载图片失败: {str(e)}")
            print(f"Error loading image for preview: {e}")
            
            # Fallback to Qt's native loading with size check
            try:
                logger.debug("尝试Qt原生加载")
                pixmap = QPixmap(image_path)
                
                if not pixmap.isNull():
                    # 检查Qt加载的图片尺寸
                    if pixmap.width() * pixmap.height() > 1920 * 1080 * 2:
                        # 如果太大，缩放它
                        max_size = 1920
                        if pixmap.width() > pixmap.height():
                            pixmap = pixmap.scaledToWidth(max_size, Qt.SmoothTransformation)
                        else:
                            pixmap = pixmap.scaledToHeight(max_size, Qt.SmoothTransformation)
                        logger.info(f"Qt加载后缩放: {pixmap.width()}x{pixmap.height()}")
                    
                    self.image_item = self.scene.addPixmap(pixmap)
                    self.scene.setSceneRect(QRectF(pixmap.rect()))
                    self.fit_in_view()
                    logger.info("Qt原生加载成功")
                else:
                    logger.error("Qt原生加载也失败")
                    
            except Exception as e2:
                logger.error(f"Qt原生加载也失败: {str(e2)}")
                print(f"Fallback image loading also failed: {e2}")
    
    def clear_image(self):
        """Clear the current image"""
        self.scene.clear()
        self.image_item = None
        self.watermark_overlay = None
    
    def fit_in_view(self):
        """Fit image in view"""
        if self.image_item:
            self.fitInView(self.image_item, Qt.KeepAspectRatio)
            self.zoom_factor = 1.0
    
    def zoom_in(self):
        """Zoom in"""
        if self.zoom_factor < self.max_zoom:
            self.scale(1.25, 1.25)
            self.zoom_factor *= 1.25
    
    def zoom_out(self):
        """Zoom out"""
        if self.zoom_factor > self.min_zoom:
            self.scale(0.8, 0.8)
            self.zoom_factor *= 0.8
    
    def reset_zoom(self):
        """Reset zoom to fit"""
        if self.image_item:
            self.resetTransform()
            self.fit_in_view()
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming"""
        if event.modifiers() == Qt.ControlModifier:
            # Zoom with mouse wheel
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)
    
    def update_watermark_overlay(self, config: WatermarkConfig, image_path: str):
        """Update watermark overlay"""
        if not self.image_item or not image_path:
            return
        
        try:
            # Generate watermarked image
            watermarked_pixmap = self.generate_watermarked_preview(image_path, config)
            if watermarked_pixmap:
                self.scene.clear()
                self.image_item = self.scene.addPixmap(watermarked_pixmap)
                self.scene.setSceneRect(QRectF(watermarked_pixmap.rect()))
        except Exception as e:
            print(f"Error updating watermark overlay: {e}")
    
    @log_exception
    def generate_watermarked_preview(self, image_path: str, config: WatermarkConfig) -> Optional[QPixmap]:
        """Generate preview with watermark applied"""
        try:
            logger.info(f"开始生成水印预览: {os.path.basename(image_path)}")
            logger.debug(f"预览图片路径: {image_path}")
            logger.debug(f"水印配置: 类型={config.watermark_type}, 位置={config.position}")
            
            # Load original image with size constraints
            logger.debug("加载原始图片")
            with Image.open(image_path) as img:
                # Check image size and resize if too large for preview
                original_size = img.size
                logger.debug(f"原始图片尺寸: {original_size[0]}x{original_size[1]}")
                
                max_preview_size = (1920, 1080)  # Maximum preview resolution
                if img.size[0] > max_preview_size[0] or img.size[1] > max_preview_size[1]:
                    logger.info(f"图片尺寸超过预览限制，需要缩放: {original_size} -> 适合尺寸")
                    # Calculate scale factor to fit within max size
                    scale_x = max_preview_size[0] / img.size[0]
                    scale_y = max_preview_size[1] / img.size[1]
                    scale = min(scale_x, scale_y)
                    new_size = (int(img.size[0] * scale), int(img.size[1] * scale))
                    logger.debug(f"缩放比例: {scale:.3f}, 新尺寸: {new_size[0]}x{new_size[1]}")
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                    logger.debug("图片缩放完成")
                else:
                    logger.debug("图片尺寸在预览范围内，无需缩放")
                
                # Preserve the original image format and color profile
                original_mode = img.mode
                logger.debug(f"原始颜色模式: {original_mode}")
                
                # Only convert if absolutely necessary
                if original_mode in ('L', 'P', 'CMYK'):
                    # Convert grayscale, palette, or CMYK to RGB
                    if 'transparency' in img.info:
                        logger.debug(f"转换 {original_mode} 到 RGBA (包含透明度)")
                        img = img.convert('RGBA')
                    else:
                        logger.debug(f"转换 {original_mode} 到 RGB")
                        img = img.convert('RGB')
                elif original_mode == 'LA':
                    # Convert grayscale with alpha to RGBA
                    logger.debug("转换 LA 到 RGBA")
                    img = img.convert('RGBA')
                else:
                    logger.debug(f"保持原始颜色模式: {original_mode}")
                
                # Create a copy for watermarking
                logger.debug("创建图片副本用于水印处理")
                preview_img = img.copy()
                
                # Apply watermark based on type
                if config.watermark_type == WatermarkType.TEXT:
                    logger.debug("应用文本水印到预览图")
                    preview_img = self.apply_text_watermark(preview_img, config)
                elif config.watermark_type == WatermarkType.IMAGE:
                    logger.debug("应用图片水印到预览图")
                    preview_img = self.apply_image_watermark(preview_img, config)
                else:
                    logger.warning(f"未知的水印类型: {config.watermark_type}")
                
                # Convert PIL image to QPixmap
                logger.debug("转换PIL图片为QPixmap")
                result_pixmap = self.pil_to_qpixmap(preview_img)
                
                if result_pixmap:
                    logger.info(f"水印预览生成成功: {result_pixmap.width()}x{result_pixmap.height()}")
                else:
                    logger.error("水印预览生成失败: QPixmap转换失败")
                
                return result_pixmap
                
        except Exception as e:
            logger.error(f"生成水印预览失败: {str(e)}")
            print(f"Error generating watermarked preview: {e}")
            return None
    
    @log_exception
    def apply_text_watermark(self, img: Image.Image, config: WatermarkConfig) -> Image.Image:
        """Apply text watermark to image"""
        logger.debug(f"开始应用文本水印: '{config.text_config.text}'")
        draw = ImageDraw.Draw(img)
        text = config.text_config.text
        logger.debug(f"水印文本: '{text}', 字体大小: {config.text_config.font_size}")
        
        # Try to load font with multiple fallbacks
        font = None
        font_paths = [
            config.text_config.font_family,
            "arial.ttf",
            "Arial",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/msyh.ttc"
        ]
        
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, config.text_config.font_size)
                break
            except (OSError, IOError):
                continue
        
        if font is None:
            font = ImageFont.load_default()
        
        # Get text dimensions
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except (AttributeError, TypeError):
            # Fallback for older Pillow versions
            try:
                text_width, text_height = font.getsize(text)
            except AttributeError:
                # Ultimate fallback
                text_width, text_height = len(text) * config.text_config.font_size // 2, config.text_config.font_size
        
        # Calculate position
        img_width, img_height = img.size
        x, y = self.calculate_watermark_position(
            img_width, img_height, text_width, text_height, config
        )
        
        # Apply text color with opacity
        color = config.text_config.color
        alpha = int(config.text_config.opacity * 255)
        text_color = (*color, alpha)
        
        # Optimize for large images: use local overlay instead of full-size
        # Calculate padding for the text area
        padding = max(20, config.text_config.font_size // 4)
        overlay_width = text_width + padding * 2
        overlay_height = text_height + padding * 2
        
        # Ensure overlay doesn't exceed image bounds
        overlay_width = min(overlay_width, img.size[0])
        overlay_height = min(overlay_height, img.size[1])
        
        try:
            # Create small overlay only for text area
            overlay = Image.new('RGBA', (overlay_width, overlay_height), (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            # Draw text on small overlay (adjust coordinates)
            text_x = padding
            text_y = padding
            overlay_draw.text((text_x, text_y), text, font=font, fill=text_color)
            
            # Composite small overlay onto main image
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Paste the small overlay at the calculated position
            # Adjust position to account for overlay padding
            paste_x = max(0, min(x - padding, img.size[0] - overlay_width))
            paste_y = max(0, min(y - padding, img.size[1] - overlay_height))
            
            img.paste(overlay, (paste_x, paste_y), overlay)
            
        except MemoryError:
            print(f"Memory error with overlay size {overlay_width}x{overlay_height}, falling back to direct drawing")
            # Fallback: draw directly on image (no transparency effects)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            draw = ImageDraw.Draw(img)
            # Use RGB color instead of RGBA
            rgb_color = color[:3]  # Remove alpha channel
            draw.text((x, y), text, font=font, fill=rgb_color)
        
        # Only convert back to RGB if the original was RGB
        # This preserves transparency for RGBA images
        if img.mode == 'RGBA' and 'transparency' not in img.info:
            # Check if there's actual transparency
            alpha = img.split()[-1]
            if alpha.getextrema()[0] == 255:  # No transparency
                img = img.convert('RGB')
        
        return img
    
    def apply_image_watermark(self, img: Image.Image, config: WatermarkConfig) -> Image.Image:
        """Apply image watermark to image with memory optimization"""
        if not config.image_config.image_path or not os.path.exists(config.image_config.image_path):
            return img
        
        try:
            with Image.open(config.image_config.image_path) as watermark_img:
                # Check memory constraints for large watermarks
                max_watermark_pixels = 2000 * 2000  # 4MP limit for watermark
                watermark_pixels = watermark_img.width * watermark_img.height
                
                if watermark_pixels > max_watermark_pixels:
                    # Pre-resize watermark to reasonable size
                    scale_factor = (max_watermark_pixels / watermark_pixels) ** 0.5
                    temp_size = (
                        int(watermark_img.width * scale_factor),
                        int(watermark_img.height * scale_factor)
                    )
                    watermark_img = watermark_img.resize(temp_size, Image.Resampling.LANCZOS)
                
                # Scale watermark according to config
                scale = config.image_config.scale
                new_size = (
                    int(watermark_img.width * scale),
                    int(watermark_img.height * scale)
                )
                
                # Ensure final watermark size is reasonable
                max_final_size = min(img.size[0] // 2, img.size[1] // 2, 1000)
                if new_size[0] > max_final_size or new_size[1] > max_final_size:
                    aspect_ratio = watermark_img.width / watermark_img.height
                    if aspect_ratio > 1:
                        new_size = (max_final_size, int(max_final_size / aspect_ratio))
                    else:
                        new_size = (int(max_final_size * aspect_ratio), max_final_size)
                
                watermark_img = watermark_img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Calculate position
                img_width, img_height = img.size
                wm_width, wm_height = watermark_img.size
                x, y = self.calculate_watermark_position(
                    img_width, img_height, wm_width, wm_height, config
                )
                
                # Memory-efficient compositing
                try:
                    # Apply opacity
                    if watermark_img.mode != 'RGBA':
                        watermark_img = watermark_img.convert('RGBA')
                    
                    # Adjust opacity
                    alpha = int(config.image_config.opacity * 255)
                    # Create alpha channel efficiently
                    alpha_channel = Image.new('L', watermark_img.size, alpha)
                    watermark_img.putalpha(alpha_channel)
                    
                    # Composite with proper alpha handling
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    
                    # Use paste with alpha mask for proper blending
                    img.paste(watermark_img, (x, y), watermark_img)
                    
                    # Only convert back to RGB if original was RGB and no transparency
                    if img.mode == 'RGBA':
                        alpha = img.split()[-1]
                        if alpha.getextrema()[0] == 255:  # No transparency
                            img = img.convert('RGB')
                            
                except MemoryError:
                    print("Memory error during watermark compositing, using simpler method")
                    # Fallback to simple paste without transparency
                    if watermark_img.mode == 'RGBA':
                        watermark_img = watermark_img.convert('RGB')
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img.paste(watermark_img, (x, y))
                
        except MemoryError:
            print(f"Memory error loading watermark image: {config.image_config.image_path}")
        except Exception as e:
            print(f"Error applying image watermark: {e}")
        
        return img
    
    def calculate_watermark_position(self, img_w: int, img_h: int, wm_w: int, wm_h: int, 
                                   config: WatermarkConfig) -> tuple:
        """Calculate watermark position"""
        margin_x = config.margin_x
        margin_y = config.margin_y
        
        if config.position == WatermarkPosition.TOP_LEFT:
            return (margin_x, margin_y)
        elif config.position == WatermarkPosition.TOP_CENTER:
            return ((img_w - wm_w) // 2, margin_y)
        elif config.position == WatermarkPosition.TOP_RIGHT:
            return (img_w - wm_w - margin_x, margin_y)
        elif config.position == WatermarkPosition.CENTER_LEFT:
            return (margin_x, (img_h - wm_h) // 2)
        elif config.position == WatermarkPosition.CENTER:
            return ((img_w - wm_w) // 2, (img_h - wm_h) // 2)
        elif config.position == WatermarkPosition.CENTER_RIGHT:
            return (img_w - wm_w - margin_x, (img_h - wm_h) // 2)
        elif config.position == WatermarkPosition.BOTTOM_LEFT:
            return (margin_x, img_h - wm_h - margin_y)
        elif config.position == WatermarkPosition.BOTTOM_CENTER:
            return ((img_w - wm_w) // 2, img_h - wm_h - margin_y)
        elif config.position == WatermarkPosition.BOTTOM_RIGHT:
            return (img_w - wm_w - margin_x, img_h - wm_h - margin_y)
        elif config.position == WatermarkPosition.CUSTOM:
            return (config.custom_x, config.custom_y)
        else:
            return (margin_x, img_h - wm_h - margin_y)  # Default to bottom-left
    
    @log_exception
    @log_exception
    def set_image_from_pil(self, pil_image: Image.Image) -> bool:
        """Set image from PIL Image object with memory management"""
        logger.debug(f"Setting preview from PIL Image: {pil_image.size} ({pil_image.mode})")
        
        self.scene.clear()
        self.image_item = None
        self.watermark_overlay = None
        
        try:
            original_size = pil_image.size
            total_pixels = original_size[0] * original_size[1]
            logger.debug(f"原始图片尺寸: {original_size}, 像素数: {total_pixels/1e6:.1f}MP")
            
            # 对于超大图片，使用更保守的缩放策略
            max_preview_pixels = 1920 * 1080  # 更保守的预览像素数 (2MP)
            if total_pixels > max_preview_pixels:
                # 计算缩放比例
                scale = (max_preview_pixels / total_pixels) ** 0.5
                new_size = (int(original_size[0] * scale), int(original_size[1] * scale))
                logger.info(f"大图片预览缩放: {original_size} -> {new_size} (缩放比例: {scale:.3f})")
                
                # 使用渐进式缩放以避免内存问题
                try:
                    # 首先尝试高质量缩放
                    pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
                except (MemoryError, OSError) as e:
                    logger.warning(f"高质量缩放失败: {e}, 使用快速缩放")
                    pil_image = pil_image.resize(new_size, Image.Resampling.BILINEAR)
            
            # 转换为QPixmap
            pixmap = self.pil_to_qpixmap(pil_image)
            
            if not pixmap.isNull():
                logger.debug(f"QPixmap创建成功: {pixmap.width()}x{pixmap.height()}")
                self.image_item = self.scene.addPixmap(pixmap)
                self.scene.setSceneRect(QRectF(pixmap.rect()))
                self.fit_in_view()
                logger.debug("预览图片设置成功")
                return True
            else:
                logger.error("QPixmap创建失败")
                return False
                
        except MemoryError as e:
            logger.error(f"内存不足，无法加载图片到预览: {e}")
            return False
        except Exception as e:
            logger.error(f"预览图片设置失败: {e}")
            return False

    def pil_to_qpixmap(self, pil_image: Image.Image) -> QPixmap:
        """Convert PIL image to QPixmap with memory management"""
        try:
            width, height = pil_image.size
            total_pixels = width * height
            logger.debug(f"Converting PIL image to QPixmap: {width}x{height} ({total_pixels:,} pixels)")
            
            # Ultra-aggressive scaling for maximum system compatibility
            # This system appears to have severe Qt conversion limitations
            max_safe_pixels = 1_000_000  # 1MP ultra-safe limit
            if total_pixels > max_safe_pixels:
                scale_factor = (max_safe_pixels / total_pixels) ** 0.5
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                logger.info(f"Ultra-aggressive scaling for system stability: {width}x{height} -> {new_width}x{new_height}")
                
                # Use the most reliable PIL scaling method with multiple fallbacks
                scaling_methods = [
                    ("BILINEAR", Image.BILINEAR),
                    ("NEAREST", Image.NEAREST),
                    ("BOX", Image.BOX)
                ]
                
                scaled_successfully = False
                for method_name, method in scaling_methods:
                    try:
                        logger.debug(f"Attempting PIL scaling with {method_name}")
                        pil_image = pil_image.resize((new_width, new_height), method)
                        logger.debug(f"PIL scaling with {method_name} completed successfully")
                        scaled_successfully = True
                        break
                    except Exception as e:
                        logger.warning(f"PIL scaling with {method_name} failed: {e}")
                        continue
                
                if not scaled_successfully:
                    logger.error("All PIL scaling methods failed, using emergency fallback")
                    # Emergency fallback: create a very small placeholder
                    pil_image = Image.new('RGB', (800, 600), color='lightgray')
                    new_width, new_height = 800, 600
                
                width, height = new_width, new_height
            
            # Convert image to appropriate format
            logger.debug(f"Converting PIL image mode: {pil_image.mode}")
            if pil_image.mode == 'RGBA':
                # For RGBA images, convert to Format_RGBA8888_Premultiplied for better quality
                logger.debug("Converting RGBA image to QImage")
                img_data = pil_image.tobytes('raw', 'RGBA')
                qimg = QImage(img_data, width, height, QImage.Format_RGBA8888)
            elif pil_image.mode == 'RGB':
                # For RGB images, keep the original channel order
                logger.debug("Converting RGB image to QImage")
                img_data = pil_image.tobytes('raw', 'RGB')
                logger.debug(f"Created RGB data of size: {len(img_data)} bytes")
                qimg = QImage(img_data, width, height, QImage.Format_RGB888)
                logger.debug("QImage created from RGB data")
            else:
                # Convert other formats to RGB first
                logger.debug(f"Converting {pil_image.mode} to RGB for QPixmap")
                rgb_img = pil_image.convert('RGB')
                img_data = rgb_img.tobytes('raw', 'RGB')
                qimg = QImage(img_data, width, height, QImage.Format_RGB888)
            
            # Validate QImage before conversion
            logger.debug("Validating QImage")
            if qimg.isNull():
                logger.error("Failed to create QImage - image is null")
                return QPixmap()
            
            logger.debug(f"QImage is valid: {qimg.width()}x{qimg.height()}")
            
            # Ultra-conservative QPixmap conversion with progressive fallbacks
            logger.debug("Converting QImage to QPixmap")
            
            # Progressive size reduction until we find something that works
            fallback_sizes = [
                (qimg.width(), qimg.height()),  # Original (should be ~1MP)
                (800, 600),                     # Smaller fallback
                (640, 480),                     # Even smaller
                (400, 300),                     # Very small
            ]
            
            for attempt, (target_w, target_h) in enumerate(fallback_sizes):
                try:
                    # Scale the QImage if needed
                    if attempt > 0:
                        logger.warning(f"QPixmap conversion attempt {attempt+1}: trying {target_w}x{target_h}")
                        qimg_scaled = qimg.scaled(target_w, target_h, Qt.KeepAspectRatio, Qt.FastTransformation)
                    else:
                        qimg_scaled = qimg
                        logger.debug(f"QPixmap conversion attempt {attempt+1}: using original {qimg_scaled.width()}x{qimg_scaled.height()}")
                    
                    # Attempt the conversion
                    pixmap = QPixmap.fromImage(qimg_scaled)
                    
                    if not pixmap.isNull():
                        logger.debug(f"QPixmap conversion successful on attempt {attempt+1}: {pixmap.width()}x{pixmap.height()}")
                        return pixmap
                    else:
                        logger.warning(f"QPixmap conversion attempt {attempt+1} produced null result")
                        
                except Exception as e:
                    logger.warning(f"QPixmap conversion attempt {attempt+1} failed: {e}")
                    continue
            
            # If all attempts failed, create a basic colored placeholder
            logger.error("All QPixmap conversion attempts failed, creating basic placeholder")
            fallback_pixmap = QPixmap(400, 300)
            fallback_pixmap.fill(Qt.lightGray)
            return fallback_pixmap
            
        except MemoryError as e:
            logger.error(f"Memory error converting PIL image to QPixmap: {e}")
            return QPixmap()
        except Exception as e:
            logger.error(f"Error converting PIL image to QPixmap: {e}")
            return QPixmap()


class PreviewWidget(QWidget):
    """Main preview widget with controls"""
    
    def __init__(self):
        super().__init__()
        
        self.current_image_path = None
        self.current_config = None
        
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel("预览")
        title_label.setStyleSheet("""
            QLabel {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC", "SimHei", "黑体", sans-serif;
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 8px;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Zoom controls
        zoom_label = QLabel("缩放:")
        header_layout.addWidget(zoom_label)
        
        self.zoom_out_btn = QPushButton("-")
        self.zoom_out_btn.setFixedSize(25, 30)
        header_layout.addWidget(self.zoom_out_btn)
        
        self.zoom_fit_btn = QPushButton("适应")
        self.zoom_fit_btn.setFixedSize(40, 30)
        header_layout.addWidget(self.zoom_fit_btn)
        
        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setFixedSize(25, 30)
        header_layout.addWidget(self.zoom_in_btn)
        
        layout.addLayout(header_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("color: #ddd;")
        layout.addWidget(separator)
        
        # Preview area
        self.preview_view = PreviewGraphicsView()
        self.preview_view.setStyleSheet("""
            QGraphicsView {
                border: 1px solid #ddd;
                border-radius: 3px;
                background-color: #f8f8f8;
            }
        """)
        layout.addWidget(self.preview_view)
        
        # Status label
        self.status_label = QLabel("选择图片以查看预览")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #888; padding: 10px;")
        layout.addWidget(self.status_label)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.zoom_in_btn.clicked.connect(self.preview_view.zoom_in)
        self.zoom_out_btn.clicked.connect(self.preview_view.zoom_out)
        self.zoom_fit_btn.clicked.connect(self.preview_view.reset_zoom)
    
    @log_exception
    def set_image(self, image_path: str):
        """Set image for preview"""
        logger.info(f"设置预览图片: {os.path.basename(image_path)}")
        logger.debug(f"预览图片路径: {image_path}")
        
        self.current_image_path = image_path
        self.preview_view.set_image(image_path)
        
        # Update status
        filename = os.path.basename(image_path)
        self.status_label.setText(f"预览: {filename}")
        logger.debug(f"预览状态更新: {filename}")
        
        # Update watermark if config is available
        if self.current_config:
            self.update_watermark_preview()
    
    @log_exception
    def set_watermark_config(self, config: WatermarkConfig):
        """Set watermark configuration"""
        logger.debug(f"设置水印配置: 类型={config.watermark_type}, 位置={config.position}")
        self.current_config = config
        self.update_watermark_preview()
    
    @log_exception
    def update_watermark_preview(self):
        """Update watermark preview"""
        logger.debug("更新水印预览")
        if self.current_image_path and self.current_config:
            logger.debug(f"当前预览图片: {os.path.basename(self.current_image_path)}")
            logger.debug(f"水印配置: 类型={self.current_config.watermark_type}")
            self.preview_view.update_watermark_overlay(self.current_config, self.current_image_path)
        else:
            logger.debug("无法更新水印预览: 缺少图片或配置")
    
    def clear(self):
        """Clear preview"""
        self.current_image_path = None
        self.current_config = None
        self.preview_view.clear_image()
        self.status_label.setText("选择图片以查看预览")