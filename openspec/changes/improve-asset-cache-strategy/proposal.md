# 改进素材预览缓存策略

## 概述

当前系统对需要生成预览图的文件格式（PDF、犀牛 .3dm）存在以下问题：

1. **存储位置不合理**：PDF 预览图存储在 `./tmp/` 临时目录，容易被误删除
2. **缺乏有效性验证**：源文件修改后，预览图不会自动更新
3. **存储策略不统一**：犀牛文件实时提取预览（正确），PDF 扫描时生成并缓存（有风险）

## 目标

1. 将预览缓存存储到持久化目录，跟随项目/库的生命周期
2. 添加有效性校验机制，确保预览图与源文件同步
3. 支持按需生成预览图，作为缓存失效时的后备方案
4. 提供灵活的配置选项，适应不同部署场景（本地/Docker/服务器）

## 范围

### 包含
- PDF 页面缩略图存储策略改进
- 预览图有效性检查机制
- 按需生成预览图的后备方案
- 缓存目录配置化

### 不包含
- 犀牛文件处理（当前实时提取策略已正确）
- 视频帧缩略图（当前直接使用帧数据，无需缓存）
- 前端修改（API 保持不变）

## 技术方案

### 存储目录结构

```
instance/
├── permanent.db
├── permanent_cache/              ← 永久库缓存
│   └── pdf_pages/
│       └── {checksum}_p{page}.jpg
├── projects/
│   ├── proj_xxxx.db
│   └── proj_xxxx_cache/          ← 项目级缓存
│       └── pdf_pages/
│           └── {checksum}_p{page}.jpg
└── projects_metadata.db
```

### 有效性检查策略

| 检查时机 | 检查方式 | 动作 |
|---------|---------|------|
| 扫描时 | 比较 `modify_time` | 变化则重新生成缩略图 |
| API 请求时 | 检查缩略图文件是否存在 | 不存在则按需生成 |

### 配置项

```python
# config.py 新增
CACHE_BASE_DIR = os.getenv('CACHE_BASE_DIR', './instance')
PDF_CACHE_SUBDIR = 'pdf_pages'
ENABLE_ON_DEMAND_PDF_RENDER = True  # 是否启用按需渲染
```

## 优先级

**中等** - 改善用户体验，但不阻塞核心功能。建议在完成 `refactor-supabase-migration` 后实施。

## 依赖

- `refactor-supabase-migration` 变更（需完成迁移后再调整缓存路径）
- Poppler 工具（PDF 渲染，已在项目中配置）

## 风险

1. **迁移现有缓存**：需要处理旧的 `./tmp/pdf_pages/` 数据
2. **磁盘空间**：PDF 缩略图会占用额外空间，需要考虑清理策略
