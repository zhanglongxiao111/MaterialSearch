# Spec Delta: 按库搜索

## 能力描述

扩展搜索功能，支持在永久库或选定项目库中搜索素材。产品策略明确：**不提供跨库（“所有库”）的合并搜索**。

## ADDED Requirements

### Requirement: 图片文本搜索
系统 SHALL 支持在指定库中搜索图片。

#### Scenario: 在永久库中搜索
- **GIVEN** 永久库包含 10000 张图片
- **AND** 项目库 `proj_2025_万科_01` 包含 100 张图片
- **AND** 用户选择搜索范围 "永久库"
- **WHEN** 用户搜索 "建筑外观"
- **THEN** 系统仅在 `permanent.db` 中搜索
- **AND** 返回结果仅来自永久库
- **AND** 每条结果标注 `source: "永久库"`
- **AND** 搜索时间 < 3 秒

#### Scenario: 在项目库中搜索
- **GIVEN** 用户选择搜索范围 "项目库"
- **AND** 当前项目为 `proj_2025_万科_01`（100 张图）
- **WHEN** 用户搜索 "效果图"
- **THEN** 系统仅在 `proj_2025_万科_01.db` 中搜索
- **AND** 返回结果仅来自该项目
- **AND** 每条结果标注 `source: "万科项目"`
- **AND** 搜索时间 < 1 秒

#### Scenario: 向后兼容 - 不指定库类型
- **GIVEN** 前端调用搜索 API 不传 `library_type` 参数
- **WHEN** 执行搜索
- **THEN** 系统默认在永久库中搜索
- **AND** 行为与旧版本一致

#### Scenario: 项目库不存在时的搜索
- **GIVEN** 用户选择项目 `proj_2025_不存在_01`
- **WHEN** 用户执行搜索
- **THEN** 系统返回 404 错误
- **AND** 错误消息为 "项目不存在: proj_2025_不存在_01"

### Requirement: 图片以图搜图
系统 SHALL 支持在指定库中进行以图搜图。

#### Scenario: 在项目库中以图搜图
- **GIVEN** 用户上传参考图片
- **AND** 选择搜索范围 "当前项目"
- **AND** 当前项目为 `proj_2025_万科_01`
- **WHEN** 执行搜索
- **THEN** 系统仅在项目库中搜索相似图片
- **AND** 返回结果标注来源

#### Scenario: 在永久库中以图搜图
- **GIVEN** 用户上传参考图片
- **AND** 选择搜索范围 "永久库"
- **WHEN** 执行搜索
- **THEN** 系统仅在永久库中搜索
- **AND** 返回永久库的相似图片

### Requirement: 视频搜索
系统 SHALL 支持在指定库中搜索视频（文本和以图）。

#### Scenario: 项目库视频搜索
- **GIVEN** 项目库包含视频素材
- **AND** 用户选择搜索范围 "当前项目"
- **WHEN** 用户搜索视频
- **THEN** 系统仅在项目库中搜索视频
- **AND** 返回结果标注来源

## ADDED Requirements

### Requirement: 搜索 API 库类型参数
系统 SHALL 在搜索 API 中支持库类型参数。

#### Scenario: API 接受 library_type 参数
- **GIVEN** 搜索 API 端点 `POST /api/search`
- **WHEN** 请求体包含 `library_type: "project"`
- **AND** 包含 `project_id: "proj_2025_万科_01"`
- **THEN** 参数验证通过
- **AND** 在指定项目库中搜索

#### Scenario: library_type 参数默认值
- **GIVEN** 请求体不包含 `library_type`
- **WHEN** 执行搜索
- **THEN** 使用默认值 `library_type: "permanent"`

#### Scenario: library_type=project 但缺少 project_id
- **GIVEN** 请求体 `library_type: "project"`
- **AND** 未提供 `project_id`
- **WHEN** 执行搜索
- **THEN** 返回 400 Bad Request
- **AND** 错误消息 "library_type='project' 时必须提供 project_id"

#### Scenario: library_type 无效值
- **GIVEN** 请求体 `library_type: "all"` 或其他未支持的值
- **WHEN** 执行搜索
- **THEN** 返回 400 Bad Request
- **AND** 错误消息提示 “library_type 仅支持 permanent/project”

### Requirement: 搜索结果来源标注
系统 SHALL 在搜索结果中标注图片来源。

#### Scenario: 标注永久库来源
- **GIVEN** 搜索结果包含永久库的图片
- **WHEN** 返回结果
- **THEN** 每条结果包含 `source: "永久库"`
- **AND** 前端可显示来源标签

#### Scenario: 标注项目库来源
- **GIVEN** 搜索结果包含项目库的图片
- **AND** 项目名称为 "万科广场项目"
- **WHEN** 返回结果
- **THEN** 每条结果包含 `source: "万科广场项目"`
- **AND** 可点击跳转到该项目

### Requirement: 搜索缓存分离
系统 SHALL 为不同库的搜索结果独立缓存。

#### Scenario: 永久库和项目库缓存独立
- **GIVEN** 用户在永久库搜索 "建筑"
- **AND** 结果已缓存
- **WHEN** 用户在项目库搜索 "建筑"
- **THEN** 不使用永久库的缓存
- **AND** 重新执行搜索
- **AND** 缓存项目库的结果

#### Scenario: 相同搜索词不同库命中不同缓存
- **GIVEN** 缓存键包含 `(search_term, library_type, project_id)`
- **WHEN** 搜索 `("建筑", "permanent", None)`
- **THEN** 命中永久库缓存
- **WHEN** 搜索 `("建筑", "project", "proj_xxx")`
- **THEN** 命中项目库缓存（不同缓存条目）

### Requirement: 搜索性能
系统 SHALL 确保库类型选择不降低搜索性能。

#### Scenario: 项目库搜索性能
- **GIVEN** 项目库包含 100 张图片
- **WHEN** 执行搜索
- **THEN** 响应时间 < 1 秒
- **AND** 比永久库搜索快（数据量小）

#### Scenario: 永久库搜索性能保持
- **GIVEN** 永久库包含 10000 张图片
- **WHEN** 执行搜索（library_type=permanent）
- **THEN** 响应时间 < 3 秒
- **AND** 与旧版本性能相同

## 相关能力

- **扫描到库** (`scan-to-library`): 扫描后可搜索
- **项目管理** (`add-project-database-architecture/specs/project-management`): 获取项目信息用于标注来源
- **前端界面** (`frontend-library-ui`): 提供库选择器
