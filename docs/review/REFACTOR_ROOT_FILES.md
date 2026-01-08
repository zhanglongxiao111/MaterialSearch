# 根目录核心文件重构任务

## 背景

当前项目采用了 Bridge 兼容层模式，根目录保留了一些"桥接"文件供旧代码引用。现在需要将所有引用指向 `app/` 下的模块，然后删除根目录的冗余文件。

## 需要重构的文件

| 根目录文件 | 真正实现位置 | 引用次数 |
|-----------|-------------|---------|
| `models.py` | `app/models/` | ~15处 |
| `config.py` | 无（需创建 `app/config.py`） | ~6处 |
| `env.py` | 无（需创建 `app/env.py`） | 1处 |

---

## 任务 1: 迁移 `models.py`

### 当前状态
根目录 `models.py` 是一个重导出文件：
```python
from app.models import *
from app.integrations.sqlite_manager import DatabaseSession
```

### 需要修改的文件
将所有 `from models import` 改为 `from app.models import`：

```
app/api/__init__.py (6处)
app/api/assets.py (1处)
app/services/scan_service.py (1处)
app/services/search_service.py (1处)
tests/test_core_functions.py (3处)
tools/migrate_to_supabase.py (3处)
```

### 注意
`DatabaseSession` 需要从 `app.integrations.sqlite_manager` 导入。

---

## 任务 2: 迁移 `config.py`

### 当前状态
`config.py` 是真正的配置文件，包含所有配置项定义。

### 步骤
1. 将 `config.py` 移动到 `app/config.py`
2. 将所有 `from config import` 改为 `from app.config import`

### 需要修改的文件
```
app/api/__init__.py
app/services/asset_service.py
app/services/scan_service.py
app/services/search_service.py
app/utils/common.py
app/integrations/sqlite_manager.py
benchmark.py (已删除，忽略)
```

---

## 任务 3: 迁移 `env.py`

### 当前状态
`env.py` 负责加载环境变量，被 `config.py` 引用。

### 步骤
1. 将 `env.py` 移动到 `app/env.py`
2. 修改 `app/config.py` 中的 `from env import *` 为 `from app.env import *`

---

## 执行顺序

1. **先迁移 env.py** → `app/env.py`
2. **再迁移 config.py** → `app/config.py`（同时更新 env 导入）
3. **最后清理 models.py 引用**
4. **删除根目录的旧文件**

---

## 验证

重构后运行测试确保无回归：
```bash
pytest tests/test_core_functions.py -v
python main.py  # 确保服务正常启动
```

---

## 预期结果

根目录将只保留：
- `main.py` - 主入口（可考虑改为调用 `app.main`）
- `manage.py` - 管理脚本
- 其他非 Python 文件（README、Dockerfile 等）
