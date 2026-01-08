# Change: 增加 PDF 索引与预览

## Why
- 批量索引目前仅支持图片/视频，PDF 素材无法搜索和入库，素材覆盖不足。
- 前端只能展示 PDF 图标，缺少首页/多页预览，用户无法快速判断内容。

## What Changes
- 扩展批量索引支持 PDF：渲染页面、提取 CLIP 特征并入库，生成缓存缩略图。
- 搜索结果展示 PDF 首页，点击放大后可浏览所有页面（懒加载）。
- 输出页数、页码等元数据与新接口，限制页数/大小保护性能。

## Impact
- 受影响规范：batch-indexing、search、frontend-library-ui
- 受影响代码：routes.py（batch_index/thumbnail/API 扩展）、process_assets、database schema/DAO、search 结果序列化、static 前端 UI
