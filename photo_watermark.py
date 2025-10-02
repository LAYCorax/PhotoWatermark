import os
import sys
import argparse
from PIL import Image, ImageDraw, ImageFont
import piexif
from datetime import datetime

# Supported positions
POSITIONS = {
    'left_top': (0, 0),
    'center': 'center',
    'right_bottom': 'right_bottom'
}

def get_exif_datetime(image_path):
    try:
        exif_dict = piexif.load(image_path)
        dt = exif_dict['Exif'].get(piexif.ExifIFD.DateTimeOriginal)
        if dt:
            dt_str = dt.decode('utf-8')
            date = datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S')
            return date.strftime('%Y-%m-%d')
    except Exception:
        pass
    return None

def add_watermark(img_path, text, font_size, color, position, out_path):
    image = Image.open(img_path)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()
    w, h = image.size
    text_w, text_h = draw.textsize(text, font=font)
    if position == 'left_top':
        xy = (10, 10)
    elif position == 'center':
        xy = ((w - text_w) // 2, (h - text_h) // 2)
    elif position == 'right_bottom':
        xy = (w - text_w - 10, h - text_h - 10)
    else:
        xy = (10, 10)
    draw.text(xy, text, fill=color, font=font)
    image.save(out_path)

def main():
    parser = argparse.ArgumentParser(description='图片批量添加拍摄日期水印')
    parser.add_argument('img_dir', help='图片文件夹路径')
    parser.add_argument('--font_size', type=int, default=32, help='字体大小')
    parser.add_argument('--color', type=str, default='white', help='字体颜色')
    parser.add_argument('--position', type=str, choices=['left_top', 'center', 'right_bottom'], default='right_bottom', help='水印位置')
    args = parser.parse_args()

    img_dir = args.img_dir
    font_size = args.font_size
    color = args.color
    position = args.position

    if not os.path.isdir(img_dir):
        print('图片文件夹路径不存在')
        sys.exit(1)

    out_dir = os.path.join(img_dir, os.path.basename(img_dir) + '_watermark')
    os.makedirs(out_dir, exist_ok=True)

    for fname in os.listdir(img_dir):
        fpath = os.path.join(img_dir, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            date_text = get_exif_datetime(fpath)
            if not date_text:
                print(f'{fname} 没有拍摄日期 exif 信息，跳过')
                continue
            out_path = os.path.join(out_dir, fname)
            add_watermark(fpath, date_text, font_size, color, position, out_path)
            print(f'已处理: {fname}')
        except Exception as e:
            print(f'处理 {fname} 时出错: {e}')

if __name__ == '__main__':
    main()
