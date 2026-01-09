# 复审报告：前端修复确认（v2）

**复审 Agent**: OpenAI Codex  
**复审时间**: 2026-01-09 22:12

---

对比文件：
- `static/index_workspace.html`
- `static/index_workspace_v2.html`
- `static/assets/workspace.js`

## 1. 上次 5 项问题修复状态

| 项目 | 状态 | 证据 |
| --- | --- | --- |
| 1) 上传进度/结果字段缺失 | 已修复 | 新增计算属性：`static/assets/workspace.js:341`、`static/assets/workspace.js:344`、`static/assets/workspace.js:351` |
| 2) 结果卡片单项归档/删除按钮 | 已修复 | 结果卡片按钮已补：`static/index_workspace_v2.html:415`、`static/index_workspace_v2.html:418` |
| 3) 详情弹窗“打开原文件”按钮 | 已修复 | PDF 按钮已补：`static/index_workspace_v2.html:716`；方法存在：`static/assets/workspace.js:1064` |
| 4) 项目对话框客户名称字段 | 已修复 | 表单字段已补：`static/index_workspace_v2.html:741`；数据/提交已接入：`static/assets/workspace.js:132`、`static/assets/workspace.js:620` |
| 5) 上传进度明细面板 | **部分修复** | v2 有“查看明细”与异常计数：`static/index_workspace_v2.html:612`、`static/index_workspace_v2.html:616`；但旧版包含失败/重复/截断的**逐项列表**：`static/index_workspace.html:1693`、`static/index_workspace.html:1703`、`static/index_workspace.html:1713` |

## 2. 新发现问题/回归

1) **项目创建按钮不可用**（功能回归）
- v2 绑定了不存在的方法 `submitProjectDialog`：`static/index_workspace_v2.html:755`
- 实际方法是 `submitProject`：`static/assets/workspace.js:620`
- 结果：点击“创建/保存”不会触发提交（控制台会报未定义方法）。

2) **项目对话框模式字段未定义**（显示/逻辑异常）
- v2 模板使用 `projectDialog.mode` 控制标题/按钮文案：`static/index_workspace_v2.html:731`、`static/index_workspace_v2.html:755`
- JS 数据中未定义 `projectDialog.mode`：`static/assets/workspace.js:132`
- 结果：标题/按钮默认落到“编辑/保存”，且无编辑逻辑对齐旧版行为。

## 3. 仍缺失或被削弱的功能点（对比旧版）

1) **上传进度“剩余时间”显示缺失**
- 旧版显示 `remain_time`：`static/index_workspace.html:1683`
- v2 仅显示进度/当前文件，无剩余时间字段。

2) **上传完成后的异常明细列表缺失**
- 旧版在完成页展示失败/重复/截断的逐项列表：`static/index_workspace.html:1756`、`static/index_workspace.html:1766`、`static/index_workspace.html:1777`
- v2 完成页仅有成功/跳过/失败三项汇总：`static/index_workspace_v2.html:636`、`static/index_workspace_v2.html:640`、`static/index_workspace_v2.html:644`

---

如需我直接修复上述新问题（如将 `submitProjectDialog` 纠正为 `submitProject`、补 `projectDialog.mode`、恢复上传明细列表），请告知。
