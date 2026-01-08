# MaterialSearch API 文档

## 概述

MaterialSearch 提供 RESTful API 进行素材搜索、项目管理和用户认证。

### 基础信息

- **Base URL**: `http://localhost:5000/api`
- **认证**: Bearer Token (JWT)
- **响应格式**: JSON

### 通用响应格式

**成功响应**:
```json
{
  "success": true,
  "data": { ... }
}
```

**错误响应**:
```json
{
  "success": false,
  "error": "错误信息"
}
```

---

## 认证 API

### POST /api/auth/login

用户登录，获取访问令牌。

**请求**:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGci...",
    "refresh_token": "eyJhbGci...",
    "user": {
      "id": "uuid",
      "email": "user@example.com"
    }
  }
}
```

### POST /api/auth/logout

用户登出。需要认证。

### POST /api/auth/refresh

刷新访问令牌。

**请求**:
```json
{
  "refresh_token": "eyJhbGci..."
}
```

### GET /api/auth/me

获取当前用户信息。需要认证。

**响应**:
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "designer"
  }
}
```

---

## 搜索 API

### POST /api/search/match

统一搜索接口，支持多种搜索类型。

**请求**:
```json
{
  "search_type": 0,
  "positive": "现代建筑",
  "negative": "",
  "positive_threshold": 0.27,
  "negative_threshold": 0.27,
  "library_type": "permanent",
  "project_id": null,
  "top_n": 100
}
```

**search_type 说明**:
| 值 | 描述 |
|----|------|
| 0 | 文字搜图片 |
| 1 | 图片搜图片（上传文件） |
| 2 | 文字搜视频 |
| 3 | 图片搜视频（上传文件） |
| 4 | 计算图文相似度 |
| 5 | 图片搜图片（使用 ID） |
| 6 | 图片搜视频（使用 ID） |
| 9 | 搜索 Pexels 视频 |

**响应**:
```json
[
  {
    "id": 1,
    "path": "/path/to/image.jpg",
    "score": 45.2,
    "width": 1920,
    "height": 1080
  }
]
```

### POST /api/search/images/text

文字搜图片（简化接口）。

**请求**:
```json
{
  "positive_prompt": "玻璃幕墙",
  "negative_prompt": "",
  "threshold": 0.27,
  "limit": 100,
  "project_id": null
}
```

### POST /api/search/videos/text

文字搜视频（简化接口）。

---

## 项目 API

### GET /api/projects/

获取项目列表。

**查询参数**:
- `status`: 过滤状态 (active/completed/archived)
- `include_deleted`: 是否包含已删除 (true/false)

**响应**:
```json
{
  "success": true,
  "data": [
    {
      "id": "proj_2025_万科_01",
      "name": "万科城市花园",
      "client_name": "万科地产",
      "status": "active",
      "image_count": 156,
      "video_count": 12,
      "created_time": "2025-01-01T10:00:00"
    }
  ]
}
```

### POST /api/projects/

创建项目。

**请求**:
```json
{
  "name": "新建项目",
  "client_name": "客户名称",
  "description": "项目描述"
}
```

### GET /api/projects/{project_id}

获取项目详情。

### PUT /api/projects/{project_id}

更新项目。

### DELETE /api/projects/{project_id}

删除项目。

**查询参数**:
- `hard_delete`: 是否永久删除 (true/false)

### GET /api/projects/{project_id}/stats

获取项目统计信息。

### POST /api/projects/{project_id}/images/delete

删除项目中的图片记录。

**请求**:
```json
{
  "image_ids": [1, 2, 3]
}
```

---

## 素材 API

### POST /api/assets/upload

上传文件（用于以图搜图）。

**请求**: `multipart/form-data`
- `file`: 图片文件

### GET /api/assets/images/{image_id}

获取图片。

**查询参数**:
- `target`: 目标库 (permanent/proj_xxx)
- `thumbnail`: 是否返回缩略图 (true/false)

### GET /api/assets/videos/{video_path}

获取视频（video_path 需 base64 编码）。

### GET /api/assets/videos/{video_path}/clip

获取视频片段。

**查询参数**:
- `start_time`: 开始时间（秒）
- `end_time`: 结束时间（秒）

---

## 归档 API

### POST /api/archive/projects/{project_id}/archive

归档项目图片到永久库。

**请求**:
```json
{
  "image_ids": [1, 2, 3],
  "mark_archived": true
}
```

### GET /api/archive/projects/{project_id}/archived

获取已归档的图片列表。

### POST /api/archive/projects/{project_id}/unarchive

取消归档标记。

---

## 扫描 API

### POST /api/scan/start

启动扫描任务。

**请求**:
```json
{
  "target": "permanent",
  "paths": []
}
```

### GET /api/scan/status

获取扫描状态。

**响应**:
```json
{
  "is_scanning": true,
  "progress": 45,
  "current_file": "/path/to/file.jpg",
  "total_files": 1000,
  "processed_files": 450
}
```

### POST /api/scan/stop

停止扫描任务。

---

## 去重 API

### POST /api/dedup/jobs

创建去重任务。

**请求**:
```json
{
  "library_type": "permanent",
  "include_phash": true,
  "include_clip": true
}
```

### GET /api/dedup/jobs

获取去重任务列表。

### GET /api/dedup/jobs/{job_id}

获取去重任务详情。

### GET /api/dedup/status

获取去重服务状态。

---

## 管理 API

需要 admin 角色。

### GET /api/admin/system/info

获取系统信息。

**响应**:
```json
{
  "success": true,
  "data": {
    "python_version": "3.10.0",
    "platform": "Linux",
    "gpu_available": true,
    "gpu_name": "NVIDIA GeForce RTX 3090"
  }
}
```

### GET /api/admin/users

获取用户列表。

### POST /api/admin/users

创建用户。

### GET /api/admin/audit-logs

获取审计日志。

---

## 健康检查

### GET /api/health

```json
{
  "status": "ok",
  "message": "MaterialSearch API is running"
}
```

---

## 错误码

| HTTP 状态码 | 说明 |
|-------------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 409 | 资源冲突（如扫描进行中） |
| 500 | 服务器内部错误 |
| 501 | 功能未实现 |

---

## 认证示例

### 使用 curl

```bash
# 登录
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}' \
  | jq -r '.data.access_token')

# 携带 Token 请求
curl -X POST http://localhost:5000/api/search/images/text \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"positive_prompt":"现代建筑","limit":10}'
```

### 使用 Python

```python
import requests

# 登录
resp = requests.post('http://localhost:5000/api/auth/login', json={
    'email': 'admin@example.com',
    'password': 'password'
})
token = resp.json()['data']['access_token']

# 搜索
resp = requests.post(
    'http://localhost:5000/api/search/images/text',
    headers={'Authorization': f'Bearer {token}'},
    json={'positive_prompt': '现代建筑', 'limit': 10}
)
print(resp.json())
```
