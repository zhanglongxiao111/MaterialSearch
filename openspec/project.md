# 项目上下文

## 目的

MaterialSearch 是一个基于 AI 的本地素材搜索系统，允许用户通过自然语言或图片来搜索本地存储的图片和视频。

**核心功能：**
- 文本搜图：通过描述性文字搜索相关图片
- 以图搜图：通过上传图片找到相似图片
- 文本搜视频：根据描述找到匹配的视频片段
- 以图搜视频：通过截图找到对应的视频段落
- **多库管理**：永久库 + 项目库分离存储
- **批量索引**：支持上传导入和批量特征提取

**项目定位：**
这是从开源项目分叉的二次开发版本，原项目地址：https://github.com/chn-lee-yumi/MaterialSearch
本仓库专注于企业级多用户部署和建筑设计事务所工作流整合。

---

## 技术栈

### 后端架构
- **Python 3.9+**：主要开发语言
- **Flask 2.2.2+**：Web 框架 + Blueprint 模块化
- **SQLAlchemy 2.0.20+**：ORM 框架
- **App Factory 模式**：`app/__init__.py` 创建应用实例

### 数据存储（双模式）
| 模式 | 数据库 | 向量存储 | 适用场景 |
|-----|--------|---------|---------|
| **SQLite 模式** | SQLite | FAISS | 本地开发、单机部署 |
| **Supabase 模式** | PostgreSQL | pgvector | 多用户、服务器部署 |

### AI/机器学习
- **PyTorch 2.0+**：深度学习框架
- **Transformers 4.28.1+**：HuggingFace 模型库
- **CLIP 模型**：默认 `OFA-Sys/chinese-clip-vit-base-patch16`
- **FAISS**：向量相似度搜索（SQLite 模式）

### 前端
- **Vue.js 3** + **Axios**：响应式 UI
- **原生 HTML/CSS/JavaScript**：静态页面
- 位于 `static/` 目录

### 桌面客户端
- **Tauri**：跨平台桌面应用框架
- 位于 `desktop/` 目录

---

## 项目结构

```
MaterialSearch/
├── app/                      # 核心应用代码
│   ├── __init__.py          # App Factory
│   ├── api/                 # API Blueprint 模块
│   │   ├── __init__.py      # 路由注册与兼容层
│   │   ├── assets.py        # 素材处理 API
│   │   ├── projects.py      # 项目管理 API
│   │   ├── scan.py          # 扫描索引 API
│   │   └── search.py        # 搜索 API
│   ├── models/              # 数据模型
│   │   ├── __init__.py      # 模型导出
│   │   ├── image.py         # Image/ProjectImage
│   │   ├── video.py         # Video/VideoFrame
│   │   ├── pdf.py           # PDFPage/ProjectPDFPage
│   │   ├── project.py       # Project
│   │   ├── user.py          # User/UserProfile
│   │   └── audit.py         # AuditLog
│   ├── services/            # 业务逻辑层
│   │   ├── scan_service.py  # 扫描服务
│   │   ├── search_service.py# 搜索服务
│   │   ├── project_service.py# 项目管理
│   │   ├── asset_service.py # 素材处理
│   │   ├── archive_service.py# 归档服务
│   │   └── dedup_service.py # 去重服务
│   ├── integrations/        # 外部集成
│   │   ├── sqlite_manager.py# SQLite 数据库管理
│   │   └── supabase_client.py# Supabase 客户端
│   └── utils/               # 工具函数
│       ├── common.py        # 通用工具
│       └── image.py         # 图像处理
├── static/                  # 前端静态文件
├── desktop/                 # Tauri 桌面客户端
├── supabase/                # Supabase 配置
├── openspec/                # OpenSpec 变更管理
├── tests/                   # 测试文件
├── main.py                  # 应用入口
├── config.py                # 配置中心
└── models.py                # 兼容层（重导出）
```

---

## 架构模式

### 分层架构
```
┌─────────────────────────────────────┐
│         API Layer (Blueprint)       │  ← HTTP 请求处理
├─────────────────────────────────────┤
│         Service Layer               │  ← 业务逻辑
├─────────────────────────────────────┤
│      Integration Layer              │  ← 数据库/外部服务
├─────────────────────────────────────┤
│         Model Layer                 │  ← 数据模型
└─────────────────────────────────────┘
```

### Bridge 兼容模式
为保持向后兼容，根目录保留桥接文件：
- `models.py` → 重导出 `app.models`
- `config.py` → 配置中心（被所有模块引用）

### Library-Aware Model Branching
项目库与永久库使用不同的模型类：
- `Image` / `ProjectImage`
- `PDFPage` / `ProjectPDFPage`
- `Video` / `ProjectVideo`

---

## 项目约定

### 代码风格
- **PEP 8**：Python 代码规范
- **文件大小限制**：每文件 ≤300 行（AI 友好）
- **命名约定**：
  - 变量/函数：`snake_case`
  - 常量：`UPPER_CASE`
  - 类名：`PascalCase`

### Git 工作流
- **dev 分支**：主开发分支
- **OpenSpec**：使用 `/openspec-proposal` 管理变更
- **提交规范**：
  - `feat:` 新功能
  - `fix:` 修复
  - `chore:` 维护
  - `refactor:` 重构

### 测试策略
```bash
pytest tests/test_core_functions.py -v  # 核心功能测试
python main.py                          # 服务启动验证
```

---

## 外部依赖

### AI 模型
- **HuggingFace Hub**：模型下载
- 支持离线模式：`TRANSFORMERS_OFFLINE=1`

### 可选依赖
- **FFmpeg**：视频片段下载
- **Poppler**：PDF 渲染
- **CUDA**：GPU 加速

### 部署选项
| 方式 | 说明 |
|-----|------|
| 本地运行 | `python main.py` |
| Docker | `docker-compose up` |
| Tauri | 桌面应用 |

---

## 当前开发状态

### 已完成
- ✅ 模块化架构重构 (Blueprint + Services)
- ✅ 多库支持 (永久库 + 项目库)
- ✅ 批量索引 API
- ✅ Tauri 桌面客户端框架
- ✅ User/AuditLog 模型

### 进行中
- 🔄 Supabase 集成（需要云服务或 Docker）
- 🔄 缓存策略优化

### 待实施
- ⏳ 多用户认证 (Supabase Auth)
- ⏳ pgvector 向量存储
- ⏳ Row Level Security
