## ADDED Requirements

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
