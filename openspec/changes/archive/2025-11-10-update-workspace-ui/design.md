# Workspace UI 重设计方案

## 参考
- 原型：`D:\AI\materialsearch\.superdesign\design_iterations\materialsearch_3.html`
- 主题变量：`materialsearch_theme_2.css`（包含自定义 CSS 变量、暗色/亮色组合）

## 结构概览
```
body.material-layout
├─ header.material-header                # 顶部工具栏
├─ div.material-shell
│  ├─ aside.material-sidebar             # 库/项目切换与列表
│  └─ main.material-main
│     ├─ tabs + scope 描述行
│     ├─ section#search-panel            # 搜索命令面板（仅搜索 Tab 显示）
│     ├─ section#results-section         # 瀑布流/网格结果
│     ├─ section#upload-section          # Upload Tab 内容
│     └─ section#stats-section           # Stats Tab 内容
```

## 交互分层
1. **Shell（Header + Sidebar）**
   - Header 负责显示当前范围（chip）、主题切换、全局动作（上传、扫描）。
   - Sidebar 负责库类型切换（permanent/project）并展示对应列表；点击项驱动 scope 文案与搜索参数。
2. **Command Surface**
   - 搜索命令条聚合输入、Top N、搜索按钮。
   - 模式 pill + “复制全部路径” + 视图/缩略图控制共同位于命令条下方，方便频繁交互。
   - 高级面板默认折叠，由 JS 控制显示。
3. **Workspace Tabs**
   - Search Tab：展示命令面板 + 结果区。
   - Upload / Stats Tab：隐藏命令面板，呈现自定义内容面板（后续组件的容器）。
4. **结果视图**
   - 默认 `results-masonry`（column-count）渲染，切换 Grid 时改用 CSS Grid。
   - 结果卡包含来源 tag、匹配度、路径及操作按钮；脚本根据 data 属性控制样式/按钮可见性。

## 状态与数据流
- **主题状态**：保存在 `localStorage`, key=`materialsearch-theme`；切换时更新 `<html>` 上的 `data-theme` 及 `color-scheme`，确保在刷新后恢复。
- **范围状态**：由 sidebar pill + 列表控制；点击后写入 `localStorage`（沿用现有 `currentLibrary` / `currentProject`），并调用既有搜索/扫描 API。
- **视图状态**：`view-toggle` 切换 `results-wrapper` 的类名；缩略图 slider 修改 `column-count` 或 `grid-template-columns`。
- **Tab 状态**：通过 dataset 更新 active tab，同时控制 `search-panel` 显隐；`open-upload-btn` 直接激活 Upload tab。

- **统计状态**：Sidebar/Scope/Stats tab 展示的数量全部来自 `/api/status`、`/api/projects` 数据源，刷新或切换时应重新拉取并缓存，禁止硬编码占位数字。
- **详情/Viewer 状态**：每个 result item 需保留完整 DB 字段（path/source/score/size/captured_at 等），点击后通过 overlay + Viewer 组件渲染，保证可以恢复到上一次浏览的素材。

## 响应式
- 1440px+: 侧栏 + 4 列瀑布流。
- 1024px-1440px: 侧栏折叠（隐藏），瀑布流 3 列，主区域 padding 收缩。
- 768px-1024px: 瀑布流 2 列；Tabs、命令 panel 变为垂直堆叠。
- <768px: 1 列瀑布流，顶部/Sidebar 采用抽屉（后续迭代，可先隐藏 sidebar）。

## 与现有功能的衔接
- Search/Upload/Stats 功能沿用现有 axios 调用，只重构 DOM 布局。
- 批量上传对话框、项目管理对话框仍在顶层，通过按钮触发即可，无需完全重写逻辑。
- 设计稿中的统计卡片、上传详情目前以占位文本实现，后续迭代可在对应 section 内插入真实组件。

## 实施守则 / 工作流提示
1. **先 1:1 复制原型骨架**：把 `.superdesign` 中的 HTML/CSS/JS 结构完整复制为 `index_workspace.html`（或等效模板），确保类名、DOM 层级与设计稿一致，再逐步注入真实数据。
2. **共存策略**：保留 `index.html` 作为 classic 入口，新版 Workspace 通过单独路由或 query 参数访问，互不干扰，便于对比/灰度。
3. **逐块替换内容**：在 Workspace 模板内，用 Vue/ElementPlus 绑定真实数据时，尽量不要调整外层容器；如果需要自定义组件，在内部嵌套并沿用 `material-*` 类名。
4. **先静态后联动**：优先让 Workspace UI 以静态数据渲染并通过主题/响应式验收，再一点点接入搜索/上传/统计 API，避免同时引入多个变量。
5. **CSS 扩展策略**：如需自定义变量或覆盖主题，额外创建覆盖文件，而不是直接修改设计稿附带的 `materialsearch_theme_2.css`，确保将来可以直接同步新版本原型。
6. **实时数据与统计**：任何出现在 sidebar、Scope chip、Stats tab 的数量/状态都必须调用 `/api/status`、`/api/projects` 或衍生接口读取，不得写死示例数字。
7. **Viewer 集成**：结果卡片点击后统一进入 Viewer overlay，图片交互（缩放/旋转/拖拽/键盘）依赖成熟库（Viewer.js/PhotoSwipe），同时在 overlay 内展示数据库字段和操作按钮，保持与设计稿一致。


