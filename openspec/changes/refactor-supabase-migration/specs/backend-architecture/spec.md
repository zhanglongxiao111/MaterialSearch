# Backend Architecture Specification

## ADDED Requirements

### Requirement: 分层架构

系统 SHALL 采用 API → Services → Repositories 三层分离架构，每层职责明确。

#### Scenario: API 层职责
- **WHEN** 请求到达 API 层 (`app/api/`)
- **THEN** API 层仅处理 HTTP 请求解析和响应序列化
- **AND** API 层不包含业务逻辑，仅调用 Service 层

#### Scenario: Service 层职责
- **WHEN** API 层调用 Service 层 (`app/services/`)
- **THEN** Service 层处理业务逻辑和跨 Repository 协调
- **AND** Service 层负责事务管理

#### Scenario: Repository 层职责
- **WHEN** Service 层调用 Repository 层 (`app/repositories/`)
- **THEN** Repository 层封装所有数据访问操作
- **AND** Repository 层屏蔽底层存储细节 (Supabase/SQLite)

### Requirement: 模块化文件大小限制

系统 SHALL 限制单个模块文件不超过 300 行代码，以保证 AI 辅助编程的可读性。

#### Scenario: Blueprint 模块大小
- **WHEN** 创建新的 API Blueprint 模块
- **THEN** 每个 Blueprint 文件不超过 300 行 (不含空行和注释)
- **AND** 如超过限制则拆分为多个子模块

#### Scenario: Service 模块大小
- **WHEN** 创建新的 Service 模块
- **THEN** 每个 Service 文件不超过 300 行
- **AND** 复杂业务逻辑拆分为多个专用 Service

### Requirement: App Factory 模式

系统 SHALL 使用 Flask App Factory 模式创建应用实例。

#### Scenario: 创建应用
- **WHEN** 调用 `create_app(config_name)` 函数
- **THEN** 返回配置完成的 Flask 应用实例
- **AND** 所有 Blueprint 已注册

#### Scenario: 配置隔离
- **WHEN** 使用不同的 `config_name` ('development', 'production', 'testing')
- **THEN** 应用加载对应的配置类
- **AND** 配置通过环境变量覆盖

### Requirement: Blueprint 路由组织

系统 SHALL 将 API 路由按功能域组织为独立的 Blueprint 模块。

#### Scenario: Blueprint 注册
- **WHEN** 应用初始化时
- **THEN** 自动注册以下 Blueprint:
  - `auth_bp` → `/api/auth`
  - `search_bp` → `/api/search`
  - `projects_bp` → `/api/projects`
  - `assets_bp` → `/api/assets`
  - `archive_bp` → `/api/archive`
  - `dedup_bp` → `/api/dedup`
  - `scan_bp` → `/api/scan`

#### Scenario: 版本化 API
- **WHEN** 需要引入破坏性变更
- **THEN** 新 Blueprint 注册到 `/api/v2/` 前缀
- **AND** 旧 Blueprint 保留至少一个版本周期

### Requirement: 数据库抽象层

系统 SHALL 通过环境变量切换 Supabase/SQLite 数据库后端。

#### Scenario: Supabase 模式
- **WHEN** 环境变量 `USE_SUPABASE=true`
- **THEN** Repository 层使用 Supabase Python SDK
- **AND** 向量搜索使用 pgvector

#### Scenario: SQLite 兼容模式
- **WHEN** 环境变量 `USE_SUPABASE=false` 或未设置
- **THEN** Repository 层使用 SQLAlchemy + SQLite
- **AND** 向量搜索使用 FAISS
- **AND** 此模式用于开发和单机部署

### Requirement: 向量搜索统一接口

系统 SHALL 提供统一的向量搜索接口，屏蔽底层实现差异。

#### Scenario: 搜索接口定义
- **WHEN** 调用 `ImageRepository.search_by_vector(vector, threshold, limit)`
- **THEN** 返回按相似度排序的图片列表
- **AND** 结果包含 id, path, similarity 字段
- **AND** 底层实现可能是 pgvector 或 FAISS

#### Scenario: pgvector 实现
- **WHEN** 使用 Supabase 模式
- **THEN** 通过 PostgreSQL RPC 调用 `search_images_by_vector` 函数
- **AND** 使用余弦距离计算相似度

#### Scenario: FAISS 实现
- **WHEN** 使用 SQLite 兼容模式
- **THEN** 从数据库加载特征向量到内存
- **AND** 使用 FAISS IndexFlatIP 进行搜索
