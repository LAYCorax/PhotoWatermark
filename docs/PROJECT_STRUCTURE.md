# PhotoWatermark 项目结构

## 📁 目录结构

```
PhotoWatermark/
├── 📄 main.py                     # 主程序入口
├── 📄 launcher.py                 # 启动器脚本
├── 📄 requirements.txt            # Python依赖列表
├── 📄 LICENSE                     # 开源协议
├── 📄 README.md                   # 项目说明文档
├── 📄 .gitignore                  # Git忽略规则
│
├── 📁 ui/                         # 用户界面模块
│   ├── 📄 __init__.py
│   ├── 📄 main_window.py          # 主窗口
│   ├── 📁 widgets/                # UI组件
│   │   ├── 📄 __init__.py
│   │   ├── 📄 image_list_widget.py      # 图片列表组件
│   │   ├── 📄 preview_widget.py         # 预览组件
│   │   └── 📄 watermark_config_widget.py # 水印配置组件
│   └── 📁 dialogs/               # 对话框
│       ├── 📄 __init__.py
│       ├── 📄 file_import_progress_dialog.py    # 文件导入进度对话框
│       └── 📄 watermark_progress_dialog.py      # 水印处理进度对话框
│
├── 📁 core/                       # 核心功能模块
│   ├── 📄 __init__.py
│   └── 📄 watermark_engine.py     # 水印处理引擎
│
├── 📁 models/                     # 数据模型
│   ├── 📄 __init__.py
│   ├── 📄 image_info.py           # 图片信息模型
│   └── 📄 watermark_config.py     # 水印配置模型
│
├── 📁 utils/                      # 工具函数
│   ├── 📄 __init__.py
│   ├── 📄 file_utils.py           # 文件处理工具
│   ├── 📄 logger.py               # 日志系统
│   └── 📄 memory_manager.py       # 内存管理工具
│
├── 📁 resources/                  # 资源文件
│   ├── 📁 icons/                  # 图标资源
│   └── 📁 styles/                 # 样式文件
│
├── 📁 config/                     # 配置文件
│   └── 📄 default_config.json     # 默认配置
│
├── 📁 tests/                      # 测试文件
│   ├── 📄 __init__.py
│   ├── 📄 README.md              # 测试说明
│   ├── 📁 unit/                  # 单元测试
│   │   ├── 📄 test_core.py
│   │   ├── 📄 test_logging.py
│   │   └── 📄 test_watermark_engine_logging.py
│   ├── 📁 integration/           # 集成测试
│   │   ├── 📄 test_complete_logging.py
│   │   ├── 📄 test_all_modules_logging.py
│   │   └── 📄 test_app_startup.py
│   └── 📁 功能测试文件...
│
├── 📁 scripts/                    # 开发脚本
│   ├── 📄 font_system_info.py     # 字体系统信息
│   ├── 📄 test_*.py              # 各种测试脚本
│   └── 📄 create_small_test.py    # 创建测试文件
│
├── 📁 docs/                       # 文档
│   ├── 📄 PhotoWatermark_GUI_Design.md  # GUI设计文档
│   ├── 📄 PROJECT_SUMMARY.md            # 项目总结
│   ├── 📄 STATUS.md                     # 状态文档
│   └── 📁 reports/                      # 开发报告
│       ├── 📄 final_logging_integration_report.py
│       ├── 📄 preview_import_enhancement_report.py
│       ├── 📄 project_structure_report.py
│       ├── 📄 robustness_enhancement_report.py
│       └── 📄 watermark_enhancement_report.py
│
├── 📁 logs/                       # 日志文件 (gitignore)
├── 📁 temp_thumbnails/           # 临时缩略图 (gitignore)
├── 📁 build/                     # 构建文件 (gitignore)
└── 📁 dist/                      # 发布文件 (gitignore)
```

## 🎯 核心功能模块

### 1. 用户界面 (ui/)
- **main_window.py**: 主窗口，应用程序的核心界面
- **widgets/**: 可重用的UI组件
- **dialogs/**: 各种对话框，包括进度显示

### 2. 核心引擎 (core/)
- **watermark_engine.py**: 水印处理的核心逻辑，支持文本和图片水印

### 3. 数据模型 (models/)
- **image_info.py**: 图片信息的数据结构
- **watermark_config.py**: 水印配置的数据结构

### 4. 工具函数 (utils/)
- **logger.py**: 统一的日志系统
- **file_utils.py**: 文件操作工具
- **memory_manager.py**: 内存管理工具

## 🚀 关键特性

- ✅ **大图片支持**: 智能缩放，支持超大图片(>50MP)预览
- ✅ **内存优化**: 保守内存管理，防止崩溃
- ✅ **中文字体**: 美观的中文字体显示系统
- ✅ **进度显示**: 用户友好的进度对话框
- ✅ **全面日志**: 完整的调试和错误日志
- ✅ **批量处理**: 支持批量导入和处理图片
- ✅ **多格式支持**: 支持 JPEG, PNG, BMP, TIFF 等格式

## 📝 开发规范

- 所有Python文件都有适当的docstring
- 使用统一的中文字体系统
- 错误处理和日志记录完善
- 代码结构清晰，模块化设计
- Git提交使用规范的中文commit message