# User Authentication Specification

## ADDED Requirements

### Requirement: 多用户登录

系统 SHALL 支持多用户通过邮箱密码登录。

#### Scenario: 用户登录成功
- **WHEN** 用户提供有效的邮箱和密码
- **THEN** 系统返回 JWT access_token 和 refresh_token
- **AND** 返回用户基本信息 (id, email, role)
- **AND** 记录登录审计日志

#### Scenario: 用户登录失败
- **WHEN** 用户提供无效的邮箱或密码
- **THEN** 系统返回 401 Unauthorized
- **AND** 返回错误消息 "邮箱或密码错误"
- **AND** 记录失败的登录尝试

#### Scenario: Token 刷新
- **WHEN** access_token 过期且 refresh_token 有效
- **THEN** 系统返回新的 access_token
- **AND** refresh_token 保持不变

### Requirement: 用户注册

系统 SHALL 允许管理员创建新用户账户。

#### Scenario: 管理员创建用户
- **WHEN** 管理员调用 POST /api/auth/register
- **AND** 提供有效的 email, password, role
- **THEN** 系统创建新用户
- **AND** 返回用户 ID

#### Scenario: 邮箱唯一性验证
- **WHEN** 创建用户时提供已存在的邮箱
- **THEN** 系统返回 400 Bad Request
- **AND** 返回错误消息 "该邮箱已被注册"

#### Scenario: 密码强度验证
- **WHEN** 创建用户时提供弱密码
- **THEN** 系统返回 400 Bad Request
- **AND** 返回错误消息说明密码要求

### Requirement: 角色权限控制

系统 SHALL 基于用户角色限制 API 访问权限。

#### Scenario: 角色定义
- **WHEN** 系统初始化
- **THEN** 定义以下角色:
  - `admin` - 完全权限，可管理用户和配置
  - `designer` - 标准权限，可搜索和上传素材
  - `viewer` - 只读权限，仅可搜索和查看

#### Scenario: 管理员专属操作
- **WHEN** 非管理员用户尝试以下操作:
  - 创建/删除用户
  - 修改系统配置
  - 查看审计日志
  - 删除项目
- **THEN** 系统返回 403 Forbidden

#### Scenario: 设计师操作权限
- **WHEN** designer 角色用户操作
- **THEN** 可执行: 搜索、上传、创建项目、归档
- **AND** 不可执行: 用户管理、系统配置

#### Scenario: 只读用户权限
- **WHEN** viewer 角色用户操作
- **THEN** 可执行: 搜索、查看项目和素材
- **AND** 不可执行: 上传、创建项目、归档、删除

### Requirement: JWT 认证中间件

系统 SHALL 对受保护的 API 端点进行 JWT 认证验证。

#### Scenario: 有效 Token 访问
- **WHEN** 请求头包含有效的 Bearer Token
- **THEN** 请求继续处理
- **AND** 当前用户信息可通过 `g.user` 访问

#### Scenario: 无效 Token 访问
- **WHEN** 请求头包含无效或过期的 Token
- **THEN** 系统返回 401 Unauthorized
- **AND** 返回错误消息 "Token 无效或已过期"

#### Scenario: 无 Token 访问受保护端点
- **WHEN** 请求不包含 Authorization 头
- **AND** 访问的是受保护端点
- **THEN** 系统返回 401 Unauthorized
- **AND** 返回错误消息 "需要认证"

#### Scenario: 公开端点访问
- **WHEN** 请求不包含 Authorization 头
- **AND** 访问的是公开端点 (如 /api/auth/login)
- **THEN** 请求正常处理

### Requirement: 审计日志

系统 SHALL 记录所有安全相关操作的审计日志。

#### Scenario: 登录审计
- **WHEN** 用户登录成功或失败
- **THEN** 记录以下信息:
  - user_id (成功时) 或 attempted_email (失败时)
  - action: "login_success" 或 "login_failed"
  - ip_address
  - timestamp
  - user_agent

#### Scenario: 敏感操作审计
- **WHEN** 用户执行以下操作:
  - 上传素材
  - 删除素材
  - 创建/删除项目
  - 归档操作
- **THEN** 记录:
  - user_id
  - action
  - resource_type
  - resource_id
  - details (JSON 格式的操作详情)
  - ip_address
  - timestamp

#### Scenario: 审计日志查询
- **WHEN** 管理员查询审计日志
- **THEN** 可按 user_id, action, 时间范围 过滤
- **AND** 结果按时间倒序排列

### Requirement: Session 管理

系统 SHALL 支持用户登出和 Session 失效。

#### Scenario: 用户登出
- **WHEN** 用户调用 POST /api/auth/logout
- **THEN** 当前 Session 失效
- **AND** 后续使用该 Token 的请求返回 401

#### Scenario: 获取当前用户信息
- **WHEN** 已登录用户调用 GET /api/auth/me
- **THEN** 返回用户详细信息:
  - id
  - email
  - role
  - created_at
  - last_login_at
