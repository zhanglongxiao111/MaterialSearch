# 库范围/Workspace 界面联动评审（2025-11-10）

> 评审目标：确认“永久库 / 项目库”强隔离策略落实、路由安全、UI 交互与 Viewer 行为是否符合最新 OpenSpec。

## 结论
- ✅ **范围隔离已实现**：`routes.py` 与 `search.py` 在 `/api/match`、以图搜图、视频检索等路径均拒绝 `library_type=all`，项目模式强制 `project_id`（routes.py:133-189，search.py:149-215）。前端 `static/index_workspace.html`、`static/index_classic.html` 也只暴露永久/项目两个入口。
- ✅ **项目操作回到项目库**：新建 API `POST /api/projects/<project_id>/images/delete` 与归档接口一起，仅标记数据库，不动源文件（routes.py:553-582，project_manager.py:394-458）。Workspace 批量栏仅在项目模式启用，相同项目 ID 才能共批（static/assets/workspace.js:520-640）。
- ✅ **Viewer/放大遵循设计稿**：Workspace 细节抽屉使用 `viewer.js` 提供缩放、旋转、镜像，展示 path/source/score/size/captured_at 等字段，匹配 `.superdesign/design_iterations/materialsearch_3.html`（static/index_workspace.html:300-360，static/assets/workspace.js:560-620）。
- ⚠️ **Upload/Stats 仍为占位**：`tasks.md` 第 6.3、7.x 未完成——上传面板仍跳转经典 UI，响应式与视觉回归尚未验证。需要迁移 `tmp_add_dialog.html` / `tmp_upload_dialog.html` 的真实流程，补完验证记录。

## 漏洞/风险
1. **上传/历史路径迁移未开始**  
   - 文件：`static/index_workspace.html:270-310`；`openspec/changes/update-workspace-ui/tasks.md`（任务 6.3、7.x）。  
   - 影响：Workspace Tab 暂不支持真实上传，spec 要求“复制原始上传对话框”尚缺实现。需要在 Workspace 中嵌入/移植经典上传逻辑或与后端 API 打通。

2. **响应式/主题验证缺数据**  
   - 文件：`openspec/changes/update-workspace-ui/tasks.md` 任务 7.1-7.3。  
   - 影响：缺少 1440/1024/768 视口截图和主题切换验证记录，可能与设计稿出现偏差。需补充测试计划及截图或自动化校验。

## 建议
- 先完成 `tasks.md` 6.3 与 7.x，再在本档案追加验证要点与截图链接。
- Upload Tab 推荐将经典对话框拆成组件，直接内嵌（避免 context switch）。同时在 spec 中记录任何偏离设计稿的取舍。
- 后续若引入永久库删除能力，需在 spec 中补充“只删除数据库记录、不删除源文件”的共性条款，确保 API 行为一致。

## 附录
- 设计稿：`.superdesign/design_iterations/materialsearch_3.html`
- OpenSpec 变更：`openspec/changes/update-workspace-ui/specs/frontend-library-ui/spec.md`
- 关联 API：`routes.py`（`/api/match`, `/api/projects/*/archive`, `/api/projects/*/images/delete`）
- 前端逻辑：`static/assets/workspace.js`，`static/index_workspace.html`
