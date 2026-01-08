# Change: 后端架构重构 - Supabase 迁移与模块化改造

## Why

当前项目存在以下架构问题：
1. **单体文件过大** - `routes.py` 有 1452 行，`database.py` 654 行，对 AI 辅助编程极不友好
2. **单用户认证** - 仅支持单用户登录，无法满足事务所多人协作需求
3. **SQLite 并发限制** - 不支持多客户端同时写入，无法部署为服务器模式
4. **缺乏数据安全** - 无审计日志、无权限控制、无密码加密

本次重构旨在将项目升级为**企业级多用户系统**，支持服务器部署模式，并通过模块化改造使代码对 AI 编程更友好（每文件 ≤300 行）。

## What Changes

### 核心变更
- **BREAKING** 数据库从 SQLite 迁移到 PostgreSQL (via Supabase)
- **BREAKING** 认证系统从 Flask Session 迁移到 Supabase Auth (JWT)
- **BREAKING** API 路由从单文件拆分为 Blueprint 模块

### 架构变更
- 引入分层架构：API → Services → Repositories
- 向量存储从 FAISS 文件迁移到 PostgreSQL pgvector
- 文件存储可选迁移到 Supabase Storage

### 新增能力
- 多用户登录与注册
- 基于角色的权限控制 (RBAC)
- 操作审计日志
- Row Level Security (RLS) 数据隔离

### 模块化拆分
- `routes.py` → `app/api/` (8 个 Blueprint 模块)
- `database.py` → `app/repositories/` (5 个数据访问模块)
- `models.py` → `app/models/` (4 个模型模块)
- 新增 `app/services/` (6 个业务逻辑模块)
- 新增 `app/integrations/` (3 个外部集成模块)

## Impact

### 受影响的规范
- `image-storage` - 数据模型迁移到 PostgreSQL
- `project-management` - 项目隔离与权限控制
- `search` - 向量搜索迁移到 pgvector
- `upload-to-library` - 存储后端抽象
- `scan-to-library` - 扫描服务模块化
- `batch-indexing` - 批量任务队列化

### 受影响的代码
- `routes.py` (删除，拆分为多模块)
- `database.py` (删除，拆分为多模块)
- `models.py` (删除，拆分为多模块)
- `main.py` (重构为 App Factory 模式)
- `search.py` → `app/services/search_service.py`
- `scan.py` → `app/services/scan_service.py`
- `project_manager.py` → `app/services/project_service.py`

### 新增代码
- `app/` 目录结构 (完整的分层架构)
- `supabase/` 目录 (数据库迁移脚本)
- `docker-compose.yml` (Supabase 自托管配置)
- `scripts/migrate_to_supabase.py` (数据迁移脚本)

### 外部依赖变更
- 新增: `supabase>=2.0.0` (Supabase Python SDK)
- 新增: `python-jose>=3.3.0` (JWT 处理)
- 新增: `bcrypt>=4.0.0` (密码加密，Supabase 已内置)
- 保留: `sqlalchemy` (仅用于兼容模式)

### 部署变更
- **BREAKING** 服务器模式需要 Docker + Supabase
- **保留** 单机模式仍可使用 SQLite (开发/兼容模式)

## Rollback Plan

1. 保留 `database.py` 和 `models.py` 的备份
2. 通过环境变量 `USE_SUPABASE=false` 切换回 SQLite 模式
3. 数据迁移脚本支持双向迁移
