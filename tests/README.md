# PhotoWatermark Tests

本目录包含PhotoWatermark应用程序的所有测试文件和报告。

## 测试文件分类

### 核心功能测试
- `test_core.py` - 核心功能测试
- `test_color.py` - 颜色处理测试
- `test_rgba_fix.py` - RGBA格式修复测试
- `test_rgba_simple.py` - RGBA简单测试

### 性能和极限测试
- `test_large_image.py` - 大图片处理测试
- `test_large_scale.py` - 大规模文件处理测试
- `test_real_large_image.py` - 真实大图片测试
- `test_extreme_cases.py` - 极限情况测试

### 日志和应用程序测试
- `test_logging.py` - 基础日志功能测试
- `test_complete_logging.py` - 完整应用日志测试
- `test_app_startup.py` - 应用启动测试
- `test_all_modules_logging.py` - 全模块日志功能测试

### 报告和文档
- `robustness_enhancement_report.py` - 鲁棒性增强报告
- `final_logging_integration_report.py` - 最终日志集成报告

## 运行测试

### 单个测试
```bash
python tests/test_core.py
```

### 所有测试
```bash
# 从项目根目录运行
python -m pytest tests/
```

### 特定类型测试
```bash
# 日志测试
python tests/test_all_modules_logging.py

# 性能测试
python tests/test_large_image.py
```

## 测试环境要求

- Python 3.7+
- PyQt5
- Pillow (PIL)
- 足够的内存处理大图片测试

## 注意事项

1. 大图片测试可能需要较长时间
2. 极限测试会使用大量内存
3. 日志测试会在logs目录生成日志文件
4. 部分测试需要创建临时文件