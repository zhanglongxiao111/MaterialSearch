# 缓存管理规范

## ADDED Requirements

### Requirement: 持久化缓存目录

系统 **MUST** 将生成的预览缓存存储在持久化目录中，而非临时目录。

#### Scenario: PDF 缩略图存储到持久化目录

**Given** 用户扫描包含 PDF 文件的目录
**When** 系统生成 PDF 页面缩略图
**Then** 缩略图 **MUST** 存储到 `{CACHE_BASE_DIR}/{target}_cache/pdf_pages/` 目录
**And** 目录 **SHALL** 自动创建（如不存在）

---

### Requirement: 预览图有效性检查

系统 **MUST** 在扫描时检查源文件是否已修改，并更新过期的预览图。

#### Scenario: 检测 PDF 文件修改并更新缩略图

**Given** 数据库中存在某 PDF 文件的记录
**And** 该 PDF 文件的 `modify_time` 已发生变化
**When** 系统重新扫描该目录
**Then** 系统 **MUST** 重新生成该 PDF 的所有页面缩略图
**And** 系统 **MUST** 更新数据库中的 `thumbnail_path` 和 `modify_time`

---

### Requirement: 按需生成预览图

当缓存的预览图不存在时，API **SHALL** 能按需生成。

#### Scenario: 缩略图丢失时按需生成

**Given** 数据库中存在某 PDF 页面的记录
**And** 该页面的缩略图文件不存在
**When** 用户请求 `/api/pdf/page/{id}`
**Then** 系统 **SHALL** 使用 Poppler 实时渲染该页面
**And** 系统 **SHALL** 将渲染结果保存到正确的缓存目录
**And** 系统 **MUST** 返回渲染后的图片

---

### Requirement: 缓存目录配置化

系统 **MUST** 支持通过配置项自定义缓存目录位置。

#### Scenario: 使用环境变量配置缓存目录

**Given** 用户设置环境变量 `CACHE_BASE_DIR=/data/cache`
**When** 系统启动并生成预览缓存
**Then** 缓存文件 **MUST** 存储到 `/data/cache/{target}_cache/` 目录
