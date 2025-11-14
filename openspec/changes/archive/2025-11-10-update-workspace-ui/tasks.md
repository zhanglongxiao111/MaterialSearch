# 实施任务清单

## 1. Workspace Shell 与主题
- [x] 1.1 顶部应用栏：logo、当前范围 chip、快速按钮（上传 / 扫描）与主题切换器
- [x] 1.2 主题切换逻辑：auto/light/dark 三态，保存在 `localStorage`，切换时更新 `data-theme` 和 `color-scheme`

## 2. 侧边栏范围管理
- [x] 2.1 实现库类型 pill（permanent/project），点击切换显示对应列表
- [x] 2.2 永久库分组列表（全部、效果图、AI 生成、参考图、材质等）及统计标签
- [x] 2.3 项目列表（含 + 新建项占位），点击后更新篮信息并触发后端参数
- [x] 2.4 统一更新顶栏 chip 和 scope 描述文案

## 3. 搜索命令面板
- [x] 3.1 主输入框 + Top N 下拉 + 搜索按钮布局
- [x] 3.2 搜索模式 pill（文本/图片/视频/混合）与 copy-all-path 操作
- [x] 3.3 高级筛选面板（包含/排除路径输入、快速 chips）
- [x] 3.4 视图切换器（瀑布流/网格）与缩略图大小 slider

## 4. 结果视图与卡片
- [x] 4.1 默认瀑布流布局，支持响应式列数
- [x] 4.2 Grid 模式切换：在 CSS/JS 中切换 `results-masonry` / grid 样式
- [x] 4.3 结果卡片字段：库/项目标签、匹配度、路径、操作按钮（复制、归档、删除）
- [x] 4.4 骨架/占位卡片，用于加载状态

## 5. Tab 导航与内容区
- [x] 5.1 上方 tab（Search/Upload/Stats）与 `open-upload-btn` 联动
- [x] 5.2 Tab 切换时控制 `search-panel` 显示/隐藏
- [x] 5.3 Upload / Stats 面板容器和说明文案，预留后续组件挂载点

## 6. 数据/状态联动
- [x] 6.1 将范围切换结果反映到搜索参数、`localStorage`
- [x] 6.2 整合现有 axios / API 调用逻辑，确保命令面板按钮触发搜索
- [x] 6.3 保留/迁移原有历史路径、批量上传对话框等入口（与新 UI 兼容）

## 7. 验证
- [x] 7.1 交互冒烟：库/项目切换、搜索、视图切换、主题切换
- [x] 7.2 浏览器适配（≥1440px 与 1024px/768px 响应式行为）
- [x] 7.3 文案/Chip 与设计稿一致性复查，并附上截图供 PR 审阅

## 8. 数据同步与详情 Viewer
- [x] 8.1 Sidebar 永久库统计、项目素材数量/状态改为读取 `/api/status`、`/api/projects`，禁止硬编码。
- [x] 8.2 Scope chip、Stats Tab、顶部提示条等所有计数统一复用后端返回值，刷新后可恢复。
- [x] 8.3 结果卡片点击打开设计稿同款 overlay，使用 Viewer.js / PhotoSwipe 实现缩放/旋转/拖拽，并在详情区展示 path/source/score/size/captured_at 等字段及操作按钮。
