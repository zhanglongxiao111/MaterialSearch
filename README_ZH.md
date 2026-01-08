# MaterialSearch

**AI 驱动的本地素材搜索引擎** | 用自然语言或图片搜索你的设计素材库

---

## ✨ 特性

- 🔍 **文字搜图/视频** - 用中文描述找到匹配素材
- 🖼️ **以图搜图/视频** - 上传图片找相似内容
- 📁 **多库管理** - 永久库 + 项目库分离存储
- 📄 **PDF 索引** - 自动渲染并索引 PDF 页面
- 🚀 **批量导入** - 拖拽文件夹快速建库
- 🖥️ **桌面客户端** - Tauri 跨平台应用

---

## 🎯 项目愿景

打造建筑设计事务所的 **AI 工作站**：

| 阶段 | 功能 | 状态 |
|-----|------|------|
| **Phase 1** | 素材搜索引擎 | ✅ 已完成 |
| **Phase 2** | RAG 知识库助手 | 🔜 规划中 |
| **Phase 3** | AI 图像生成集成 | 🔜 规划中 |
| **Phase 4** | Agent 工作流自动化 | 🔜 规划中 |

---

## 🚀 快速开始

### 本地运行

```bash
# 安装依赖
pip install -r requirements_windows.txt

# 配置素材路径（编辑 .env）
ASSETS_PATH=D:/你的素材目录

# 启动服务
python main.py
```

访问 http://localhost:58888

### Docker 部署

```bash
docker-compose up -d
```

---

## 🛠️ 技术栈

| 组件 | 技术 |
|-----|------|
| 后端 | Python + Flask + SQLAlchemy |
| AI 模型 | Chinese-CLIP (HuggingFace) |
| 向量搜索 | FAISS / pgvector |
| 前端 | Vue.js + Vanilla CSS |
| 桌面 | Tauri (Rust) |
| 部署 | Docker + Supabase (可选) |

---

## 📖 文档

- [项目文档](openspec/project.md)
- [变更日志](CHANGELOG_PROJECT.md)
- [开发指南](docs/MIGRATION_SPEC.md)

---

## 📄 许可证

基于 [MaterialSearch](https://github.com/chn-lee-yumi/MaterialSearch) 二次开发  
GNU GPLv3 License
