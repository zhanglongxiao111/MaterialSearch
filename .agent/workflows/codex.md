---
description: 后台调用 Codex CLI 执行任务（非阻塞）
---

# 调用 Codex Agent 执行任务

此 workflow 用于在后台启动 Codex CLI 执行审核、代码生成或其他任务，**不会阻塞当前对话**。

---

## Codex 特性

**Codex 极其细致和稳定**，适合以下任务：

| 适合任务 | 说明 |
|---------|------|
| ✅ 代码审核 | 细致检查每一处细节 |
| ✅ 大规模重构 | 长链路复杂任务，需要耐心和细心 |
| ✅ 跨文件分析 | 需要理解整体架构的任务 |
| ✅ 代码生成 | 需要一致性和完整性的生成任务 |

**不适合**：需要多轮快速交互的任务（用 Antigravity 更合适）

---

## 核心原则

1. **文档驱动**: 所有任务要求必须写入任务文档
2. **短提示词**: 命令行提示词只引用文档路径
3. **输出规范**: Codex 的回复必须输出到指定位置
4. **可见窗口**: 必须使用显式窗口，让用户观察
5. **⚠️ 避免过拟合**: 不要在任务文档中过度限制 Codex

---

## ⚠️ 避免过拟合

### 错误示范 ❌

```markdown
## 任务内容

请检查以下功能是否存在：
- [ ] switchSidebar
- [ ] selectProject
- [ ] openDetail
- [ ] ...（列出 50 个功能点）
```

**问题**: 如果 Antigravity 遗漏了某些功能，Codex 也不会检查！

### 正确示范 ✅

```markdown
## 任务内容

请全面对比两个前端文件的功能差异：
- 原版: static/index_workspace.html
- 新版: static/index_workspace_v2.html

自行分析所有 Vue 绑定、事件处理、UI 组件，找出新版缺失的功能。
不要局限于任何预设清单，请独立发现问题。
```

**原则**: 告诉 Codex **目标**，不要限制 Codex **方法**。让 Codex 自主分析！

---

## 文档规范

### 存放位置

```
docs/临时沟通/
├── 任务_[主题]_Codex.md           # 任务要求
├── 审核任务_[主题]_Codex.md       # 审核类任务
└── 审核报告_[主题]_Codex_[日期].md # 输出报告
```

### 任务文档模板（简洁版）

```markdown
# [任务标题]

**来源 Agent**: Gemini Antigravity  
**创建时间**: [YYYY-MM-DD HH:MM]  
**任务类型**: [审核/生成/重构]  

---

## 背景

[简要背景]

---

## 任务目标

[描述目标，不要限制方法]

---

## 相关文件

| 文件 | 路径 |
|------|------|
| ... | ... |

---

## 输出要求

请将报告保存至: `docs/临时沟通/[输出文件名].md`

---

**请开始执行。自主分析，不要局限于上述描述，发现任何问题都请报告。**
```

---

## 执行步骤

### 1. 确认任务并创建文档

创建**简洁**的任务文档，描述目标，不限制方法。

### 2. 检查旧进程

// turbo
```powershell
$existing = Get-Process -Name "codex" -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "⚠️ 发现 $($existing.Count) 个 Codex 进程:"
    $existing | Select-Object Id, StartTime | Format-Table
} else {
    Write-Host "✅ 无 Codex 进程，可启动"
}
```

### 3. 启动 Codex（正确格式！）

**⚠️ 重要**: 必须使用 `--%` 停止 PowerShell 解析，确保参数正确传递：

**⚠️ 已知问题**: `--full-auto` 和 `--sandbox workspace-write` 存在 bug，实际仍为 read-only。
必须使用 `--dangerously-bypass-approvals-and-sandbox` 才能让 Codex 写入文件。

// turbo
```powershell
Start-Process cmd -ArgumentList '/c', 'cd /d "d:\AI\materialsearch" && codex exec --dangerously-bypass-approvals-and-sandbox "请阅读 docs/临时沟通/[任务文档].md 并按要求执行" & echo. & echo 完成 & pause'
```

**参数说明**：
- `cd /d "[路径]"` - 先切换目录
- `--dangerously-bypass-approvals-and-sandbox` - 绕过 sandbox 限制（本地环境安全）
- `& pause` - 完成后暂停，用户可查看

### 4. 通知用户

```
✅ Codex 已在新窗口启动（有写入权限）
📄 任务: docs/临时沟通/[任务文档].md
📤 输出: docs/临时沟通/[输出文档].md
🖥️ 请观察弹出的 CMD 窗口
```

---

## 完整示例

### 审核任务（正确方式）

**任务文档** `docs/临时沟通/审核任务_前端功能对比_Codex.md`:

```markdown
# 审核任务：新旧前端功能对比

**来源 Agent**: Gemini Antigravity  
**创建时间**: 2026-01-09 21:40  

---

## 背景

我们创建了新前端 index_workspace_v2.html，需要确认功能完整性。

---

## 任务目标

全面对比以下两个文件，找出新版缺失的所有功能：
- 原版: static/index_workspace.html
- 新版: static/index_workspace_v2.html

自主分析所有 Vue 绑定、事件、组件，不要局限于任何预设清单。

---

## 输出要求

报告保存至: `docs/临时沟通/审核报告_前端功能对比_Codex_0109.md`

---

**请开始。发现任何问题都请报告。**
```

**启动命令**:

```powershell
Start-Process cmd -ArgumentList '/c', 'cd /d "d:\AI\materialsearch" && codex exec --dangerously-bypass-approvals-and-sandbox "请阅读 docs/临时沟通/审核任务_前端功能对比_Codex.md 并按要求执行" & pause'
```

---

## 注意事项

1. **不要过度限制 Codex** - 描述目标，不限制方法
2. **使用 --dangerously-bypass-approvals-and-sandbox** - 绕过 sandbox bug
3. **显式窗口** - 用户可观察
4. **启动前检查旧进程** - 防止重复
5. **让 Codex 自主分析** - 它比你更细致！

---

## 常用命令

```powershell
# 检查 Codex 状态
Get-Process -Name "codex" -ErrorAction SilentlyContinue

# 终止所有 Codex（需确认）
Stop-Process -Name "codex" -Force

# 查看最近输出
Get-ChildItem "docs/临时沟通" -Filter "*Codex*.md" | Sort-Object LastWriteTime -Desc | Select -First 5
```
