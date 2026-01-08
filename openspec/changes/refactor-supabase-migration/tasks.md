## Phase 0: 准备工作

- [x] 0.1 创建 `app/` 目录骨架结构
  - 验证：`ls app/` 显示 api/, services/, repositories/, models/, integrations/, utils/ 子目录 ✅
- [x] 0.2 创建 `.env.example` 环境变量模板
  - 验证：包含 SUPABASE_URL, SUPABASE_ANON_KEY, USE_SUPABASE 等变量 ✅
- [x] 0.3 更新 `requirements.txt` 添加 Supabase 依赖
  - 验证：添加 supabase>=2.0.0, python-jose[cryptography]>=3.3.0 ✅


## Phase 1: API 模块化拆分

### 1.1 Flask App Factory
- [x] 1.1.1 创建 `app/__init__.py` 实现 App Factory 模式
  - 验证：`python -c "from app import create_app; app = create_app()"` 成功 ✅
- [x] 1.1.2 创建 `app/settings.py` 配置类（注：使用 settings.py 避免 .gitignore 冲突）
  - 验证：支持 development/production/testing 配置 ✅

### 1.2 Blueprint 拆分 (从 routes.py)
- [x] 1.2.1 创建 `app/api/__init__.py` Blueprint 注册器 ✅

- [x] 1.2.2 创建 `app/api/search.py` 搜索 API (231行) ✅
  - 从 routes.py 迁移: api_match, 新增简化接口
- [x] 1.2.3 创建 `app/api/projects.py` 项目管理 API (186行) ✅
  - 从 routes.py 迁移: api_projects, api_project_detail, api_project_stats
- [x] 1.2.4 创建 `app/api/assets.py` 素材处理 API (158行) ✅
  - 从 routes.py 迁移: api_get_image, api_get_video, api_upload
- [x] 1.2.5 创建 `app/api/archive.py` 归档 API (77行) ✅
  - 从 routes.py 迁移: api_archive_images, api_unarchive_images
- [x] 1.2.6 创建 `app/api/dedup.py` 去重 API (130行) ✅
  - 新增: 去重任务管理 API
- [x] 1.2.7 创建 `app/api/scan.py` 扫描 API (97行) ✅
  - 从 routes.py 迁移: api_scan_new, api_status
- [x] 1.2.8 创建 `app/api/admin.py` 管理 API (92行) ✅
  - 预留管理员功能端点 + 系统信息
- [ ] 1.2.9 验证所有现有 API 端点正常工作
  - ⚠️ 注意：新 Blueprint 依赖旧模块（search.py/database.py），需旧 config.py 正常
  - 验证：修复用户 config.py 后运行 `python api_test.py`



### 1.3 Repository 拆分 (从 database.py)
- [x] 1.3.1 创建 `app/repositories/base.py` 基础 Repository 类 (118行) ✅
- [x] 1.3.2 创建 `app/repositories/image_repo.py` 图片数据访问 (145行) ✅
- [x] 1.3.3 创建 `app/repositories/video_repo.py` 视频数据访问 (148行) ✅
- [x] 1.3.4 创建 `app/repositories/project_repo.py` 项目数据访问 (117行) ✅
- [ ] 1.3.5 验证数据库操作正常
  - 验证：搜索、上传、项目管理功能正常


### 1.4 Service 层创建
- [x] 1.4.1 创建 `app/services/search_service.py` 封装搜索逻辑 (212行) ✅
- [x] 1.4.2 创建 `app/services/project_service.py` 封装项目逻辑 (177行) ✅
- [x] 1.4.3 创建 `app/services/asset_service.py` 封装素材逻辑 (133行) ✅
- [x] 1.4.4 创建 `app/services/scan_service.py` 封装扫描逻辑 (101行) ✅

### 1.5 Model 拆分 (从 models.py)
- [x] 1.5.1 创建 `app/models/asset.py` 图片/视频模型 (196行) ✅
- [x] 1.5.2 创建 `app/models/project.py` 项目模型 (73行) ✅

## Phase 2: Supabase 集成

### 2.1 Supabase 客户端
- [x] 2.1.1 创建 `app/integrations/supabase_client.py` (202行) ✅
  - 验证：`from app.integrations.supabase_client import get_supabase` 成功
- [x] 2.1.2 创建 `app/integrations/sqlite_compat.py` SQLite 兼容层 (175行) ✅
  - 验证：USE_SUPABASE=false 时使用 SQLite

### 2.2 数据库迁移脚本
- [x] 2.2.1 创建 `supabase/migrations/001_initial_schema.sql` (230行) ✅
  - 包含: user_profiles, projects, images, videos, audit_logs, dedup_jobs 表
- [x] 2.2.2 创建 `supabase/migrations/002_add_vector_support.sql` (175行) ✅
  - 启用 pgvector 扩展
  - 创建向量搜索函数: search_images_by_vector, search_videos_by_vector
- [x] 2.2.3 创建 `supabase/migrations/003_add_rls_policies.sql` (218行) ✅
  - 添加 Row Level Security 策略
  - 实现基于角色的权限控制

### 2.3 向量搜索迁移
- [x] 2.3.1 修改 `app/repositories/image_repo.py` 和 `video_repo.py` 使用 pgvector ✅
  - 实现 Supabase 向量搜索函数调用
- [ ] 2.3.2 创建基准测试对比 FAISS vs pgvector 性能
  - 验证：性能差距在可接受范围内 (<2x)

## Phase 3: 认证系统

### 3.1 用户模型
- [ ] 3.1.1 创建 `app/models/user.py` 用户模型
  - 注: 已在 Supabase migration SQL 中定义
- [ ] 3.1.2 创建 `app/models/audit.py` 审计日志模型
  - 注: 已在 Supabase migration SQL 中定义

### 3.2 认证 API
- [x] 3.2.1 创建 `app/api/auth.py` 认证 Blueprint (290行) ✅
  - 端点: /login, /logout, /refresh, /me, /register
- [x] 3.2.2 创建 `app/utils/jwt_auth.py` JWT 工具 (152行) ✅
  - 验证：受保护端点需要 Bearer Token
- [x] 3.2.3 创建 `app/repositories/user_repo.py` 用户数据访问 (105行) ✅

### 3.3 权限控制
- [x] 3.3.1 实现角色装饰器 `@require_role('admin')` ✅
  - 已在 auth.py 中实现
- [x] 3.3.2 更新敏感 API 添加权限检查 ✅
  - admin.py: 所有用户管理和审计日志 API
  - projects.py: delete_project, delete_project_images

### 3.4 审计日志
- [x] 3.4.1 创建审计日志服务 `app/services/audit_service.py` (178行) ✅
- [x] 3.4.2 在关键操作中记录审计日志 ✅
  - auth.py: 登录成功/失败

## Phase 4: 数据迁移

- [x] 4.1 创建迁移脚本 `tools/migrate_to_supabase.py` (246行) ✅
  - 功能: SQLite → PostgreSQL 数据迁移
  - 支持 --dry-run 预演模式
- [ ] 4.2 迁移现有图片数据
  - 验证：图片数量与原数据库一致
- [ ] 4.3 迁移现有视频数据
  - 验证：视频帧数量与原数据库一致
- [ ] 4.4 迁移现有项目数据
  - 验证：项目及其关联素材正确迁移
- [ ] 4.5 验证向量索引完整性
  - 验证：搜索结果与迁移前一致

## Phase 5: 部署配置

### 5.1 Docker 配置
- [x] 5.1.1 创建 `docker-compose.yml` Supabase 自托管配置 (147行) ✅
- [x] 5.1.2 创建 `docker-compose.dev.yml` 开发环境配置 (81行) ✅
- [x] 5.1.3 更新 `Dockerfile` 适配新架构 (74行) ✅

### 5.2 文档
- [x] 5.2.1 更新 `README.md` 服务器部署说明 ✅
- [x] 5.2.2 创建 `docs/DEPLOYMENT.md` 详细部署指南 (260行) ✅
- [x] 5.2.3 创建 `docs/API.md` API 文档 (380行) ✅
- [x] 5.2.4 创建 `docs/SUPABASE_SETUP.md` Supabase 配置指南 (190行) ✅

### 5.3 端到端测试
- [ ] 5.3.1 在 Docker 环境中运行完整测试
  - 验证：所有功能在容器环境正常工作
- [ ] 5.3.2 测试多用户并发场景
  - 验证：3 个用户同时搜索/上传无冲突
- [ ] 5.3.3 测试权限隔离
  - 验证：普通用户无法访问管理功能

## 依赖关系

```
Phase 0 → Phase 1.1 → Phase 1.2 → Phase 1.3
                            ↓
                       Phase 1.4 → Phase 1.5
                            ↓
              Phase 2.1 → Phase 2.2 → Phase 2.3
                            ↓
                       Phase 3 (可与 Phase 2 并行)
                            ↓
                       Phase 4
                            ↓
                       Phase 5
```

## 可并行任务

- Phase 1.2.2 ~ 1.2.8 可并行拆分
- Phase 1.3.2 ~ 1.3.4 可并行拆分
- Phase 2 和 Phase 3 的模型/API 部分可并行
- Phase 5.2 文档可与 Phase 4/5.1 并行
