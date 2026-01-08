# 旧代码迁移规范

## 目标

将根目录的旧 .py 文件逻辑迁移到 `app/` 模块化架构，清理根目录。

## 迁移原则

1. **保持功能不变** - 迁移后所有 API 行为必须与现在一致
2. **渐进式迁移** - 每个模块单独迁移，独立验证
3. **保留兼容层** - 在根目录保留 stub 文件，避免外部依赖断裂

## 文件映射

| 旧文件 (根目录) | 新位置 | 说明 |
|----------------|--------|------|
| `search.py` | `app/services/search_service.py` | 搜索逻辑 |
| `scan.py` | `app/services/scan_service.py` | 扫描逻辑 |
| `database.py` | `app/integrations/sqlite_manager.py` | 数据库管理 |
| `models.py` | `app/models/*.py` | 数据模型 |
| `routes.py` | `app/api/*.py` | 拆分到各 Blueprint |
| `process_assets.py` | `app/services/asset_service.py` | 资源处理 |
| `project_manager.py` | `app/services/project_service.py` | 项目管理 |
| `archive.py` | `app/services/archive_service.py` | 归档功能 |
| `dedup_service.py` | `app/services/dedup_service.py` | 去重服务 |
| `utils.py` | `app/utils/common.py` | 通用工具 |
| `utils_image.py` | `app/utils/image.py` | 图片工具 |

## 迁移步骤

### Step 1: models.py → app/models/

拆分为：
- `app/models/image.py` - Image, ImageArchived
- `app/models/video.py` - Video
- `app/models/pdf.py` - PDFPage
- `app/models/project.py` - Project
- `app/models/dedup.py` - DedupJob, DedupResult
- `app/models/base.py` - BaseModel, BaseModelProject

### Step 2: database.py → app/integrations/sqlite_manager.py

移动：
- `DatabaseManager` 类
- `get_db_manager()` 函数
- 所有数据库操作函数

更新导入：
```python
# 所有 from database import xxx
# 改为 from app.integrations.sqlite_manager import xxx
```

### Step 3: search.py → app/services/search_service.py

将以下函数迁移到 `SearchService` 类：
- `clean_cache` → 全局函数
- `search_image_by_feature` → `_search_by_feature`
- `search_image_by_text_path_time` → `search_images_by_text`
- `search_image_by_image` → `search_images_by_image`
- `search_video_by_feature` → `_search_video_by_feature`
- `search_video_by_text_path_time` → `search_videos_by_text`
- `search_video_by_image` → `search_videos_by_image`
- `get_index_pairs` → `_get_index_pairs`
- `get_video_range` → `_get_video_range`

### Step 4: scan.py → app/services/scan_service.py

将以下迁移到 `ScanService` 类：
- `scanning` 全局变量 → 类属性
- `status` 全局变量 → 类属性
- `do_scan_new` → `start_scan`
- 扫描线程管理

### Step 5: routes.py → app/api/*.py

已有 Blueprint 结构，需要：
1. 将 `routes.py` 中的实际逻辑移入对应 Blueprint
2. 删除 Blueprint 中对 `routes.py` 的调用

### Step 6: 其他模块

按照相同模式迁移 archive.py, dedup_service.py, project_manager.py, process_assets.py, utils.py, utils_image.py

## 验证清单

每个模块迁移后验证：

- [ ] `python -c "from app import create_app; app = create_app()"`
- [ ] `python -m pytest tests/test_core_functions.py -v`
- [ ] 手动测试：搜索、扫描、项目管理

## 根目录兼容层 (可选)

迁移后可在根目录保留 stub 文件：

```python
# search.py (stub)
from app.services.search_service import *
from app.services.search_service import clean_cache
```

这样外部脚本的 `from search import xxx` 仍然有效。

## 注意事项

1. **config.py 保留** - 不迁移，保持在根目录
2. **main.py 精简** - 只保留 `from app import create_app; app.run()`
3. **process_assets.py 特殊** - 包含 CLIP 模型加载，需要小心处理
4. **循环导入** - 注意避免 app ↔ legacy 循环导入
