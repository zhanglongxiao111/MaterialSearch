## ADDED Requirements
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
