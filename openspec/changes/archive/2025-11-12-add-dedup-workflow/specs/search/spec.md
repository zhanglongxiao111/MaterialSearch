## ADDED Requirements

### Requirement: 永久库搜索去重
系统 SHALL 默认在永久库搜索中排除已标记为重复的素材。

#### Scenario: 默认过滤重复
- **WHEN** `library_type='permanent'`
- **AND** 用户未显式请求包含重复
- **THEN** 搜索 SQL/向量过滤条件包含 `is_duplicate=0 OR master_image_id IS NULL`
- **AND** 结果中仅返回主图

#### Scenario: 可选包含重复
- **WHEN** 请求参数包含 `include_duplicates=true`
- **THEN** 系统移除 `is_duplicate` 过滤
- **AND** 结果中仍标注 `duplicate_type` 与 `duplicate_group`
- **AND** 分页/缓存键需包含此参数避免串缓存

#### Scenario: 项目库不去重
- **WHEN** `library_type='project'`
- **THEN** 搜索逻辑不强制过滤重复
- **AND** 允许同一素材在不同项目中分别出现

#### Scenario: 缓存失效
- **WHEN** 去重任务完成或有图片被标记/取消标记重复
- **THEN** 永久库缓存条目失效
- **AND** 下次搜索重新计算结果
