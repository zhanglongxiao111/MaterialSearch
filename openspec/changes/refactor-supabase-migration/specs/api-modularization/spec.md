# API Modularization Specification

## ADDED Requirements

### Requirement: 搜索 API Blueprint

系统 SHALL 提供独立的搜索 API Blueprint (`app/api/search.py`)。

#### Scenario: 文本搜索图片
- **WHEN** 调用 POST /api/search/images/text
- **WITH** body: { positive_prompt, negative_prompt?, threshold?, limit?, project_id? }
- **THEN** 返回匹配的图片列表，按相似度降序排列

#### Scenario: 图片搜索图片
- **WHEN** 调用 POST /api/search/images/image
- **WITH** body: { image_id | image_base64 | image_path, threshold?, limit?, project_id? }
- **THEN** 返回相似图片列表，按相似度降序排列

#### Scenario: 文本搜索视频
- **WHEN** 调用 POST /api/search/videos/text
- **WITH** body: { positive_prompt, negative_prompt?, threshold?, limit?, project_id? }
- **THEN** 返回匹配的视频片段列表，包含 start_time, end_time

### Requirement: 项目管理 API Blueprint

系统 SHALL 提供独立的项目管理 API Blueprint (`app/api/projects.py`)。

#### Scenario: 获取项目列表
- **WHEN** 调用 GET /api/projects
- **WITH** query: { status?, include_deleted? }
- **THEN** 返回项目列表

#### Scenario: 创建项目
- **WHEN** 调用 POST /api/projects
- **WITH** body: { name, client_name?, description? }
- **THEN** 创建项目并返回项目详情

#### Scenario: 获取项目详情
- **WHEN** 调用 GET /api/projects/{project_id}
- **THEN** 返回项目详情，包含统计信息

#### Scenario: 更新项目
- **WHEN** 调用 PUT /api/projects/{project_id}
- **WITH** body: { name?, client_name?, description?, status? }
- **THEN** 更新项目并返回更新后的详情

#### Scenario: 删除项目
- **WHEN** 调用 DELETE /api/projects/{project_id}
- **AND** 用户角色为 admin
- **THEN** 软删除项目 (is_deleted=true)

### Requirement: 素材 API Blueprint

系统 SHALL 提供独立的素材处理 API Blueprint (`app/api/assets.py`)。

#### Scenario: 获取图片
- **WHEN** 调用 GET /api/assets/images/{image_id}
- **THEN** 返回图片文件或元数据

#### Scenario: 获取图片缩略图
- **WHEN** 调用 GET /api/assets/images/{image_id}/thumbnail
- **WITH** query: { size? }
- **THEN** 返回指定尺寸的缩略图

#### Scenario: 上传图片
- **WHEN** 调用 POST /api/assets/images
- **WITH** multipart form: { file, target?, project_id? }
- **THEN** 上传图片并返回 image_id

#### Scenario: 获取视频
- **WHEN** 调用 GET /api/assets/videos/{video_id}
- **THEN** 返回视频文件或元数据

#### Scenario: 下载视频片段
- **WHEN** 调用 GET /api/assets/videos/{video_id}/clip
- **WITH** query: { start_time, end_time }
- **THEN** 返回视频片段文件

### Requirement: 归档 API Blueprint

系统 SHALL 提供独立的归档 API Blueprint (`app/api/archive.py`)。

#### Scenario: 归档图片到永久库
- **WHEN** 调用 POST /api/archive/images
- **WITH** body: { project_id, image_ids[] }
- **THEN** 将项目库图片复制到永久库
- **AND** 返回归档成功的图片数量

#### Scenario: 取消归档
- **WHEN** 调用 DELETE /api/archive/images
- **WITH** body: { project_id, image_ids[] }
- **THEN** 移除归档标记

#### Scenario: 获取归档列表
- **WHEN** 调用 GET /api/archive/images
- **WITH** query: { project_id }
- **THEN** 返回该项目已归档的图片列表

### Requirement: 扫描 API Blueprint

系统 SHALL 提供独立的扫描 API Blueprint (`app/api/scan.py`)。

#### Scenario: 启动扫描
- **WHEN** 调用 POST /api/scan/start
- **WITH** body: { target, paths[]? }
- **THEN** 启动异步扫描任务
- **AND** 返回 task_id

#### Scenario: 获取扫描状态
- **WHEN** 调用 GET /api/scan/status
- **THEN** 返回扫描进度和状态

#### Scenario: 停止扫描
- **WHEN** 调用 POST /api/scan/stop
- **THEN** 停止当前扫描任务

### Requirement: 认证 API Blueprint

系统 SHALL 提供独立的认证 API Blueprint (`app/api/auth.py`)。

#### Scenario: 用户登录
- **WHEN** 调用 POST /api/auth/login
- **WITH** body: { email, password }
- **THEN** 返回 { access_token, refresh_token, user }

#### Scenario: 用户登出
- **WHEN** 调用 POST /api/auth/logout
- **WITH** header: Authorization: Bearer {token}
- **THEN** 返回 { message: "已登出" }

#### Scenario: 刷新 Token
- **WHEN** 调用 POST /api/auth/refresh
- **WITH** body: { refresh_token }
- **THEN** 返回新的 access_token

#### Scenario: 获取当前用户
- **WHEN** 调用 GET /api/auth/me
- **WITH** header: Authorization: Bearer {token}
- **THEN** 返回当前用户信息

### Requirement: 管理 API Blueprint

系统 SHALL 提供独立的管理员 API Blueprint (`app/api/admin.py`)，仅限管理员访问。

#### Scenario: 用户管理
- **WHEN** 调用 GET /api/admin/users
- **AND** 用户角色为 admin
- **THEN** 返回所有用户列表

#### Scenario: 创建用户
- **WHEN** 调用 POST /api/admin/users
- **AND** 用户角色为 admin
- **WITH** body: { email, password, role, department? }
- **THEN** 创建用户并返回用户信息

#### Scenario: 审计日志查询
- **WHEN** 调用 GET /api/admin/audit-logs
- **AND** 用户角色为 admin
- **WITH** query: { user_id?, action?, start_date?, end_date?, limit? }
- **THEN** 返回审计日志列表

### Requirement: 统一错误响应格式

系统 SHALL 使用统一的错误响应格式。

#### Scenario: 错误响应结构
- **WHEN** API 返回错误
- **THEN** 响应体结构为:
  ```json
  {
    "error": {
      "code": "ERROR_CODE",
      "message": "人类可读的错误消息",
      "details": { ... }  // 可选
    }
  }
  ```

#### Scenario: 常见错误码
- **WHEN** 发生错误
- **THEN** 使用以下错误码:
  - `UNAUTHORIZED` (401) - 未认证
  - `FORBIDDEN` (403) - 无权限
  - `NOT_FOUND` (404) - 资源不存在
  - `VALIDATION_ERROR` (400) - 参数验证失败
  - `INTERNAL_ERROR` (500) - 服务器内部错误
