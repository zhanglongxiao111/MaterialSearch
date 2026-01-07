# Change: 添加 Tauri 桌面客户端

## Why

当前 MaterialSearch 是纯 Web 应用，存在以下限制：
1. **Web 权限限制**：无法将素材直接拖拽到 InDesign/Photoshop 等桌面软件
2. **依赖浏览器**：用户需要手动启动服务器并打开浏览器
3. **无法利用本地 GPU**：未来 C/S 架构中，客户端无法分担服务器算力压力
4. **扩展受限**：难以集成系统级功能（托盘图标、全局快捷键、文件关联等）

为建设 SA 建筑事务所的系统级 AI 工作平台，需要将 Web 应用封装为原生桌面客户端。

## What Changes

### Phase 1: 基础桌面客户端（本提案范围）
- 创建 Tauri 项目框架，内嵌现有前端
- 实现本地 Python 服务作为 Sidecar 进程
- **关键功能**：原生拖拽素材到外部应用（InDesign/PS/AI/Windows 资源管理器）
- 系统托盘图标与最小化支持
- 打包为 Windows 安装程序（.msi/.exe）

### 技术选型决策
- **Tauri**：相比 Electron 更轻量（~10MB vs ~150MB），内存占用更低
- **Sidecar 模式**：将 Python 后端打包为独立可执行文件，Tauri 前端通过 localhost 通信
- **渐进式迁移**：保留现有 Flask 后端架构，仅在客户端层封装

### 未来扩展（后续提案）
- C/S 架构：本地客户端连接公司服务器
- 本地 GPU 算力分担
- AI 生图、RAG 知识库、Agent PPT 等功能模块

## Impact

- **新增能力**：`desktop-client`
- **受影响代码**：
  - 新增 `src-tauri/` 目录（Tauri Rust 后端）
  - 新增 `desktop/` 目录（桌面客户端入口）
  - 修改 `static/` 前端代码（添加拖拽 API 调用）
  - 新增 `scripts/build_desktop.ps1`（打包脚本）
- **不影响**：
  - 现有 Flask 后端 API（完全兼容）
  - 现有 Web 界面（可继续浏览器访问）
