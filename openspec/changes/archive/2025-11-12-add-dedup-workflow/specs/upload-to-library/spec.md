## MODIFIED Requirements

### Requirement: 重复文件智能检测
上传流程 SHALL 根据目标库类型自动处理完全重复素材（永久库跳过、项目库提示）。

#### Scenario: 永久库自动跳过完全重复
- **GIVEN** 上传目标为 `target='permanent'`
- **WHEN** `(file_size, checksum)` 命中现有记录
- **THEN** 上传流程 SHALL 直接返回 200 + `{ "duplicate": true, "action": "skipped" }`
- **AND** 不再写入新记录
- **AND** 响应体包含已存在素材的路径、分辨率、上传者

#### Scenario: 分辨率优先保留
- **GIVEN** 命中的重复素材与新素材分辨率不同
- **WHEN** 现有素材分辨率更低
- **THEN** 系统 SHALL 用新素材覆盖旧纪录（更新文件与元数据）
- **AND** 将旧纪录标记为 `is_duplicate=1`，`duplicate_type='exact'`
- **AND** 在响应中提示“已替换为更高分辨率”

#### Scenario: 项目库允许重复
- **GIVEN** 目标为项目库
- **WHEN** 检测到重复
- **THEN** 仅返回警告信息，默认继续写入
- **AND** 响应中带上“该项目库允许重复；如需去重请归档后运行永久库任务”

#### Scenario: 批量索引重复策略
- **GIVEN** 批量索引任务
- **WHEN** `target='permanent'`
- **THEN** `duplicate_strategy` 默认为 `"skip"`
- **AND** 命中重复的条目写入任务报告 `duplicates` 数组，以便上传完成后查看
