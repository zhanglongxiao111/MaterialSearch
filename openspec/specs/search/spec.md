# search 规范

## Purpose
待定 - 通过归档变更 add-project-database-architecture 创建。归档后更新目的。
## Requirements
### Requirement: 高级筛选条件
系统 SHALL 支持基于元数据的高级筛选条件，结合向量搜索提供精准结果。

#### Scenario: 按宽高比筛选
- **WHEN** 用户搜索时添加宽高比筛选（如 `aspect_ratio_standard='16:9'`）
- **THEN** 系统先用 SQL 筛选符合宽高比的图片
- **AND** 在筛选后的结果中进行向量相似度计算
- **AND** 提升搜索精准度和性能

#### Scenario: 按分类筛选
- **WHEN** 用户搜索时指定分类（如 `category='现代风格'`）
- **THEN** 系统先筛选该分类的图片
- **AND** 在筛选结果中计算向量相似度

#### Scenario: 按上传时间范围筛选
- **WHEN** 用户搜索时指定时间范围（如"最近一周"）
- **THEN** 系统添加 SQL 条件 `WHERE upload_time >= <start_date>`
- **AND** 在时间范围内的图片中搜索

#### Scenario: 组合多个筛选条件
- **WHEN** 用户同时指定多个筛选条件
  - 例如：`category='效果图'` AND `aspect_ratio_standard='16:9'` AND `building_type='住宅'`
- **THEN** 系统用 SQL 的 AND 条件组合筛选
- **AND** 在满足所有条件的图片中进行向量搜索
- **AND** 大幅减少需要计算相似度的图片数量

---

### Requirement: 搜索结果来源标注
系统 SHALL 在搜索结果中清晰标注每张图片的来源。

#### Scenario: 标注永久库图片
- **WHEN** 搜索结果包含永久库的图片
- **THEN** 结果中包含字段：
  - `source_type='permanent'`
  - `source_label='永久库'`
- **AND** 如果图片是从项目归档来的，额外标注 `source_project`

#### Scenario: 标注项目库图片
- **WHEN** 搜索结果包含项目库的图片
- **THEN** 结果中包含字段：
  - `source_type='project'`
  - `project_id='proj_2025_万科_01'`
  - `project_name='2025万科城市之光项目'`
  - `source_label='项目: 2025万科城市之光'`

#### Scenario: 全局搜索结果混合展示
- **WHEN** 用户进行全局搜索
- **THEN** 结果中混合永久库和多个项目的图片
- **AND** 每张图片清晰标注来源
- **AND** 前端可按来源分组展示

---

### Requirement: 搜索性能优化
系统 SHALL 针对不同搜索范围优化性能。

#### Scenario: 项目内搜索性能
- **WHEN** 用户在项目内搜索（约 100 张图片）
- **THEN** 系统直接暴力搜索（遍历所有向量）
- **AND** 响应时间 < 1 秒
- **AND** 不使用向量索引（数据量小，索引开销大于收益）

#### Scenario: 永久库搜索性能
- **WHEN** 用户在永久库搜索（约 1 万张图片）
- **THEN** 系统暴力搜索（SQLite + FAISS 可选）
- **AND** 响应时间 < 3 秒（J3455 CPU 基准）
- **AND** 未来数据量增长可引入 FAISS 索引

#### Scenario: 全局搜索性能警告
- **WHEN** 用户尝试全局搜索（50+ 项目，约 6 万张图片）
- **THEN** 系统提示"全局搜索可能较慢，建议指定项目"
- **AND** 可选：限制全局搜索的项目数量（如最近 10 个活跃项目）
- **AND** 响应时间约 10-30 秒（取决于项目数量）

---

### Requirement: 搜索缓存管理
系统 SHALL 维护搜索结果缓存，提升重复查询性能（更新：按库分别缓存）。

#### Scenario: 永久库搜索缓存
- **WHEN** 用户在永久库搜索
- **THEN** 系统缓存搜索文本/图片 ID 和结果
- **AND** 相同搜索在缓存有效期内直接返回缓存结果
- **AND** 缓存容量：64 条（可配置）
- **AND** 使用 LRU 策略淘汰旧缓存

#### Scenario: 项目库搜索缓存
- **WHEN** 用户在项目库搜索
- **THEN** 系统为每个项目独立维护缓存
- **AND** 项目切换时缓存不混淆

#### Scenario: 缓存失效
- **WHEN** 有新图片上传到数据库
- **THEN** 系统清空对应库的搜索缓存
- **OR** 标记缓存为过期，下次搜索重新计算

---

### Requirement: 排除已归档图片
系统 SHALL 在项目库搜索时默认排除已归档的图片。

#### Scenario: 项目库搜索排除已归档
- **WHEN** 用户在项目中搜索
- **THEN** 系统添加 SQL 条件 `WHERE archived=0`
- **AND** 已归档到永久库的图片不出现在结果中
- **AND** 用户可通过参数 `include_archived=true` 显示已归档图片

#### Scenario: 永久库搜索不受影响
- **WHEN** 用户在永久库搜索
- **THEN** `archived` 字段不存在或忽略
- **AND** 搜索所有永久库图片（包括归档来的）

---

### Requirement: 搜索结果分页
系统 SHALL 支持搜索结果分页，避免一次性返回大量数据。

#### Scenario: 分页查询
- **WHEN** 用户搜索返回大量结果（如 500 张图片）
- **THEN** 系统默认返回前 N 张（如 20 张）
- **AND** 提供 `limit` 和 `offset` 参数
- **AND** 返回总结果数量

#### Scenario: 向量搜索的分页优化
- **WHEN** 进行向量相似度搜索
- **THEN** 系统计算所有图片的相似度（无法避免）
- **AND** 按相似度排序后返回前 N 条
- **AND** 用户请求下一页时，从已排序结果中取下一批
- **AND** 缓存排序结果避免重复计算

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

### Requirement: 项目库空查询列出全部素材
系统 SHALL 仅在项目库空查询时返回该库全部素材（受 top_n/去重限制）；永久库空查询应被拒绝。

#### Scenario: 项目库空搜索
- **WHEN** 用户在项目库模式下提交空搜索（无关键词、路径或时间范围）
- **THEN** 系统返回该项目库的全部素材
- **AND** 结果与项目库计数一致（受 top_n/去重参数影响）

#### Scenario: 永久库空搜索被拒绝
- **WHEN** 用户在永久库提交空搜索（无关键词、路径或时间范围）
- **THEN** 系统返回提示，要求输入关键词或路径
- **AND** 不执行全量查询，避免大规模数据扫描

### Requirement: PDF 页面搜索与结果聚合
系统 SHALL 将 PDF 页面作为可检索对象参与文本/以图搜索，并以文件级聚合呈现。

#### Scenario: 搜索结果返回 PDF 首页
- **GIVEN** 目标库存在 PDF 页面记录（`page_no=1`, `page_count=10`, `is_primary=true`）
- **WHEN** 用户以文本或图片发起搜索
- **THEN** 该首页按相似度参与检索并可能出现在结果中
- **AND** 结果包含字段：`type='pdf'`、`page_no=1`、`page_count=10`、`doc_path=<pdf 绝对路径>`、`thumbnail=/api/thumbnail?...`
- **AND** 同一 PDF 的非首页页面默认不出现在第一页结果中（除非显式按页查询）

#### Scenario: 查看 PDF 全部页面
- **GIVEN** 用户点击搜索结果中的 PDF 项
- **WHEN** 前端请求页面列表接口（例如 `GET /api/pdf_pages?path=<encoded>&limit=...&offset=...`）
- **THEN** 系统返回页数与页面元数据数组：`page_no`、`thumbnail`、`width`、`height`（如可得）
- **AND** 支持分页/按需加载，按页码顺序返回

