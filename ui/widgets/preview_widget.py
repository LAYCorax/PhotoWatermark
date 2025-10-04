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
from core.advanced_text_renderer import AdvancedTextRenderer
from utils.logger import logger, log_exception
from utils.font_manager import FontManager
import os
try:
    from PyQt5.QtGui import QFontDatabase
except ImportError:
    QFontDatabase = None


class PreviewGraphicsView(QGraphicsView):
    """Custom graphics view for image preview with zoom and pan"""
    
    # Signal for watermark position change
    watermark_position_changed = pyqtSignal(int, int)
    
    def __init__(self):
        super().__init__()
        
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Configure view
        self.setDragMode(QGraphicsView.NoDrag)  # Handle drag manually
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Image item
        self.image_item = None
        self.watermark_overlay = None
        
        # Advanced text renderer
        self.advanced_text_renderer = AdvancedTextRenderer()
        
        # Zoom settings
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        
        # Drag mode for watermark positioning
        self.is_dragging_watermark = False
        self.drag_start_pos = None
        self.current_config = None
        self.current_image_path = None
        
        # 性能优化方案：智能预览 + 精确映射
        self.original_image_size = None  # 原图尺寸
        self.preview_image_size = None   # 预览图尺寸
        self.preview_scale_ratio = 1.0   # 预览缩放比例（用于坐标映射）
        
        # 性能优化参数 - 优化为1K分辨率以获得最佳性能
        self.MAX_PREVIEW_PIXELS = 1920 * 1080  # 1K分辨率，最优性能
        self.PERFORMANCE_THRESHOLD = 1920 * 1080  # 1K以上启用优化
        
        # Enable mouse tracking
        self.setMouseTracking(True)
        
        # 性能优化的缓存系统
        self._original_cache = {}  # 原图缓存
        self._preview_cache = {}   # 预览图缓存
        self._cache_max_size = 2   # 限制缓存大小
    
    @log_exception
    def set_image(self, image_path: str):
        """Set image to preview with intelligent performance optimization"""
        logger.info(f"预览: 智能加载图片 {os.path.basename(image_path)}")
        
        self.scene.clear()
        self.image_item = None
        self.watermark_overlay = None
        
        if not os.path.exists(image_path):
            logger.error(f"预览图片文件不存在: {image_path}")
            return
        
        try:
            # 首先获取原图信息
            with Image.open(image_path) as pil_img:
                self.original_image_size = pil_img.size
                total_pixels = self.original_image_size[0] * self.original_image_size[1]
                logger.info(f"预览: 原图尺寸 {self.original_image_size[0]}x{self.original_image_size[1]} ({total_pixels/1e6:.1f}MP)")
                
                # 智能预览策略决策
                if total_pixels > self.PERFORMANCE_THRESHOLD:
                    # 大图片：使用性能优化预览
                    preview_img, scale_ratio = self._create_performance_preview(pil_img)
                    self.preview_scale_ratio = scale_ratio
                    self.preview_image_size = preview_img.size
                    logger.info(f"预览: 性能优化 - 预览尺寸 {preview_img.size[0]}x{preview_img.size[1]}, 缩放比例 {scale_ratio:.3f}")
                else:
                    # 小图片：直接使用原图
                    preview_img = pil_img.copy()
                    self.preview_scale_ratio = 1.0
                    self.preview_image_size = self.original_image_size
                    logger.info(f"预览: 直接使用原图 无需优化")
                
                # 缓存原图和预览图
                self._add_to_cache(image_path, pil_img.copy(), preview_img.copy())
            
            # 转换为QPixmap
            pixmap = self.pil_to_qpixmap(preview_img)
                
            if not pixmap.isNull():
                logger.info(f"预览: QPixmap创建成功 {pixmap.width()}x{pixmap.height()}")
                self.image_item = self.scene.addPixmap(pixmap)
                
                # 关键：场景坐标系统使用原图尺寸（保持一致性）
                original_rect = QRectF(0, 0, self.original_image_size[0], self.original_image_size[1])
                self.scene.setSceneRect(original_rect)
                logger.info(f"预览: 场景坐标系统设置为原图尺寸 {self.original_image_size[0]}x{self.original_image_size[1]}")
                
                # 设置图片项的位置和缩放
                if self.preview_scale_ratio != 1.0:
                    # 如果使用了性能优化，需要调整图片项在场景中的显示
                    scale_factor = 1.0 / self.preview_scale_ratio
                    self.image_item.setScale(scale_factor)
                    logger.info(f"预览: 设置图片项缩放 {scale_factor:.3f}")
                    logger.info(f"预览: 图片项边界 {self.image_item.boundingRect()}")
                else:
                    logger.info("预览: 无需缩放图片项，preview_scale_ratio = 1.0")
                
                # 记录视图和场景信息
                logger.info(f"预览: 场景矩形 {self.scene.sceneRect()}")
                logger.info(f"预览: 视图尺寸 {self.viewport().width()}x{self.viewport().height()}")
                
                # 调用fit_in_view前的状态
                logger.info("预览: 调用fit_in_view()前的变换矩阵:")
                transform = self.transform()
                logger.info(f"预览: m11={transform.m11():.3f}, m22={transform.m22():.3f}")
                
                # 关键修复：使用场景矩形来适应，而不是图片项
                # 因为场景矩形是原图尺寸，而图片项被缩放后也应该占据整个场景
                self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
                self.zoom_factor = 1.0
                
                # 调用fit_in_view后的状态
                logger.info("预览: 调用fitInView(sceneRect)后的变换矩阵:")
                transform = self.transform()
                logger.info(f"预览: m11={transform.m11():.6f}, m22={transform.m22():.6f}")
                logger.info(f"预览: zoom_factor={self.zoom_factor}")
                logger.info("预览: 性能优化预览加载完成，自动适应窗口")
                
            else:
                logger.error("QPixmap创建失败")
                raise Exception("QPixmap创建失败")
                
        except Exception as e:
            logger.error(f"加载原图失败: {str(e)}")
            print(f"Error loading image for preview: {e}")
            
            # Fallback to Qt's native loading
            try:
                logger.debug("尝试Qt原生加载")
                pixmap = QPixmap(image_path)
                
                if not pixmap.isNull():
                    self.original_image_size = (pixmap.width(), pixmap.height())
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
            logger.info(f"fit_in_view: 图片项边界 {self.image_item.boundingRect()}")
            logger.info(f"fit_in_view: 场景矩形 {self.scene.sceneRect()}")
            logger.info(f"fit_in_view: 视口尺寸 {self.viewport().width()}x{self.viewport().height()}")
            
            self.fitInView(self.image_item, Qt.KeepAspectRatio)
            self.zoom_factor = 1.0
            
            logger.info("fit_in_view: fitInView()调用完成")
            transform = self.transform()
            logger.info(f"fit_in_view: 变换后 m11={transform.m11():.6f}, m22={transform.m22():.6f}")
    
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
    
    def mousePressEvent(self, event):
        """Handle mouse press for watermark dragging"""
        if event.button() == Qt.LeftButton and event.modifiers() == Qt.ControlModifier:
            # Start dragging watermark with Ctrl+LeftClick
            self.is_dragging_watermark = True
            self.drag_start_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            
            # 如果从预设位置切换到自定义位置，需要初始化custom_x/custom_y
            from models.watermark_config import WatermarkPosition
            if (self.current_config and 
                self.current_config.position != WatermarkPosition.CUSTOM and
                self.original_image_size is not None):
                
                # 计算当前水印在原图上的位置（使用原图坐标）
                from PIL import ImageFont, ImageDraw, Image
                try:
                    font = self._load_font_with_style(
                        self.current_config.text_config.font_family,
                        self.current_config.text_config.font_size,
                        self.current_config.text_config.font_bold,
                        self.current_config.text_config.font_italic
                    )
                    temp_img = Image.new('RGB', (100, 100))
                    temp_draw = ImageDraw.Draw(temp_img)
                    bbox = temp_draw.textbbox((0, 0), self.current_config.text_config.text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    
                    # 使用原图尺寸计算位置（原图坐标）
                    position = self.calculate_watermark_position(
                        self.original_image_size[0], self.original_image_size[1],
                        text_width, text_height,
                        self.current_config
                    )
                    
                    # 保存原图坐标
                    self.current_config.custom_x = position[0]
                    self.current_config.custom_y = position[1]
                    logger.info(f"拖拽初始化: 原图坐标 ({position[0]}, {position[1]})")
                    
                except Exception as e:
                    logger.warning(f"初始化拖拽位置失败: {e}")
            
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for watermark dragging with coordinate mapping"""
        if self.is_dragging_watermark and self.drag_start_pos and self.current_config:
            # Calculate drag delta in scene coordinates
            current_pos = event.pos()
            delta = current_pos - self.drag_start_pos
            self.drag_start_pos = current_pos
            
            # Convert delta to scene coordinates
            scene_delta = self.mapToScene(delta.x(), delta.y()) - self.mapToScene(0, 0)
            
            # 场景坐标系统使用原图坐标，直接使用即可
            # 这保证了拖动结果与导出完全一致
            delta_x = int(scene_delta.x())
            delta_y = int(scene_delta.y())
            
            # Update custom position (always in original coordinates)
            from models.watermark_config import WatermarkPosition
            self.current_config.position = WatermarkPosition.CUSTOM
            old_x = self.current_config.custom_x
            old_y = self.current_config.custom_y
            self.current_config.custom_x += delta_x
            self.current_config.custom_y += delta_y
            
            logger.info(f"拖拽: ({old_x},{old_y}) -> ({self.current_config.custom_x},{self.current_config.custom_y}), 移动量({delta_x},{delta_y})")
            
            # Emit signal to update UI and regenerate preview
            self.watermark_position_changed.emit(
                self.current_config.custom_x,
                self.current_config.custom_y
            )
            
            event.accept()
        elif event.modifiers() == Qt.ControlModifier:
            # Show drag cursor when Ctrl is held
            self.setCursor(Qt.OpenHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.LeftButton and self.is_dragging_watermark:
            self.is_dragging_watermark = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def _create_performance_preview(self, original_img: Image.Image) -> tuple[Image.Image, float]:
        """Create performance-optimized preview image"""
        original_pixels = original_img.size[0] * original_img.size[1]
        
        if original_pixels <= self.MAX_PREVIEW_PIXELS:
            return original_img.copy(), 1.0
        
        # 计算最优缩放比例
        scale_ratio = (self.MAX_PREVIEW_PIXELS / original_pixels) ** 0.5
        new_size = (
            int(original_img.size[0] * scale_ratio),
            int(original_img.size[1] * scale_ratio)
        )
        
        # 高质量缩放
        try:
            preview_img = original_img.resize(new_size, Image.Resampling.LANCZOS)
        except (MemoryError, OSError):
            # 如果内存不足，使用快速缩放
            preview_img = original_img.resize(new_size, Image.Resampling.BILINEAR)
        
        return preview_img, scale_ratio
    
    def _add_to_cache(self, image_path: str, original_img: Image.Image, preview_img: Image.Image):
        """Add images to cache with LRU eviction"""
        # 清理缓存
        if len(self._original_cache) >= self._cache_max_size:
            oldest_key = next(iter(self._original_cache))
            del self._original_cache[oldest_key]
            del self._preview_cache[oldest_key]
            logger.debug(f"缓存已满，移除: {os.path.basename(oldest_key)}")
        
        self._original_cache[image_path] = original_img
        self._preview_cache[image_path] = preview_img
        logger.debug(f"缓存大小: {len(self._original_cache)}/{self._cache_max_size}")
    
    def clear_cache(self):
        """Clear image cache"""
        self._original_cache.clear()
        self._preview_cache.clear()
        logger.debug("图片缓存已清空")
    
    def original_to_preview_coords(self, original_x: int, original_y: int) -> tuple[int, int]:
        """Convert original image coordinates to preview coordinates"""
        preview_x = int(original_x * self.preview_scale_ratio)
        preview_y = int(original_y * self.preview_scale_ratio)
        return preview_x, preview_y
    
    def preview_to_original_coords(self, preview_x: int, preview_y: int) -> tuple[int, int]:
        """Convert preview coordinates to original image coordinates"""
        if self.preview_scale_ratio > 0:
            original_x = int(preview_x / self.preview_scale_ratio)
            original_y = int(preview_y / self.preview_scale_ratio)
        else:
            original_x, original_y = preview_x, preview_y
        return original_x, original_y
    
    def set_config_for_drag(self, config: WatermarkConfig, image_path: str):
        """Set configuration for drag support"""
        self.current_config = config
        self.current_image_path = image_path
    
    def update_watermark_overlay(self, config: WatermarkConfig, image_path: str):
        """Update watermark overlay"""
        # Store config for drag support
        self.set_config_for_drag(config, image_path)
        
        if not self.image_item or not image_path:
            return
        
        try:
            # Generate watermarked image
            watermarked_pixmap = self.generate_watermarked_preview(image_path, config)
            if watermarked_pixmap:
                logger.info(f"预览: 更新水印覆盖层 - 水印图{watermarked_pixmap.width()}x{watermarked_pixmap.height()}")
                
                self.scene.clear()
                self.image_item = self.scene.addPixmap(watermarked_pixmap)
                
                # 关键：保持场景矩形为原图尺寸（与set_image一致）
                if self.original_image_size:
                    original_rect = QRectF(0, 0, self.original_image_size[0], self.original_image_size[1])
                    self.scene.setSceneRect(original_rect)
                    logger.info(f"预览: 水印覆盖层场景矩形保持原图尺寸 {self.original_image_size[0]}x{self.original_image_size[1]}")
                    
                    # 如果使用了性能优化，需要缩放图片项
                    if self.preview_scale_ratio != 1.0:
                        scale_factor = 1.0 / self.preview_scale_ratio
                        self.image_item.setScale(scale_factor)
                        logger.info(f"预览: 水印覆盖层设置图片项缩放 {scale_factor:.3f}")
                    
                    # 使用场景矩形适应视图（与set_image一致）
                    self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
                    logger.info("预览: 水印覆盖层自动适应窗口完成")
                else:
                    # Fallback: 使用水印图尺寸
                    self.scene.setSceneRect(QRectF(watermarked_pixmap.rect()))
                    self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        except Exception as e:
            logger.error(f"更新水印覆盖层失败: {e}")
            print(f"Error updating watermark overlay: {e}")
    
    @log_exception
    def generate_watermarked_preview(self, image_path: str, config: WatermarkConfig) -> Optional[QPixmap]:
        """Generate preview with watermark applied - performance optimized"""
        try:
            logger.info(f"预览: 生成水印预览 {os.path.basename(image_path)}")
            
            # 智能选择渲染策略
            if image_path in self._preview_cache:
                # 使用预览图缓存（性能优化）
                preview_img = self._preview_cache[image_path].copy()
                original_img = self._original_cache[image_path]
                logger.debug(f"预览: 使用缓存 - 预览图{preview_img.size}, 原图{original_img.size}")
            else:
                logger.debug("预览: 从文件重新加载")
                with Image.open(image_path) as img:
                    original_img = img.copy()
                    if original_img.mode not in ('RGB', 'RGBA'):
                        original_img = original_img.convert('RGB')
                    
                    # 创建性能优化预览图
                    preview_img, scale_ratio = self._create_performance_preview(original_img)
                    self.preview_scale_ratio = scale_ratio
                    
                    # 更新尺寸信息
                    self.original_image_size = original_img.size
                    self.preview_image_size = preview_img.size
                    
                    # 缓存
                    self._add_to_cache(image_path, original_img, preview_img)
            
            # 关键决策：水印渲染策略
            total_pixels = self.original_image_size[0] * self.original_image_size[1]
            
            if total_pixels > self.PERFORMANCE_THRESHOLD and self.preview_scale_ratio < 1.0:
                # 大图片：在预览图上渲染，但使用原图坐标系统计算位置
                logger.info(f"预览: 性能模式 - 在预览图({preview_img.size[0]}x{preview_img.size[1]})上渲染水印")
                watermarked_img = self._apply_watermark_to_preview(preview_img, config, original_img.size)
            else:
                # 小图片：直接在原图上渲染
                logger.info(f"预览: 质量模式 - 在原图({original_img.size[0]}x{original_img.size[1]})上渲染水印")
                watermarked_img = self._apply_watermark_to_original(original_img, config)
            
            # Convert to QPixmap
            result_pixmap = self.pil_to_qpixmap(watermarked_img)
            
            if result_pixmap:
                logger.info(f"预览: 水印预览生成成功 {result_pixmap.width()}x{result_pixmap.height()}")
            else:
                logger.error("预览: QPixmap转换失败")
            
            return result_pixmap
                
        except Exception as e:
            logger.error(f"预览: 生成水印预览失败: {str(e)}")
            print(f"Error generating watermarked preview: {e}")
            return None
    
    def _apply_watermark_to_preview(self, preview_img: Image.Image, config: WatermarkConfig, original_size: tuple) -> Image.Image:
        """Apply watermark to preview image using original coordinate system"""
        if config.watermark_type == WatermarkType.TEXT:
            return self._apply_text_watermark_preview_mode(preview_img, config, original_size)
        elif config.watermark_type == WatermarkType.IMAGE:
            return self._apply_image_watermark_preview_mode(preview_img, config, original_size)
        return preview_img
    
    def _apply_watermark_to_original(self, original_img: Image.Image, config: WatermarkConfig) -> Image.Image:
        """Apply watermark to original image (for small images)"""
        if config.watermark_type == WatermarkType.TEXT:
            return self.apply_text_watermark(original_img, config)
        elif config.watermark_type == WatermarkType.IMAGE:
            return self.apply_image_watermark(original_img, config)
        return original_img
    def _apply_text_watermark_preview_mode(self, preview_img: Image.Image, config: WatermarkConfig, original_size: tuple) -> Image.Image:
        """Apply text watermark in preview mode - calculate using original size but render on preview"""
        text_config = config.text_config
        text = text_config.text
        
        logger.info(f"预览: 性能模式文本水印 - 预览图{preview_img.size}, 原图{original_size}, 文本:'{text}'")
        
        # Step 1: 使用原图尺寸和原始字体大小计算位置（保证一致性）
        original_font = self._load_font_with_style(
            text_config.font_family, 
            text_config.font_size,
            text_config.font_bold, 
            text_config.font_italic
        )
        
        # 在虚拟原图上计算文本尺寸和位置
        temp_img = Image.new('RGB', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        
        try:
            bbox = temp_draw.textbbox((0, 0), text, font=original_font)
            original_text_width = bbox[2] - bbox[0]
            original_text_height = bbox[3] - bbox[1]
            baseline_offset = -bbox[1] if bbox[1] < 0 else 0
        except:
            try:
                original_text_width, original_text_height = original_font.getsize(text)
                baseline_offset = 0
            except AttributeError:
                original_text_width = len(text) * text_config.font_size // 2
                original_text_height = text_config.font_size
                baseline_offset = 0
        
        # 使用原图尺寸计算位置
        original_x, original_y = self.calculate_watermark_position(
            original_size[0], original_size[1], original_text_width, original_text_height, config
        )
        original_y += baseline_offset
        
        # Step 2: 将位置和字体大小缩放到预览图
        preview_x, preview_y = self.original_to_preview_coords(original_x, original_y)
        preview_font_size = max(1, int(text_config.font_size * self.preview_scale_ratio))
        
        # 创建预览字体
        preview_font = self._load_font_with_style(
            text_config.font_family, 
            preview_font_size,
            text_config.font_bold, 
            text_config.font_italic
        )
        
        logger.info(f"预览: 坐标映射 原图({original_x},{original_y}) -> 预览({preview_x},{preview_y}), 字体{text_config.font_size}->{preview_font_size}")
        
        # Step 3: 缩放特效参数
        import copy
        preview_text_config = copy.deepcopy(text_config)
        preview_text_config.font_size = preview_font_size
        
        if preview_text_config.has_shadow:
            original_offset = preview_text_config.shadow_offset
            preview_text_config.shadow_offset = (
                int(original_offset[0] * self.preview_scale_ratio),
                int(original_offset[1] * self.preview_scale_ratio)
            )
        
        if preview_text_config.has_outline:
            preview_text_config.outline_width = max(1, int(preview_text_config.outline_width * self.preview_scale_ratio))
        
        # Step 4: 在预览图上渲染
        return self.advanced_text_renderer.render_text_with_effects(
            preview_img, preview_text_config, (preview_x, preview_y), text, config.rotation
        )
    
    @log_exception
    def apply_text_watermark(self, img: Image.Image, config: WatermarkConfig) -> Image.Image:
        """Apply text watermark to image - for original size images"""
        text_config = config.text_config
        text = text_config.text
        
        logger.info(f"预览: 质量模式文本水印 - 原图 {img.size[0]}x{img.size[1]}, 文本: '{text}', 字体大小: {text_config.font_size}")
        
        # Load font with original size
        font = self._load_font_with_style(
            text_config.font_family, 
            text_config.font_size,
            text_config.font_bold, 
            text_config.font_italic
        )
        
        # Calculate text dimensions
        temp_draw = ImageDraw.Draw(img)
        try:
            bbox = temp_draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            baseline_offset = -bbox[1] if bbox[1] < 0 else 0
        except:
            try:
                text_width, text_height = font.getsize(text)
                baseline_offset = 0
            except AttributeError:
                text_width = len(text) * text_config.font_size // 2
                text_height = text_config.font_size
                baseline_offset = 0
        
        # Calculate position using image size (which is original size)
        x, y = self.calculate_watermark_position(
            img.size[0], img.size[1], text_width, text_height, config
        )
        
        # Adjust for baseline
        y = y + baseline_offset
        
        logger.info(f"预览: 文本尺寸({text_width}x{text_height}), 位置({x},{y})")
        
        # Use advanced renderer (supports rotation, effects, and styled fonts)
        return self.advanced_text_renderer.render_text_with_effects(
            img, text_config, (x, y), text, config.rotation
        )
    
    def _apply_image_watermark_preview_mode(self, preview_img: Image.Image, config: WatermarkConfig, original_size: tuple) -> Image.Image:
        """Apply image watermark in preview mode"""
        watermark_path = config.image_config.image_path
        if not watermark_path or not os.path.exists(watermark_path):
            return preview_img
        
        try:
            with Image.open(watermark_path) as watermark_img:
                # Step 1: 使用原图尺寸计算水印大小和位置
                original_scale = config.image_config.scale
                original_wm_size = (
                    int(watermark_img.width * original_scale),
                    int(watermark_img.height * original_scale)
                )
                
                # 使用原图尺寸计算位置
                original_x, original_y = self.calculate_watermark_position(
                    original_size[0], original_size[1],
                    original_wm_size[0], original_wm_size[1],
                    config
                )
                
                # Step 2: 缩放到预览坐标
                preview_x, preview_y = self.original_to_preview_coords(original_x, original_y)
                preview_wm_size = (
                    int(original_wm_size[0] * self.preview_scale_ratio),
                    int(original_wm_size[1] * self.preview_scale_ratio)
                )
                
                # 调整水印大小
                if watermark_img.size != preview_wm_size:
                    watermark_img = watermark_img.resize(preview_wm_size, Image.Resampling.LANCZOS)
                
                # 应用透明度和旋转
                if config.image_config.opacity < 1.0 or config.rotation != 0:
                    if watermark_img.mode != 'RGBA':
                        watermark_img = watermark_img.convert('RGBA')
                    
                    if config.image_config.opacity < 1.0:
                        r, g, b, a = watermark_img.split()
                        a = a.point(lambda x: int(x * config.image_config.opacity))
                        watermark_img = Image.merge('RGBA', (r, g, b, a))
                    
                    if config.rotation != 0:
                        watermark_img = watermark_img.rotate(
                            config.rotation, resample=Image.BICUBIC, expand=True, fillcolor=(0, 0, 0, 0)
                        )
                
                # 合成到预览图
                if preview_img.mode != 'RGBA':
                    preview_img = preview_img.convert('RGBA')
                
                preview_img.paste(watermark_img, (preview_x, preview_y), watermark_img)
                
        except Exception as e:
            logger.error(f"预览图片水印失败: {e}")
        
        return preview_img
    
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
                    # Convert to RGBA for alpha handling
                    if watermark_img.mode != 'RGBA':
                        watermark_img = watermark_img.convert('RGBA')
                    
                    # Adjust opacity while preserving existing alpha channel
                    opacity = config.image_config.opacity
                    if opacity < 1.0:
                        # Get existing alpha channel
                        r, g, b, a = watermark_img.split()
                        # Multiply existing alpha by opacity factor
                        a = a.point(lambda x: int(x * opacity))
                        # Merge back
                        watermark_img = Image.merge('RGBA', (r, g, b, a))
                    
                    # Apply rotation if needed
                    if config.rotation != 0:
                        watermark_img = watermark_img.rotate(
                            config.rotation,
                            resample=Image.BICUBIC,
                            expand=True,
                            fillcolor=(0, 0, 0, 0)
                        )
                        # Recalculate position after rotation
                        wm_width, wm_height = watermark_img.size
                        x, y = self.calculate_watermark_position(
                            img_width, img_height, wm_width, wm_height, config
                        )
                    
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
    
    def _test_large_image_compatibility(self, img: Image.Image, text_config) -> bool:
        """Test if large image can handle effects without distortion"""
        try:
            # Quick compatibility test
            test_size = min(img.size[0], img.size[1])
            if test_size > 4000:  # Very high resolution
                return False
            return True
        except Exception:
            return False
    
    def _render_basic_text_for_large_preview(self, img: Image.Image, text_config, text: str, config) -> Image.Image:
        """Fallback basic text rendering for very large images"""
        try:
            logger.debug("使用安全模式渲染大图片文本")
            draw = ImageDraw.Draw(img)
            
            # Load font safely
            font = self._load_font_with_style(
                text_config.font_family, 
                text_config.font_size, 
                text_config.font_bold, 
                text_config.font_italic
            )
            
            # Calculate position
            try:
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except:
                text_width = len(text) * text_config.font_size // 2
                text_height = text_config.font_size
            
            x, y = self.calculate_watermark_position(
                img.size[0], img.size[1], text_width, text_height, config
            )
            
            # Draw text directly without effects to avoid distortion
            color = text_config.color
            alpha = int(text_config.opacity * 255)
            text_color = (*color, alpha) if len(color) == 3 else color
            
            draw.text((x, y), text, font=font, fill=text_color)
            return img
            
        except Exception as e:
            logger.error(f"安全模式渲染失败: {e}")
            return img
    
    def calculate_watermark_position(self, img_w: int, img_h: int, wm_w: int, wm_h: int, 
                                   config: WatermarkConfig) -> tuple:
        """Calculate watermark position with improved positioning"""
        margin_x = config.margin_x
        margin_y = config.margin_y
        
        # 位置优化：将所有位置稍微向上调整，解决偏下问题
        vertical_adjustment = max(10, int(img_h * 0.01))  # 动态调整，最小10像素
        
        if config.position == WatermarkPosition.TOP_LEFT:
            return (margin_x, margin_y)
        elif config.position == WatermarkPosition.TOP_CENTER:
            return ((img_w - wm_w) // 2, margin_y)
        elif config.position == WatermarkPosition.TOP_RIGHT:
            return (img_w - wm_w - margin_x, margin_y)
        elif config.position == WatermarkPosition.CENTER_LEFT:
            return (margin_x, (img_h - wm_h) // 2 - vertical_adjustment)
        elif config.position == WatermarkPosition.CENTER:
            return ((img_w - wm_w) // 2, (img_h - wm_h) // 2 - vertical_adjustment)
        elif config.position == WatermarkPosition.CENTER_RIGHT:
            return (img_w - wm_w - margin_x, (img_h - wm_h) // 2 - vertical_adjustment)
        elif config.position == WatermarkPosition.BOTTOM_LEFT:
            return (margin_x, img_h - wm_h - margin_y - vertical_adjustment)
        elif config.position == WatermarkPosition.BOTTOM_CENTER:
            return ((img_w - wm_w) // 2, img_h - wm_h - margin_y - vertical_adjustment)
        elif config.position == WatermarkPosition.BOTTOM_RIGHT:
            return (img_w - wm_w - margin_x, img_h - wm_h - margin_y - vertical_adjustment)
        elif config.position == WatermarkPosition.CUSTOM:
            return (config.custom_x, config.custom_y)
        else:
            return (margin_x, img_h - wm_h - margin_y - vertical_adjustment)  # Default to bottom-left
    
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
        """Convert PIL image to QPixmap"""
        try:
            width, height = pil_image.size
            logger.debug(f"Converting PIL image to QPixmap: {width}x{height}")
            
            # Convert image to appropriate format
            # CRITICAL: Must keep reference to img_data to prevent garbage collection
            logger.debug(f"Converting PIL image mode: {pil_image.mode}")
            if pil_image.mode == 'RGBA':
                # For RGBA images, convert to Format_RGBA8888
                logger.debug("Converting RGBA image to QImage")
                img_data = pil_image.tobytes('raw', 'RGBA')
                bytes_per_line = width * 4  # 4 bytes per pixel (RGBA)
                qimg = QImage(img_data, width, height, bytes_per_line, QImage.Format_RGBA8888)
                # Make a deep copy to avoid data corruption
                qimg = qimg.copy()
            elif pil_image.mode == 'RGB':
                # For RGB images, ensure proper stride alignment
                logger.debug("Converting RGB image to QImage")
                img_data = pil_image.tobytes('raw', 'RGB')
                bytes_per_line = width * 3  # 3 bytes per pixel (RGB)
                logger.debug(f"Created RGB data: {len(img_data)} bytes, stride: {bytes_per_line}")
                qimg = QImage(img_data, width, height, bytes_per_line, QImage.Format_RGB888)
                # Make a deep copy to prevent data from being garbage collected
                qimg = qimg.copy()
                logger.debug("QImage created from RGB data with deep copy")
            else:
                # Convert other formats to RGB first
                logger.debug(f"Converting {pil_image.mode} to RGB for QPixmap")
                rgb_img = pil_image.convert('RGB')
                img_data = rgb_img.tobytes('raw', 'RGB')
                bytes_per_line = width * 3
                qimg = QImage(img_data, width, height, bytes_per_line, QImage.Format_RGB888)
                # Make a deep copy
                qimg = qimg.copy()
            
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
    
    def _render_large_image_with_warning(self, img: Image.Image, text_config, text: str, 
                                        config: WatermarkConfig, megapixels: float) -> Image.Image:
        """为超大图片渲染基础文本水印，并添加警告提示"""
        logger.info(f"使用基础渲染模式处理超大图片预览: {megapixels:.1f}MP")
        
        # Create result image
        result = img.copy()
        draw = ImageDraw.Draw(result)
        
        # Load font for watermark
        font = self._load_font_with_style(
            text_config.font_family,
            text_config.font_size,
            text_config.font_bold,
            text_config.font_italic
        )
        
        # Calculate watermark position
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except:
            text_width = len(text) * text_config.font_size // 2
            text_height = text_config.font_size
        
        x, y = self.calculate_watermark_position(
            img.size[0], img.size[1], text_width, text_height, config
        )
        
        # Draw watermark text (basic, without effects)
        color_with_alpha = (*text_config.color, int(255 * text_config.opacity))
        draw.text((x, y), text, font=font, fill=color_with_alpha)
        
        # Add warning overlay at top
        warning_text = f"⚠ 图片过大({megapixels:.1f}MP)，预览已简化特效效果"
        warning_font_size = max(20, img.size[1] // 40)  # Dynamic font size based on image height
        
        try:
            warning_font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", warning_font_size)
        except:
            try:
                warning_font = ImageFont.truetype("arial.ttf", warning_font_size)
            except:
                warning_font = ImageFont.load_default()
        
        # Calculate warning position (top center)
        try:
            warning_bbox = draw.textbbox((0, 0), warning_text, font=warning_font)
            warning_width = warning_bbox[2] - warning_bbox[0]
        except:
            warning_width = len(warning_text) * warning_font_size // 2
        
        warning_x = (img.size[0] - warning_width) // 2
        warning_y = 20
        
        # Draw semi-transparent background for warning
        padding = 10
        draw.rectangle(
            [warning_x - padding, warning_y - padding, 
             warning_x + warning_width + padding, warning_y + warning_font_size + padding],
            fill=(255, 200, 0, 200)
        )
        
        # Draw warning text
        draw.text((warning_x, warning_y), warning_text, font=warning_font, fill=(0, 0, 0, 255))
        
        logger.info("超大图片预览完成（带警告提示）")
        return result
    
    def _load_font_with_style(self, font_family: str, font_size: int, bold: bool = False, italic: bool = False) -> ImageFont.FreeTypeFont:
        """Load font with proper bold and italic support"""
        
        # 首先尝试使用FontManager获取字体路径（最可靠的方法）
        font_path = FontManager.get_font_path(font_family, bold, italic)
        if font_path:
            try:
                font = ImageFont.truetype(font_path, font_size)
                logger.debug(f"成功使用FontManager加载字体: {font_family} -> {font_path}")
                return font
            except Exception as e:
                logger.warning(f"FontManager找到字体文件但加载失败 {font_path}: {e}")
        
        # 如果FontManager返回None（说明该字体不支持该样式），使用Arial作为替代字体
        # 这与AdvancedTextRenderer的行为保持一致
        if (bold or italic) and font_path is None:
            logger.info(f"预览: {font_family} 不支持当前样式(粗体:{bold}, 斜体:{italic})，使用Arial替代")
            # 尝试使用对应样式的Arial字体
            arial_font_path = FontManager.get_font_path("Arial", bold, italic)
            if arial_font_path:
                try:
                    font = ImageFont.truetype(arial_font_path, font_size)
                    logger.info(f"预览: 成功使用Arial替代字体: {arial_font_path}")
                    return font
                except Exception as e:
                    logger.warning(f"Arial替代字体加载失败 {arial_font_path}: {e}")
            
            # 如果Arial也失败，尝试使用基础字体（最后的fallback）
            font_path = FontManager.get_font_path(font_family, False, False)
            if font_path:
                try:
                    font = ImageFont.truetype(font_path, font_size)
                    logger.warning(f"预览: Arial替代失败，使用基础字体: {font_family} -> {font_path}")
                    return font
                except Exception as e:
                    logger.warning(f"基础字体加载失败 {font_path}: {e}")
        
        # 如果FontManager失败，尝试使用QFontDatabase
        font_paths = []
        if QFontDatabase:
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
        
        # 通用fallback字体
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
        
        # 尝试加载字体
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, font_size)
                logger.debug(f"成功加载字体: {font_path} (字体:{font_family}, 粗体:{bold}, 斜体:{italic})")
                return font
            except (OSError, IOError):
                continue
        
        logger.warning(f"无法加载字体 {font_family}，使用默认字体")
        return ImageFont.load_default()


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