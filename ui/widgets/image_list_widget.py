"""
Image List Widget
Displays and manages a list of loaded images with thumbnails
"""
import os
from typing import List, Optional

try:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
        QLabel, QPushButton, QFrame, QSizePolicy, QAbstractItemView,
        QMenu, QMessageBox, QCheckBox
    )
    from PyQt5.QtCore import Qt, QSize, pyqtSignal, pyqtSlot, QThread, QObject
    from PyQt5.QtGui import QPixmap, QIcon, QFont, QDragEnterEvent, QDropEvent
except ImportError:
    print("PyQt5 is required but not installed.")
    raise

from PIL import Image
from models.image_info import ImageListModel, ImageInfo
from utils.logger import logger, log_exception


class ThumbnailGenerator(QObject):
    """Worker class for generating thumbnails in background"""
    
    thumbnail_ready = pyqtSignal(int, str)  # index, thumbnail_path
    progress_update = pyqtSignal(int, int)  # current, total
    
    def __init__(self):
        super().__init__()
        self.thumbnail_size = (100, 100)
        self.thumbnail_dir = "temp_thumbnails"
        os.makedirs(self.thumbnail_dir, exist_ok=True)
        
        # Queue management
        self.request_queue = []
        self.is_processing = False
        self.max_concurrent = 3  # Limit concurrent processing
    
    def generate_thumbnail(self, index: int, image_path: str):
        """Generate thumbnail for image with memory optimization"""
        try:
            # Check file exists and is accessible
            if not os.path.exists(image_path) or not os.access(image_path, os.R_OK):
                print(f"Cannot access image file: {image_path}")
                return
            
            # Check if thumbnail already exists
            thumbnail_name = f"thumb_{index}_{os.path.basename(image_path)}.jpg"
            thumbnail_path = os.path.join(self.thumbnail_dir, thumbnail_name)
            
            if os.path.exists(thumbnail_path):
                logger.debug(f"缩略图已存在: {thumbnail_name}")
                self.thumbnail_ready.emit(index, thumbnail_path)
                return
            
            with Image.open(image_path) as img:
                # Limit memory usage by checking image size
                max_size_for_thumbnail = (4096, 4096)  # 16MP limit
                if img.size[0] * img.size[1] > max_size_for_thumbnail[0] * max_size_for_thumbnail[1]:
                    # Pre-resize very large images to avoid memory issues
                    scale = min(max_size_for_thumbnail[0] / img.size[0], 
                               max_size_for_thumbnail[1] / img.size[1])
                    new_size = (int(img.size[0] * scale), int(img.size[1] * scale))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA' and len(img.split()) == 4:
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Create thumbnail
                img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
                
                # Save thumbnail with error handling
                try:
                    img.save(thumbnail_path, 'JPEG', quality=75, optimize=True)
                    self.thumbnail_ready.emit(index, thumbnail_path)
                except Exception as save_error:
                    print(f"Error saving thumbnail for {image_path}: {save_error}")
                
        except MemoryError:
            print(f"Memory error processing large image: {image_path}")
        except Exception as e:
            print(f"Error generating thumbnail for {image_path}: {e}")


class ImageListItem(QWidget):
    """Custom widget for image list item with thumbnail and info"""
    
    def __init__(self, image_info: ImageInfo, index: int):
        super().__init__()
        self.image_info = image_info
        self.index = index
        self.thumbnail_path = None
        self.checkbox = None  # Will be created in init_ui
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 3, 5, 3)
        layout.setSpacing(8)
        
        # Checkbox for selection
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.image_info.is_selected)
        self.checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #bbb;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:hover {
                border-color: #2196f3;
            }
            QCheckBox::indicator:checked {
                background-color: #2196f3;
                border-color: #2196f3;
                image: url(none);
            }
            QCheckBox::indicator:checked:hover {
                background-color: #1976d2;
            }
        """)
        layout.addWidget(self.checkbox)
        
        # Thumbnail label
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(60, 60)
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ddd;
                border-radius: 3px;
                background-color: #f5f5f5;
            }
        """)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setText("...")
        layout.addWidget(self.thumbnail_label)
        
        # Info layout
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        # File name
        filename = self.image_info.file_name
        # Truncate long filenames for display
        if len(filename) > 30:
            filetype = os.path.splitext(filename)[1]
            filename = filename[:27 - len(filetype)] + "..." + filetype
        self.name_label = QLabel(filename)
        self.name_label.setStyleSheet("""
            QLabel {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC", "SimSun", "宋体", sans-serif;
                font-size: 12px;
                font-weight: bold;
                color: #2c3e50;
                line-height: 1.3;
            }
        """)
        info_layout.addWidget(self.name_label)
        
        # Dimensions and size
        info_text = f"{self.image_info.get_dimensions_string()} • {self.image_info.get_size_string()}"
        self.info_label = QLabel(info_text)
        self.info_label.setStyleSheet("""
            QLabel {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", "SimSun", "宋体", sans-serif;
                font-size: 10px;
                color: #6c757d;
                line-height: 1.3;
            }
        """)
        info_layout.addWidget(self.info_label)
        
        # Format info
        format_info = f"{self.image_info.format}"
        if self.image_info.has_alpha:
            format_info += " (透明)"
        self.format_label = QLabel(format_info)
        self.format_label.setStyleSheet("""
            QLabel {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", "SimSun", "宋体", sans-serif;
                font-size: 9px;
                color: #adb5bd;
                font-weight: 500;
                background-color: #e9ecef;
                padding: 2px 6px;
                border-radius: 3px;
            }
        """)
        info_layout.addWidget(self.format_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
    
    def set_thumbnail(self, thumbnail_path: str):
        """Set thumbnail image"""
        self.thumbnail_path = thumbnail_path
        pixmap = QPixmap(thumbnail_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                self.thumbnail_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.thumbnail_label.setPixmap(scaled_pixmap)
    
    def set_selected(self, selected: bool):
        """Set selection state visual feedback"""
        # Update checkbox state
        if self.checkbox:
            self.checkbox.setChecked(selected)
        
        # Update background style
        if selected:
            self.setStyleSheet("""
                ImageListItem {
                    background-color: #e3f2fd;
                    border: 1px solid #2196f3;
                    border-radius: 3px;
                }
            """)
        else:
            self.setStyleSheet("")


class ImageListWidget(QWidget):
    """Widget for displaying and managing list of images"""
    
    # Signals
    image_selected = pyqtSignal(int)  # index
    images_dropped = pyqtSignal(list)  # file paths
    
    def __init__(self, model: ImageListModel):
        super().__init__()
        self.model = model
        self.thumbnail_generator = ThumbnailGenerator()
        self.thumbnail_thread = QThread()
        
        self.init_ui()
        self.setup_connections()
        self.setup_drag_drop()
        
        # Move thumbnail generator to thread
        self.thumbnail_generator.moveToThread(self.thumbnail_thread)
        self.thumbnail_thread.started.connect(lambda: None)  # Ensure thread is properly started
        self.thumbnail_thread.start()
    
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("图片列表")
        header_label.setStyleSheet("""
            QLabel {
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC", "SimHei", "黑体", sans-serif;
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 7px;
                border-bottom: 2px solid #3498db;
                margin-bottom: 0px;
            }
        """)
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        # Control buttons
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.setFixedSize(50, 30)
        header_layout.addWidget(self.select_all_btn)
        
        self.clear_btn = QPushButton("清空")
        self.clear_btn.setFixedSize(50, 30)
        header_layout.addWidget(self.clear_btn)
        
        layout.addLayout(header_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("color: #ddd;")
        layout.addWidget(separator)
        
        # List widget
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 3px;
                background-color: white;
                outline: none;
            }
            QListWidget::item {
                border-bottom: 1px solid #eee;
                padding: 2px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                border: 1px solid #2196f3;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        layout.addWidget(self.list_widget)
        
        # Status info
        self.status_label = QLabel("拖拽图片文件到此处")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #888; padding: 10px;")
        layout.addWidget(self.status_label)
    
    def setup_connections(self):
        """Setup signal connections"""
        # Model signals
        self.model.images_changed.connect(self.refresh_list)
        self.model.selection_changed.connect(self.update_selection)
        
        # UI signals
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.select_all_btn.clicked.connect(self.model.select_all)
        self.clear_btn.clicked.connect(self.confirm_clear)
        
        # Thumbnail generator
        self.thumbnail_generator.thumbnail_ready.connect(self.on_thumbnail_ready)
    
    def setup_drag_drop(self):
        """Setup drag and drop functionality"""
        self.setAcceptDrops(True)
        self.list_widget.setAcceptDrops(True)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event"""
        file_paths = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if self.is_image_file(file_path):
                file_paths.append(file_path)
        
        if file_paths:
            self.images_dropped.emit(file_paths)
    
    def is_image_file(self, file_path: str) -> bool:
        """Check if file is a supported image format"""
        supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        return os.path.splitext(file_path.lower())[1] in supported_formats
    
    @pyqtSlot()
    def refresh_list(self):
        """Refresh the image list"""
        self.list_widget.clear()
        
        images = self.model.get_images()
        for i, image_info in enumerate(images):
            # Create list item
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 70))
            
            # Create custom widget
            item_widget = ImageListItem(image_info, i)
            
            # Connect checkbox signal
            if item_widget.checkbox:
                item_widget.checkbox.stateChanged.connect(
                    lambda state, idx=i: self.on_checkbox_changed(idx, state)
                )
            
            # Add to list
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, item_widget)
            
            # Queue thumbnail generation safely
            try:
                self.queue_thumbnail_generation(i, image_info.file_path)
            except Exception as e:
                print(f"Error queueing thumbnail for {image_info.file_path}: {e}")
        
        # Update status
        count = len(images)
        if count == 0:
            self.status_label.setText("拖拽图片文件到此处")
        else:
            self.status_label.setText(f"共 {count} 张图片")
    
    def queue_thumbnail_generation(self, index: int, image_path: str):
        """Queue thumbnail generation with concurrent limit"""
        # Add to queue
        self.thumbnail_generator.request_queue.append((index, image_path))
        
        # Process queue if not already processing
        if not self.thumbnail_generator.is_processing:
            self.process_thumbnail_queue()
    
    def process_thumbnail_queue(self):
        """Process thumbnail generation queue"""
        if not self.thumbnail_generator.request_queue:
            return
        
        self.thumbnail_generator.is_processing = True
        
        # Process up to max_concurrent items
        current_batch = self.thumbnail_generator.request_queue[:self.thumbnail_generator.max_concurrent]
        self.thumbnail_generator.request_queue = self.thumbnail_generator.request_queue[self.thumbnail_generator.max_concurrent:]
        
        for index, image_path in current_batch:
            try:
                self.thumbnail_generator.generate_thumbnail(index, image_path)
            except Exception as e:
                print(f"Error processing thumbnail {image_path}: {e}")
        
        # Continue processing if more items in queue
        if self.thumbnail_generator.request_queue:
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, self.process_thumbnail_queue)  # Small delay
        else:
            self.thumbnail_generator.is_processing = False
    
    @pyqtSlot()
    def update_selection(self):
        """Update selection visual feedback"""
        images = self.model.get_images()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if isinstance(widget, ImageListItem) and i < len(images):
                widget.set_selected(images[i].is_selected)
    
    def on_checkbox_changed(self, index: int, state: int):
        """Handle checkbox state change"""
        is_checked = (state == Qt.Checked)
        self.model.set_selection(index, is_checked)
        logger.debug(f"图片 {index} 选中状态: {is_checked}")
    
    @pyqtSlot(QListWidgetItem)
    def on_item_clicked(self, item: QListWidgetItem):
        """Handle item click"""
        index = self.list_widget.row(item)
        if index >= 0:
            # Emit selection signal for preview
            self.image_selected.emit(index)
    
    @pyqtSlot(int, str)
    def on_thumbnail_ready(self, index: int, thumbnail_path: str):
        """Handle thumbnail ready"""
        if index < self.list_widget.count():
            item = self.list_widget.item(index)
            widget = self.list_widget.itemWidget(item)
            if isinstance(widget, ImageListItem):
                widget.set_thumbnail(thumbnail_path)
    
    def show_context_menu(self, position):
        """Show context menu"""
        item = self.list_widget.itemAt(position)
        if item is None:
            return
        
        menu = QMenu(self)
        
        # Selection actions
        menu.addAction("选择", lambda: self.toggle_item_selection(item))
        menu.addAction("取消选择", lambda: self.clear_item_selection(item))
        menu.addSeparator()
        
        # Remove actions
        menu.addAction("删除此项", lambda: self.remove_item(item))
        menu.addAction("删除选中项", self.remove_selected)
        
        menu.exec_(self.list_widget.mapToGlobal(position))
    
    def toggle_item_selection(self, item: QListWidgetItem):
        """Toggle item selection"""
        index = self.list_widget.row(item)
        image_info = self.model.get_image(index)
        if image_info:
            self.model.set_selection(index, not image_info.is_selected)
    
    def clear_item_selection(self, item: QListWidgetItem):
        """Clear item selection"""
        index = self.list_widget.row(item)
        self.model.set_selection(index, False)
    
    def remove_item(self, item: QListWidgetItem):
        """Remove single item"""
        index = self.list_widget.row(item)
        self.model.remove_image(index)
    
    def remove_selected(self):
        """Remove selected items"""
        self.model.remove_selected()
    
    def get_selected_images(self):
        """Get all selected images"""
        return self.model.get_selected_images()
    
    def confirm_clear(self):
        """Confirm and clear all images"""
        if self.model.count() > 0:
            reply = QMessageBox.question(
                self,
                "确认清空",
                f"确定要清空所有 {self.model.count()} 张图片吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.model.clear()
    
    def closeEvent(self, event):
        """Handle widget close event"""
        self.cleanup_thread()
        event.accept()
    
    def cleanup_thread(self):
        """Clean up thumbnail thread"""
        if hasattr(self, 'thumbnail_thread') and self.thumbnail_thread.isRunning():
            self.thumbnail_thread.quit()
            self.thumbnail_thread.wait(3000)  # Wait up to 3 seconds
            if self.thumbnail_thread.isRunning():
                self.thumbnail_thread.terminate()
                self.thumbnail_thread.wait(1000)
    
    def __del__(self):
        """Destructor - ensure thread cleanup"""
        try:
            self.cleanup_thread()
        except:
            pass