# Spec Delta: 上传到指定库

## 能力描述

扩展上传功能，支持将图片上传到指定的库（永久库或项目库）。

## ADDED Requirements

### Requirement: 图片上传
系统 SHALL 支持将图片上传到指定的目标库。

#### Scenario: 上传到永久库
- **GIVEN** 用户选择上传目标 "永久库"
- **AND** 用户选择图片文件 `reference.jpg`
- **WHEN** 用户上传图片
- **THEN** 系统将图片存储到永久库路径
- **AND** 在 `permanent.db` 中创建图片记录
- **AND** 计算并存储图片属性（宽高比、文件大小等）
- **AND** 返回成功消息

#### Scenario: 上传到项目库
- **GIVEN** 用户选择上传目标 "当前项目"
- **AND** 当前项目为 `proj_2025_万科_01`
- **AND** 用户选择图片文件 `sketch.jpg`
- **WHEN** 用户上传图片
- **THEN** 系统将图片存储到项目路径（或保持 NAS 原路径）
- **AND** 在 `proj_2025_万科_01.db` 中创建图片记录
- **AND** 计算并存储图片属性
- **AND** 更新项目统计信息（图片数、总大小）

#### Scenario: 上传到不存在的项目
- **GIVEN** 用户选择上传目标 `proj_2025_不存在_01`
- **WHEN** 用户上传图片
- **THEN** 系统返回 404 错误
- **AND** 错误消息 "项目不存在: proj_2025_不存在_01"
- **AND** 图片未保存

#### Scenario: 向后兼容 - 不指定目标
- **GIVEN** 前端调用上传 API 不传 `target` 参数
- **WHEN** 上传图片
- **THEN** 系统默认上传到永久库
- **AND** 行为与旧版本一致

### Requirement: 批量上传
系统 SHALL 支持批量上传图片到指定库。

#### Scenario: 批量上传到项目库
- **GIVEN** 用户选择 50 张图片
- **AND** 选择上传目标 "当前项目"
- **AND** 当前项目为 `proj_2025_万科_01`
- **WHEN** 用户批量上传
- **THEN** 所有图片按队列顺序处理
- **AND** 每张图片存入 `proj_2025_万科_01.db`
- **AND** 显示上传进度条
- **AND** 完成后更新项目统计

#### Scenario: 批量上传并发控制
- **GIVEN** 用户上传 100 张图片
- **WHEN** 上传进行中
- **THEN** 系统使用队列机制串行化向量计算
- **AND** 避免并发写入数据库冲突
- **AND** 每处理完一张更新进度

## ADDED Requirements

### Requirement: 上传 API 目标参数
系统 SHALL 在上传 API 中支持目标库参数。

#### Scenario: API 接受 target 参数
- **GIVEN** 上传 API 端点 `POST /api/upload`
- **WHEN** 表单数据包含 `target=proj_2025_万科_01`
- **AND** 包含图片文件
- **THEN** 参数验证通过
- **AND** 图片上传到指定项目库

#### Scenario: target 参数默认值
- **GIVEN** 上传请求不包含 `target` 参数
- **WHEN** 执行上传
- **THEN** 使用默认值 `target='permanent'`

#### Scenario: target 参数验证
- **GIVEN** 请求包含 `target=invalid_format`
- **WHEN** 执行上传
- **THEN** 返回 400 Bad Request
- **AND** 错误消息 "无效的目标库格式"

### Requirement: 上传路径策略
系统 SHALL 根据目标库确定图片存储路径。

#### Scenario: 永久库图片存储
- **GIVEN** 上传到永久库
- **WHEN** 保存图片文件
- **THEN** 存储路径为 `/mnt/nas/permanent/<hash>.jpg`
- **AND** 数据库记录该路径

#### Scenario: 项目库图片存储
- **GIVEN** 上传到项目库 `proj_2025_万科_01`
- **WHEN** 保存图片文件
- **THEN** 存储路径为 `/mnt/nas/projects/proj_2025_万科_01/<hash>.jpg`
- **AND** 或保持用户原 NAS 路径（仅索引）

#### Scenario: 图片去重检查
- **GIVEN** 上传的图片 checksum 已存在于目标库
- **WHEN** 检测到重复
- **THEN** 返回警告 "该图片已存在于目标库"
- **AND** 询问用户是否继续

### Requirement: 上传后统计更新
系统 SHALL 在上传完成后更新目标库统计。

#### Scenario: 更新项目库统计
- **GIVEN** 上传 10 张图片到 `proj_2025_万科_01`
- **AND** 总大小 50 MB
- **WHEN** 上传完成
- **THEN** 项目图片数 += 10
- **AND** 项目总大小 += 50 MB
- **AND** `updated_time` 更新为当前时间

#### Scenario: 永久库统计
- **GIVEN** 上传 5 张图片到永久库
- **WHEN** 上传完成
- **THEN** 全局图片数 += 5
- **AND** 前端状态栏实时更新

### Requirement: 上传队列管理
系统 SHALL 使用队列避免并发写入冲突。

#### Scenario: 队列串行化上传
- **GIVEN** 两个用户同时上传到同一项目库
- **WHEN** 上传请求到达
- **THEN** 系统将任务加入队列
- **AND** 按队列顺序逐个处理
- **AND** 避免数据库锁冲突

#### Scenario: 不同库并发上传
- **GIVEN** 用户 A 上传到永久库
- **AND** 用户 B 同时上传到项目库 `proj_xxx`
- **WHEN** 两个上传并发执行
- **THEN** 无冲突（不同数据库文件）
- **AND** 可同时进行

## 相关能力

- **扫描到库** (`scan-to-library`): 类似的目标库选择逻辑
- **项目管理** (`add-project-database-architecture/specs/project-management`): 验证项目存在
- **图片存储** (`add-project-database-architecture/specs/image-storage`): 属性计算复用
