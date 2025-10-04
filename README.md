# PhotoWatermark

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/LAYCorax/PhotoWatermark/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://github.com/LAYCorax/PhotoWatermark)

> 功能强大的图片批量水印工具，支持文本和图片水印，提供丰富的配置选项和模板系统。

## 📥 下载

**最新版本：v2.0.0**

- [下载 Windows 可执行文件](https://github.com/LAYCorax/PhotoWatermark/releases/latest) (46 MB)
- 系统要求：Windows 7/8/10/11 (64位)
- 无需安装Python环境，双击即可运行

## ✨ 主要功能

### 🎨 水印功能
- **文本水印** - 自定义文字、字体、颜色、大小、透明度
- **图片水印** - 支持PNG/JPG，可缩放和调节透明度
- **描边效果** - 可调颜色、宽度、透明度
- **阴影效果** - 可调颜色、偏移、透明度
- **位置控制** - 九宫格定位 + 自定义坐标 + 旋转角度

### 🚀 高级功能
- **模板系统** - 保存/加载/导入/导出水印配置
- **批量处理** - 一次处理多张图片
- **实时预览** - 所见即所得
- **导出选项** - 多格式、图片缩放、质量控制
- **智能检查** - 覆盖警告、进度显示

## 🚀 快速开始

### 使用可执行文件（推荐）

1. [下载最新版本](https://github.com/LAYCorax/PhotoWatermark/releases/latest)
2. 双击运行 `PhotoWatermark.exe`
3. 拖拽图片到窗口
4. 配置水印设置
5. 导出处理后的图片

### 从源码运行

```bash
# 克隆项目
git clone https://github.com/LAYCorax/PhotoWatermark.git
cd PhotoWatermark

# 安装依赖
pip install -r requirements.txt

# 运行程序
python launcher.py
```

## 📖 使用指南

详细使用方法请参考 [用户手册](USER_GUIDE.md)

### 基本操作流程

1. **导入图片**
   - 拖拽图片/文件夹到窗口
   - 或通过菜单：文件 → 导入图片/导入文件夹

2. **配置水印**
   - 选择"文本水印"或"图片水印"标签
   - 设置文字、字体、颜色等参数
   - 可选：启用描边或阴影效果
   - 调整位置、边距、旋转角度

3. **预览效果**
   - 在中央预览区域查看实时效果
   - 可使用鼠标滚轮缩放预览

4. **导出图片**
   - 菜单：文件 → 导出设置
   - 选择输出路径和格式
   - 可选：设置图片缩放
   - 点击"开始导出"

### 使用模板

- **保存模板**：工具 → 模板管理 → 保存当前配置为模板
- **应用模板**：工具 → 模板管理 → 选择模板 → 应用
- **管理模板**：支持导入/导出/删除模板

## 📋 适用场景

| 场景 | 说明 |
|------|------|
| 📷 摄影作品 | 为照片添加版权信息和署名 |
| 🎨 设计图片 | 批量添加品牌标识或logo |
| 📱 社交媒体 | 快速处理发布图片 |
| 📄 文档配图 | 统一添加来源标注 |
| 🏢 企业用途 | 批量加工产品图片 |

## 🛠️ 技术栈

- **Python** 3.13
- **PyQt5** - GUI框架
- **Pillow** - 图像处理
- **PyInstaller** - 应用打包

## 📊 项目特性

- ✅ 直观的图形界面
- ✅ 实时预览功能
- ✅ 批量处理能力
- ✅ 模板管理系统
- ✅ 多格式支持
- ✅ 高性能处理
- ✅ 智能内存管理

## ⚠️ 注意事项

- 首次启动可能需要5-10秒加载
- 超大图片（>25MP）处理较慢，程序会自动优化
- 杀毒软件可能误报，请添加信任
- 建议使用系统自带字体以获得最佳兼容性

## 🐛 问题反馈

遇到问题或有建议？

- [提交Issue](https://github.com/LAYCorax/PhotoWatermark/issues)
- 请附上错误信息和日志文件（位于 `logs/` 目录）

## 📜 许可证

本项目基于 MIT License 开源 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

感谢以下开源项目：
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI框架
- [Pillow](https://python-pillow.org/) - 图像处理
- [PyInstaller](https://www.pyinstaller.org/) - 应用打包

## 📈 版本历史

- **v2.0.0** (2025-10-04) - 正式发布，完整功能实现
- **v1.0.0** (2025-10-02) - 初始版本

---

**PhotoWatermark** - 让图片水印变得简单专业 ✨

**开发者**: LAYCorax  
**项目地址**: https://github.com/LAYCorax/PhotoWatermark
