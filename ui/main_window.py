"""
Main Window for PhotoWatermark Application
Based on MaaAssistantArknights GUI design principles
"""
import sys
import os
from typing import Optional, List

try:
    from PyQt5.QtWidgets import (
        QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
        QSplitter, QMenuBar, QStatusBar, QLabel, QFrame,
        QApplication, QMessageBox
    )
    from PyQt5.QtCore import Qt, QSize, pyqtSlot
    from PyQt5.QtGui import QIcon, QPixmap
except ImportError:
    print("PyQt5 is required but not installed. Please install it using:")
    print("pip install PyQt5")
    sys.exit(1)

from models.image_info import ImageListModel
from models.watermark_config import WatermarkConfig
from ui.widgets.image_list_widget import ImageListWidget
from ui.widgets.preview_widget import PreviewWidget
from ui.widgets.watermark_config_widget import WatermarkConfigWidget
from utils.memory_manager import memory_manager
from core.watermark_engine import WatermarkEngine
from utils.logger import logger, log_exception, log_performance
from ui.dialogs.watermark_progress_dialog import WatermarkProgressDialog
from ui.dialogs.file_import_progress_dialog import FileImportProgressDialog


class MainWindow(QMainWindow):
    """Main application window with three-panel layout"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        logger.info("初始化主窗口...")
        
        try:
            # Models
            logger.debug("创建数据模型...")
            self.image_list_model = ImageListModel()
            self.watermark_config = WatermarkConfig()
            
            # Watermark engine for large image processing
            logger.debug("创建水印引擎...")
            self.watermark_engine = WatermarkEngine()
            
            logger.debug("数据模型创建完成")
        except Exception as e:
            logger.error(f"数据模型创建失败: {e}")
            raise
        
        # Initialize UI
        logger.info("初始化用户界面...")
        try:
            self.init_ui()
            logger.debug("UI组件创建完成")
            
            self.setup_connections()
            logger.debug("信号连接设置完成")
        except Exception as e:
            logger.error(f"UI初始化失败: {e}")
            raise
        
        # Set window properties
        self.setWindowTitle("PhotoWatermark - Professional Photo Watermarking Tool")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Center window
        self.center_window()
        
        # Setup memory monitoring
        self.setup_memory_monitoring()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.create_menus()
        self.create_status_bar()
        self.create_central_widget()
    
    def create_menus(self):
        """Create application menus"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('文件(&F)')
        file_menu.addAction('导入图片...', self.import_images, 'Ctrl+O')
        file_menu.addAction('导入文件夹...', self.import_folder, 'Ctrl+Shift+O')
        file_menu.addSeparator()
        file_menu.addAction('清空列表', self.clear_images, 'Ctrl+N')
        file_menu.addSeparator()
        file_menu.addAction('退出', self.close, 'Ctrl+Q')
        
        # Edit menu
        edit_menu = menubar.addMenu('编辑(&E)')
        edit_menu.addAction('全选', self.select_all_images, 'Ctrl+A')
        edit_menu.addAction('取消选择', self.clear_selection, 'Ctrl+D')
        edit_menu.addAction('删除选中', self.remove_selected_images, 'Delete')
        
        # Watermark menu
        watermark_menu = menubar.addMenu('水印(&W)')
        watermark_menu.addAction('文本水印', self.set_text_watermark)
        watermark_menu.addAction('图片水印', self.set_image_watermark)
        watermark_menu.addSeparator()
        watermark_menu.addAction('重置设置', self.reset_watermark_config)
        
        # Export menu
        export_menu = menubar.addMenu('导出(&E)')
        export_menu.addAction('导出选中图片...', self.export_selected, 'Ctrl+E')
        export_menu.addAction('导出所有图片...', self.export_all, 'Ctrl+Shift+E')
        export_menu.addSeparator()
        export_menu.addAction('导出设置...', self.show_export_settings)
        
        # Tools menu
        tools_menu = menubar.addMenu('工具(&T)')
        tools_menu.addAction('模板管理...', self.show_template_manager)
        tools_menu.addAction('批量处理设置...', self.show_batch_settings)
        tools_menu.addSeparator()
        tools_menu.addAction('首选项...', self.show_preferences, 'Ctrl+,')
        
        # Help menu
        help_menu = menubar.addMenu('帮助(&H)')
        help_menu.addAction('使用帮助', self.show_help, 'F1')
        help_menu.addAction('关于...', self.show_about)
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = self.statusBar()
        
        # Image count label
        self.image_count_label = QLabel("图片: 0")
        self.status_bar.addWidget(self.image_count_label)
        
        # Selected count label
        self.selected_count_label = QLabel("已选择: 0")
        self.status_bar.addWidget(self.selected_count_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        self.status_bar.addWidget(separator)
        
        # Ready label
        self.ready_label = QLabel("就绪")
        self.status_bar.addWidget(self.ready_label)
    
    def create_central_widget(self):
        """Create the central widget with three-panel layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main horizontal layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Image list
        self.image_list_widget = ImageListWidget(self.image_list_model)
        splitter.addWidget(self.image_list_widget)
        
        # Center panel - Preview
        self.preview_widget = PreviewWidget()
        splitter.addWidget(self.preview_widget)
        
        # Right panel - Watermark configuration
        self.config_widget = WatermarkConfigWidget(self.watermark_config)
        splitter.addWidget(self.config_widget)
        
        # Set initial splitter sizes (25%, 50%, 25%)
        splitter.setSizes([300, 600, 300])
        
        # Set minimum sizes for each panel
        self.image_list_widget.setMinimumWidth(250)
        self.preview_widget.setMinimumWidth(400)
        self.config_widget.setMinimumWidth(250)
    
    def setup_connections(self):
        """Setup signal connections between components"""
        # Image list model signals
        self.image_list_model.images_changed.connect(self.update_image_count)
        self.image_list_model.selection_changed.connect(self.update_selection_count)
        
        # Image list widget signals
        self.image_list_widget.image_selected.connect(self.on_image_selected)
        self.image_list_widget.images_dropped.connect(self.on_images_dropped)
        
        # Config widget signals
        self.config_widget.config_changed.connect(self.on_config_changed)
    
    def center_window(self):
        """Center the window on screen"""
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
    
    # Slot methods
    @pyqtSlot()
    def update_image_count(self):
        """Update image count in status bar"""
        count = self.image_list_model.count()
        self.image_count_label.setText(f"图片: {count}")
    
    @pyqtSlot()
    def update_selection_count(self):
        """Update selection count in status bar"""
        count = self.image_list_model.selected_count()
        self.selected_count_label.setText(f"已选择: {count}")
    
    @pyqtSlot(int)
    def on_image_selected(self, index: int):
        """Handle image selection"""
        image_info = self.image_list_model.get_image(index)
        if image_info:
            self.preview_widget.set_image(image_info.file_path)
            self.preview_widget.set_watermark_config(self.watermark_config)
    
    @pyqtSlot(list)
    def on_images_dropped(self, file_paths: List[str]):
        """Handle dropped image files"""
        added_count = self.image_list_model.add_images(file_paths)
        if added_count > 0:
            self.ready_label.setText(f"已添加 {added_count} 张图片")
        else:
            self.ready_label.setText("没有有效的图片文件")
    
    @pyqtSlot()
    def on_config_changed(self):
        """Handle watermark configuration changes"""
        self.preview_widget.set_watermark_config(self.watermark_config)
        self.ready_label.setText("水印配置已更新")
    
    # Menu action methods
    @log_exception
    def import_images(self):
        """Import image files"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            
            logger.info("用户点击导入图片文件")
            
            file_paths, _ = QFileDialog.getOpenFileNames(
                self,
                "选择图片文件",
                "",
                "图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff *.tif);;JPEG 文件 (*.jpg *.jpeg);;PNG 文件 (*.png);;BMP 文件 (*.bmp);;TIFF 文件 (*.tiff *.tif);;所有文件 (*)"
            )
            
            if file_paths:
                logger.info(f"用户选择了 {len(file_paths)} 个文件")
                
                # Filter valid image files
                from utils.file_utils import FileUtils
                logger.debug("过滤有效的图片文件")
                valid_files = FileUtils.filter_image_files(file_paths)
                
                if valid_files:
                    logger.info(f"找到 {len(valid_files)} 个有效图片文件")
                    added_count = self.image_list_model.add_images(valid_files)
                    if added_count > 0:
                        logger.info(f"成功导入 {added_count} 张图片")
                        self.ready_label.setText(f"成功导入 {added_count} 张图片")
                    else:
                        logger.warning("所选图片已存在或无效")
                        self.ready_label.setText("所选图片已存在或无效")
                else:
                    logger.warning("未找到有效的图片文件")
                    self.ready_label.setText("未找到有效的图片文件")
            else:
                logger.info("用户取消了文件选择")
        except Exception as e:
            logger.error(f"导入过程中发生异常: {str(e)}")
            self.ready_label.setText(f"导入失败: {str(e)}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "导入错误", f"导入过程中发生错误:\n{str(e)}")
    
    @log_exception
    def import_folder(self):
        """Import image folder with progress tracking"""
        try:
            from PyQt5.QtWidgets import QFileDialog, QMessageBox
            
            logger.info("用户点击导入文件夹")
            
            folder_path = QFileDialog.getExistingDirectory(
                self,
                "选择包含图片的文件夹",
                ""
            )
            
            if folder_path:
                logger.info(f"用户选择文件夹: {folder_path}")
                
                # Ask if recursive
                reply = QMessageBox.question(
                    self,
                    "扫描方式",
                    "是否包含子文件夹中的图片？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                recursive = (reply == QMessageBox.Yes)
                logger.info(f"递归扫描模式: {recursive}")
                
                # Create and show progress dialog
                progress_dialog = FileImportProgressDialog(self)
                progress_dialog.cancel_requested.connect(lambda: setattr(progress_dialog, 'cancelled', True))
                progress_dialog.start_scanning(folder_path, recursive)
                
                try:
                    # Get image files from folder
                    from utils.file_utils import FileUtils
                    logger.info(f"开始扫描文件夹: {folder_path}")
                    image_files = FileUtils.get_image_files_from_folder(folder_path, recursive)
                    
                    progress_dialog.finish_scanning(len(image_files))
                    logger.info(f"扫描完成，找到 {len(image_files)} 个图片文件")
                    
                    if image_files:
                        # Check for large number of files
                        if len(image_files) > 1000:
                            logger.warning(f"检测到大量文件: {len(image_files)} 个")
                            reply = QMessageBox.question(
                                self,
                                "大量文件",
                                f"找到 {len(image_files)} 个图片文件。\n导入大量文件可能需要较长时间，确定继续吗？",
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.Yes
                            )
                            if reply != QMessageBox.Yes:
                                logger.info("用户取消大量文件导入")
                                progress_dialog.close()
                                return
                        
                        # Start importing
                        progress_dialog.start_importing(len(image_files))
                        
                        # Import in chunks to avoid blocking UI
                        chunk_size = 50  # 减少块大小以更频繁更新进度
                        added_count = 0
                        total_processed = 0
                        
                        logger.info(f"开始分块导入，块大小: {chunk_size}")
                        
                        for i in range(0, len(image_files), chunk_size):
                            if progress_dialog.cancelled:
                                logger.info(f"用户取消导入 (已处理 {total_processed}/{len(image_files)})")
                                break
                                
                            chunk = image_files[i:i + chunk_size]
                            current_file = os.path.basename(chunk[0]) if chunk else ""
                            
                            logger.debug(f"处理块 {i//chunk_size + 1}: {len(chunk)} 个文件")
                            
                            chunk_added = self.image_list_model.add_images(chunk)
                            added_count += chunk_added
                            total_processed = min(i + chunk_size, len(image_files))
                            
                            progress_dialog.update_import_progress(total_processed, added_count, current_file)
                        
                        # Finish importing
                        skipped_count = len(image_files) - added_count
                        progress_dialog.finish_importing(added_count, skipped_count)
                        
                        if added_count > 0:
                            logger.info(f"文件夹导入成功: {added_count} 张图片")
                            self.ready_label.setText(f"从文件夹导入 {added_count} 张图片")
                        else:
                            logger.warning("文件夹中的图片已存在或无效")
                            self.ready_label.setText("文件夹中的图片已存在或无效")
                    else:
                        progress_dialog.finish_importing(0, 0)
                        logger.info("文件夹中未找到图片文件")
                        self.ready_label.setText("文件夹中未找到图片文件")
                        
                    # 延迟显示结果
                    from PyQt5.QtCore import QTimer
                    QTimer.singleShot(2000, progress_dialog.close)
                    
                except Exception as e:
                    progress_dialog.close()
                    logger.error(f"扫描文件夹失败: {str(e)}")
                    self.ready_label.setText(f"扫描文件夹失败: {str(e)}")
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.critical(self, "扫描错误", f"扫描文件夹过程中发生错误:\n{str(e)}")
            else:
                logger.info("用户取消了文件夹选择")
                    
        except Exception as e:
            logger.error(f"文件夹导入过程中发生异常: {str(e)}")
            self.ready_label.setText(f"导入失败: {str(e)}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "导入错误", f"文件夹导入过程中发生错误:\n{str(e)}")
    
    def clear_images(self):
        """Clear all images"""
        self.image_list_model.clear()
        self.preview_widget.clear()
        self.ready_label.setText("已清空图片列表")
    
    def select_all_images(self):
        """Select all images"""
        self.image_list_model.select_all()
    
    def clear_selection(self):
        """Clear image selection"""
        self.image_list_model.clear_selection()
    
    def remove_selected_images(self):
        """Remove selected images"""
        count = self.image_list_model.remove_selected()
        if count > 0:
            self.ready_label.setText(f"已删除 {count} 张图片")
    
    def set_text_watermark(self):
        """Set text watermark mode"""
        logger.info("用户设置水印类型为文字")
        from models.watermark_config import WatermarkType
        self.watermark_config.watermark_type = WatermarkType.TEXT
        self.config_widget.update_config()
        logger.debug(f"文字水印配置: {self.watermark_config.text_config.text}")
        self.ready_label.setText("已切换到文本水印模式")
    
    def set_image_watermark(self):
        """Set image watermark mode"""
        logger.info("用户设置水印类型为图片")
        from models.watermark_config import WatermarkType
        self.watermark_config.watermark_type = WatermarkType.IMAGE
        self.config_widget.update_config()
        logger.debug(f"图片水印配置: {self.watermark_config.image_config.image_path}")
        self.ready_label.setText("已切换到图片水印模式")
    
    def reset_watermark_config(self):
        """Reset watermark configuration"""
        self.watermark_config = WatermarkConfig()
        self.config_widget.set_config(self.watermark_config)
        self.ready_label.setText("水印配置已重置")
    
    def export_selected(self):
        """Export selected images"""
        self._export_images(selected_only=True)
    
    def export_all(self):
        """Export all images"""
        self._export_images(selected_only=False)
    
    def show_export_settings(self):
        """Show export settings dialog"""
        self.ready_label.setText("导出设置将在下一版本实现")
    
    def show_template_manager(self):
        """Show template manager dialog"""
        self.ready_label.setText("模板管理将在下一版本实现")
    
    def show_batch_settings(self):
        """Show batch processing settings"""
        self.ready_label.setText("批量处理设置将在下一版本实现")
    
    def show_preferences(self):
        """Show preferences dialog"""
        self.ready_label.setText("首选项将在下一版本实现")
    
    def show_help(self):
        """Show help dialog"""
        QMessageBox.information(
            self,
            "帮助",
            "PhotoWatermark 专业照片水印工具\n\n"
            "基本使用方法：\n"
            "1. 拖拽图片文件到左侧列表或使用菜单导入\n"
            "2. 在右侧配置面板设置水印参数\n"
            "3. 在中央预览窗口查看效果\n"
            "4. 使用导出菜单保存处理后的图片\n\n"
            "更多功能正在开发中..."
        )
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "关于 PhotoWatermark",
            "PhotoWatermark v1.0.0\n\n"
            "专业的照片水印桌面应用程序\n"
            "支持文本和图片水印，批量处理功能\n\n"
            "基于 MaaAssistantArknights 设计风格\n"
            "使用 PyQt5 和 Pillow 开发"
        )
    
    def closeEvent(self, event):
        """Handle window close event"""
        reply = QMessageBox.question(
            self,
            "确认退出",
            "确定要退出 PhotoWatermark 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Cleanup before closing
            try:
                memory_manager.cleanup_memory()
                if hasattr(self, 'memory_timer'):
                    self.memory_timer.stop()
            except Exception as e:
                print(f"Cleanup error: {e}")
            event.accept()
        else:
            event.ignore()
    
    def setup_memory_monitoring(self):
        """Setup memory monitoring timer"""
        try:
            from PyQt5.QtCore import QTimer
            self.memory_timer = QTimer()
            self.memory_timer.timeout.connect(self.check_memory_usage)
            self.memory_timer.start(30000)  # Check every 30 seconds
        except Exception as e:
            print(f"Memory monitoring setup error: {e}")
    
    def check_memory_usage(self):
        """Check memory usage and cleanup if necessary"""
        try:
            if memory_manager.is_memory_critical():
                print("Critical memory usage detected, performing cleanup...")
                memory_manager.cleanup_memory()
                self.ready_label.setText("内存使用过高，已执行清理")
            elif memory_manager.is_memory_warning():
                print("High memory usage detected")
                memory_manager.force_garbage_collection()
        except Exception as e:
            print(f"Memory check error: {e}")
    
    @log_performance
    def _export_images(self, selected_only: bool = True):
        """导出图片加水印"""
        try:
            from PyQt5.QtWidgets import QFileDialog, QMessageBox
            
            logger.info(f"开始导出图片，仅选中的: {selected_only}")
            
            # Get images to export
            if selected_only:
                images = self.image_list_model.get_selected_images()
                if not images:
                    logger.warning("用户未选择任何图片进行导出")
                    QMessageBox.information(self, "提示", "请先选择要导出的图片")
                    return
            else:
                images = self.image_list_model.get_images()
                if not images:
                    logger.warning("没有图片可以导出")
                    QMessageBox.information(self, "提示", "没有图片可以导出")
                    return
            
            logger.info(f"将导出 {len(images)} 张图片")
            
            # Choose output directory
            logger.debug("显示文件夹选择对话框")
            output_dir = QFileDialog.getExistingDirectory(
                self,
                "选择导出文件夹",
                ""
            )
            
            if not output_dir:
                logger.info("用户取消了文件夹选择")
                return
            
            logger.info(f"选择的导出目录: {output_dir}")
            
            # Create and show progress dialog
            progress_dialog = WatermarkProgressDialog(self)
            progress_dialog.cancel_requested.connect(lambda: setattr(progress_dialog, 'cancelled', True))
            progress_dialog.start_processing(len(images))
            
            # Export images
            exported_count = 0
            failed_count = 0
            
            logger.info("开始批量处理图片水印")
            
            for i, image_info in enumerate(images):
                if progress_dialog.cancelled:
                    logger.info(f"用户取消了导出操作 (已处理 {i}/{len(images)})")
                    break
                
                # Update progress dialog
                progress_dialog.update_progress(image_info.file_name, i + 1)
                
                logger.info(f"开始处理图片 {i+1}/{len(images)}: {image_info.file_name}")
                logger.debug(f"图片路径: {image_info.file_path}")
                logger.debug(f"水印配置: 类型={self.watermark_config.watermark_type}, 位置={self.watermark_config.position}")
                
                try:
                    # Generate output filename
                    base_name = os.path.splitext(image_info.file_name)[0]
                    output_filename = f"{base_name}_watermarked.jpg"
                    output_path = os.path.join(output_dir, output_filename)
                    
                    # Ensure unique filename
                    counter = 1
                    original_output_path = output_path
                    while os.path.exists(output_path):
                        output_filename = f"{base_name}_watermarked_{counter}.jpg"
                        output_path = os.path.join(output_dir, output_filename)
                        counter += 1
                        
                    if counter > 1:
                        logger.debug(f"输出文件名已调整以避免重复: {output_filename}")
                    
                    logger.debug(f"输出路径: {output_path}")
                    
                    # 检查原始文件存在性和可读性
                    if not os.path.exists(image_info.file_path):
                        logger.error(f"原始文件不存在: {image_info.file_path}")
                        failed_count += 1
                        progress_dialog.add_log(f"✗ {image_info.file_name}: 文件不存在")
                        continue
                    
                    # 记录水印处理开始
                    logger.info(f"开始为图片添加水印: {image_info.file_name}")
                    progress_dialog.add_log(f"正在处理: {image_info.file_name}...")
                    
                    # Process image with watermark
                    result_path = self.watermark_engine.process_image(
                        image_info.file_path, 
                        self.watermark_config, 
                        output_path
                    )
                    
                    if result_path:
                        exported_count += 1
                        file_size = os.path.getsize(result_path) if os.path.exists(result_path) else 0
                        logger.info(f"✓ 成功导出: {image_info.file_name} -> {os.path.basename(result_path)} ({file_size} 字节)")
                        progress_dialog.add_log(f"✓ 完成: {os.path.basename(result_path)}")
                    else:
                        failed_count += 1
                        logger.error(f"✗ 水印处理失败: {image_info.file_name}")
                        progress_dialog.add_log(f"✗ 失败: {image_info.file_name}")
                        
                except Exception as e:
                    failed_count += 1
                    logger.error(f"导出异常 {image_info.file_name}: {str(e)}")
                    progress_dialog.add_log(f"✗ 异常: {image_info.file_name} - {str(e)[:50]}")
            
            # Finish progress dialog
            progress_dialog.finish_processing(exported_count, failed_count)
            
            logger.info(f"水印处理完成: 成功 {exported_count}, 失败 {failed_count}")
            
            # Show results after a short delay
            from PyQt5.QtCore import QTimer
            def show_results():
                progress_dialog.close()
                
                if exported_count > 0:
                    message = f"成功导出 {exported_count} 张图片到:\n{output_dir}"
                    if failed_count > 0:
                        message += f"\n\n{failed_count} 张图片导出失败"
                    QMessageBox.information(self, "导出完成", message)
                    self.ready_label.setText(f"已导出 {exported_count} 张图片")
                    logger.info("向用户显示成功导出消息")
                else:
                    QMessageBox.warning(self, "导出失败", "没有图片导出成功")
                    self.ready_label.setText("导出失败")
                    logger.warning("所有图片导出失败")
            
            # 延迟2秒显示结果，让用户看到完成状态
            QTimer.singleShot(2000, show_results)
                
        except Exception as e:
            logger.error(f"导出图片过程中发生异常: {str(e)}")
            self.ready_label.setText(f"导出失败: {str(e)}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "导出错误", f"处理过程中发生错误:\n{str(e)}")