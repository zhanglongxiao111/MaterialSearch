## ADDED Requirements

### Requirement: Workspace Shell 与主题切换
系统 SHALL 提供与设计稿一致的工作台顶栏与主题控制，并允许与经典 UI 并存。

#### Scenario: 顶栏显示当前上下文
- **GIVEN** 用户位于 Workspace 任意 Tab
- **WHEN** 页面加载或库范围更新
- **THEN** 顶部左侧区域显示（logo + “MaterialSearch Workspace” + 当前范围 chip）
- **AND** 右侧展示“添加素材”“触发扫描”按钮与当前上下文 chip

#### Scenario: 经典 UI 共存
- **GIVEN** 需要与老版页面对比
- **WHEN** 用户访问 `index_classic.html`（或等效入口）
- **THEN** 传统 UI 保持可用
- **AND** Workspace 版本可通过新路由/入口访问，并共享同一后端 API

#### Scenario: 主题切换与持久化
- **GIVEN** 用户点击主题 chip
- **WHEN** 依次切换 auto → light → dark
- **THEN** `<html data-theme>` 与 `color-scheme` 更新
- **AND** 选择写入 `localStorage`，刷新后保持

### Requirement: 侧边栏范围与列表
系统 SHALL 在左侧侧边栏中管理永久库 / 项目库分组。

#### Scenario: 库类型 pill 切换
- **GIVEN** 侧栏顶部存在“永久库 / 项目库” pill
- **WHEN** 用户点击任一 pill
- **THEN** 激活状态切换
- **AND** 根据类型显示对应列表（永久库分组或项目列表）
- **AND** 顶栏 chip 与 scope 描述同步更新

#### Scenario: 永久库分组
- **GIVEN** 选择“永久库”且存在分组统计
- **WHEN** 用户点击“效果图/AI 生成/参考素材/材质库”等条目
- **THEN** 该条目高亮显示统计信息
- **AND** 搜索范围限定在对应分组（传入后端过滤参数）

#### Scenario: 项目列表与创建入口
- **GIVEN** 选择“项目库”
- **WHEN** 用户点击任一项目或“+ 新建项目”占位
- **THEN** 激活状态更新、顶栏 chip 显示“项目库 · <项目名>”
- **AND** 点击“+ 新建项目”时呼出既有创建项目前端流程

### Requirement: 搜索命令面板
系统 SHALL 在 Search Tab 顶部展示统一的命令面板。

#### Scenario: 主命令条
- **GIVEN** Search Tab 激活
- **WHEN** 命令面板可见
- **THEN** 包含：主输入框、Top N 下拉（30/60/150/全部）、搜索按钮
- **AND** 按钮触发既有 `/api/match` 调用，参数取自输入与当前范围

#### Scenario: 搜索模式与快速操作
- **GIVEN** 命令条下方的操作区
- **WHEN** 用户点击“文本/图片/视频/混合” pill
- **THEN** 激活状态唯一，更新 `form.search_type`
- **AND** “复制全部路径”按钮可一次性复制结果路径列表

#### Scenario: 视图/缩略图控制
- **GIVEN** 命令条下方的视图开关与 slider
- **WHEN** 切换“瀑布流/网格”或拖动 slider
- **THEN** 改变 `results-wrapper` 布局（column-count 或 grid-template），调整卡片尺寸

#### Scenario: 高级面板
- **GIVEN** 用户点击“高级筛选”开关
- **WHEN** 面板展开
- **THEN** 显示“包含路径”“排除关键字”输入与预设 chips（时间范围、授权状态等）
- **AND** 关闭开关时折叠面板

### Requirement: 结果瀑布流与卡片交互
系统 SHALL 以设计稿样式展示搜索结果。

#### Scenario: 瀑布流默认呈现
- **GIVEN** Search Tab 有结果
- **WHEN** 未启用网格模式
- **THEN** `results-wrapper` 使用瀑布流布局（>=1440px 4 列，宽度缩小时 3/2/1 列）
- **AND** 每个 `result-card` 展示：来源 tag（永久库/项目 + 分组）、匹配度、路径、操作按钮（复制、归档/删除）

#### Scenario: 网格模式
- **GIVEN** 用户切换到 Grid
- **WHEN** view-toggle=grid
- **THEN** wrapper 采用 CSS Grid，自适应列宽
- **AND** 卡片样式保持一致，保留操作按钮

#### Scenario: 占位骨架
- **GIVEN** 结果加载中
- **WHEN** 后端响应未到
- **THEN** 显示若干 `result-card` 骨架（灰色块 + 动画）代替真实内容

### Requirement: Workspace Tabs
系统 SHALL 通过 Tab 控制 Search/Upload/Stats 区域。

#### Scenario: Tab 激活逻辑
- **GIVEN** 顶部存在 Search / Upload / Stats 三个 tab
- **WHEN** 用户点击任意 tab
- **THEN** 激活状态更新
- **AND** 仅 Search tab 显示命令面板与结果区
- **AND** Upload/Stats 显示对应 section，装载后续批量上传/统计模块

#### Scenario: 从按钮进入 Upload
- **GIVEN** Header 中的“添加素材”按钮
- **WHEN** 用户点击按钮
- **THEN** Tab 自动切换到 Upload，显示上传面板占位内容

### Requirement: 库范围隔离
Workspace SHALL keep permanent/project scopes fully separated，禁止“所有库”这类组合选项。

#### Scenario: 仅暴露永久/项目
- **GIVEN** 用户位于 Workspace 搜索区
- **WHEN** 切换范围 chip/pill
- **THEN** 可选值仅包含 `permanent` 与具体项目 ID
- **AND** UI 不得提供 “all/全部库” 之类融合选项。

#### Scenario: 参数校验
- **GIVEN** 前端准备调用 `/api/match`
- **WHEN** `library_type` 缺失或不在 {permanent, project}
- **THEN** 前端需提示并阻止请求，若为项目模式还必须注入 `project_id`。

#### Scenario: 切换归零
- **GIVEN** 已勾选若干项目素材
- **WHEN** 用户切回永久库或更换项目
- **THEN** 既有选中状态、批量操作提示需清空，以防跨库操作。

### Requirement: 设计稿传承
Workspace SHALL 保持与 `.superdesign/design_iterations/materialsearch_3.html` 1:1 的布局与样式。

#### Scenario: 模板复制
- **GIVEN** 需要更新 Workspace HTML
- **WHEN** 初始化或刷新样式结构
- **THEN** 工程师应直接复制设计稿 HTML/CSS 至 `static/index_workspace.html` 与 `static/assets/materialsearch_theme_2.css`，仅做必要变量/指令替换。

#### Scenario: 双 UI 共存
- **GIVEN** 经典界面仍用于对照
- **WHEN** Workspace 发生结构变更
- **THEN** 保留 `static/index_classic.html` 原样可访问，并提供 `/classic` 与 `/workspace` 显式入口。

#### Scenario: 样式最小化修改
- **GIVEN** 设计稿未变
- **WHEN** 需要新增状态色或动画
- **THEN** 修改应集中在 `materialsearch_theme_2.css`，并记录在 spec/review，以便设计团队追踪偏差。

### Requirement: 实时库统计
Workspace SHALL display library/project counts using live backend data.

#### Scenario: Sidebar 统计来自接口
- **GIVEN** Workspace sidebar renders永久库分类或项目列表
- **WHEN** 页面加载或切换库类型
- **THEN** 客户端调用 `/api/status`（永久库）与 `/api/projects`（项目库）并填充 `image_count`/`video_count`/状态等字段
- **AND** 任何 chip/标签上不再出现硬编码示例数字。

#### Scenario: Scope/Stats 同步
- **GIVEN** 用户切换库或刷新页面
- **WHEN** scope chip、Stats tab 或顶部提示展示总量
- **THEN** 数值与最新接口一致，可在刷新后恢复，且会区分永久库/项目库。

### Requirement: 结果详情 Viewer
Workspace SHALL open a high-fidelity detail overlay with Viewer capabilities.

#### Scenario: 点击结果卡片
- **GIVEN** 搜索结果已渲染
- **WHEN** 用户点击任意结果卡
- **THEN** 弹出与设计稿一致的 overlay，显示大图预览与数据库字段（path/source/score/size/captured_at 等）
- **AND** 提供复制路径、归档/删除等 CTA。

#### Scenario: Viewer 交互
- **GIVEN** overlay 已打开
- **WHEN** 用户滚轮/拖动/使用工具栏按钮
- **THEN** 依托 Viewer.js / PhotoSwipe 等标准库提供缩放、旋转、拖拽、键盘导航能力，并可关闭返回列表。


