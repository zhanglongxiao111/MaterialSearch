# Change: 增加 Rhino (.3dm) 文件提取预览图支持

## Why
目前素材库仅支持常规图片（jpg, png 等）和视频。在设计领域（尤其是建筑、室内、景观），Rhino (.3dm) 是核心生产力工具。3dm 文件通常包含高价值的预览图，能直接反映模型内容。
支持索引 .3dm 文件并提取其预览图，将极大地扩展素材库在专业设计场景下的可用性，使用户能像搜索图片一样搜索模型文件。

## What Changes
- **扫描器升级**：`scan.py` 支持识别 `.3dm` 后缀。
- **预览图提取**：新增 `extract_rhino_preview` 工具函数，通过读取二进制文件头（无需安装 Rhino）直接提取内嵌的 BMP/PNG 预览图。
- **数据存储**：`Image` 表将存储 `.3dm` 文件记录，但在前端展示和特征计算时使用提取出的预览图。
- **API 适配**：后端 API 在服务 `.3dm` 类型的图片请求时，动态返回提取的预览图流。

## Impact
- **受影响的规范**：
    - `scan-to-library`: 扫描规则变更。
    - `image-storage`: 图片处理与存储逻辑变更。
- **受影响的代码**：
    - `scan.py`: 文件扩展名白名单。
    - `utils_image.py` / `process_assets.py`: 新增提取逻辑。
    - `routes.py`: 图片流服务逻辑。

## Notes
- Windows 场景若希望通过系统缩略图提取，需要安装 `comtypes` + `pywin32`；未安装时会自动使用二进制解析，仍可工作。
- 预览图会缓存在项目下 `rhino_preview_cache/`，基于路径+mtime+size 生成 key，文件修改后自动失效重建。
- 手工验证：`python verify_binary_parser.py "<3dm 文件路径>"` 可直接输出提取到的预览图（`test_binary_parser_output.png`）。
