# Workspace 上传向导评审（2025-11-10）

## 结论
- ✅ **路径收集与历史回写**：Upload Step 0 复用了经典界面的 `materialPathHistory` 存储，支持批量粘贴、历史 chip 追加（`static/assets/workspace.js:470-520`，`static/index_workspace.html:360-420`）。
- ✅ **预览/筛选/批处理**：Step 1 依赖 `/api/preview_files` 结果，提供全选/反选、类型筛选、体积统计与复制路径操作；选中集会传递到 `/api/batch_index`（`workspace.js:521-640`，`index_workspace.html:404-450`）。
- ✅ **进度 & 冲突处理**：Step 2/3 读取 `/api/batch_index/<task>/status`，展示实时进度、失败/重复列表及 Viewer.js 重复对话框替代方案（`workspace.js:641-860`，`index_workspace.html:452-520`）。
- ⚠️ **验证尚未落地**：任务 7.1-7.3 仍需要在真实浏览器上完成冒烟、响应式截图与文案核对；目前仅完成代码侧实现与逻辑走查。

## 功能点覆盖
1. **历史路径共享**  
   - 与经典 UI 共用 `materialPathHistory` 键；按库（永久/项目）隔离，切换库时自动切换历史集合。  
   - 支持 chip 点击回填与清空、粘贴自动去引号。
2. **素材预览与选择**  
   - 当 `preview_upload` 成功后默认选中未索引素材，并保留筛选前的选中状态。  
   - 统计所选体积、提供复制路径、类型标签和“已索引/待入库”徽标。
3. **批量索引流程**  
   - 进度卡片显示 processed/total、预计剩余时间（秒级）。  
   - 可随时取消任务；取消后刷新库统计与项目计数。  
   - 重复文件弹窗支持“记住本次决策”并调用 `/api/batch_index/<task>/decision`。

## 建议/验证待办
1. **任务 7.1：交互冒烟**  
   - 手动验证：路径粘贴 → 预览 → 选择 → 发起索引 → 重复弹窗决策 → 任务完成。  
   - 记录关键截屏（Step 0~3、重复弹窗）并附于 PR/文档。
2. **任务 7.2：响应式视图**  
   - 在 1440px / 1024px / 768px 下抓取 Search + Upload 页的布局，确认 stepper、列表溢出与 selection-bar 显示。  
   - 结果附带到本评审或 `docs/frontend-ui-redesign.md`。
3. **任务 7.3：文本/Chip 对齐**  
   - 对照 `.superdesign/design_iterations/materialsearch_3.html`，确认 Stepper、按钮文案、色值一致；如有偏差需在 spec 中登记。

## 参考
- 前端：`static/index_workspace.html`、`static/assets/workspace.js`
- 后端：`routes.py` (`/api/preview_files`, `/api/batch_index*`)
- 设计稿：`.superdesign/design_iterations/materialsearch_3.html`
