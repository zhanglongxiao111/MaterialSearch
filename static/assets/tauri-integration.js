/**
 * MaterialSearch Tauri 桌面客户端集成
 * 
 * 此脚本提供桌面客户端专属功能：
 * - 原生文件拖拽到外部应用（InDesign、Photoshop 等）
 * - 环境检测
 * - 后端服务通信
 */

// 检测是否在 Tauri 环境中运行
const isTauri = window.__TAURI__ !== undefined;

// Tauri API 引用
let tauriInvoke = null;
if (isTauri) {
    // Tauri v2 API
    tauriInvoke = window.__TAURI__.core?.invoke || window.__TAURI__.invoke;
}

/**
 * 获取后端服务端口
 * 桌面客户端模式下从 Tauri 获取，浏览器模式下使用默认值
 */
async function getBackendPort() {
    if (isTauri && tauriInvoke) {
        try {
            return await tauriInvoke('get_backend_port');
        } catch (e) {
            console.warn('获取后端端口失败，使用默认值:', e);
            return 5000;
        }
    }
    return 5000;
}

/**
 * 获取 API 基础 URL
 */
async function getApiBaseUrl() {
    const port = await getBackendPort();
    return `http://localhost:${port}`;
}

/**
 * 准备文件用于拖拽
 * 如果是网络路径，会先复制到本地临时目录
 * 
 * @param {string} filePath - 文件路径
 * @returns {Promise<string>} - 可用于拖拽的本地路径
 */
async function prepareFileForDrag(filePath) {
    if (!isTauri || !tauriInvoke) {
        console.warn('非桌面客户端环境，无法准备拖拽文件');
        return null;
    }

    try {
        const localPath = await tauriInvoke('prepare_file_for_drag', { filePath });
        return localPath;
    } catch (e) {
        console.error('准备拖拽文件失败:', e);
        throw e;
    }
}

/**
 * 初始化拖拽功能
 * 为搜索结果卡片添加拖拽事件
 */
function initDragFeature() {
    if (!isTauri) {
        console.log('浏览器模式，跳过拖拽初始化');
        return;
    }

    console.log('桌面客户端模式，初始化原生拖拽功能');

    // 使用事件委托监听拖拽
    document.addEventListener('dragstart', async (e) => {
        const card = e.target.closest('.el-card');
        if (!card) return;

        // 查找卡片中的文件路径
        const pathElement = card.querySelector('.copy[data-clipboard-text]');
        if (!pathElement) return;

        const filePath = pathElement.getAttribute('data-clipboard-text');
        if (!filePath) return;

        console.log('开始拖拽文件:', filePath);

        // 阻止默认行为
        e.preventDefault();

        // 显示加载提示
        showDragLoading(true);

        try {
            // 准备文件（如果是网络路径，会复制到本地）
            const localPath = await prepareFileForDrag(filePath);

            if (localPath) {
                // 使用 Tauri 的原生拖拽 API
                // 注意：实际的拖拽操作需要通过 Tauri 插件实现
                console.log('文件准备完成:', localPath);

                // 设置拖拽数据
                e.dataTransfer.setData('text/plain', localPath);
                e.dataTransfer.effectAllowed = 'copy';
            }
        } catch (err) {
            console.error('拖拽准备失败:', err);
            showDragError(err.message || '拖拽准备失败');
        } finally {
            showDragLoading(false);
        }
    });
}

/**
 * 显示拖拽加载状态
 */
function showDragLoading(show) {
    let overlay = document.getElementById('drag-loading-overlay');

    if (show) {
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'drag-loading-overlay';
            overlay.innerHTML = `
                <div class="drag-loading-content">
                    <div class="drag-loading-spinner"></div>
                    <div class="drag-loading-text">正在准备文件...</div>
                </div>
            `;
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 9999;
            `;
            document.body.appendChild(overlay);
        }
        overlay.style.display = 'flex';
    } else if (overlay) {
        overlay.style.display = 'none';
    }
}

/**
 * 显示拖拽错误
 */
function showDragError(message) {
    // 使用 Element Plus 的消息提示
    if (window.ElementPlus?.ElMessage) {
        window.ElementPlus.ElMessage.error({
            message: message,
            duration: 3000
        });
    } else {
        alert('错误: ' + message);
    }
}

/**
 * 添加桌面版提示
 */
function addDesktopHint() {
    if (isTauri) {
        // 桌面模式：添加拖拽提示
        const style = document.createElement('style');
        style.textContent = `
            .el-card:hover::after {
                content: '拖拽到设计软件';
                position: absolute;
                bottom: 5px;
                right: 5px;
                background: rgba(64, 158, 255, 0.9);
                color: white;
                padding: 2px 8px;
                border-radius: 3px;
                font-size: 12px;
                pointer-events: none;
            }
            .el-card {
                position: relative;
                cursor: grab;
            }
            .el-card:active {
                cursor: grabbing;
            }
            
            /* 拖拽加载动画 */
            .drag-loading-content {
                text-align: center;
                color: white;
            }
            .drag-loading-spinner {
                width: 50px;
                height: 50px;
                border: 4px solid rgba(255, 255, 255, 0.3);
                border-top-color: white;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 15px;
            }
            .drag-loading-text {
                font-size: 16px;
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);

        // 设置卡片可拖拽
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) {
                        const cards = node.querySelectorAll ? node.querySelectorAll('.el-card') : [];
                        cards.forEach(card => {
                            card.setAttribute('draggable', 'true');
                        });
                        if (node.classList?.contains('el-card')) {
                            node.setAttribute('draggable', 'true');
                        }
                    }
                });
            });
        });
        observer.observe(document.body, { childList: true, subtree: true });

    } else {
        // 浏览器模式：显示下载桌面版提示
        const banner = document.createElement('div');
        banner.id = 'desktop-hint-banner';
        banner.innerHTML = `
            <span>💡 使用桌面版可直接拖拽素材到 InDesign、Photoshop 等设计软件</span>
            <button onclick="this.parentElement.style.display='none'" style="margin-left: 10px; cursor: pointer;">×</button>
        `;
        banner.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            z-index: 1000;
            font-size: 14px;
            max-width: 400px;
        `;

        // 检查是否已经关闭过
        if (!localStorage.getItem('desktopHintDismissed')) {
            setTimeout(() => {
                document.body.appendChild(banner);
            }, 3000);
        }
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    console.log('MaterialSearch 桌面集成初始化');
    console.log('运行环境:', isTauri ? 'Tauri 桌面客户端' : '浏览器');

    if (isTauri) {
        initDragFeature();
    }
    addDesktopHint();
});

// 导出给全局使用
window.MaterialSearchDesktop = {
    isTauri,
    getBackendPort,
    getApiBaseUrl,
    prepareFileForDrag
};
