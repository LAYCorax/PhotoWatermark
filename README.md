# PhotoWatermark

## 工具简介
PhotoWatermark 是一个 Python 命令行工具，可批量为图片添加拍摄日期水印。水印内容自动读取图片 exif 拍摄日期（如无则用文件修改日期），支持自定义字体大小、颜色和位置。

## 安装依赖
```bash
pip install Pillow piexif
```

## 使用方法
```bash
python photo_watermark.py <图片文件夹路径> [--font_size 字体大小] [--color 颜色] [--position 位置]
```

参数说明：
- `图片文件夹路径`：待处理图片所在文件夹。
- `--font_size`：水印字体大小，默认 32。
- `--color`：水印字体颜色，默认 white。
- `--position`：水印位置，可选 left_top、center、right_bottom，默认 right_bottom。

## 示例
```bash
python photo_watermark.py ./tests --font_size 64 --color yellow --position center
```

处理结果会保存到原目录下的 `_watermark` 子目录。

## 支持格式
支持常见图片格式（如 JPG、PNG）。

## 注意事项
- 若图片无 exif 拍摄日期，则使用文件修改时间。
- 需确保图片文件有读写权限。

## 许可证
MIT
