# 技术设计：集成库类型选择功能

## 架构概览

本变更在现有双数据库架构基础上，添加前后端集成层，使库类型选择贯穿扫描、搜索、上传全流程。

```
┌─────────────────────────────────────────────────────────┐
│                      前端 UI                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ 项目选择器    │  │ 扫描目标选择  │  │ 搜索范围选择  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
└─────────┼──────────────────┼──────────────────┼─────────┘
          │                  │                  │
┌─────────┼──────────────────┼──────────────────┼─────────┐
│         ▼                  ▼                  ▼         │
│    routes.py (Flask API)                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  /api/scan   │  │ /api/search  │  │ /api/upload  │  │
│  │ +target参数  │  │ +library_type│  │ +target参数  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
└─────────┼──────────────────┼──────────────────┼─────────┘
          │                  │                  │
┌─────────┼──────────────────┼──────────────────┼─────────┐
│         ▼                  ▼                  ▼         │
│   scan.py          search.py             process.py     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ scan_to_lib()│  │ search_lib() │  │ upload_to()  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
└─────────┼──────────────────┼──────────────────┼─────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌──────────────────────────────────────────────────────────┐
│            ProjectDatabaseManager                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ permanent.db │  │metadata.db   │  │  proj_*.db   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────────┘
```

## 核心设计决策

### 决策 1：扫描目标参数传递方式

**问题**：扫描操作如何知道应该存入哪个数据库？

**选项**：

| 方案 | 优点 | 缺点 | 选择 |
|-----|------|------|------|
| A. 全局配置 | 简单 | 无法动态切换，不支持多项目 | ❌ |
| B. API 参数传递 | 灵活，支持前端选择 | 需修改多个函数签名 | ✅ |
| C. 会话存储 | 前端无感 | 并发扫描冲突风险 | ❌ |

**选择**：**方案 B - API 参数传递**

**原因**：
1. 支持前端动态选择目标库
2. 无状态设计，避免并发问题
3. 明确的数据流向

**实现**：
```python
# routes.py
@app.route("/api/scan", methods=["GET"])
def api_scan():
    target = request.args.get('target', 'permanent')  # 默认永久库
    # target 格式：'permanent' 或 'proj_2025_xxx_01'
    scanner.scan(target=target)
```

### 决策 2：搜索库类型选择策略

**问题**：如何最小化对现有搜索逻辑的改动？

**选项**：

| 方案 | 复杂度 | 性能 | 兼容性 | 选择 |
|-----|--------|------|--------|------|
| A. 修改底层 session 获取逻辑 | 低 | 高 | 差 | ❌ |
| B. 在搜索函数增加参数 | 中 | 高 | 好 | ✅ |
| C. 包装器函数 | 高 | 中 | 好 | ❌ |

**选择**：**方案 B - 在搜索函数增加参数**

**实现**：
```python
def search_image_by_text_path_time(
    positive_prompt="",
    negative_prompt="",
    positive_threshold=POSITIVE_THRESHOLD,
    negative_threshold=NEGATIVE_THRESHOLD,
    filter_path="",
    start_time=None,
    end_time=None,
    library_type="permanent",      # 新增
    project_id=None                # 新增
):
    # 根据 library_type 获取对应 session
    if library_type == "permanent":
        session = get_db_manager().get_permanent_session()
    elif library_type == "project" and project_id:
        session = get_db_manager().get_project_session(project_id)
    else:
        # 向后兼容：默认永久库
        session = DatabaseSession()

    # 其余逻辑不变
    ...
```

### 决策 3：前端状态管理

**问题**：如何在前端持久化"当前活动项目"？

**选项**：

| 方案 | 持久性 | 复杂度 | 选择 |
|-----|--------|--------|------|
| A. Vue 组件状态 | 刷新丢失 | 低 | ❌ |
| B. LocalStorage | 跨会话保留 | 低 | ✅ |
| C. 服务器会话 | 持久 | 高 | ❌ |

**选择**：**方案 B - LocalStorage**

**实现**：
```javascript
// 保存当前项目
localStorage.setItem('currentProject', JSON.stringify({
    id: 'proj_2025_万科_01',
    name: '万科项目',
    type: 'project'  // 或 'permanent'
}));

// 读取当前项目
const current = JSON.parse(localStorage.getItem('currentProject') || '{"type":"permanent"}');
```

### 决策 4：向后兼容处理

**策略**：渐进增强，默认值保证现有行为

```python
# 所有新参数都有默认值
def scan(target='permanent'):  # 默认永久库
def search(..., library_type='permanent', project_id=None):  # 默认永久库
def upload(..., target='permanent'):  # 默认永久库
```

**测试用例**：
- ✅ 不传参数 → 使用永久库（现有行为）
- ✅ 传 `target='permanent'` → 永久库
- ✅ 传 `target='proj_xxx'` → 项目库

## 数据流

### 扫描流程

```
用户选择 → 前端发送 → API 接收 → Scanner 处理 → 存入目标库
   │         │          │           │            │
   │      /api/scan   routes.py   scan.py    database
   │      ?target=    extract      select      write to
   │      proj_xxx    parameter    session     proj_xxx.db
   ▼
┌────────────────────────────────────────────────────────┐
│ 1. 用户点击"扫描"                                       │
│ 2. 选择目标：[永久库] [新建项目] [现有项目 ▼]          │
│ 3. 若选"新建项目"：弹窗输入项目名、客户名              │
│ 4. 确认 → axios.get('/api/scan?target=proj_xxx')      │
│ 5. 后端扫描 → 图片存入 proj_xxx.db                     │
│ 6. 前端显示进度条，完成后刷新项目统计                  │
└────────────────────────────────────────────────────────┘
```

### 搜索流程

```
用户搜索 → 选择范围 → API 请求 → search.py → 返回结果
   │          │          │           │          │
   │      library_type routes.py   select    标注来源
   │      + project_id  parse      session    (permanent
   ▼                   params     get data    /project)
┌────────────────────────────────────────────────────────┐
│ 1. 用户输入搜索词："建筑外观"                           │
│ 2. 选择范围：[永久库] [当前项目] [所有库]              │
│ 3. 若选"当前项目" → project_id from localStorage       │
│ 4. axios.post('/api/search', {                        │
│      positive: "建筑外观",                             │
│      library_type: "project",                         │
│      project_id: "proj_2025_万科_01"                  │
│    })                                                  │
│ 5. 后端仅在 proj_2025_万科_01.db 中搜索               │
│ 6. 返回结果，标注 source: "万科项目"                   │
└────────────────────────────────────────────────────────┘
```

## API 变更

### 1. GET /api/scan

**新增查询参数**：
- `target` (可选, 默认 `'permanent'`): 扫描目标库
  - `'permanent'`: 永久库
  - `'proj_xxx'`: 指定项目库

**示例**：
```bash
# 扫描到永久库（默认）
GET /api/scan

# 扫描到指定项目
GET /api/scan?target=proj_2025_万科_01
```

### 2. POST /api/search (所有类型)

**新增请求体字段**：
```json
{
  "positive": "建筑外观",
  "negative": "",
  "library_type": "project",      // 新增：'permanent' | 'project' | 'all'
  "project_id": "proj_2025_万科_01"  // library_type='project' 时必填
}
```

**响应体变更**：
```json
{
  "results": [
    {
      "url": "api/get_image/123",
      "path": "/mnt/nas/project/image.jpg",
      "score": 92.5,
      "source": "万科项目"  // 新增：标注来源
    }
  ]
}
```

### 3. POST /api/upload

**新增表单字段**：
- `target` (可选, 默认 `'permanent'`): 上传目标库

**示例**：
```javascript
formData.append('file', file);
formData.append('target', 'proj_2025_万科_01');
```

## 数据库交互

### Session 选择逻辑

```python
# database.py 添加辅助函数
def get_session_by_target(target: str) -> Session:
    """
    根据目标获取数据库 session

    Args:
        target: 'permanent' 或 'proj_xxx'

    Returns:
        Session 对象
    """
    db_manager = get_db_manager()

    if target == 'permanent':
        return db_manager.get_permanent_session()
    elif target.startswith('proj_'):
        return db_manager.get_project_session(target)
    else:
        # 向后兼容：默认永久库
        return db_manager.get_permanent_session()
```

## 前端组件设计

### 1. 项目选择器组件

```vue
<template>
  <el-select v-model="currentLibrary" @change="handleLibraryChange">
    <el-option
      label="永久素材库"
      value="permanent"
      :icon="StarFilled">
    </el-option>
    <el-option-group label="项目库">
      <el-option
        v-for="proj in projects"
        :key="proj.id"
        :label="proj.name"
        :value="proj.id">
      </el-option>
    </el-option-group>
    <el-option
      label="+ 新建项目"
      value="__new__"
      :icon="Plus">
    </el-option>
  </el-select>
</template>

<script>
export default {
  data() {
    return {
      currentLibrary: 'permanent',
      projects: []
    }
  },
  methods: {
    async loadProjects() {
      const res = await axios.get('/api/projects?status=active');
      this.projects = res.data.projects;
    },
    handleLibraryChange(value) {
      if (value === '__new__') {
        this.showCreateProjectDialog();
      } else {
        localStorage.setItem('currentLibrary', value);
      }
    }
  },
  mounted() {
    this.loadProjects();
    this.currentLibrary = localStorage.getItem('currentLibrary') || 'permanent';
  }
}
</script>
```

### 2. 扫描目标选择

```vue
<el-button @click="showScanDialog">扫描</el-button>

<el-dialog v-model="scanDialogVisible" title="扫描设置">
  <el-form>
    <el-form-item label="扫描目标">
      <el-radio-group v-model="scanTarget">
        <el-radio label="permanent">永久素材库</el-radio>
        <el-radio :label="currentLibrary" v-if="currentLibrary !== 'permanent'">
          当前项目（{{ getCurrentProjectName() }}）
        </el-radio>
        <el-radio label="__new__">新建项目</el-radio>
      </el-radio-group>
    </el-form-item>

    <el-form-item v-if="scanTarget === '__new__'" label="项目名称">
      <el-input v-model="newProjectName" />
    </el-form-item>
  </el-form>

  <template #footer>
    <el-button @click="scanDialogVisible = false">取消</el-button>
    <el-button type="primary" @click="startScan">开始扫描</el-button>
  </template>
</el-dialog>
```

## 缓存策略

### 搜索缓存键生成

```python
# search.py
@lru_cache(maxsize=CACHE_SIZE)
def search_image_by_text_path_time(
    positive_prompt="",
    negative_prompt="",
    ...,
    library_type="permanent",
    project_id=None
):
    # 缓存键自动包含 library_type 和 project_id
    # 同一搜索词在不同库中有独立缓存
    ...
```

**缓存键示例**：
- `("建筑外观", "", ..., "permanent", None)` → 永久库结果
- `("建筑外观", "", ..., "project", "proj_xxx")` → 项目库结果

### 缓存失效时机

- 扫描完成 → `clean_cache()` 清空所有缓存
- 切换项目 → 不清缓存（不同 key）
- 归档操作 → 仅清空相关库的缓存

## 性能考虑

### 项目列表加载

**策略**：仅加载活动项目

```python
@app.route("/api/projects", methods=["GET"])
def api_projects():
    status = request.args.get('status', 'active')  # 默认仅活动项目
    projects = pm.list_projects(status=status, include_deleted=False)
    ...
```

**优势**：
- 减少前端下拉列表长度
- 降低数据传输量
- 提升响应速度

### 搜索性能

**无性能损失**：
- 项目库搜索：100 张图 → 比永久库**快 100 倍**
- 永久库搜索：与原实现**相同**
- 参数传递开销：可忽略（<1ms）

## 测试策略

### 单元测试

```python
# tests/test_scan_target.py
def test_scan_to_permanent():
    """测试扫描到永久库"""
    response = client.get('/api/scan?target=permanent')
    assert response.status_code == 200
    # 验证图片存入 permanent.db

def test_scan_to_project():
    """测试扫描到项目库"""
    response = client.get('/api/scan?target=proj_2025_test_01')
    # 验证图片存入 proj_2025_test_01.db
```

### 集成测试

```python
def test_search_in_project():
    """测试项目内搜索"""
    # 1. 创建项目
    # 2. 扫描图片到项目库
    # 3. 搜索并验证结果
    # 4. 验证不会搜到永久库的图片
```

### 前端测试

- [ ] 项目选择器：切换项目，localStorage 更新
- [ ] 扫描对话框：选择目标，API 参数正确
- [ ] 搜索：选择范围，结果标注正确

## 错误处理

### 项目不存在

```python
# routes.py
@app.route("/api/scan")
def api_scan():
    target = request.args.get('target', 'permanent')

    if target.startswith('proj_'):
        pm = get_project_manager()
        project = pm.get_project(target)
        if not project:
            return jsonify({"error": f"项目不存在: {target}"}), 404

    scanner.scan(target=target)
```

### 并发扫描冲突

**策略**：扫描互斥锁

```python
# scan.py
class Scanner:
    def scan(self, target='permanent'):
        if self.is_scanning:
            raise ValueError("扫描进行中，请稍后再试")

        self.is_scanning = True
        try:
            self._do_scan(target)
        finally:
            self.is_scanning = False
```

## 迁移路径

### 现有用户

**自动迁移**：
1. 现有数据库 → 作为永久库
2. 首次启动检测 `permanent.db` 不存在
3. 自动复制 `assets.db` → `permanent.db`

**手动迁移** （可选）：
```bash
# 将现有数据作为永久库
cp instance/assets.db instance/permanent.db

# 或迁移后删除旧库
python manage.py migrate --from assets.db --to permanent.db --delete-old
```

### 新用户

直接使用双库模式，无需迁移。

## 扩展性

### 支持更多库类型

当前架构支持未来扩展：
- 客户库：`client_xxx.db`
- 部门库：`dept_xxx.db`

只需修改：
1. 前端选择器选项
2. `get_session_by_target()` 添加分支
3. 数据库管理器添加对应方法

### 跨库搜索

```python
# 未来扩展
def search_all_libraries(...):
    results = []
    results += search_in_permanent(...)
    for project_id in active_projects:
        results += search_in_project(project_id, ...)
    return merge_and_rank(results)
```

## 依赖版本

无新增依赖，使用现有技术栈：
- Python 3.9+
- Flask 2.2.2+
- SQLAlchemy 2.0.20+
- Vue 3 + Element Plus（前端）
