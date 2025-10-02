"""
File utilities for handling image files and directories
"""
import os
from typing import List, Set
from PIL import Image
from utils.logger import logger, log_exception


class FileUtils:
    """Utility class for file operations"""
    
    # Supported image formats
    SUPPORTED_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'
    }
    
    # MIME type mapping
    FORMAT_MIME_MAP = {
        'JPEG': 'image/jpeg',
        'PNG': 'image/png',
        'BMP': 'image/bmp',
        'TIFF': 'image/tiff'
    }
    
    @classmethod
    @log_exception
    def is_image_file(cls, file_path: str) -> bool:
        """Check if file is a supported image format"""
        logger.debug(f"检查文件格式: {os.path.basename(file_path)}")
        if not os.path.isfile(file_path):
            logger.debug(f"文件不存在: {file_path}")
            return False
        
        ext = os.path.splitext(file_path.lower())[1]
        is_supported = ext in cls.SUPPORTED_EXTENSIONS
        logger.debug(f"文件格式 {ext} 支持状态: {is_supported}")
        return is_supported
    
    @classmethod
    @log_exception
    def get_image_files_from_folder(cls, folder_path: str, recursive: bool = False, max_files: int = 10000) -> List[str]:
        """Get all image files from a folder with size limit"""
        logger.info(f"扫描文件夹: {folder_path}, 递归={recursive}, 最大文件数={max_files}")
        image_files = []
        
        if not os.path.isdir(folder_path):
            logger.warning(f"文件夹不存在: {folder_path}")
            return image_files
        
        try:
            if recursive:
                for root, dirs, files in os.walk(folder_path):
                    # Skip hidden directories and system directories
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d.lower() not in ['$recycle.bin', 'system volume information']]
                    
                    for file in files:
                        if len(image_files) >= max_files:
                            logger.warning(f"已达到最大文件限制 ({max_files}), 停止扫描")
                            break
                            
                        file_path = os.path.join(root, file)
                        try:
                            if cls.is_image_file(file_path):
                                image_files.append(file_path)
                                logger.debug(f"找到图片文件: {file_path}")
                        except (OSError, PermissionError) as e:
                            logger.debug(f"无法访问文件 {file_path}: {e}")
                            continue
                    
                    if len(image_files) >= max_files:
                        break
            else:
                try:
                    files = os.listdir(folder_path)
                    for file in files:
                        if len(image_files) >= max_files:
                            break
                            
                        file_path = os.path.join(folder_path, file)
                        try:
                            if cls.is_image_file(file_path):
                                image_files.append(file_path)
                        except (OSError, PermissionError):
                            # Skip files that can't be accessed
                            continue
                except PermissionError as e:
                    logger.error(f"无权访问文件夹: {folder_path} - {e}")
                    
        except PermissionError as e:
            logger.error(f"无权访问文件夹: {folder_path} - {e}")
        except Exception as e:
            logger.error(f"扫描文件夹错误 {folder_path}: {e}")
        
        logger.info(f"扫描完成, 找到 {len(image_files)} 个图片文件")
        return sorted(image_files)
    
    @classmethod
    @log_exception
    def filter_image_files(cls, file_paths: List[str]) -> List[str]:
        """Filter list to only include valid image files"""
        logger.debug(f"过滤图片文件, 输入 {len(file_paths)} 个文件")
        valid_files = [path for path in file_paths if cls.is_image_file(path)]
        logger.debug(f"过滤后剩余 {len(valid_files)} 个有效图片文件")
        return valid_files
    
    @classmethod
    def validate_image_file(cls, file_path: str) -> bool:
        """Validate that file is a readable image"""
        if not cls.is_image_file(file_path):
            return False
        
        try:
            with Image.open(file_path) as img:
                img.verify()  # Verify the image integrity
            return True
        except Exception:
            return False
    
    @classmethod
    def get_image_format(cls, file_path: str) -> str:
        """Get image format string"""
        try:
            with Image.open(file_path) as img:
                return img.format or "Unknown"
        except Exception:
            return "Unknown"
    
    @classmethod
    def get_file_size_string(cls, file_path: str) -> str:
        """Get human-readable file size"""
        try:
            size = os.path.getsize(file_path)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except Exception:
            return "Unknown"
    
    @classmethod
    def ensure_directory_exists(cls, directory: str) -> bool:
        """Ensure directory exists, create if necessary"""
        try:
            os.makedirs(directory, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directory {directory}: {e}")
            return False
    
    @classmethod
    def get_safe_filename(cls, filename: str) -> str:
        """Get safe filename by removing invalid characters"""
        invalid_chars = '<>:"/\\|?*'
        safe_name = filename
        for char in invalid_chars:
            safe_name = safe_name.replace(char, '_')
        return safe_name
    
    @classmethod
    def generate_output_filename(cls, original_path: str, prefix: str = "", 
                                suffix: str = "", extension: str = None) -> str:
        """Generate output filename with prefix/suffix"""
        base_name = os.path.splitext(os.path.basename(original_path))[0]
        original_ext = os.path.splitext(original_path)[1]
        
        # Use provided extension or original
        output_ext = extension if extension else original_ext
        
        # Construct new filename
        new_name = f"{prefix}{base_name}{suffix}{output_ext}"
        return cls.get_safe_filename(new_name)
    
    @classmethod
    def is_path_safe(cls, path: str, base_path: str = None) -> bool:
        """Check if path is safe (no directory traversal)"""
        try:
            abs_path = os.path.abspath(path)
            if base_path:
                abs_base = os.path.abspath(base_path)
                return abs_path.startswith(abs_base)
            return True
        except Exception:
            return False