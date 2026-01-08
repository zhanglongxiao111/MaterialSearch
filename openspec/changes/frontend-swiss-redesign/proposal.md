# Change: Workspace 前端瑞士国际主义风格重构

## Why

当前 workspace 前端使用深紫色调和圆角设计，用户希望改为更具建筑美学的瑞士国际主义风格（Swiss International Style），参考设计稿 `.superdesign/design_iterations/superdesign_master_v2.html`。

**目标：**
- 统一视觉语言，体现建筑设计事务所专业形象
- 保持所有现有功能不变
- 品牌定位：SA Architects

## What Changes

### 核心变更
- **配色方案**：深紫色调 → 黑白灰 + 橙色强调 (#FF3300)
- **边角风格**：圆角 → 方角 (border-radius: 0)
- **字体系统**：添加 JetBrains Mono 用于技术标签
- **品牌标识**：左上角显示 "SA ARCHITECTS" + 副标题

### 布局调整
- **侧边栏宽度**：260px → 320px
- **响应式侧边栏**：窄屏时可滑动隐藏/显示
- **保留瀑布流**：网格+瀑布流双模式保持不变
- **保留单图宽度调节**：现有功能保持

### 视觉元素
- **背景**：添加建筑网格背景纹理
- **滚动条**：极简风格 (4px 黑色)
- **标签系统**：UPPERCASE + 加大字间距
- **图片效果**：保持始终彩色（不使用灰度）

### 语言策略
- **主 UI**：保持中文
- **装饰标签**：使用英文 (如 `INDEX_RESULT`、`ONLINE` 等)
- **中英混排**：标题区域可中英混排

## Impact

### 受影响的文件
- `static/assets/materialsearch_theme_2.css` (主要修改)
- `static/index_workspace.html` (品牌标识、类名调整)
- `static/assets/workspace.js` (侧边栏响应式逻辑)

### 不受影响
- 所有后端 API
- 所有业务逻辑
- 搜索、上传、项目管理等功能

## Rollback Plan

1. CSS 使用新文件 `materialsearch_theme_swiss.css`
2. 通过 CSS 变量切换主题
3. 保留原 CSS 文件作为备份
