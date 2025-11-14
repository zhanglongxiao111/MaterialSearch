# frontend-library-ui 规范

## Purpose
待定 - 通过归档变更 integrate-library-selection 创建。归档后更新目的。
## Requirements
### Requirement: 项目选择器组件
系统 SHALL 提供全局项目选择器组件。

#### Scenario: 显示项目列表
- **GIVEN** 系统存在 3 个活动项目
- **WHEN** 用户打开项目选择器
- **THEN** 下拉列表显示：
  - "永久素材库"（默认选项）
  - 项目 1："万科广场项目"
  - 项目 2："华润中心项目"
  - 项目 3："恒大海上威尼斯"
  - "+ 新建项目"（底部）

#### Scenario: 切换到项目库
- **GIVEN** 当前选中 "永久素材库"
- **WHEN** 用户点击选择 "万科广场项目"
- **THEN** 当前库切换为 `proj_2025_万科广场项目_01`
- **AND** 保存到 `localStorage`
- **AND** 页面标题栏显示 "当前: 万科广场项目"
- **AND** 搜索/扫描默认使用该项目

#### Scenario: 切换到永久库
- **GIVEN** 当前选中某个项目
- **WHEN** 用户切换回 "永久素材库"
- **THEN** 当前库设为 `permanent`
- **AND** 页面标题显示 "当前: 永久素材库"

#### Scenario: 刷新后恢复选择
- **GIVEN** 用户上次选择了 "万科广场项目"
- **WHEN** 用户刷新页面或重新打开
- **THEN** 从 `localStorage` 读取上次选择
- **AND** 自动恢复到 "万科广场项目"

### Requirement: 新建项目对话框
系统 SHALL 提供新建项目对话框。

#### Scenario: 打开新建项目对话框
- **GIVEN** 用户点击 "+ 新建项目"
- **WHEN** 对话框打开
- **THEN** 显示表单字段：
  - 项目名称（必填）
  - 客户名称（可选）
  - 项目描述（可选）
- **AND** 显示 "取消" 和 "创建" 按钮

#### Scenario: 创建新项目成功
- **GIVEN** 用户输入项目名称 "绿地中心"
- **AND** 输入客户名称 "绿地集团"
- **WHEN** 用户点击 "创建"
- **THEN** 调用 `POST /api/projects`
- **AND** 创建成功后关闭对话框
- **AND** 自动切换到新项目
- **AND** 更新项目选择器列表
- **AND** 提示 "项目创建成功"

#### Scenario: 项目名称为空
- **GIVEN** 用户未输入项目名称
- **WHEN** 用户点击 "创建"
- **THEN** 显示验证错误 "项目名称不能为空"
- **AND** 对话框不关闭

#### Scenario: 项目已存在
- **GIVEN** 已存在项目 "万科广场项目"
- **WHEN** 用户尝试创建同名项目
- **THEN** API 返回 400 错误
- **AND** 显示错误提示 "项目已存在"

### Requirement: 扫描目标选择
系统 SHALL 在扫描操作中提供目标库选择。

#### Scenario: 点击扫描按钮显示选择
- **GIVEN** 用户点击 "扫描" 按钮
- **WHEN** 扫描对话框打开
- **THEN** 显示单选框：
  - [ ] 永久素材库
  - [x] 当前项目（默认选中，若有）
  - [ ] 新建项目
- **AND** 显示当前项目名称（如有）

#### Scenario: 选择"新建项目"触发创建
- **GIVEN** 用户选择 "新建项目"
- **WHEN** 在扫描对话框中
- **THEN** 下方展开项目名称输入框
- **AND** 输入框必填
- **WHEN** 用户点击 "开始扫描"
- **THEN** 先创建项目，再执行扫描

#### Scenario: 选择永久库扫描
- **GIVEN** 用户选择 "永久素材库"
- **WHEN** 点击 "开始扫描"
- **THEN** 调用 `GET /api/scan?target=permanent`
- **AND** 图片存入永久库

#### Scenario: 选择当前项目扫描
- **GIVEN** 当前项目为 `proj_2025_万科_01`
- **AND** 用户选择 "当前项目"
- **WHEN** 点击 "开始扫描"
- **THEN** 调用 `GET /api/scan?target=proj_2025_万科_01`
- **AND** 图片存入该项目库

### Requirement: 搜索范围选择
系统 SHALL 在搜索操作中提供库范围选择。

#### Scenario: 搜索时显示范围选项
- **GIVEN** 搜索表单
- **WHEN** 用户展开 "高级搜索"
- **THEN** 显示单选框 "搜索范围"：
  - [ ] 永久库
  - [x] 当前项目（默认，若有）
  - [ ] 所有库

#### Scenario: 搜索当前项目
- **GIVEN** 当前项目为 `proj_2025_万科_01`
- **AND** 用户选择 "当前项目"
- **WHEN** 用户搜索 "效果图"
- **THEN** 调用 API 传递：
  ```json
  {
    "positive": "效果图",
    "library_type": "project",
    "project_id": "proj_2025_万科_01"
  }
  ```
- **AND** 仅显示该项目的结果

#### Scenario: 搜索永久库
- **GIVEN** 用户选择 "永久库"
- **WHEN** 搜索 "建筑参考"
- **THEN** `library_type: "permanent"`
- **AND** 仅显示永久库结果

#### Scenario: 搜索所有库
- **GIVEN** 用户选择 "所有库"
- **WHEN** 搜索 "室内设计"
- **THEN** `library_type: "all"`
- **AND** 显示所有库的结果
- **AND** 每条结果显示来源标签

### Requirement: 搜索结果来源显示
系统 SHALL 在搜索结果中显示图片来源。

#### Scenario: 显示永久库来源标签
- **GIVEN** 搜索结果来自永久库
- **WHEN** 显示结果
- **THEN** 每张图片右上角显示标签 "永久库"
- **AND** 标签颜色为蓝色

#### Scenario: 显示项目库来源标签
- **GIVEN** 搜索结果来自 "万科广场项目"
- **WHEN** 显示结果
- **THEN** 每张图片右上角显示标签 "万科广场项目"
- **AND** 标签颜色为绿色
- **AND** 点击标签可跳转到该项目

#### Scenario: 跨库搜索显示混合来源
- **GIVEN** 搜索结果包含多个来源
- **WHEN** 显示结果列表
- **THEN** 不同来源显示不同颜色标签
- **AND** 可按来源筛选结果

### Requirement: 项目管理面板
系统 SHALL 提供项目管理面板。

#### Scenario: 打开项目管理面板
- **GIVEN** 用户点击 "项目管理" 按钮
- **WHEN** 面板打开
- **THEN** 显示项目列表表格：
  - 列：项目名称、客户、图片数、总大小、状态、操作
  - 每行一个项目

#### Scenario: 查看项目详情
- **GIVEN** 项目列表中有 "万科广场项目"
- **WHEN** 用户点击项目名称
- **THEN** 打开详情对话框
- **AND** 显示：
  - 项目信息（名称、客户、描述）
  - 统计数据（图片数、视频数、总大小）
  - 创建时间、更新时间
  - 数据库路径
- **AND** 提供 "编辑" 和 "删除" 按钮

#### Scenario: 删除项目
- **GIVEN** 用户点击项目的 "删除" 按钮
- **WHEN** 确认对话框出现
- **THEN** 显示警告 "删除后无法恢复，确认删除？"
- **AND** 提供选项 "软删除" 或 "硬删除"
- **WHEN** 用户确认
- **THEN** 调用 `DELETE /api/projects/<id>`
- **AND** 从列表移除该项目
- **AND** 若是当前项目，切换回永久库

#### Scenario: 项目状态筛选
- **GIVEN** 项目管理面板
- **WHEN** 用户选择状态筛选 "已完成"
- **THEN** 仅显示 `status='completed'` 的项目
- **AND** 可切换 "全部" / "活动" / "已完成" / "已删除"

### Requirement: 状态栏库信息显示
系统 SHALL 在状态栏显示当前库信息。

#### Scenario: 显示当前库名称
- **GIVEN** 当前选中 "万科广场项目"
- **WHEN** 页面加载完成
- **THEN** 状态栏显示标签 "当前库: 万科广场项目"
- **AND** 标签颜色为绿色（项目库）

#### Scenario: 永久库状态显示
- **GIVEN** 当前选中 "永久素材库"
- **WHEN** 页面加载完成
- **THEN** 状态栏显示 "当前库: 永久素材库"
- **AND** 标签颜色为蓝色

#### Scenario: 显示当前库统计
- **GIVEN** 当前项目为 `proj_2025_万科_01`
- **WHEN** 切换到该项目
- **THEN** 状态栏显示：
  - "当前库: 万科广场项目"
  - "图片: 120"
  - "总大小: 1.2 GB"

### Requirement: 响应式布局
系统 SHALL 确保库选择界面在不同屏幕尺寸下正常工作。

#### Scenario: 桌面端显示
- **GIVEN** 屏幕宽度 >= 1024px
- **WHEN** 显示界面
- **THEN** 项目选择器在顶部导航栏
- **AND** 项目管理面板为侧边栏

#### Scenario: 移动端适配
- **GIVEN** 屏幕宽度 < 768px
- **WHEN** 显示界面
- **THEN** 项目选择器为下拉列表
- **AND** 项目管理面板为全屏对话框

### Requirement: 添加素材对话框
系统 SHALL 在项目库模式下提供添加素材对话框。

#### Scenario: 切换到项目库显示添加入口
- **GIVEN** 用户切换到项目 "万科广场项目"
- **WHEN** 页面刷新完成
- **THEN** 顶部显示 "添加素材" 按钮
- **AND** 按钮位于 "项目管理" 按钮旁边

#### Scenario: 切换到永久库隐藏添加入口
- **GIVEN** 用户切换回 "永久素材库"
- **WHEN** 页面刷新
- **THEN** "添加素材" 按钮隐藏
- **AND** 保留原有扫描按钮

#### Scenario: 打开添加素材对话框
- **GIVEN** 当前项目为 "万科广场项目"
- **WHEN** 用户点击 "添加素材" 按钮
- **THEN** 打开对话框
- **AND** 标题显示 "为项目添加素材：万科广场项目"
- **AND** 显示路径输入区域

### Requirement: 路径输入和粘贴
系统 SHALL 支持复制粘贴文件/文件夹路径。

#### Scenario: 粘贴单个文件夹路径
- **GIVEN** 用户复制文件夹路径 `\\Daga-nas5\...\1102`
- **WHEN** 粘贴到输入框
- **THEN** 输入框显示该路径
- **AND** 显示 "预览文件" 按钮

#### Scenario: 粘贴多个路径（混合）
- **GIVEN** 用户复制多行路径：
  ```
  "\\Daga-nas5\...\1102\image.jpg"
  "\\Daga-nas5\...\1102\渲染图"
  ```
- **WHEN** 粘贴到输入框
- **THEN** 自动去除引号
- **AND** 识别为2个路径

#### Scenario: 历史路径快速选择
- **GIVEN** 用户之前使用过路径 `\\Daga-nas5\...\1101`
- **WHEN** 点击 "历史路径" 下拉菜单
- **THEN** 显示最近使用的10个路径
- **AND** 按项目分组显示
- **AND** 点击路径自动填充到输入框

### Requirement: 文件预览列表
系统 SHALL 显示待索引文件的预览列表。

#### Scenario: 点击预览文件
- **GIVEN** 用户输入路径 `\\Daga-nas5\...\1102`
- **WHEN** 点击 "预览文件" 按钮
- **THEN** 调用 `POST /api/preview_files`
- **AND** 显示加载动画 "正在扫描文件..."
- **AND** 扫描完成后显示文件列表

#### Scenario: 显示文件列表
- **GIVEN** 预览返回 28 个文件
- **WHEN** 列表显示
- **THEN** 每行显示：
  - 勾选框（默认勾选，已索引文件除外）
  - 文件类型图标（图片/视频/PDF）
  - 缩略图占位符
  - 文件名
  - 文件大小
- **AND** 底部显示 "已选择 25 个文件，总大小 320 MB"

#### Scenario: 缩略图懒加载
- **GIVEN** 文件列表有 50 个文件
- **WHEN** 对话框打开
- **THEN** 首屏（前20个）立即请求缩略图
- **AND** 显示加载中占位符
- **WHEN** 用户滚动列表
- **THEN** 可见区域的文件请求缩略图
- **AND** 缩略图加载后替换占位符

#### Scenario: 已索引文件标识
- **GIVEN** 文件 `image.jpg` 已在项目库中
- **WHEN** 显示在列表中
- **THEN** 勾选框默认取消
- **AND** 显示标签 "已索引"
- **AND** 文件名为灰色
- **AND** 用户可手动勾选（重新索引）

### Requirement: 文件筛选和操作
系统 SHALL 提供文件筛选功能。

#### Scenario: 全选/反选
- **GIVEN** 文件列表有 28 个文件
- **WHEN** 用户点击 "全选"
- **THEN** 所有文件（包括已索引）被勾选
- **WHEN** 用户点击 "反选"
- **THEN** 已勾选变未勾选，未勾选变勾选

#### Scenario: 按类型筛选
- **GIVEN** 文件列表包含图片、视频、PDF
- **WHEN** 用户点击 "仅图片"
- **THEN** 仅显示图片文件
- **AND** 其他类型文件隐藏
- **AND** 勾选状态保持

#### Scenario: 手动取消单个文件
- **GIVEN** 文件 `~$temp.docx` 在列表中
- **WHEN** 用户取消勾选
- **THEN** 该文件不被索引
- **AND** 底部统计更新："已选择 24 个文件"

#### Scenario: 批量删除未勾选项
- **GIVEN** 10 个文件未勾选
- **WHEN** 用户点击 "清理未勾选"
- **THEN** 从列表移除这10个文件
- **AND** 列表仅显示勾选的文件

### Requirement: 索引进度显示
系统 SHALL 显示实时索引进度。

#### Scenario: 开始索引
- **GIVEN** 用户勾选 25 个文件
- **WHEN** 点击 "开始索引" 按钮
- **THEN** 按钮变为 "索引中..." 不可点击
- **AND** 显示进度条（0%）
- **AND** 显示 "正在索引: 准备中..."

#### Scenario: 实时进度更新
- **GIVEN** 索引任务正在执行
- **WHEN** 每 500ms 轮询一次进度
- **THEN** 进度条更新
- **AND** 显示当前文件："正在索引: image_10.jpg (10/25)"
- **AND** 显示预计剩余时间："预计剩余: 23秒"

#### Scenario: 索引完成显示报告
- **GIVEN** 索引完成
- **WHEN** 所有文件处理完毕
- **THEN** 显示完成对话框：
  ```
  索引完成
  成功: 23个文件
  失败: 1个文件
  重复跳过: 1个文件

  [查看详情] [关闭]
  ```

#### Scenario: 查看详细报告
- **GIVEN** 索引完成对话框
- **WHEN** 用户点击 "查看详情"
- **THEN** 展开显示：
  - 失败文件列表（文件名 + 错误原因）
  - 重复文件列表（文件名 + 处理方式）
  - 总耗时

#### Scenario: 中途取消索引
- **GIVEN** 索引进行到 10/25
- **WHEN** 用户点击 "取消" 按钮
- **THEN** 显示确认对话框："已处理10个文件将保留，确认取消？"
- **WHEN** 用户确认
- **THEN** 停止索引
- **AND** 显示部分完成报告："已索引 10/25 个文件"

### Requirement: 重复文件处理对话框
系统 SHALL 在检测到重复文件时提供对比界面。

#### Scenario: 检测到重复文件
- **GIVEN** 索引到文件 `render_final.png`
- **AND** 数据库中存在相同 phash
- **WHEN** 索引暂停
- **THEN** 显示重复文件对话框
- **AND** 标题："发现重复文件"

#### Scenario: 显示对比预览
- **GIVEN** 重复文件对话框
- **WHEN** 对话框打开
- **THEN** 左右两栏显示：
  - 左侧：已有文件（缩略图、路径、大小、修改时间）
  - 右侧：新文件（缩略图、路径、大小、修改时间）
- **AND** 突出显示差异（如较新的文件标记"更新"）

#### Scenario: 用户选择跳过
- **GIVEN** 重复文件对话框
- **WHEN** 用户点击 "跳过"
- **THEN** 关闭对话框
- **AND** 不索引该文件
- **AND** 继续下一个文件

#### Scenario: 用户选择覆盖
- **GIVEN** 重复文件对话框
- **WHEN** 用户点击 "覆盖"
- **THEN** 删除旧记录
- **AND** 索引新文件
- **AND** 继续下一个文件

#### Scenario: 记住选择应用到后续
- **GIVEN** 重复文件对话框
- **WHEN** 用户勾选 "记住选择，应用到所有重复文件"
- **AND** 点击 "跳过"
- **THEN** 后续重复文件自动跳过
- **AND** 不再弹出对话框

#### Scenario: 批量操作按钮
- **GIVEN** 重复文件对话框
- **WHEN** 显示按钮
- **THEN** 提供四个按钮：
  - "跳过" - 跳过当前文件
  - "覆盖" - 覆盖当前文件
  - "全部跳过" - 跳过所有重复
  - "全部覆盖" - 覆盖所有重复

### Requirement: 历史路径管理
系统 SHALL 记录和管理历史使用的路径。

#### Scenario: 保存路径到历史
- **GIVEN** 用户成功索引路径 `\\Daga-nas5\...\1102`
- **WHEN** 索引完成
- **THEN** 保存到 `localStorage`
- **AND** 与项目ID关联
- **AND** 记录使用时间

#### Scenario: 显示项目路径历史
- **GIVEN** 当前项目 "万科广场项目"
- **WHEN** 打开历史路径下拉
- **THEN** 仅显示该项目的历史路径
- **AND** 按时间倒序排列
- **AND** 最多显示10条

#### Scenario: 清理历史路径
- **GIVEN** 历史路径下拉菜单
- **WHEN** 用户点击 "清空历史"
- **THEN** 确认对话框："确认清空所有历史路径？"
- **WHEN** 确认
- **THEN** 清空 `localStorage` 中该项目的路径记录

### Requirement: 响应式适配
系统 SHALL 确保添加素材对话框在不同设备上可用。

#### Scenario: 桌面端大屏显示
- **GIVEN** 屏幕宽度 >= 1024px
- **WHEN** 打开对话框
- **THEN** 对话框宽度 800px
- **AND** 文件列表高度 500px（可滚动）
- **AND** 左右分栏（路径输入 | 预览列表）

#### Scenario: 笔记本小屏适配
- **GIVEN** 屏幕宽度 1366px
- **WHEN** 打开对话框
- **THEN** 对话框宽度 80%
- **AND** 文件列表高度 60vh

#### Scenario: 移动端禁用
- **GIVEN** 屏幕宽度 < 768px
- **WHEN** 检测到移动设备
- **THEN** "添加素材" 按钮禁用
- **AND** 悬停提示："移动端不支持路径上传，请使用桌面浏览器"

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

### Requirement: 去重入口与报告展示
Workspace/Classic UI SHALL 提供手动去重入口，仅对永久库启用，并能展示最新报告。

#### Scenario: 入口仅在永久库启用
- **WHEN** 用户在 Workspace/Classic 中选择永久库
- **THEN** 顶栏或命令面板显示“去重扫描”按钮
- **AND** 切换到项目库时按钮禁用并提示“项目库允许重复”

#### Scenario: 确认与触发
- **WHEN** 用户点击“去重扫描”
- **THEN** 弹出确认框，说明扫描耗时/不会删除原文件
- **AND** 确认后调用 `POST /api/dedup/jobs`
- **AND** 期间在按钮旁显示运行状态（spinning / progress）

#### Scenario: 报告面板
- **WHEN** 任务结束或用户点击“查看去重报告”
- **THEN** 展示最近一次报告摘要：生成时间、扫描总数、重复组统计、可释放空间
- **AND** 若无报告则显示占位文案“尚未运行”

### Requirement: “包含重复”过滤控件
Workspace SHALL 在搜索面板提供仅对永久库有效的“包含重复”开关。

#### Scenario: 控件可见性
- **WHEN** 库类型=永久
- **THEN** 搜索面板显示 toggle，默认关闭
- **AND** 切换到项目库时隐藏或禁用该控件

#### Scenario: 参数联动
- **WHEN** 用户打开 toggle
- **THEN** 搜索请求附带 `include_duplicates=true`
- **AND** 关闭时移除该参数并刷新结果

#### Scenario: Classic UI
- **WHEN** 用户通过经典界面搜索永久库
- **THEN** 经典 UI 亦需提供相同的 toggle 或下拉选项，确保行为一致

