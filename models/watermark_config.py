"""
Watermark Configuration Model
Defines the structure for watermark settings
"""
from dataclasses import dataclass, field
from typing import Optional, Tuple
from enum import Enum
from utils.logger import logger, log_exception


class WatermarkType(Enum):
    """Types of watermarks"""
    TEXT = "text"
    IMAGE = "image"


class WatermarkPosition(Enum):
    """Predefined watermark positions"""
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"
    CUSTOM = "custom"


@dataclass
class TextWatermarkConfig:
    """Configuration for text watermarks"""
    text: str = "Watermark"
    font_family: str = "Arial"
    font_size: int = 32
    font_bold: bool = False
    font_italic: bool = False
    color: Tuple[int, int, int] = (255, 255, 255)  # RGB
    opacity: float = 0.8  # 0.0 to 1.0
    
    # Advanced text effects
    has_shadow: bool = False
    shadow_offset: Tuple[int, int] = (2, 2)
    shadow_color: Tuple[int, int, int] = (0, 0, 0)
    has_outline: bool = False
    outline_width: int = 1
    outline_color: Tuple[int, int, int] = (0, 0, 0)


@dataclass
class ImageWatermarkConfig:
    """Configuration for image watermarks"""
    image_path: str = ""
    scale: float = 1.0  # Scale factor
    opacity: float = 0.8  # 0.0 to 1.0
    maintain_aspect_ratio: bool = True
    

@dataclass
class WatermarkConfig:
    """Complete watermark configuration"""
    # Type and position
    watermark_type: WatermarkType = WatermarkType.TEXT
    position: WatermarkPosition = WatermarkPosition.BOTTOM_RIGHT
    custom_x: int = 0
    custom_y: int = 0
    margin_x: int = 10
    margin_y: int = 10
    rotation: float = 0.0  # degrees
    
    # Type-specific configs
    text_config: TextWatermarkConfig = field(default_factory=TextWatermarkConfig)
    image_config: ImageWatermarkConfig = field(default_factory=ImageWatermarkConfig)
    
    @log_exception
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        logger.debug(f"将水印配置转换为字典: 类型={self.watermark_type.value}, 位置={self.position.value}")
        return {
            'watermark_type': self.watermark_type.value,
            'position': self.position.value,
            'custom_x': self.custom_x,
            'custom_y': self.custom_y,
            'margin_x': self.margin_x,
            'margin_y': self.margin_y,
            'rotation': self.rotation,
            'text_config': {
                'text': self.text_config.text,
                'font_family': self.text_config.font_family,
                'font_size': self.text_config.font_size,
                'font_bold': self.text_config.font_bold,
                'font_italic': self.text_config.font_italic,
                'color': self.text_config.color,
                'opacity': self.text_config.opacity,
                'has_shadow': self.text_config.has_shadow,
                'shadow_offset': self.text_config.shadow_offset,
                'shadow_color': self.text_config.shadow_color,
                'has_outline': self.text_config.has_outline,
                'outline_width': self.text_config.outline_width,
                'outline_color': self.text_config.outline_color,
            },
            'image_config': {
                'image_path': self.image_config.image_path,
                'scale': self.image_config.scale,
                'opacity': self.image_config.opacity,
                'maintain_aspect_ratio': self.image_config.maintain_aspect_ratio,
            }
        }
    
    @classmethod
    @log_exception
    def from_dict(cls, data: dict) -> 'WatermarkConfig':
        """Create from dictionary"""
        logger.debug(f"从字典创建水印配置: {len(data)} 个参数")
        config = cls()
        
        config.watermark_type = WatermarkType(data.get('watermark_type', 'text'))
        config.position = WatermarkPosition(data.get('position', 'bottom_right'))
        config.custom_x = data.get('custom_x', 0)
        config.custom_y = data.get('custom_y', 0)
        config.margin_x = data.get('margin_x', 10)
        config.margin_y = data.get('margin_y', 10)
        config.rotation = data.get('rotation', 0.0)
        
        # Text config
        text_data = data.get('text_config', {})
        config.text_config = TextWatermarkConfig(
            text=text_data.get('text', 'Watermark'),
            font_family=text_data.get('font_family', 'Arial'),
            font_size=text_data.get('font_size', 32),
            font_bold=text_data.get('font_bold', False),
            font_italic=text_data.get('font_italic', False),
            color=tuple(text_data.get('color', [255, 255, 255])),
            opacity=text_data.get('opacity', 0.8),
            has_shadow=text_data.get('has_shadow', False),
            shadow_offset=tuple(text_data.get('shadow_offset', [2, 2])),
            shadow_color=tuple(text_data.get('shadow_color', [0, 0, 0])),
            has_outline=text_data.get('has_outline', False),
            outline_width=text_data.get('outline_width', 1),
            outline_color=tuple(text_data.get('outline_color', [0, 0, 0])),
        )
        
        # Image config
        image_data = data.get('image_config', {})
        config.image_config = ImageWatermarkConfig(
            image_path=image_data.get('image_path', ''),
            scale=image_data.get('scale', 1.0),
            opacity=image_data.get('opacity', 0.8),
            maintain_aspect_ratio=image_data.get('maintain_aspect_ratio', True),
        )
        
        return config