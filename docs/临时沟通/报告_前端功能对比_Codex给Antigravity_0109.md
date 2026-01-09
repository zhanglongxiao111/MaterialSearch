# 审核报告：新旧前端功能对比

**审核 Agent**: OpenAI Codex  
**审核时间**: 2026-01-09 21:30  
**原任务文档**: docs/临时沟通/审核任务_前端功能对比_Codex.md

---

<!-- 请将 Codex 的审核结果粘贴到下方 -->

对比文件：
- `static/index_workspace.html`
- `static/index_workspace_v2.html`
- `static/assets/workspace.js`

## 1. 功能对比表

### A. 侧边栏功能
| 功能点 | 旧版 | 新版 | 备注 |
| --- | --- | --- | --- |
| 永久库/项目库切换 (`switchSidebar`) | 有 | 有 |  |
| 永久库分类选择 (`selectPermanentGroup`) | 有 | 有 |  |
| 项目选择 (`selectProject`) | 有 | 有 |  |
| 新建项目对话框 (`openProjectDialog`) | 有 | 有 |  |
| 系统状态显示 (`statusSummary`) | 无 | 有 | 新版新增显示 |

### B. 搜索功能
| 功能点 | 旧版 | 新版 | 备注 |
| --- | --- | --- | --- |
| 文字搜索 (`search`, `form.positive`) | 有 | 有 |  |
| 以图搜图 (`searchImage`, `triggerSearchImagePick`, `handleSearchImageChange`) | 有 | 有 |  |
| 搜索模式切换 (`selectSearchMode`, `searchModes`) | 有 | 有 |  |
| 高级筛选面板 (`advancedOpen`, `form.path`, `form.negative`) | 有 | 有 |  |
| 时间筛选 (`applyTimeFilter`, `clearTimeFilter`) | 有 | 有 |  |
| 包含重复选项 (`form.include_duplicates`) | 有 | 有 |  |

### C. 结果展示
| 功能点 | 旧版 | 新版 | 备注 |
| --- | --- | --- | --- |
| 瀑布流/网格切换 (`setViewMode`, `viewMode`) | 有 | 有 |  |
| 缩略图缩放 (`thumbnailScale`) | 有 | 有 |  |
| 图片点击打开详情 (`openDetail`) | 有 | 有 |  |
| 找相似 (`searchSimilar`) | 有 | 有 |  |
| 复制路径 (`copyPath`) | 有 | 有 |  |
| 复制全部路径 (`copyAllPaths`) | 有 | 有 |  |
| 批量选择 (`toggleSelection`, `isSelected`) | 有 | 有 |  |

### D. 批量操作
| 功能点 | 旧版 | 新版 | 备注 |
| --- | --- | --- | --- |
| 选择栏显示 (`selectionVisible`, `selectedCount`) | 有 | 有 |  |
| 归档选中 (`archiveSelected`) | 有 | 有 |  |
| 删除选中 (`deleteSelected`) | 有 | 有 |  |
| 清除选择 (`clearSelection`) | 有 | 有 |  |

### E. 上传流程
| 功能点 | 旧版 | 新版 | 备注 |
| --- | --- | --- | --- |
| 步骤 0: 路径输入 (`uploadPathInput`, `uploadHistory`) | 有 | 有 |  |
| 扫描预览 (`previewUploadFiles`) | 有 | 有 |  |
| 步骤 1: 文件列表 (`filteredUploadFiles`) | 有 | 有 |  |
| 步骤 1: 文件列表 (`uploadPreviewFiles`) | 无 | 无 | 未在模板中直接绑定（由 `filteredUploadFiles` 间接使用） |
| 文件类型过滤 (`setUploadFilter`, `uploadFilter`) | 有 | 有 |  |
| 全选/反选 (`selectAllUploadFiles`, `invertUploadSelection`) | 有 | 有 |  |
| 开始索引 (`startUploadIndex`) | 有 | 有 |  |
| 步骤 2: 进度显示 (`uploadProgress`, `uploadProgressMessage`) | 无 | 有 | 新版绑定，但 JS 未定义字段 |
| 取消任务 (`cancelUploadTask`) | 有 | 有 |  |
| 步骤 3: 完成报告 (`uploadResult`) | 无 | 有 | 新版绑定，但 JS 未定义字段 |
| 查看素材/继续导入 (`finishUploadWizard`, `resetUploadWizard`) | 部分 | 有 | 旧版仅 `finishUploadWizard` |

### F. 对话框
| 功能点 | 旧版 | 新版 | 备注 |
| --- | --- | --- | --- |
| 图片详情弹窗 (`detailDialog`, `detailImageSrc`, `detailMetadata`) | 有 | 有 |  |
| 项目创建对话框 (`projectDialog`) | 有 | 有 |  |
| 重复文件决策对话框 (`uploadDuplicateDialog`, `duplicateNewFile`) | 有 | 有 |  |
| 去重报告对话框 (`dedupReportDialog`) | 有 | 有 |  |

### G. 其他
| 功能点 | 旧版 | 新版 | 备注 |
| --- | --- | --- | --- |
| 主题切换 (`cycleTheme`) | 有 | 有 |  |
| Toast 通知 (`toast`) | 有 | 有 |  |
| 去重扫描 (`startDedupJob`, `openDedupReport`) | 有 | 有 |  |
| Lucide 图标初始化 | 有 | 有 | `lucide.min.js` + `window.lucide.createIcons()` |

## 2. 缺失清单（新版相对旧版）

1. 上传进度/结果绑定字段缺失
   新版模板使用 `uploadProgress`、`uploadProgressMessage`、`uploadResult`（`static/index_workspace_v2.html:591`, `static/index_workspace_v2.html:600`, `static/index_workspace_v2.html:616`），但 JS 仅定义 `uploadTaskProgress`/`uploadTaskInfo`/`uploadCurrentFile`（`static/assets/workspace.js:97`、`static/assets/workspace.js:105` 等），导致进度与结果显示失效。
2. 结果卡片单项归档/删除按钮缺失
   旧版在卡片操作区有 `archiveItems([item])` 与 `deleteItems([item])`（`static/index_workspace.html:1480`, `static/index_workspace.html:1482`），新版无对应按钮。
3. 详情弹窗缺少“打开原文件”按钮
   旧版在 PDF 详情中提供 `openOriginalFile`（`static/index_workspace.html:1847`），新版无。
4. 项目对话框缺少客户名称输入
   旧版存在 `projectDialog.form.client_name`（`static/index_workspace.html:1911`），新版无。
5. 上传进度明细面板缺失
   旧版提供 `uploadShowDetails` 切换及失败/重复/截断列表（`static/index_workspace.html:1686` 及后续明细区），新版无等价入口。

## 3. 风险评估

- 高：上传进度与完成报告显示失效会让用户无法确认任务状态与结果，误判任务失败/卡住。
- 中：缺少单项归档/删除按钮，日常清理只能依赖批量选择，操作成本上升。
- 中：缺少“打开原文件”按钮会影响 PDF 或原文件定位与检查流程。
- 低-中：项目客户名称字段缺失会造成项目元信息损失，影响后续筛选或统计。
- 低：缺少上传明细面板影响问题排查与失败回溯效率。

## 4. 修复建议（代码片段）

### 4.1 对齐上传进度/结果字段（推荐：在 JS 添加计算属性）
在 `static/assets/workspace.js` 的 `computed` 中增加：
```js
uploadProgress() {
    return this.uploadTaskProgress || 0;
},
uploadProgressMessage() {
    const info = this.uploadTaskInfo || {};
    const processed = info.processed || 0;
    const total = info.total || 0;
    const remain = info.remain_time;
    const remainText = remain ? ` · 剩余 ${remain} 秒` : '';
    const current = this.uploadCurrentFile || '';
    return `${current} (${processed}/${total})${remainText}`;
},
uploadResult() {
    const info = this.uploadTaskInfo || {};
    const failed = (info.failed || []).length;
    const skipped = (info.duplicates || []).length + (info.truncated || []).length;
    return {
        success: info.success || 0,
        failed,
        skipped
    };
}
```

### 4.2 恢复单项归档/删除按钮（`static/index_workspace_v2.html` 结果卡片操作区）
```html
<button @click.stop="archiveItems([item])"
    class="bg-white p-1 hover:bg-arch-accent hover:text-white">
    <i data-lucide="archive" class="w-3 h-3"></i>
</button>
<button @click.stop="deleteItems([item])"
    class="bg-white p-1 hover:bg-arch-accent hover:text-white">
    <i data-lucide="trash-2" class="w-3 h-3"></i>
</button>
```

### 4.3 详情弹窗补“打开原文件”（`static/index_workspace_v2.html` 详情按钮区）
```html
<button v-if="detailDialog.item && detailDialog.item.type === 'pdf'"
    @click="openOriginalFile(detailDialog.item.path)"
    class="w-full border border-gray-300 py-3 text-xs font-bold uppercase hover:border-black hover:bg-black hover:text-white transition-all">
    打开原文件
</button>
```

### 4.4 项目对话框补客户名称输入（`static/index_workspace_v2.html`）
```html
<label class="typo-label block mb-2">客户名称</label>
<input v-model="projectDialog.form.client_name"
    class="w-full bg-gray-50 border border-gray-300 p-3 text-sm focus:border-black focus:bg-white outline-none"
    placeholder="可选">
```

### 4.5 补上传明细入口（可选，恢复旧版问题排查能力）
```html
<button @click="uploadShowDetails = !uploadShowDetails"
    class="text-xs font-bold uppercase tracking-widest text-gray-400 hover:text-black">
    {{ uploadShowDetails ? '收起明细' : '查看明细' }}
</button>
<div v-if="uploadShowDetails" class="mt-4 w-full max-w-lg text-xs">
    <div v-if="(uploadTaskInfo.failed || []).length">失败：{{ (uploadTaskInfo.failed || []).length }}</div>
    <div v-if="(uploadTaskInfo.duplicates || []).length">重复：{{ (uploadTaskInfo.duplicates || []).length }}</div>
    <div v-if="(uploadTaskInfo.truncated || []).length">截断：{{ (uploadTaskInfo.truncated || []).length }}</div>
</div>
```
```
