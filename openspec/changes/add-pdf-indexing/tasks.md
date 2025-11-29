## 1. 实施
- [x] 1.1 扩展数据库/DAO 支持 PDF 页面记录（page_no、page_count、source_path、primary 标记）。
- [x] 1.2 batch_index 支持 PDF：渲染前 N 页、提取 CLIP 特征、写入缩略图与元数据，加入失败/截断报告。
- [x] 1.3 新增/扩展 API：页面列表与单页缩略图（含 page_no），带登录校验与超时保护。
- [x] 1.4 搜索层返回 PDF 首页，详情接口返回全部页面元数据。
- [x] 1.5 前端：搜索卡片与索引预览显示 PDF 首页+页数，点击弹窗懒加载全部页面。
- [x] 1.6 Dockerfile 添加 poppler-utils 依赖。
- [x] 1.7 README 添加 Poppler 安装说明（Windows/Linux/macOS）。
- [x] 1.8 前端添加"打开原文件"按钮（PDF 详情弹窗）。
- [x] 1.9 增强 PDF 特征提取失败时的日志记录。
- [x] 1.10 scan.py 添加 PDF 自动扫描支持（修复遗漏）。
- [x] 1.11 database.py 添加 delete_pdf_if_outdated 变更检测函数。

## 2. 验证
- [ ] 2.1 单测/集成：PDF 3 页与超限文档（>N 页）索引结果正确，截断标记生效。（未执行）
- [ ] 2.2 回归：图片/视频索引与缩略图不受影响；依赖缺失时错误提示与默认图。（未执行）
- [ ] 2.3 性能：大文件/多页超时保护与缓存目录写入正常。（未执行）
- [x] 2.4 `openspec validate add-pdf-indexing --strict`

## 3. 技术债务 (Non-Blocking)
- [x] 3.1 重构：提取 `process_pdf_pages()` 等公共函数到 `process_assets.py`，消除 `routes.py` 与 `scan.py` 的 PDF 处理重复代码。
