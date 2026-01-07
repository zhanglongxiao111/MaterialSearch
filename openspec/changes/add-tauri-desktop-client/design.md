# Design: Tauri 桌面客户端架构

## Context

### 背景
MaterialSearch 是建筑设计事务所的 AI 素材搜索系统，用户主要在 Windows 环境下使用 InDesign、Photoshop、Illustrator 等设计软件。当前 Web 应用无法实现与这些软件的深度集成（如拖拽素材）。

### 约束
- **用户群体**：建筑设计师，非技术人员，需要极简安装体验
- **技术栈**：现有后端为 Python/Flask，前端为原生 HTML/CSS/JS
- **开发资源**：用户不熟悉 Rust，AI 助手负责 Rust 代码编写
- **未来规划**：C/S 架构、本地 GPU 算力分担、多功能 AI 平台

### 利益相关者
- **最终用户**：建筑设计师（需要拖拽功能、简单安装）
- **开发者**：龙潇（需要可维护的代码，详细注释）
- **运维**：IT 部门（需要简单部署方案）

## Goals / Non-Goals

### Goals
1. 实现原生拖拽功能，素材可直接拖入 InDesign/PS
2. 一键启动，无需手动启动服务器或打开浏览器
3. 安装包体积控制在 3GB 以内（含 Python 环境和模型）
4. 为未来 C/S 架构打好基础
5. Rust 代码详细注释，降低维护门槛

### Non-Goals
1. ❌ 本阶段不实现 C/S 架构（服务器部署）
2. ❌ 本阶段不实现本地 GPU 算力分担
3. ❌ 本阶段不新增 AI 功能（生图、RAG 等）
4. ❌ 不支持 macOS/Linux（仅 Windows）

## Decisions

### Decision 1: 使用 Tauri 而非 Electron

**选择**：Tauri v2

**理由**：
| 对比项 | Tauri | Electron |
|-------|-------|----------|
| 安装包增量 | ~10MB | ~150MB |
| 运行内存 | ~30MB | ~150MB |
| 原生拖拽 | ✅ Rust API | ✅ Node.js |
| 安全性 | ✅ 默认禁用危险 API | ⚠️ 需手动配置 |
| 与 Python 集成 | ✅ Sidecar | ✅ child_process |

**替代方案**：
- Electron：生态更成熟，但体积大、资源占用高
- PyWebView：纯 Python，但原生能力有限，拖拽支持不完整
- .NET MAUI：Windows 原生最佳，但需要完全重写前端

### Decision 2: Python 后端作为 Sidecar 进程

**选择**：使用 PyInstaller 打包 Python 后端为 `.exe`，Tauri 通过 Sidecar 机制启动和管理

**架构**：
```
┌─────────────────────────────────────────────────────┐
│           MaterialSearch.exe (Tauri)                │
│  ┌─────────────────────────────────────────────┐    │
│  │         WebView (前端 HTML/CSS/JS)          │    │
│  │         ↓ fetch() / WebSocket               │    │
│  └─────────────────────────────────────────────┘    │
│                      ↓ http://127.0.0.1:5000        │
│  ┌─────────────────────────────────────────────┐    │
│  │     materialsearch-server.exe (Sidecar)     │    │
│  │     - Flask API 服务器                       │    │
│  │     - CLIP 模型推理                          │    │
│  │     - SQLite 数据库                          │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

**理由**：
- 保持现有 Python 代码不变，迁移成本最低
- Sidecar 进程独立，崩溃不影响 Tauri 主进程
- 可复用 PyInstaller 打包流程

**替代方案**：
- 嵌入 Python 解释器：复杂度高，依赖管理困难
- 全部用 Rust 重写后端：开发周期过长

### Decision 3: 原生拖拽实现方案

**选择**：使用 Tauri 的 `startDrag` API + 临时文件

**流程**：
```
1. 用户在前端长按/拖动素材卡片
2. 前端调用 Tauri Command: start_drag(file_path)
3. Tauri 后端：
   a. 如果是网络路径 (\\server\...)，先复制到本地临时目录
   b. 调用 tauri-plugin-drag 启动系统级拖放
4. 用户将素材拖入 InDesign/PS
5. InDesign/PS 接收本地文件路径
```

**技术细节**：
- 使用 `tauri-plugin-drag` 或 Windows API `DoDragDrop`
- 临时文件存放在 `%TEMP%\MaterialSearch\drag_cache\`
- 定期清理（应用退出时或超过 24 小时）

### Decision 4: 安装包构建策略

**选择**：分层打包

```
MaterialSearch-Setup.exe (~2.5GB)
├── tauri-app.msi (~15MB)           # Tauri 主程序
├── python-runtime.zip (~800MB)     # PyInstaller 打包的后端
├── models/ (~300MB)                # CLIP 模型文件
└── poppler/ (~30MB)                # PDF 处理依赖
```

**安装流程**：
1. Inno Setup 解压所有文件到 `C:\Program Files\MaterialSearch\`
2. 创建开始菜单快捷方式
3. 注册 `materialsearch://` 协议（可选）
4. 首次启动检测模型，缺失则自动下载

## Risks / Trade-offs

### Risk 1: Python 打包体积过大
- **风险**：PyInstaller 打包包含 PyTorch、Transformers 等大型库，体积可能超过 2GB
- **缓解**：
  - 使用 `--exclude-module` 排除未使用的模块
  - 考虑 UPX 压缩（但可能影响启动速度）
  - 分离模型文件，按需下载

### Risk 2: 网络路径拖拽延迟
- **风险**：从 NAS 复制大文件到本地可能需要数秒
- **缓解**：
  - 显示复制进度条
  - 拖拽小于 10MB 的缩略图/预览图，完整文件异步复制
  - 缓存常用文件

### Risk 3: Rust 代码维护
- **风险**：用户不熟悉 Rust，未来维护困难
- **缓解**：
  - Rust 代码保持最小化（仅窗口管理、拖放、Sidecar 启动）
  - 所有复杂逻辑放在 Python 端
  - 详细的中文注释和文档

### Risk 4: 端口冲突
- **风险**：5000 端口可能被其他应用占用
- **缓解**：
  - 启动时检测端口，冲突时自动选择可用端口
  - 前端动态获取后端端口

## Migration Plan

### 阶段 1: 开发环境搭建
1. 安装 Rust、Node.js、Tauri CLI
2. 初始化 Tauri 项目
3. 验证基本窗口功能

### 阶段 2: 前端迁移
1. 将 `static/` 内容复制到 Tauri 前端目录
2. 修改 API 调用地址为动态端口
3. 添加 Tauri API 调用（拖拽等）

### 阶段 3: Sidecar 集成
1. 使用 PyInstaller 打包 Flask 后端
2. 配置 Tauri Sidecar
3. 实现启动/停止/健康检查

### 阶段 4: 原生功能实现
1. 实现原生拖拽
2. 系统托盘
3. 全局快捷键（可选）

### 阶段 5: 打包发布
1. 配置 Inno Setup 安装脚本
2. 测试安装/卸载流程
3. 发布给同事测试

### 回滚方案
- 所有功能保持 Web 可用
- 即使桌面客户端有问题，用户可继续使用浏览器访问 `http://localhost:5000`

## Open Questions

1. **模型文件分发策略**：是打包在安装包内（体积大但离线可用），还是首次启动时下载（体积小但需联网）？
   - **建议**：打包在安装包内，确保建筑事务所内网环境可用

2. **是否需要自动更新功能**？
   - **建议**：Phase 1 暂不实现，后续版本添加

3. **是否需要支持多账户/登录**？
   - **建议**：Phase 1 暂不实现，C/S 架构阶段再考虑
