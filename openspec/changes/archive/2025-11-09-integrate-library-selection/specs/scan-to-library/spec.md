# Spec Delta: 扫描到指定库

## 能力描述

扩展扫描功能，支持将扫描结果存入指定的数据库（永久库或项目库）。

## ADDED Requirements

### Requirement: 文件扫描
系统 SHALL 支持将扫描结果存入指定的目标库。

#### Scenario: 扫描到永久库
- **GIVEN** 用户选择扫描目标为"永久库"
- **WHEN** 用户发起扫描
- **THEN** 系统将发现的图片存入 `permanent.db`
- **AND** 自动计算图片属性（宽高比、文件大小等）
- **AND** 永久库图片数量增加

#### Scenario: 扫描到新建项目
- **GIVEN** 用户选择"新建项目"作为扫描目标
- **AND** 输入项目名称 "万科广场项目"
- **AND** 输入客户名称 "万科集团"
- **WHEN** 用户发起扫描
- **THEN** 系统创建项目 `proj_2025_万科广场项目_01`
- **AND** 创建项目数据库 `proj_2025_万科广场项目_01.db`
- **AND** 将扫描图片存入该项目数据库
- **AND** 更新项目统计信息（图片数、总大小）

#### Scenario: 扫描到现有项目
- **GIVEN** 已存在项目 `proj_2025_万科_01`
- **AND** 用户选择该项目作为扫描目标
- **WHEN** 用户发起扫描
- **THEN** 系统将图片存入 `proj_2025_万科_01.db`
- **AND** 更新该项目的统计信息
- **AND** 不影响其他项目或永久库

#### Scenario: 项目不存在时的错误处理
- **GIVEN** 用户选择项目 `proj_2025_不存在_01`
- **WHEN** 用户发起扫描
- **THEN** 系统返回 404 错误
- **AND** 错误消息为 "项目不存在: proj_2025_不存在_01"
- **AND** 不执行扫描

#### Scenario: 并发扫描冲突
- **GIVEN** 系统正在进行扫描（target=permanent）
- **WHEN** 用户尝试发起另一次扫描（target=proj_xxx）
- **THEN** 系统返回 409 Conflict 错误
- **AND** 错误消息为 "扫描进行中，请稍后再试"

#### Scenario: 向后兼容 - 不指定目标
- **GIVEN** 用户调用 `/api/scan` 不传 `target` 参数
- **WHEN** 扫描执行
- **THEN** 系统默认存入永久库 `permanent.db`
- **AND** 行为与旧版本一致

### Requirement: 扫描 API
系统 SHALL 提供 `/api/scan` 接口支持目标库选择。

#### Scenario: API 参数验证
- **GIVEN** API 端点 `GET /api/scan`
- **WHEN** 请求包含 `target=permanent`
- **THEN** 参数验证通过
- **AND** 扫描到永久库

#### Scenario: API 参数 - 项目库
- **GIVEN** API 端点 `GET /api/scan`
- **WHEN** 请求包含 `target=proj_2025_万科_01`
- **THEN** 参数验证通过
- **AND** 扫描到指定项目库

#### Scenario: API 参数 - 默认值
- **GIVEN** API 端点 `GET /api/scan`
- **WHEN** 请求不包含 `target` 参数
- **THEN** 使用默认值 `target='permanent'`

## ADDED Requirements

### Requirement: 扫描前项目验证
系统 SHALL 在扫描前验证目标项目是否存在。

#### Scenario: 验证现有项目
- **GIVEN** 请求扫描到 `proj_2025_万科_01`
- **WHEN** 系统执行项目验证
- **THEN** 查询项目元信息库
- **AND** 确认项目存在且未删除
- **AND** 继续扫描

#### Scenario: 验证不存在的项目
- **GIVEN** 请求扫描到 `proj_2025_不存在_01`
- **WHEN** 系统执行项目验证
- **THEN** 查询项目元信息库
- **AND** 发现项目不存在
- **AND** 返回错误，终止扫描

#### Scenario: 跳过永久库验证
- **GIVEN** 请求扫描到 `permanent`
- **WHEN** 系统执行验证
- **THEN** 跳过项目验证（永久库始终存在）
- **AND** 直接执行扫描

### Requirement: 扫描统计更新
系统 SHALL 在扫描完成后更新对应库的统计信息。

#### Scenario: 更新项目统计
- **GIVEN** 扫描到项目 `proj_2025_万科_01`
- **AND** 新增 50 张图片
- **WHEN** 扫描完成
- **THEN** 项目图片数量 += 50
- **AND** 项目总大小 += 新增图片大小之和
- **AND** `updated_time` 更新为当前时间

#### Scenario: 永久库统计
- **GIVEN** 扫描到永久库
- **AND** 新增 100 张图片
- **WHEN** 扫描完成
- **THEN** 全局图片数量 += 100
- **AND** 状态栏显示最新数量

## 相关能力

- **项目管理** (`add-project-database-architecture/specs/project-management`): 依赖项目 CRUD
- **图片存储** (`add-project-database-architecture/specs/image-storage`): 使用属性计算
- **搜索功能** (`search-by-library`): 扫描后可在对应库中搜索
