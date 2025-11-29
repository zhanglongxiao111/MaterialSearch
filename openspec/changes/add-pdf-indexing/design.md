## Context
- 现状：批量索引仅处理图片/视频；缩略图 API 已支持 PDF 首页渲染但未入库。搜索/前端仅返回可视素材（图片/视频）。
- 目标：让 PDF 成为可检索素材，默认以首页呈现，放大时可浏览全部页面。
- 约束：性能与依赖（pdf2image+poppler）；避免大文件/超长文档耗尽资源。

## Goals / Non-Goals
- Goals: 将 PDF 页面转换为图像提取 CLIP 特征；首页参与检索；返回页数/页码元数据；提供页面列表/预览接口；前端展示首页并支持多页查看。
- Non-Goals: 实现 PDF 文本语义搜索（仅图片特征）；全文 OCR；在线编辑/批注。

## Decisions
- 数据模型：每个 PDF 页面视为一条可检索的“页面记录”，存储 page_no、page_count、source_path、thumbnail_path/URL、features。首页标记 primary。
- 页数限制：默认仅处理前 N 页（建议 10，可配置），超出记录 truncation 标记，保护性能。
- 缩略图复用：索引时生成/缓存页面 JPG，复用现有 /api/thumbnail 缓存目录。
- 搜索聚合：结果层仅返回首页（primary）；详情接口返回全部页面元数据，前端懒加载。
- API：新增页面列表/单页缩略图接口（path + page_no + size），权限沿用登录态。

## Risks / Trade-offs
- 大文件性能：通过页数/尺寸上限、超时保护，必要时跳过并报告 failed。
- 依赖缺失：缺少 poppler/pdf2image 时降级为默认图，报告错误并跳过索引。
- 存储膨胀：缓存 JPG 与特征占用增加；通过页数上限与缓存 TTL 控制。

## Migration Plan
1) 扩展 DB/DAO 支持 PDF 页面记录与 page 元数据；添加必要迁移脚本。
2) 更新 batch_index 处理 PDF：渲染页面、生成缩略图、写入特征与页码。
3) 暴露页面列表/缩略图 API，返回 page_count/page_no。
4) 前端搜索卡片/预览对接新字段；新增多页查看弹窗。
5) 验证与回归测试；性能与依赖检查。

## Open Questions
- 页数上限默认值（已定 15，可通过环境变量配置）。
- 缩略图/特征分辨率标准（已定横向 1920，等比缩放）。
