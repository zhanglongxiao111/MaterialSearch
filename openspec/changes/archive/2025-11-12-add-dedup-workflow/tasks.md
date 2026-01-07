# 实施任务清单

## 1. 上传实时去重
- [x] 1.1 扩展上传（permanent）逻辑：checksum+size 命中即返回重复，比较分辨率自动保留高分版本
- [x] 1.2 更新批量索引策略：项目库仅提示，永久库默认 `skip`，并将命中记录到重复列表

## 2. 去重任务与数据标记
- [x] 2.1 新增 dedup job 模型/API（创建、查询状态、读取上次报告）
- [x] 2.2 实现后台扫描器：checksum -> phash -> clip embedding，写入 `duplicate_group/master_image_id/duplicate_type/duplicate_confidence`
- [x] 2.3 选择主图规则（按像素数、修改时间）并 soft delete/标记副本

## 3. 搜索与缓存
- [x] 3.1 永久库搜索默认排除 `is_duplicate=1` 副本，提供 `include_duplicates` 参数
- [x] 3.2 缓存层在库状态变更/完成去重时清空，确保结果一致

## 4. 前端 Workspace / Classic
- [x] 4.1 Search 面板新增“包含重复” toggle，仅永久库可见，并反向驱动 API 参数
- [x] 4.2 顶栏或侧栏提供“手动去重”按钮 + 报告弹窗，展示扫描统计/时间
- [x] 4.3 Classic UI 同步添加入口或至少提示去重状态

## 5. 验证
- [ ] 5.1 单元/集成测试：上传重复素材、触发去重任务、确认搜索过滤
- [ ] 5.2 端到端验证：运行一次手动任务，检查报告、搜索结果、UI 开关
