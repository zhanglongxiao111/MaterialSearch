# 任务清单

## Phase 1: 配置与基础设施

- [ ] **1.1** 在 `config.py` 中添加缓存目录配置项
  - `CACHE_BASE_DIR`：缓存根目录
  - `PDF_CACHE_SUBDIR`：PDF 缓存子目录名
  - `ENABLE_ON_DEMAND_PDF_RENDER`：是否启用按需渲染
  - 验证：配置项可通过环境变量覆盖

- [ ] **1.2** 创建缓存目录管理工具函数
  - `get_cache_dir(target: str) -> Path`：获取指定库的缓存目录
  - `get_pdf_cache_dir(target: str) -> Path`：获取 PDF 缓存目录
  - `ensure_cache_dir(target: str) -> Path`：确保目录存在
  - 验证：单元测试覆盖 permanent/project 两种场景

## Phase 2: 扫描服务改进

- [ ] **2.1** 修改 PDF 扫描逻辑，将缩略图存储到新目录
  - 修改 `app/services/scan_service.py` 中 PDF 相关处理
  - 缩略图路径格式：`{cache_dir}/pdf_pages/{checksum}_p{page}.jpg`
  - 验证：新扫描的 PDF 缩略图存储到正确位置

- [ ] **2.2** 添加 PDF 有效性检查
  - 扫描时比较源文件 `modify_time` 与数据库记录
  - 变化时重新生成缩略图并更新数据库
  - 验证：修改 PDF 后重新扫描，缩略图更新

## Phase 3: API 改进

- [ ] **3.1** 实现按需生成 PDF 缩略图
  - 修改 `/api/pdf/page/<id>` 路由
  - 缩略图不存在时，尝试使用 Poppler 实时渲染
  - 渲染后保存到缓存目录供后续使用
  - 验证：删除缩略图后请求 API，能正确返回图片

- [ ] **3.2** 添加缓存健康检查 API（可选）
  - `GET /api/admin/cache/status`：返回缓存目录使用情况
  - `POST /api/admin/cache/rebuild`：重建指定库的缩略图缓存
  - 验证：API 正常响应并执行操作

## Phase 4: 迁移与兼容

- [ ] **4.1** 编写迁移脚本处理旧缓存
  - 将 `./tmp/pdf_pages/` 中的文件迁移到新目录
  - 更新数据库中的 `thumbnail_path` 字段
  - 验证：迁移后旧路径的 PDF 能正常显示

- [ ] **4.2** 更新文档
  - 更新 README 中的部署说明
  - 添加缓存目录配置文档
  - 验证：文档与实现一致

## 验收标准

1. PDF 预览图存储在持久化目录，不受临时文件清理影响
2. 修改 PDF 文件后，重新扫描会更新预览图
3. 缩略图丢失时，API 能按需生成并返回
4. 配置项支持环境变量覆盖，适应不同部署场景
