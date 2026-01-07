## ADDED Requirements
### Requirement: PDF 结果展示与多页预览
系统 SHALL 在前端展示 PDF 首页，并支持在详情中查看所有页面（懒加载）。

#### Scenario: 搜索列表展示 PDF 首页
- **GIVEN** 搜索结果包含 PDF 条目（`page_no=1`, `page_count=10`）
- **WHEN** 渲染结果卡片
- **THEN** 卡片显示 PDF 图标与页数标记（如 "10 页"）
- **AND** 缩略图使用首页缩略图
- **AND** 点击卡片打开 PDF 预览弹窗

#### Scenario: 查看 PDF 全部页面
- **GIVEN** 用户打开 PDF 预览弹窗
- **WHEN** 弹窗加载
- **THEN** 首屏展示第一页大图与页面列表（侧边/底部）缩略图
- **AND** 其他页面缩略图懒加载（滚动或分页时加载）
- **AND** 点击任意页面缩略图切换主视图，支持跳转指定页码
- **AND** 提供打开原文件/下载入口（新窗口或系统关联）

#### Scenario: 批量索引预览中的 PDF
- **GIVEN** 用户在“预览文件”列表看到 PDF 文件
- **WHEN** 列表渲染
- **THEN** 显示 PDF 图标与首页缩略图占位
- **AND** 点击缩略图使用同一 PDF 预览弹窗展示所有页面
