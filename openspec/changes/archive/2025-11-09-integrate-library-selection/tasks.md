# 实施任务：集成库类型选择功能

## 概述

本任务清单用于实现双数据库架构的前后端集成，使扫描、搜索、上传功能支持库类型选择。

**估算时间**：6-9 小时
**依赖**：`add-project-database-architecture` 已实施
**并行机会**：后端（阶段 1-3）和前端（阶段 4-5）可部分并行开发

---

## 阶段 1：后端 - 扫描功能集成（1.5-2 小时）

### 1.1 修改扫描核心逻辑

- [ ] 1.1.1 在 `scan.py` 的 `Scanner.scan()` 方法添加 `target` 参数（默认 `'permanent'`）
- [ ] 1.1.2 实现 `_get_target_session(target: str)` 辅助方法
  - 调用 `database.get_session_by_target(target)`
  - 验证项目库是否存在
- [ ] 1.1.3 修改 `scan_dir()` 使用目标 session 而非全局 `DatabaseSession()`
- [ ] 1.1.4 扫描完成后更新目标库统计信息
  - 若 `target.startswith('proj_')`，调用 `pm.update_project_stats(target)`

### 1.2 修改扫描 API

- [ ] 1.2.1 在 `routes.py` 的 `/api/scan` 添加查询参数 `target`（默认 `'permanent'`）
- [ ] 1.2.2 添加项目存在性验证
  - 若 `target.startswith('proj_')`，调用 `pm.get_project(target)` 验证
  - 不存在返回 `404 Not Found`
- [ ] 1.2.3 将 `target` 参数传递给 `scanner.scan(target=target)`
- [ ] 1.2.4 添加并发扫描检查
  - 若 `scanner.is_scanning`，返回 `409 Conflict`

### 1.3 添加辅助函数

- [ ] 1.3.1 在 `database.py` 添加 `get_session_by_target(target: str) -> Session` 函数
  - `target == 'permanent'` → 返回永久库 session
  - `target.startswith('proj_')` → 返回项目 session
  - 其他 → 抛出 `ValueError("无效的目标库格式")`

---

## 阶段 2：后端 - 搜索功能集成（2-2.5 小时）

### 2.1 修改搜索核心函数

- [ ] 2.1.1 在 `search.py` 所有搜索函数添加参数：
  - `library_type: str = 'permanent'`
  - `project_id: Optional[str] = None`
  - 影响的函数：
    - `search_image_by_text_path_time()`
    - `search_image_by_image()`
    - `search_video_by_text_path_time()`
    - `search_video_by_image()`

- [ ] 2.1.2 修改 session 获取逻辑
  ```python
  if library_type == "permanent":
      session = get_db_manager().get_permanent_session()
  elif library_type == "project" and project_id:
      session = get_db_manager().get_project_session(project_id)
  elif library_type == "all":
      # 后续实现：搜索所有库
      raise NotImplementedError("全库搜索待实现")
  else:
      # 向后兼容
      session = DatabaseSession()
  ```

- [ ] 2.1.3 添加来源标注逻辑
  - 若 `library_type == "permanent"`，结果添加 `source: "永久库"`
  - 若 `library_type == "project"`，查询项目名称并添加 `source: "<项目名>"`

### 2.2 修改搜索 API

- [ ] 2.2.1 在 `routes.py` 的所有搜索接口添加请求体字段：
  - `library_type`（可选，默认 `'permanent'`）
  - `project_id`（可选）
  - 影响的端点：
    - `POST /api/search`（文本搜索）
    - `POST /api/search`（以图搜图）

- [ ] 2.2.2 添加参数验证
  - 若 `library_type == 'project'` 但缺少 `project_id`，返回 `400 Bad Request`
  - 若 `project_id` 不存在，返回 `404 Not Found`

- [ ] 2.2.3 将参数传递给搜索函数
  ```python
  results = search_image_by_text_path_time(
      ...,
      library_type=data.get('library_type', 'permanent'),
      project_id=data.get('project_id')
  )
  ```

### 2.3 缓存处理

- [ ] 2.3.1 验证 `@lru_cache` 自动包含新参数到缓存键
- [ ] 2.3.2 测试不同库的搜索结果独立缓存

---

## 阶段 3：后端 - 上传功能集成（1-1.5 小时）

### 3.1 修改上传逻辑

- [ ] 3.1.1 在 `routes.py` 的 `/api/upload` 添加表单字段 `target`（默认 `'permanent'`）
- [ ] 3.1.2 根据 `target` 选择目标 session
  - 复用 `database.get_session_by_target(target)`
- [ ] 3.1.3 添加项目存在性验证
- [ ] 3.1.4 上传完成后更新目标库统计（若为项目库）

### 3.2 路径策略（可选）

- [ ] 3.2.1 定义永久库上传路径：`/mnt/nas/permanent/<hash>.jpg`
- [ ] 3.2.2 定义项目库上传路径：`/mnt/nas/projects/<project_id>/<hash>.jpg`
- [ ] 3.2.3 或保持现有策略（用户指定路径，仅索引）

---

## 阶段 4：前端 - 项目选择器（1.5-2 小时）

### 4.1 创建项目选择器组件

- [ ] 4.1.1 在 `static/index.html` 或独立组件中创建 `<el-select>` 项目选择器
- [ ] 4.1.2 添加选项：
  - "永久素材库"（value: `'permanent'`）
  - 项目列表（从 `/api/projects?status=active` 获取）
  - "+ 新建项目"（value: `'__new__'`）

- [ ] 4.1.3 实现切换逻辑
  ```javascript
  handleLibraryChange(value) {
    if (value === '__new__') {
      this.showCreateProjectDialog();
    } else {
      this.currentLibrary = value;
      localStorage.setItem('currentLibrary', value);
      this.loadCurrentLibraryStats();
    }
  }
  ```

- [ ] 4.1.4 页面加载时从 `localStorage` 恢复选择

### 4.2 新建项目对话框

- [ ] 4.2.1 创建 `<el-dialog>` 包含表单：
  - 项目名称（必填）
  - 客户名称（可选）
  - 项目描述（可选）

- [ ] 4.2.2 实现创建逻辑
  ```javascript
  async createProject() {
    const res = await axios.post('/api/projects', {
      name: this.newProject.name,
      client_name: this.newProject.client,
      description: this.newProject.description
    });
    this.currentLibrary = res.data.id;
    this.loadProjects();
    this.createProjectDialogVisible = false;
  }
  ```

- [ ] 4.2.3 添加表单验证（项目名称非空）
- [ ] 4.2.4 错误处理（项目已存在等）

---

## 阶段 5：前端 - 扫描/搜索集成（1.5-2 小时）

### 5.1 扫描目标选择

- [ ] 5.1.1 创建扫描对话框 `<el-dialog>`
- [ ] 5.1.2 添加单选框：
  - 永久素材库
  - 当前项目（默认选中，若 `currentLibrary !== 'permanent'`）
  - 新建项目

- [ ] 5.1.3 "新建项目" 选中时展开项目名称输入框
- [ ] 5.1.4 修改扫描按钮点击事件
  ```javascript
  async startScan() {
    let target = this.scanTarget;
    if (target === '__new__') {
      // 先创建项目
      const res = await this.createProject();
      target = res.data.id;
    }
    await axios.get(`/api/scan?target=${target}`);
    this.scanDialogVisible = false;
  }
  ```

### 5.2 搜索范围选择

- [ ] 5.2.1 在高级搜索区域添加 "搜索范围" 单选框：
  - 永久库
  - 当前项目（默认）
  - 所有库

- [ ] 5.2.2 修改搜索请求
  ```javascript
  async search(searchType) {
    const data = {
      positive: this.form.positive,
      negative: this.form.negative,
      library_type: this.searchScope,  // 新增
      project_id: this.searchScope === 'project' ? this.currentLibrary : null
    };
    const res = await axios.post('/api/search', data);
    this.results = res.data.results;
  }
  ```

### 5.3 搜索结果来源显示

- [ ] 5.3.1 在结果图片卡片右上角添加标签显示 `source`
  ```html
  <el-tag type="info" size="small">{{ result.source }}</el-tag>
  ```

- [ ] 5.3.2 永久库标签使用蓝色，项目库使用绿色
- [ ] 5.3.3 点击项目标签可跳转到该项目（切换 `currentLibrary`）

---

## 阶段 6：前端 - 项目管理面板（可选，1-1.5 小时）

### 6.1 项目管理按钮和面板

- [ ] 6.1.1 在顶部添加 "项目管理" 按钮
- [ ] 6.1.2 创建项目管理抽屉/对话框
- [ ] 6.1.3 显示项目列表表格（`el-table`）：
  - 列：项目名称、客户、图片数、总大小、状态、操作

### 6.2 项目详情

- [ ] 6.2.1 点击项目名称打开详情对话框
- [ ] 6.2.2 显示项目完整信息和统计数据
- [ ] 6.2.3 提供 "编辑" 和 "删除" 按钮

### 6.3 项目删除

- [ ] 6.3.1 点击删除显示确认对话框
- [ ] 6.3.2 提供 "软删除" 和 "硬删除" 选项
- [ ] 6.3.3 调用 `DELETE /api/projects/<id>?hard_delete=true/false`
- [ ] 6.3.4 删除成功后刷新列表，若是当前项目则切回永久库

---

## 阶段 7：测试（1-1.5 小时）

### 7.1 后端单元测试

- [ ] 7.1.1 测试扫描到永久库
  ```python
  def test_scan_to_permanent():
      response = client.get('/api/scan?target=permanent')
      assert response.status_code == 200
      # 验证图片存入 permanent.db
  ```

- [ ] 7.1.2 测试扫描到项目库
  ```python
  def test_scan_to_project():
      # 先创建项目
      proj = client.post('/api/projects', json={'name': 'Test Project'})
      # 扫描到项目
      response = client.get(f'/api/scan?target={proj.json["id"]}')
      assert response.status_code == 200
      # 验证图片存入项目库
  ```

- [ ] 7.1.3 测试项目不存在错误
  ```python
  def test_scan_to_nonexistent_project():
      response = client.get('/api/scan?target=proj_2025_不存在_01')
      assert response.status_code == 404
  ```

- [ ] 7.1.4 测试搜索永久库
- [ ] 7.1.5 测试搜索项目库
- [ ] 7.1.6 测试缓存独立性

### 7.2 集成测试

- [ ] 7.2.1 端到端测试：创建项目 → 扫描 → 搜索 → 验证结果
  ```python
  def test_full_workflow():
      # 1. 创建项目
      proj = create_project("Test Project")
      # 2. 扫描到项目
      scan_to_project(proj.id)
      # 3. 搜索项目库
      results = search_in_project(proj.id, "test")
      # 4. 验证结果仅来自该项目
      assert all(r.source == "Test Project" for r in results)
  ```

- [ ] 7.2.2 测试并发上传到不同库（无冲突）
- [ ] 7.2.3 测试切换项目后搜索范围正确

### 7.3 前端手动测试

- [ ] 7.3.1 测试项目选择器切换和持久化
- [ ] 7.3.2 测试新建项目流程
- [ ] 7.3.3 测试扫描对话框和目标选择
- [ ] 7.3.4 测试搜索范围选择
- [ ] 7.3.5 测试搜索结果来源标签显示
- [ ] 7.3.6 测试项目管理面板（若实现）
- [ ] 7.3.7 测试向后兼容（不传参数时的默认行为）

---

## 阶段 8：文档和清理（0.5 小时）

### 8.1 更新文档

- [ ] 8.1.1 更新 `README.md` 添加库类型选择使用说明
- [ ] 8.1.2 更新 API 文档（`/api/scan`, `/api/search` 新参数）
- [ ] 8.1.3 添加前端使用截图（可选）

### 8.2 代码清理

- [ ] 8.2.1 移除调试 `console.log` 和注释掉的代码
- [ ] 8.2.2 确保代码符合项目规范（PEP 8, ESLint）
- [ ] 8.2.3 检查所有 TODO 标记已解决

---

## 验收标准

### 功能验收

- ✅ 扫描时可选择目标库，图片正确存入对应数据库
- ✅ 搜索时可指定范围，返回结果仅来自目标库
- ✅ 前端可创建项目、切换当前活动项目
- ✅ 项目内搜索响应时间 < 1 秒（100 张图）
- ✅ 永久库搜索响应时间 < 3 秒（1 万张图）
- ✅ 刷新页面后当前项目选择保持

### 向后兼容验收

- ✅ 不传 `target` 参数时默认使用永久库
- ✅ 不传 `library_type` 参数时默认搜索永久库
- ✅ 现有 API 调用无需修改仍可正常工作

### 性能验收

- ✅ 新增参数传递开销 < 1ms
- ✅ 项目列表加载时间 < 500ms（50 个项目）
- ✅ 搜索性能无回退

### 用户体验验收

- ✅ 界面操作符合直觉，无需查看文档
- ✅ 错误提示清晰（项目不存在、参数缺失等）
- ✅ 加载状态有明确反馈

---

## 依赖关系图

```
阶段 1 (扫描后端) ────┐
                     ├──> 阶段 7 (测试)
阶段 2 (搜索后端) ────┤
                     │
阶段 3 (上传后端) ────┘

阶段 4 (项目选择器) ──┐
                     ├──> 阶段 7 (测试)
阶段 5 (扫描搜索前端)─┤
                     │
阶段 6 (项目管理面板)─┘

阶段 7 (测试) ──> 阶段 8 (文档)
```

**并行机会**：阶段 1-3 和阶段 4-6 可并行开发（后端和前端独立）

---

## 风险缓解

| 风险 | 缓解措施 |
|-----|---------|
| 前端状态管理复杂 | 使用 localStorage 简化，Vue 响应式自动同步 |
| 搜索性能回退 | 保持向后兼容默认值，参数传递开销可忽略 |
| 缓存键冲突 | 测试验证 @lru_cache 自动包含新参数 |
| 并发扫描冲突 | 添加 `is_scanning` 互斥检查 |

---

## 可选增强（未来）

- [ ] 全库搜索功能（`library_type='all'`）并行查询优化
- [ ] 批量归档界面（当前通过 API 实现）
- [ ] 项目标签和颜色自定义
- [ ] 跨项目图片移动/复制
- [ ] 项目统计图表和可视化
