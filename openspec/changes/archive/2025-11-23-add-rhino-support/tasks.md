## 1. 核心功能实现 (Core)
- [x] 1.1 在 `utils_image.py` 中实现 `extract_rhino_preview(file_path)` 函数。
    - [x] 实现 Windows Shell (IShellItemImageFactory) 提取逻辑（首选）。
    - [x] 实现二进制扫描（BMP/PNG）提取逻辑（备选）。
    - [x] 增加多线程 COM 初始化支持。
    - [x] 调整预览图请求尺寸为 2048x2048 (2K)。

## 2. 扫描逻辑升级 (Scanner)
- [x] 2.1 修改 `config.py` 中的 `IMAGE_EXTENSIONS` 列表，加入 `.3dm`。
- [x] 2.2 验证扫描器能否正确识别 .3dm 文件并进入处理队列。

## 3. 图片处理与存储 (Processor & Storage)
- [x] 3.1 修改 `process_assets.py` 中的 `process_image` 函数。
    - [x] 当检测到 `.3dm` 时，调用提取函数获取 PIL Image 对象。
    - [x] 使用提取的 Image 对象进行 CLIP 特征计算、宽高比计算和哈希计算。
- [x] 3.2 确保数据库写入时 `file_format` 字段正确记录为 `3dm`。

## 4. API 服务适配 (Backend)
- [x] 4.1 修改 `routes.py` 中的图片服务接口。
    - [x] 增加对 `3dm` 格式的判断分支，返回实时预览流。
    - [x] 修改缩略图接口，支持 .3dm 缩略图生成。

## 5. 验证与测试
- [x] 5.1 手动测试：验证了 .3dm 文件能被扫描和索引。
- [x] 5.2 前端验证：验证了能看到高清预览图。
- [x] 5.3 集成测试：通过 `verify_integration.py` 验证了完整提取流程。
