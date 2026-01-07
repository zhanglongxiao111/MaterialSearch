# 设计：素材去重能力

## 架构概览
```
上传入口 (permanent) ──> checksum 过滤 ──> （非重复）落库
                                   │
                                   └──> 重复统计 + 高分版本对比

手动触发去重任务 ──> 任务队列表 ──> 分段扫描
                                 1. checksum 精确重复
                                 2. phash 感知重复
                                 3. CLIP 向量相似度
                       └──> 生成报告 + 标记 duplicate_group/master

搜索服务 ──> 根据库类型决定是否过滤 is_duplicate=1
前端 Workspace ──> 去重按钮 / “包含重复”筛选
```

## 核心流说明

### 1. 实时精确去重（上传路径）
- 上传永久库时，先根据 `(file_size, checksum)` 做 O(1) 命中；命中后直接返回“已存在”并附带旧图信息。
- 若尺寸不同，则比较 `width * height`，保留像素更多的一份作为 `master_image_id`，另一份标记 `duplicate_type=exact`.
- 项目库上传仍可通过校验提示，但不阻断写入。

### 2. 离线批量去重（手动任务）
- 通过 `POST /api/dedup/jobs` 创建任务，仅允许 `library_type=permanent`（可附加分组/路径过滤）。
- 任务在后台 worker 中顺序执行三个阶段，阶段间会复用扫描结果避免重复计算：
  1. `checksum` 完全相同：直接归组。
  2. `phash`（Hamming 距离 <= 5）认定为视觉重复；存下匹配距离。
  3. `clip_embedding` 余弦相似度 >= 0.95 视为内容近重复。
- 每组根据“更大分辨率 > 更新鲜更新时间”规则挑选 `master_image_id`。
- 扫描完成后写报告表（总扫描数、重复组统计、预计可释放空间），并按素材记录 `is_duplicate`、`duplicate_group`、`duplicate_type` 等字段。

### 3. 搜索和前端展示
- 搜索永久库默认添加 `WHERE is_duplicate=0 OR master_image_id IS NULL`，并允许 `include_duplicates=true` 参数覆盖。
- Workspace/Classic UI 在永久库模式下显示“去重扫描”按钮，触发 API 启动任务并实时显示最近报告。
- 搜索面板增加“包含重复”开关，默认关闭，只对永久库可见。

### 4. 失败与恢复
- 扫描过程中若 GPU/CLIP 不可用，只运行前两个阶段并在报告中注明“内容相似检测跳过”。
- 任务状态持久化，确保即使服务重启也可恢复/再次查询结果。

## 数据模型
- `dedup_jobs`（新表）：`id`, `created_at`, `created_by`, `status`, `phase`, `total_scanned`, `duplicate_groups`, `space_saving_estimate`, `notes`.
- 在 `images` 表中沿用 `checksum/phash/is_duplicate/duplicate_group/master_image_id/duplicate_type`, 新增 `duplicate_confidence`.
- 需要索引：`(library_type, is_duplicate)`, `duplicate_group`, `checksum`, `phash`.

## 前端交互细节
- Workspace header 的“更多”菜单加入“手动去重”按钮，仅在永久库时启用。
- 点击后弹出确认对话框，说明扫描时间/影响；提交后进入“处理中”状态并显示最近一次报告。
- 搜索过滤下方新增 Toggle：“包含重复结果（永久库专用）”，默认关闭。
