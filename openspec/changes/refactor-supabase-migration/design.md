## Context

MaterialSearch 正在从**个人素材管理工具**演进为**建筑设计事务所的 AI 工作站平台**。当前架构基于 Flask + SQLite，存在以下核心矛盾：

| 现状 | 目标 | 差距 |
|------|------|------|
| 单用户 | 10-20 人团队 | 缺乏认证系统 |
| SQLite 单文件 | 多客户端并发 | 数据库并发锁 |
| 单体 1400+ 行文件 | AI 友好 ≤300 行 | 无法高效维护 |
| 本地 FAISS 文件 | 分布式向量搜索 | 无法共享索引 |

### 利益相关者
- **用户**: 建筑设计事务所设计师 (10-20 人)
- **管理员**: 龙潇 (IT 管理 + 超级用户)
- **开发者**: AI 编程助手 (需要模块化代码)

### 约束
- 保持向后兼容：单机开发模式仍可使用 SQLite
- 最小化服务器运维：使用 Docker Compose 一键部署
- 代码可读性优先：每个文件不超过 300 行

## Goals / Non-Goals

### Goals
1. **多用户认证** - 支持邮箱登录、角色权限、审计日志
2. **服务器部署** - 中央服务器 + 瘦客户端架构
3. **模块化代码** - 分层架构，每文件 ≤300 行
4. **向量搜索统一** - 从 FAISS 文件迁移到 pgvector
5. **数据安全** - Row Level Security、操作审计

### Non-Goals
- 不迁移前端框架（保持 Vanilla JS，前端改造为独立 Change）
- 不更换 CLIP 模型（模型层不变）
- 不实现 OAuth 第三方登录（首期仅邮箱密码）
- 不实现多租户隔离（事务所内部单租户）

## Decisions

### Decision 1: 选择 Supabase 作为 BaaS 平台

**选择**: Supabase (自托管)

**理由**:
- PostgreSQL + pgvector = 既是业务数据库又是向量数据库
- 开箱即用的认证系统 (GoTrue)
- Row Level Security 实现数据权限
- 可完全自托管，数据不出公司内网

**备选方案**:
| 方案 | 优点 | 缺点 | 评估 |
|------|------|------|------|
| PocketBase | 极简部署 | 无 pgvector | ❌ 无法统一向量存储 |
| Appwrite | 功能全面 | 无 pgvector | ❌ 需额外向量服务 |
| 自研 PostgreSQL | 完全控制 | 需自建认证 | ⚠️ 工作量大 |
| **Supabase** | 认证+pgvector | 部署稍复杂 | ✅ 最佳平衡 |

### Decision 2: 分层架构设计

**选择**: API → Services → Repositories 三层架构

```
┌─────────────────────────────────────────────────────────┐
│                    app/api/                             │
│   Blueprint 模块，仅处理 HTTP 请求/响应，不含业务逻辑      │
│   auth.py | search.py | projects.py | assets.py | ...  │
└──────────────────────────┬──────────────────────────────┘
                           │ 调用
┌──────────────────────────▼──────────────────────────────┐
│                    app/services/                        │
│   业务逻辑层，协调多个 Repository，处理事务               │
│   search_service.py | project_service.py | ...          │
└──────────────────────────┬──────────────────────────────┘
                           │ 调用
┌──────────────────────────▼──────────────────────────────┐
│                    app/repositories/                    │
│   数据访问层，封装 Supabase API 调用                     │
│   image_repo.py | video_repo.py | project_repo.py | ... │
└─────────────────────────────────────────────────────────┘
```

**理由**:
- 每层职责单一，文件行数可控
- AI 可独立阅读和修改单个模块
- 便于单元测试（Mock Repository）

### Decision 3: 向量存储迁移到 pgvector

**选择**: PostgreSQL pgvector 扩展

**变更**:
- CLIP 特征从 `BLOB` 列改为 `vector(512)` 类型
- 相似度搜索从 Python FAISS 改为 SQL 函数
- 创建 IVFFlat 索引加速检索

**SQL 示例**:
```sql
-- 创建带向量的图片表
CREATE TABLE images (
    id SERIAL PRIMARY KEY,
    features vector(512),
    -- ...
);

-- 创建向量索引
CREATE INDEX ON images USING ivfflat (features vector_cosine_ops);

-- 相似度搜索函数
CREATE FUNCTION search_images_by_vector(
    query_vector vector(512),
    threshold float,
    limit_count int
) RETURNS TABLE (...);
```

**理由**:
- 统一数据存储，减少 FAISS 文件管理
- 支持 SQL 级别的过滤+向量搜索联合查询
- 数据备份恢复随数据库一体化

### Decision 4: 双模式运行

**选择**: 环境变量切换 Supabase/SQLite 模式

```python
# app/config.py
USE_SUPABASE = os.getenv('USE_SUPABASE', 'false').lower() == 'true'

if USE_SUPABASE:
    from app.integrations.supabase_client import get_supabase as get_db
else:
    from app.integrations.sqlite_compat import get_sqlite as get_db
```

**理由**:
- 开发环境可快速启动（无需 Docker）
- 生产环境使用完整功能
- 渐进式迁移，降低风险

## Risks / Trade-offs

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| Supabase 自托管复杂 | 部署困难 | 提供 docker-compose.yml 一键部署 |
| pgvector 性能未验证 | 搜索变慢 | 先做基准测试，保留 FAISS 回退 |
| 数据迁移丢失 | 历史数据丢失 | 迁移脚本+备份策略 |
| 认证系统学习成本 | 开发变慢 | 提供示例代码和文档 |
| API 变更 | 前端需适配 | 版本化 API (/api/v2/) |

## Migration Plan

### Phase 0: 准备 (1 天)
1. 创建 `app/` 目录结构
2. 配置 `.env.example`
3. 添加 `supabase-py` 依赖

### Phase 1: 模块化拆分 (5 天)
1. 拆分 `routes.py` → `app/api/` Blueprint
2. 拆分 `database.py` → `app/repositories/`
3. 拆分 `models.py` → `app/models/`
4. 验证所有现有功能正常

### Phase 2: Supabase 集成 (5 天)
1. 编写数据库迁移脚本
2. 实现 `app/integrations/supabase_client.py`
3. 迁移 Repository 到 Supabase API
4. 测试向量搜索性能

### Phase 3: 认证系统 (3 天)
1. 实现 `app/api/auth.py`
2. 添加 JWT 中间件
3. 实现用户管理 API
4. 添加审计日志

### Phase 4: 数据迁移 (2 天)
1. 编写 SQLite → PostgreSQL 迁移脚本
2. 迁移现有数据
3. 验证数据完整性

### Phase 5: 部署配置 (2 天)
1. 编写 `docker-compose.yml`
2. 编写部署文档
3. 测试端到端流程

### Rollback
- 每个 Phase 独立可回滚
- 保留 SQLite 兼容模式
- 数据迁移支持双向

## Open Questions

1. **前端如何适配 JWT 认证？**
   - 选项 A: 前端改造使用 token
   - 选项 B: 后端提供 session 桥接层
   
2. **是否需要迁移文件存储到 Supabase Storage？**
   - 当前: 直接读取本地/NAS 文件
   - 考虑: 对于 UNC 路径，可能需要中转

3. **pgvector 索引策略？**
   - IVFFlat (更快但需预训练)
   - HNSW (更准确但占用更多内存)
