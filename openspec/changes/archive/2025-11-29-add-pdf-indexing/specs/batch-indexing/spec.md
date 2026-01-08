## ADDED Requirements
### Requirement: PDF 文件索引与特征提取
系统 SHALL 将支持的 PDF 文件转换为页面图像，并将页面作为可检索素材入库。

#### Scenario: 索引 PDF 首页并写入元数据
- **GIVEN** `POST /api/batch_index` 接收包含 `\\share\\doc.pdf`（3 页）的文件
- **WHEN** 后端处理该文件
- **THEN** 渲染第一页为图像（保持比例，尺寸不少于 512px 边）
- **AND** 提取 CLIP 特征并存入目标库，记录 `source_path=\\share\\doc.pdf`、`page_no=1`、`page_count=3`、`is_primary=true`
- **AND** 成功计数增加，进度/状态接口可见该 PDF 的条目

#### Scenario: 限制多页索引并缓存预览
- **GIVEN** PDF 文件包含 20 页，系统页数上限为 15（可配置）
- **WHEN** 索引该文件
- **THEN** 渲染并提取前 15 页，每页一条记录（含 `page_no/page_count`），首页标记 primary
- **AND** 为每页生成缩略图写入 `/tmp/thumbnails/<md5>.jpg`（或配置的缓存目录）
- **AND** 未处理的页设置 `pages_truncated=true`（在报告/状态中可见）
- **AND** 渲染/提取超时或失败时，将该页记入 failed 列表并继续下一个文件

#### Scenario: 保持宽度1920的等比渲染
- **GIVEN** PDF 页面尺寸为任意比例
- **WHEN** 将页面转换为图像提取特征
- **THEN** 按等比缩放使宽度达到 1920（或高度达到 1920，取决于横向/纵向），不拉伸变形
- **AND** 缩略图在缩放后生成，保持清晰度用于 CLIP 特征提取与前端展示
