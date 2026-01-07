# desktop-client 规范 Delta

## ADDED Requirements

### Requirement: Tauri 桌面窗口
系统 SHALL 提供基于 Tauri 的原生桌面窗口，内嵌现有 Web 前端。

#### Scenario: 启动桌面应用
- **WHEN** 用户双击桌面快捷方式 `MaterialSearch.exe`
- **THEN** 系统显示启动画面（splash screen）
- **AND** 后台启动 Python 服务（Sidecar 进程）
- **AND** 服务就绪后显示主窗口
- **AND** 主窗口加载 MaterialSearch 界面
- **AND** 窗口标题显示 "MaterialSearch 素材搜索"

#### Scenario: 窗口默认尺寸
- **GIVEN** 用户首次启动应用
- **WHEN** 主窗口显示
- **THEN** 窗口默认尺寸为 1400x900 像素
- **AND** 窗口居中显示
- **AND** 用户可自由调整窗口大小
- **AND** 窗口尺寸记忆并在下次启动时恢复

#### Scenario: 窗口最小化到托盘
- **GIVEN** 应用正在运行
- **WHEN** 用户点击窗口关闭按钮（X）
- **THEN** 窗口隐藏而非应用退出
- **AND** 系统托盘显示 MaterialSearch 图标
- **AND** 托盘图标 tooltip 显示 "MaterialSearch 正在运行"

---

### Requirement: 系统托盘功能
系统 SHALL 提供系统托盘图标和菜单。

#### Scenario: 托盘菜单显示
- **GIVEN** 应用最小化到托盘
- **WHEN** 用户右键点击托盘图标
- **THEN** 显示托盘菜单：
  - "显示主窗口"
  - "重启服务"
  - "---"（分隔线）
  - "退出"

#### Scenario: 从托盘恢复窗口
- **GIVEN** 应用已最小化到托盘
- **WHEN** 用户双击托盘图标
- **THEN** 主窗口恢复显示
- **AND** 窗口获得焦点

#### Scenario: 从托盘退出应用
- **GIVEN** 应用正在运行
- **WHEN** 用户点击托盘菜单 "退出"
- **THEN** 停止 Python 服务进程
- **AND** 清理临时文件
- **AND** 应用完全退出

---

### Requirement: Sidecar 进程管理
系统 SHALL 管理 Python 后端服务作为 Sidecar 进程。

#### Scenario: 自动启动后端服务
- **WHEN** 桌面应用启动
- **THEN** 自动启动 `materialsearch-server.exe`
- **AND** 检测可用端口（默认 5000，冲突时使用 5001-5010）
- **AND** 等待服务就绪（健康检查通过）
- **AND** 健康检查通过后显示主窗口

#### Scenario: 后端服务健康检查
- **GIVEN** 后端服务已启动
- **WHEN** 每 5 秒检查一次
- **THEN** 调用 `GET /api/status`
- **AND** 响应 200 表示服务正常
- **AND** 连续 3 次失败则显示错误提示

#### Scenario: 后端服务崩溃恢复
- **GIVEN** 后端服务意外退出
- **WHEN** 健康检查失败
- **THEN** 显示提示 "服务已断开，正在重启..."
- **AND** 自动重启 Sidecar 进程
- **AND** 最多重试 3 次
- **AND** 重试失败后显示错误对话框

#### Scenario: 端口冲突处理
- **GIVEN** 默认端口 5000 已被占用
- **WHEN** 后端服务启动
- **THEN** 依次尝试 5001、5002...5010
- **AND** 找到可用端口后启动服务
- **AND** 前端动态获取实际端口

---

### Requirement: 原生拖拽功能
系统 SHALL 支持将素材拖拽到外部应用程序。

#### Scenario: 拖拽本地文件到外部应用
- **GIVEN** 搜索结果显示本地素材（路径如 `D:\素材\image.jpg`）
- **WHEN** 用户拖动素材卡片到 InDesign/Photoshop 窗口
- **THEN** 系统启动原生拖放操作
- **AND** 目标应用接收文件路径
- **AND** 文件成功导入目标应用

#### Scenario: 拖拽网络路径文件
- **GIVEN** 搜索结果显示 NAS 素材（路径如 `\\Daga-nas5\共享\image.jpg`）
- **WHEN** 用户拖动素材卡片
- **THEN** 系统显示 "正在准备文件..."
- **AND** 将文件复制到本地临时目录
- **AND** 复制完成后启动原生拖放
- **AND** 目标应用接收本地临时文件路径

#### Scenario: 大文件拖拽提示
- **GIVEN** 素材文件大于 50MB
- **WHEN** 用户开始拖动
- **THEN** 显示提示 "大文件复制中，请稍候..."
- **AND** 显示复制进度条
- **AND** 复制完成后可继续拖放

#### Scenario: 拖拽到 Windows 资源管理器
- **GIVEN** 桌面或资源管理器窗口可见
- **WHEN** 用户将素材拖放到文件夹
- **THEN** 文件被复制到目标文件夹
- **AND** 保留原文件名

#### Scenario: 浏览器环境降级
- **GIVEN** 用户通过浏览器访问（非桌面客户端）
- **WHEN** 用户尝试拖拽素材
- **THEN** 浏览器执行默认拖拽行为（图片预览）
- **AND** 显示提示 "使用桌面版可直接拖入设计软件"

---

### Requirement: 临时文件管理
系统 SHALL 管理拖拽操作产生的临时文件。

#### Scenario: 临时文件存储位置
- **GIVEN** 需要缓存网络路径文件
- **WHEN** 复制文件
- **THEN** 存储到 `%TEMP%\MaterialSearch\drag_cache\`
- **AND** 使用时间戳+原文件名命名避免冲突

#### Scenario: 应用退出时清理
- **GIVEN** 临时目录存在缓存文件
- **WHEN** 应用正常退出
- **THEN** 删除所有临时缓存文件
- **AND** 删除空的临时目录

#### Scenario: 过期文件自动清理
- **GIVEN** 临时目录存在超过 24 小时的缓存文件
- **WHEN** 应用启动时
- **THEN** 自动清理过期文件
- **AND** 释放磁盘空间

---

### Requirement: 环境检测与兼容
系统 SHALL 在前端检测运行环境并适配功能。

#### Scenario: 检测 Tauri 环境
- **GIVEN** 前端代码加载
- **WHEN** 检测 `window.__TAURI__`
- **THEN** 如果存在，标记为桌面客户端模式
- **AND** 启用原生拖拽功能
- **AND** 隐藏 "下载桌面版" 提示

#### Scenario: 检测浏览器环境
- **GIVEN** 前端代码加载
- **WHEN** `window.__TAURI__` 不存在
- **THEN** 标记为浏览器模式
- **AND** 使用标准 Web API
- **AND** 显示 "使用桌面版获得更多功能" 提示

#### Scenario: 动态后端端口
- **GIVEN** 桌面客户端模式
- **WHEN** 前端初始化
- **THEN** 从 Tauri 获取实际后端端口
- **AND** API 请求使用动态端口
- **AND** 非桌面模式使用默认端口 5000

---

### Requirement: 安装与卸载
系统 SHALL 提供 Windows 安装程序。

#### Scenario: 安装应用
- **GIVEN** 用户下载 `MaterialSearch-Setup.exe`
- **WHEN** 运行安装程序
- **THEN** 显示安装向导
- **AND** 默认安装到 `C:\Program Files\MaterialSearch`
- **AND** 创建开始菜单快捷方式
- **AND** 可选创建桌面快捷方式
- **AND** 安装完成后可选立即启动

#### Scenario: 安装内容
- **GIVEN** 安装完成
- **WHEN** 查看安装目录
- **THEN** 包含以下内容：
  - `MaterialSearch.exe`（Tauri 主程序）
  - `materialsearch-server.exe`（Python 后端）
  - `models/`（CLIP 模型文件）
  - `static/`（前端资源）
  - `poppler/`（PDF 处理工具）

#### Scenario: 卸载应用
- **GIVEN** 应用已安装
- **WHEN** 用户通过控制面板卸载
- **THEN** 删除安装目录所有文件
- **AND** 删除开始菜单快捷方式
- **AND** 删除桌面快捷方式（如有）
- **AND** 可选保留用户数据（数据库、配置）
