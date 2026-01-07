# Tasks: 添加 Tauri 桌面客户端

## 0. 前置准备
- [x] 0.1 安装 Rust 工具链（`rustup`）
- [x] 0.2 安装 Node.js 18+ 和 pnpm
- [x] 0.3 安装 Tauri CLI：`cargo install tauri-cli`
- [x] 0.4 验证开发环境：`cargo tauri info`

## 1. Tauri 项目初始化
- [x] 1.1 在项目根目录初始化 Tauri：`cargo tauri init`
  - 项目名称：`MaterialSearch`
  - 窗口标题：`MaterialSearch Workspace`
  - 前端路径：`../../static`
  - 前端 URL：`http://localhost:5000/workspace`（开发时）
- [x] 1.2 配置 `src-tauri/tauri.conf.json`
  - 设置窗口默认尺寸：1500x950
  - 启用系统托盘
  - 配置应用图标
- [x] 1.3 验证开发模式运行：`cargo tauri dev`
  - **验证结果**：窗口正常显示 MaterialSearch Workspace 界面 ✅

## 2. Sidecar 集成（Python 后端）
> ⚠️ Phase 2 核心功能 - 实现一键启动

- [x] 2.1 创建 `desktop/` 目录结构
  - `desktop/main_desktop.py` - 桌面版后端入口
  - `desktop/build_sidecar.ps1` - PyInstaller 打包脚本
- [x] 2.2 编写 `main_desktop.py`
  - 固定端口 5000，绑定 127.0.0.1
  - 禁用 Flask debug/reloader（PyInstaller 兼容）
- [x] 2.3 编写 PyInstaller 打包脚本 `build_sidecar.ps1`
  - 支持 --Clean, --OneFile, --Debug 参数
  - 输出到 `src-tauri/binaries/materialsearch-server-x86_64-pc-windows-msvc.exe`
- [x] 2.4 测试 Sidecar 独立运行
  - ✅ `python desktop/main_desktop.py` 测试成功
  - 确认后端运行在 http://127.0.0.1:5000
- [x] 2.5 配置 Tauri Sidecar
  - 更新 `tauri.conf.json` 添加 externalBin
  - 更新 `capabilities/default.json` 添加 shell 权限
  - 更新 `Cargo.toml` 添加 tauri-plugin-shell
  - 更新 `lib.rs` 添加 Sidecar 启动/停止/健康检查逻辑
- [x] 2.6 实现健康检查
  - ✅ `check_backend_health()` 函数已实现并验证
  - ✅ Tauri dev 模式测试通过，Sidecar 正确检测后端状态

## 3. 原生拖拽功能
- [x] 3.1 研究拖拽实现方案
  - 创建了 `prepare_file_for_drag` Tauri Command
  - 支持 UNC 网络路径复制到本地
- [x] 3.2 创建 Tauri Command：`prepare_file_for_drag`
  ```rust
  #[tauri::command]
  async fn prepare_file_for_drag(file_path: String) -> Result<String, String>
  ```
- [x] 3.3 处理网络路径（UNC 路径）
  - 检测 `\\server\...` 格式路径
  - 复制到 `%TEMP%\MaterialSearch\drag_cache\`
- [x] 3.4 创建前端拖拽集成脚本
  - 创建 `static/assets/tauri-integration.js`
  - 添加到 `index.html` 和 `index_workspace.html`
- [ ] 3.5 测试拖拽到不同应用
  - **待验证**：需要实际安装 tauri-plugin-drag
- [x] 3.6 实现临时文件清理
  - 应用启动时清理 24 小时前的缓存
  - 应用退出时清理当前缓存

## 4. 系统托盘
- [x] 4.1 配置托盘图标（使用默认 Tauri 图标）
- [x] 4.2 实现托盘菜单
  - "显示主窗口"
  - "退出"
- [x] 4.3 实现最小化到托盘
  - 点击关闭按钮时最小化而非退出
  - 托盘单击恢复窗口
- [x] 4.4 测试托盘功能
  - **验证结果**：功能正常 ✅

## 5. 前端适配
- [x] 5.1 检测运行环境（Tauri vs 浏览器）
  ```javascript
  const isTauri = window.__TAURI__ !== undefined;
  ```
- [x] 5.2 创建 Tauri 集成脚本
  - `static/assets/tauri-integration.js`
  - 导出 `window.MaterialSearchDesktop` 全局对象
- [x] 5.3 调整拖拽 UI
  - Tauri 环境：添加"拖拽到设计软件"提示
  - 浏览器环境：显示"使用桌面版可直接拖拽"提示
- [ ] 5.4 添加桌面版专属功能入口
  - 版本信息（待完成）

## 6. 打包与安装
- [x] 6.1 准备应用图标（使用默认 Tauri 图标）
- [x] 6.2 配置 Tauri 打包
  - `tauri.conf.json` 中设置产品名称、版本、作者
- [x] 6.3 构建 NSIS/MSI 安装包
  - NSIS: `MaterialSearch_1.0.0_x64-setup.exe` (2.4 MB)
  - MSI: `MaterialSearch_1.0.0_x64_en-US.msi` (3.5 MB)
- [x] 6.4 编写一键启动脚本 `desktop/start_desktop.ps1`
- [ ] 6.5 测试全新安装
  - **待验证**：需要在干净环境测试
- [ ] 6.6 测试卸载

## 7. 文档与交付
- [ ] 7.1 编写用户使用指南
- [ ] 7.2 编写开发者文档
- [ ] 7.3 更新 README.md

---

## 当前进度总结

### ✅ Phase 1 已完成 (2026-01-06)
- Tauri 项目框架搭建
- 系统托盘功能
- 基础拖拽代码
- 前端环境检测
- Release 构建 + 安装包

### ✅ Phase 2 已完成 (2026-01-06)
- Sidecar 集成代码 (`main_desktop.py`, `lib.rs`)
- 健康检查与自动启动逻辑
- Tauri dev 模式验证通过
- 配置文件更新（externalBin, capabilities, Cargo.toml）

### ⏳ Phase 3 待完成（可选，生产发布前）
- PyInstaller 打包 (`build_sidecar.ps1`)
- 完整拖拽功能（tauri-plugin-drag）
- 全新安装/卸载测试
- 文档

### 📦 交付物
- `desktop/main_desktop.py` - 桌面版后端入口
- `desktop/build_sidecar.ps1` - PyInstaller 打包脚本
- `desktop/src-tauri/src/lib.rs` - Sidecar 管理逻辑
- `desktop/start_desktop.ps1` - 一键启动脚本（开发模式）

---

## 依赖关系

```
0.x (前置准备) ✅
    ↓
1.x (Tauri 初始化) ✅
    ↓
    ├── 2.x (Sidecar 集成) ✅ ──→ 6.x (打包) ⏳
    │       ↓
    ├── 3.x (原生拖拽) ⏳ ─────→ 5.x (前端适配) ⏳
    │       ↓
    └── 4.x (系统托盘) ✅
            ↓
        7.x (文档) ⏳
```

**已完成**：0.x, 1.x, 2.x ✅, 3.x (部分), 4.x, 5.x (部分), 6.x (部分)
**待完成**：3.5, 5.4, 6.5-6.6, 7.x
