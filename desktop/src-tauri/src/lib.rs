// MaterialSearch 桌面客户端 - Tauri 后端
// 功能：系统托盘、原生拖拽、后台运行

use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Manager, WindowEvent,
};
use std::path::PathBuf;
use std::fs;

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
/// 开发模式返回 5000，生产模式从配置读取
#[tauri::command]
fn get_backend_port() -> u16 {
    // TODO: 实现动态端口检测
    5000
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

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // 启动时清理过期缓存
    cleanup_old_cache_files();
    
    tauri::Builder::default()
        // 注册插件
        .plugin(tauri_plugin_opener::init())
        
        // 注册自定义命令
        .invoke_handler(tauri::generate_handler![
            prepare_file_for_drag,
            get_backend_port,
            is_tauri_environment,
            cleanup_cache
        ])
        
        // 设置系统托盘
        .setup(|app| {
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
                            // 清理缓存并退出
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
                    // 双击托盘图标显示窗口
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
