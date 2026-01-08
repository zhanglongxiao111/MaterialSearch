# MaterialSearch 服务器部署指南

本文档介绍如何将 MaterialSearch 部署为多用户服务器应用。

## 部署模式

MaterialSearch 支持两种部署模式：

| 模式 | 数据库 | 认证 | 适用场景 |
|------|--------|------|----------|
| **SQLite 模式** | SQLite | 本地 Session | 单机/开发环境 |
| **Supabase 模式** | PostgreSQL + pgvector | JWT + RBAC | 多用户/生产环境 |

---

## 快速开始: Docker 部署

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA GPU + 驱动 (推荐)
- 16GB+ 内存

### 1. 开发环境部署 (SQLite 模式)

```bash
# 克隆仓库
git clone https://github.com/your-org/MaterialSearch.git
cd MaterialSearch

# 启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f materialsearch-dev
```

访问 `http://localhost:5000` 即可使用。

### 2. 生产环境部署 (Supabase 模式)

#### 2.1 配置环境变量

复制并编辑环境变量文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置以下关键变量：

```env
# 数据库密码
POSTGRES_PASSWORD=your-super-secret-password

# JWT 密钥 (使用强随机字符串)
JWT_SECRET=your-super-secret-jwt-token-at-least-32-chars

# Supabase 配置
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# 站点 URL
SITE_URL=https://your-domain.com
API_EXTERNAL_URL=https://api.your-domain.com
```

#### 2.2 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### 2.3 初始化数据库

数据库表会在首次启动时自动创建（通过 SQL 迁移脚本）。

#### 2.4 创建管理员用户

使用 Supabase Auth API 或直接操作数据库：

```sql
-- 在 user_profiles 表中设置管理员角色
UPDATE user_profiles SET role = 'admin' WHERE email = 'admin@example.com';
```

---

## 数据迁移

如果已有 SQLite 数据库，可以迁移到 Supabase：

```bash
# 预演模式 (不实际写入)
python tools/migrate_to_supabase.py --dry-run

# 实际迁移
python tools/migrate_to_supabase.py

# 使用自定义数据库路径
python tools/migrate_to_supabase.py \
  --permanent-db ./instance/permanent.db \
  --metadata-db ./instance/projects_metadata.db
```

---

## 架构说明

### 新模块化架构

```
app/
├── api/                  # API 路由 (Blueprint)
│   ├── auth.py           # 认证 API
│   ├── search.py         # 搜索 API
│   ├── projects.py       # 项目管理 API
│   └── ...
├── services/             # 业务逻辑层
│   ├── search_service.py
│   ├── project_service.py
│   └── ...
├── repositories/         # 数据访问层
│   ├── image_repo.py
│   ├── project_repo.py
│   └── ...
├── models/               # 数据模型
│   ├── asset.py
│   └── project.py
└── integrations/         # 外部服务集成
    ├── supabase_client.py
    └── sqlite_compat.py
```

### 分层架构原则

```
API (Blueprint) → Service → Repository → Database
```

- **API 层**: 处理 HTTP 请求/响应
- **Service 层**: 业务逻辑
- **Repository 层**: 数据访问抽象
- **Database**: Supabase 或 SQLite

---

## 角色权限

| 角色 | 权限 |
|------|------|
| **admin** | 所有操作 + 用户管理 + 审计日志 |
| **designer** | 创建项目、上传素材、搜索、归档 |
| **viewer** | 只读访问 |

---

## API 端点

### 认证

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/auth/login` | 用户登录 |
| POST | `/api/auth/logout` | 用户登出 |
| POST | `/api/auth/refresh` | 刷新 Token |
| GET | `/api/auth/me` | 当前用户信息 |

### 搜索

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/search/match` | 统一搜索接口 |
| POST | `/api/search/images/text` | 文字搜图片 |
| POST | `/api/search/videos/text` | 文字搜视频 |

### 项目管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/projects/` | 项目列表 |
| POST | `/api/projects/` | 创建项目 |
| GET | `/api/projects/<id>` | 项目详情 |
| PUT | `/api/projects/<id>` | 更新项目 |
| DELETE | `/api/projects/<id>` | 删除项目 |

---

## 监控与日志

### 查看日志

```bash
# 所有服务
docker-compose logs -f

# 仅 MaterialSearch
docker-compose logs -f materialsearch

# 最近 100 行
docker-compose logs --tail=100 materialsearch
```

### 健康检查

```bash
curl http://localhost:5000/api/health
# {"status": "ok", "message": "MaterialSearch API is running"}
```

---

## 故障排除

### 常见问题

#### 1. CUDA out of memory

减小批处理大小或使用更小的模型：

```env
SCAN_PROCESS_BATCH_SIZE=2
MODEL_NAME=OFA-Sys/chinese-clip-vit-base-patch16
```

#### 2. 数据库连接失败

检查 PostgreSQL 服务状态：

```bash
docker-compose logs postgres
docker-compose exec postgres pg_isready
```

#### 3. JWT 验证失败

确保 `JWT_SECRET` 在所有服务间一致。

---

## 备份与恢复

### 备份数据库

```bash
docker-compose exec postgres pg_dump -U postgres materialsearch > backup.sql
```

### 恢复数据库

```bash
docker-compose exec -T postgres psql -U postgres materialsearch < backup.sql
```

---

## 更新与升级

```bash
# 拉取最新代码
git pull

# 重新构建镜像
docker-compose build

# 重启服务
docker-compose up -d

# 运行数据库迁移 (如有)
docker-compose exec materialsearch python tools/run_migrations.py
```
