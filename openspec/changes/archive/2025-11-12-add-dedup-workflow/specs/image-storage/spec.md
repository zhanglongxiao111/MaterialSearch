## MODIFIED Requirements

### Requirement: 去重预留字段
系统 SHALL 利用既有重复字段在任务完成后写入主图/副本标记。
#### Scenario: 批量任务写入重复标记
- **GIVEN** 手动去重任务完成任意阶段（checksum / phash / clip）
- **WHEN** 识别出同组图片
- **THEN** 系统 SHALL 立即更新对应记录的 `is_duplicate`, `duplicate_group`, `duplicate_type`, `duplicate_confidence`
- **AND** 为被选定的主图写入 `master_image_id=NULL`
- **AND** 其余图片 `master_image_id` 指向主图 ID

#### Scenario: 分辨率优先确定主图
- **GIVEN** 同一 `duplicate_group` 包含多张图片
- **WHEN** 需要选择主图
- **THEN** 以 `width * height` 最大者为主图
- **AND** 分辨率相同时选 `modify_time` 最新者
- **AND** 把该选择记录到去重报告中

## ADDED Requirements

### Requirement: 手动去重任务
系统 SHALL 仅在手动触发时对永久库执行多阶段去重扫描。

#### Scenario: 创建任务
- **WHEN** 管理员调用 `POST /api/dedup/jobs` 且 `library_type='permanent'`
- **THEN** 创建一条待处理任务，状态为 `pending`
- **AND** 返回任务 ID、预计时长提示
- **AND** 若目标为项目库则返回 400（项目库允许重复）

#### Scenario: 阶段式扫描
- **GIVEN** 任务进入运行状态
- **WHEN** 依次执行阶段
  1. checksum 完全相同
  2. phash 感知重复（Hamming 距离 <= 5）
  3. clip_embedding 相似度 >= 0.95
- **THEN** 每阶段结束写入进度（已扫描数量、命中组数）
- **AND** 在缺少 GPU/模型时允许跳过阶段并记录 `notes`

#### Scenario: 报告生成
- **WHEN** 任务结束
- **THEN** 生成统计：扫描素材总数、重复组数量、各类型命中、预计可释放空间
- **AND** 持久化在 `dedup_jobs` 表，供 API/前端查询
- **AND** 按最新标记更新 `images` 表字段

### Requirement: 去重报告查询
系统 SHALL 提供最近一次任务结果，供前端展示。

#### Scenario: 查询最新报告
- **WHEN** 调用 `GET /api/dedup/jobs/latest`
- **THEN** 返回最近一次成功的任务摘要（时间、各阶段命中、space_saving_estimate）
- **AND** 若尚未运行过任务，返回 404 + 说明文本

#### Scenario: 任务状态跟踪
- **WHEN** 调用 `GET /api/dedup/jobs/<id>`
- **THEN** 返回 `status`, `phase`, `progress`, `duplicates_found`
- **AND** 若任务失败，包含错误信息与可重试提示
