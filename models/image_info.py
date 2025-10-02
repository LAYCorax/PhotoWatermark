"""
Image Information Model
Stores metadata and state information for loaded images
"""
import os
from dataclasses import dataclass
from typing import Optional
from PIL import Image

# Conditional import for Qt components
try:
    from PyQt5.QtCore import QObject, pyqtSignal
    QT_AVAILABLE = True
except ImportError:
    # Fallback for when PyQt5 is not available
    QT_AVAILABLE = False
    class QObject:
        def __init__(self):
            pass
    def pyqtSignal():
        return lambda: None


@dataclass
class ImageInfo:
    """Data class for storing image information"""
    file_path: str
    file_name: str
    file_size: int
    image_size: tuple
    format: str
    has_alpha: bool = False
    thumbnail_path: Optional[str] = None
    is_selected: bool = False
    
    @classmethod
    def from_file(cls, file_path: str) -> Optional['ImageInfo']:
        """Create ImageInfo from file path"""
        try:
            if not os.path.exists(file_path):
                return None
                
            file_name = os.path.basename(file_path)
            if len(file_name) > 30:
                file_type = file_name[file_name.rfind('.'):]
                file_name = file_name[:27] + '...' + file_type
            file_size = os.path.getsize(file_path)
            
            with Image.open(file_path) as img:
                image_size = img.size
                format = img.format
                has_alpha = img.mode in ('RGBA', 'LA') or 'transparency' in img.info
                
            return cls(
                file_path=file_path,
                file_name=file_name,
                file_size=file_size,
                image_size=image_size,
                format=format,
                has_alpha=has_alpha
            )
        except Exception as e:
            print(f"Error loading image info for {file_path}: {e}")
            return None
    
    def get_size_string(self) -> str:
        """Get human readable size string"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def get_dimensions_string(self) -> str:
        """Get dimensions as string"""
        return f"{self.image_size[0]} × {self.image_size[1]}"


class ImageListModel(QObject):
    """Model for managing a list of images"""
    
    # Signals
    images_changed = pyqtSignal()
    selection_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._images = []
    
    def add_image(self, file_path: str) -> bool:
        """Add an image to the list"""
        image_info = ImageInfo.from_file(file_path)
        if image_info:
            # Check if already exists
            if any(img.file_path == file_path for img in self._images):
                return False
            
            self._images.append(image_info)
            self.images_changed.emit()
            return True
        return False
    
    def add_images(self, file_paths: list) -> int:
        """Add multiple images with batch processing, return count of successfully added"""
        added_count = 0
        batch_size = 50  # Process in batches to avoid memory issues
        
        for i in range(0, len(file_paths), batch_size):
            batch = file_paths[i:i + batch_size]
            for file_path in batch:
                try:
                    if self.add_image(file_path):
                        added_count += 1
                except Exception as e:
                    print(f"Error adding image {file_path}: {e}")
                    continue
            
            # Emit progress update after each batch
            if added_count > 0:
                self.images_changed.emit()
        
        return added_count
    
    def remove_image(self, index: int) -> bool:
        """Remove image at index"""
        if 0 <= index < len(self._images):
            del self._images[index]
            self.images_changed.emit()
            return True
        return False
    
    def remove_selected(self) -> int:
        """Remove all selected images, return count removed"""
        original_count = len(self._images)
        self._images = [img for img in self._images if not img.is_selected]
        removed_count = original_count - len(self._images)
        if removed_count > 0:
            self.images_changed.emit()
        return removed_count
    
    def clear(self):
        """Clear all images"""
        if self._images:
            self._images.clear()
            self.images_changed.emit()
    
    def set_selection(self, index: int, selected: bool):
        """Set selection state for image at index"""
        if 0 <= index < len(self._images):
            if self._images[index].is_selected != selected:
                self._images[index].is_selected = selected
                self.selection_changed.emit()
    
    def select_all(self):
        """Select all images"""
        changed = False
        for img in self._images:
            if not img.is_selected:
                img.is_selected = True
                changed = True
        if changed:
            self.selection_changed.emit()
    
    def clear_selection(self):
        """Clear all selections"""
        changed = False
        for img in self._images:
            if img.is_selected:
                img.is_selected = False
                changed = True
        if changed:
            self.selection_changed.emit()
    
    def get_image(self, index: int) -> Optional[ImageInfo]:
        """Get image info at index"""
        if 0 <= index < len(self._images):
            return self._images[index]
        return None
    
    def get_images(self) -> list:
        """Get all images"""
        return self._images.copy()
    
    def get_selected_images(self) -> list:
        """Get all selected images"""
        return [img for img in self._images if img.is_selected]
    
    def count(self) -> int:
        """Get total count of images"""
        return len(self._images)
    
    def selected_count(self) -> int:
        """Get count of selected images"""
        return sum(1 for img in self._images if img.is_selected)