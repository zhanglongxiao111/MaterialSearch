// MaterialSearch 桌面客户端 - Tauri 后端
// 功能：系统托盘、原生拖拽、后台运行、Sidecar 后端管理
//
// 架构说明：
// ┌─────────────────────────────────────────────────────┐
// │           MaterialSearch.exe (Tauri)                │
// │  ┌─────────────────────────────────────────────┐    │
// │  │         WebView (前端 HTML/CSS/JS)          │    │
// │  └─────────────────────────────────────────────┘    │
// │                      ↓ http://127.0.0.1:5000        │
// │  ┌─────────────────────────────────────────────┐    │
// │  │   materialsearch-server.exe (Sidecar)       │    │
// │  │   - Flask API 服务器                         │    │
// │  │   - CLIP 模型推理                            │    │
// │  └─────────────────────────────────────────────┘    │
// └─────────────────────────────────────────────────────┘

use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Manager, WindowEvent, AppHandle,
};
use tauri_plugin_shell::ShellExt;
use tauri_plugin_shell::process::CommandChild;
use std::path::PathBuf;
use std::fs;
use std::sync::Mutex;
use std::time::Duration;

/// 全局状态：保存 Sidecar 子进程引用
struct AppState {
    sidecar_child: Mutex<Option<CommandChild>>,
}

/// 后端服务端口（固定）
const BACKEND_PORT: u16 = 5000;

/// 获取临时文件目录
/// 用于存放从网络路径复制的文件，以便拖拽到其他应用
fn get_drag_cache_dir() -> PathBuf {
    let temp_dir = std::env::temp_dir();
    temp_dir.join("MaterialSearch").join("drag_cache")
}

/// 清理过期的临时文件（超过 24 小时）
fn cleanup_old_cache_files() {
    let cache_dir = get_drag_cache_dir();
    if !cache_dir.exists() {
        return;
    }
    
    if let Ok(entries) = fs::read_dir(&cache_dir) {
        let now = std::time::SystemTime::now();
        for entry in entries.flatten() {
            if let Ok(metadata) = entry.metadata() {
                if let Ok(modified) = metadata.modified() {
                    if let Ok(duration) = now.duration_since(modified) {
                        // 超过 24 小时的文件删除
                        if duration.as_secs() > 24 * 60 * 60 {
                            let _ = fs::remove_file(entry.path());
                        }
                    }
                }
            }
        }
    }
}

/// 准备文件用于拖拽
/// 如果是网络路径（UNC），则复制到本地临时目录
/// 返回可用于拖拽的本地路径
#[tauri::command]
async fn prepare_file_for_drag(file_path: String) -> Result<String, String> {
    let path = PathBuf::from(&file_path);
    
    // 检查文件是否存在
    if !path.exists() {
        return Err(format!("文件不存在: {}", file_path));
    }
    
    // 如果是本地路径（不是 UNC 路径），直接返回
    if !file_path.starts_with(r"\\") {
        return Ok(file_path);
    }
    
    // UNC 路径，需要复制到本地
    let cache_dir = get_drag_cache_dir();
    
    // 确保缓存目录存在
    if let Err(e) = fs::create_dir_all(&cache_dir) {
        return Err(format!("无法创建缓存目录: {}", e));
    }
    
    // 生成唯一文件名（时间戳 + 原文件名）
    let file_name = path.file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("unknown");
    let timestamp = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_millis())
        .unwrap_or(0);
    let cached_name = format!("{}_{}", timestamp, file_name);
    let cached_path = cache_dir.join(&cached_name);
    
    // 复制文件
    match fs::copy(&path, &cached_path) {
        Ok(_) => Ok(cached_path.to_string_lossy().to_string()),
        Err(e) => Err(format!("复制文件失败: {}", e)),
    }
}

/// 获取后端服务端口
#[tauri::command]
fn get_backend_port() -> u16 {
    BACKEND_PORT
}

/// 检查是否为 Tauri 环境
#[tauri::command]
fn is_tauri_environment() -> bool {
    true
}

/// 清理临时缓存
#[tauri::command]
fn cleanup_cache() -> Result<(), String> {
    let cache_dir = get_drag_cache_dir();
    if cache_dir.exists() {
        fs::remove_dir_all(&cache_dir)
            .map_err(|e| format!("清理缓存失败: {}", e))?;
    }
    Ok(())
}

/// 检查后端健康状态
#[tauri::command]
async fn check_backend_health() -> Result<bool, String> {
    let url = format!("http://127.0.0.1:{}/api/status", BACKEND_PORT);
    
    // 使用简单的 TCP 连接检查端口是否可用
    match std::net::TcpStream::connect_timeout(
        &format!("127.0.0.1:{}", BACKEND_PORT).parse().unwrap(),
        Duration::from_secs(1)
    ) {
        Ok(_) => Ok(true),
        Err(_) => Ok(false),
    }
}

/// 启动 Sidecar 后端（如果尚未运行）
async fn start_sidecar(app: &AppHandle) -> Result<(), String> {
    // 先检查后端是否已经在运行
    if check_backend_health().await.unwrap_or(false) {
        println!("[Sidecar] 后端服务已在运行（可能是开发模式）");
        return Ok(());
    }
    
    println!("[Sidecar] 正在启动 Python 后端...");
    
    // 启动 Sidecar
    let shell = app.shell();
    let sidecar_command = shell.sidecar("materialsearch-server")
        .map_err(|e| format!("无法创建 Sidecar 命令: {}", e))?;
    
    let (mut rx, child) = sidecar_command.spawn()
        .map_err(|e| format!("无法启动 Sidecar: {}", e))?;
    
    // 保存子进程引用
    if let Some(state) = app.try_state::<AppState>() {
        *state.sidecar_child.lock().unwrap() = Some(child);
    }
    
    // 在后台线程中读取输出
    tauri::async_runtime::spawn(async move {
        use tauri_plugin_shell::process::CommandEvent;
        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(line) => {
                    let line_str = String::from_utf8_lossy(&line);
                    println!("[Sidecar] {}", line_str);
                }
                CommandEvent::Stderr(line) => {
                    let line_str = String::from_utf8_lossy(&line);
                    eprintln!("[Sidecar ERROR] {}", line_str);
                }
                CommandEvent::Terminated(payload) => {
                    println!("[Sidecar] 进程已终止: {:?}", payload);
                    break;
                }
                _ => {}
            }
        }
    });
    
    // 等待后端就绪（最多等待 30 秒）
    println!("[Sidecar] 等待后端就绪...");
    for i in 0..60 {
        if check_backend_health().await.unwrap_or(false) {
            println!("[Sidecar] 后端已就绪（耗时 {} 秒）", (i + 1) / 2);
            return Ok(());
        }
        std::thread::sleep(Duration::from_millis(500));
    }
    
    Err("后端启动超时（30秒）".to_string())
}

/// 停止 Sidecar 后端
fn stop_sidecar(app: &AppHandle) {
    if let Some(state) = app.try_state::<AppState>() {
        if let Some(child) = state.sidecar_child.lock().unwrap().take() {
            println!("[Sidecar] 正在停止后端...");
            let _ = child.kill();
            println!("[Sidecar] 后端已停止");
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // 启动时清理过期缓存
    cleanup_old_cache_files();
    
    tauri::Builder::default()
        // 注册全局状态
        .manage(AppState {
            sidecar_child: Mutex::new(None),
        })
        
        // 注册插件
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        
        // 注册自定义命令
        .invoke_handler(tauri::generate_handler![
            prepare_file_for_drag,
            get_backend_port,
            is_tauri_environment,
            cleanup_cache,
            check_backend_health
        ])
        
        // 设置系统托盘和启动 Sidecar
        .setup(|app| {
            // 启动 Sidecar（异步）
            let app_handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                if let Err(e) = start_sidecar(&app_handle).await {
                    eprintln!("[Sidecar] 启动失败: {}", e);
                    // 这里可以显示错误对话框
                }
            });
            
            // 创建托盘菜单
            let show_item = MenuItem::with_id(app, "show", "显示主窗口", true, None::<&str>)?;
            let quit_item = MenuItem::with_id(app, "quit", "退出", true, None::<&str>)?;
            
            let menu = Menu::with_items(app, &[&show_item, &quit_item])?;
            
            // 创建托盘图标
            let _tray = TrayIconBuilder::new()
                .icon(app.default_window_icon().unwrap().clone())
                .menu(&menu)
                .tooltip("MaterialSearch 素材搜索")
                .on_menu_event(|app, event| {
                    match event.id.as_ref() {
                        "show" => {
                            // 显示主窗口
                            if let Some(window) = app.get_webview_window("main") {
                                let _ = window.show();
                                let _ = window.set_focus();
                            }
                        }
                        "quit" => {
                            // 停止 Sidecar
                            stop_sidecar(app);
                            
                            // 清理缓存
                            let cache_dir = get_drag_cache_dir();
                            if cache_dir.exists() {
                                let _ = fs::remove_dir_all(&cache_dir);
                            }
                            
                            app.exit(0);
                        }
                        _ => {}
                    }
                })
                .on_tray_icon_event(|tray, event| {
                    // 单击托盘图标显示窗口
                    if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = event
                    {
                        let app = tray.app_handle();
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                })
                .build(app)?;
            
            Ok(())
        })
        
        // 处理窗口关闭事件（最小化到托盘而非退出）
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { api, .. } = event {
                // 阻止默认关闭行为
                api.prevent_close();
                // 隐藏窗口
                let _ = window.hide();
            }
        })
        
        .run(tauri::generate_context!())
        .expect("启动 MaterialSearch 失败");
}
