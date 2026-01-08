# -*- coding: utf-8 -*-
"""
MaterialSearch 桌面版后端入口

此文件作为 Tauri Sidecar 的入口点，与 main.py 功能相同，
但针对桌面环境进行了优化：
- 硬编码端口为 5000（Tauri 前端固定连接此端口）
- 绑定到 127.0.0.1（仅本地访问，安全性更高）
- 关闭 Flask debug 模式（避免重复启动）
- 添加健康检查端点支持

使用 PyInstaller 打包为 materialsearch-server.exe
"""

import os
import sys
import logging

# 确保当前目录在 Python 路径中（PyInstaller 打包后需要）
if getattr(sys, 'frozen', False):
    # 运行打包后的 exe
    application_path = os.path.dirname(sys.executable)
else:
    # 运行 Python 脚本
    application_path = os.path.dirname(os.path.abspath(__file__))
    # 桌面版入口在 desktop/ 目录，需要回到项目根目录
    application_path = os.path.dirname(application_path)

# 将项目根目录添加到 Python 路径
sys.path.insert(0, application_path)
os.chdir(application_path)

# 现在可以导入项目模块
import shutil
import threading

from app import create_app
from app.config import ASSETS_PATH, TEMP_PATH, AUTO_SCAN, LOG_LEVEL
from app.services.scan_service import scanner

# 桌面版固定配置
DESKTOP_PORT = 5000
DESKTOP_HOST = "127.0.0.1"

logger = logging.getLogger(__name__)


def init():
    """
    初始化桌面版后端
    - 清理和创建临时文件夹
    - 初始化扫描器和数据库
    - 根据 AUTO_SCAN 配置决定是否启动自动扫描
    """
    # 检查 ASSETS_PATH 是否存在
    for path in ASSETS_PATH:
        if not os.path.isdir(path):
            logger.warning(f"ASSETS_PATH检查：路径 {path} 不存在！请检查配置！")
    
    # 删除临时目录中所有文件
    shutil.rmtree(TEMP_PATH, ignore_errors=True)
    os.makedirs(f'{TEMP_PATH}/upload', exist_ok=True)
    os.makedirs(f'{TEMP_PATH}/video_clips', exist_ok=True)
    
    # 初始化扫描线程
    scanner.init()
    
    if AUTO_SCAN:
        auto_scan_thread = threading.Thread(target=scanner.auto_scan, daemon=True)
        auto_scan_thread.start()
        logger.info("自动扫描线程已启动")


def main():
    """
    启动桌面版后端服务
    """
    print(f"MaterialSearch 桌面版后端启动中...")
    print(f"工作目录: {os.getcwd()}")
    print(f"监听地址: http://{DESKTOP_HOST}:{DESKTOP_PORT}")
    
    # 初始化
    init()
    
    # 配置日志
    logging.getLogger('werkzeug').setLevel(LOG_LEVEL)
    
    # 启动 Flask 服务（关闭 debug 避免双重启动）
    # use_reloader=False 防止 PyInstaller 打包后出现问题
    app = create_app()
    app.run(
        port=DESKTOP_PORT,
        host=DESKTOP_HOST,
        debug=False,
        use_reloader=False,
        threaded=True
    )


if __name__ == "__main__":
    main()
