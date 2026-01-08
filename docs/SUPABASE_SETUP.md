# Supabase 配置指南

本文档说明如何配置 Supabase 环境。

## 环境选择

| 环境 | 适用场景 | 成本 | 复杂度 |
|------|----------|------|--------|
| **SQLite 本地模式** | 开发/单机 | 免费 | ⭐ |
| **Supabase Cloud** | 小团队/试用 | 免费起步 | ⭐⭐ |
| **自托管 Supabase** | 生产/大数据 | 服务器成本 | ⭐⭐⭐ |

---

## 方案 1: SQLite 本地模式

最简单的方式，适合开发和单用户使用。

```env
USE_SUPABASE=false
ENABLE_LOGIN=false
```

无需额外配置，直接运行即可。

---

## 方案 2: Supabase Cloud

### 2.1 创建项目

1. 访问 [supabase.com](https://supabase.com) 并注册
2. 点击 "New Project"
3. 选择区域（推荐：Northeast Asia 或 Southeast Asia）
4. 设置数据库密码（保存好！）
5. 等待项目初始化（约 2 分钟）

### 2.2 获取密钥

进入项目后，点击 **Settings → API**，复制：

- **Project URL**: `https://xxx.supabase.co`
- **anon public**: 用于前端
- **service_role secret**: 用于后端（保密！）

### 2.3 启用 pgvector

进入 **Database → Extensions**，搜索并启用 `vector`。

### 2.4 运行迁移脚本

在 **SQL Editor** 中，依次执行：

```
supabase/migrations/001_initial_schema.sql
supabase/migrations/002_add_vector_support.sql
supabase/migrations/003_add_rls_policies.sql
```

### 2.5 配置应用

```env
USE_SUPABASE=true
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...
SUPABASE_SERVICE_KEY=eyJhbGci...
JWT_SECRET=your-jwt-secret
```

---

## 方案 3: 自托管 Supabase

### 3.1 服务器要求

- Linux (Ubuntu 22.04 推荐)
- 4 核 CPU / 8GB 内存 / 100GB SSD（最低）
- Docker 20.10+
- 公网 IP 或内网可访问

### 3.2 快速启动

```bash
# 克隆项目
git clone https://github.com/your-org/MaterialSearch.git
cd MaterialSearch

# 配置环境变量
cp .env.example .env
# 编辑 .env，设置密码和密钥

# 启动所有服务
docker-compose up -d

# 查看状态
docker-compose ps
```

### 3.3 生成密钥

JWT 密钥可以用以下命令生成：

```bash
openssl rand -base64 32
```

### 3.4 生成 Supabase Keys

Supabase 的 anon_key 和 service_key 是 JWT Token，需要用你的 JWT_SECRET 签名。

可以使用在线工具 [jwt.io](https://jwt.io) 生成，Payload 格式：

**anon_key**:
```json
{
  "role": "anon",
  "iss": "supabase",
  "iat": 1704067200,
  "exp": 1861920000
}
```

**service_key**:
```json
{
  "role": "service_role",
  "iss": "supabase",
  "iat": 1704067200,
  "exp": 1861920000
}
```

### 3.5 配置 Kong

创建 `supabase/kong.yml`：

```yaml
_format_version: "2.1"

services:
  - name: auth
    url: http://auth:9999
    routes:
      - name: auth-route
        paths:
          - /auth/v1
    plugins:
      - name: cors

  - name: rest
    url: http://rest:3000
    routes:
      - name: rest-route
        paths:
          - /rest/v1
    plugins:
      - name: cors
```

### 3.6 HTTPS 配置

生产环境建议使用 Nginx + Let's Encrypt：

```bash
# 安装 certbot
apt install certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d your-domain.com
```

---

## 数据迁移

如果已有 SQLite 数据，迁移到 Supabase：

```bash
# 设置 Supabase 环境变量后
python tools/migrate_to_supabase.py --dry-run  # 预演
python tools/migrate_to_supabase.py            # 实际迁移
```

---

## 常见问题

### Q: Cloud 免费版够用吗？

免费版包含：
- 500MB 数据库
- 1GB 文件存储
- 2GB 带宽/月
- 50,000 月活用户

对于小团队（<10人）的素材库（<5万张图片），完全够用。

### Q: 自托管需要多大服务器？

| 规模 | 配置建议 |
|------|----------|
| < 10万素材 | 4核/16GB/256GB SSD |
| 10-100万素材 | 8核/32GB/1TB SSD |
| > 100万素材 | 16核/64GB/2TB NVMe |

### Q: 能在 NAS 上跑吗？

可以！需要 NAS 支持 Docker（如群晖 DSM 7+、威联通 QTS）。

### Q: 如何备份？

```bash
# 导出数据库
docker-compose exec postgres pg_dump -U postgres materialsearch > backup.sql

# 建议配合 cron 定时备份
```
