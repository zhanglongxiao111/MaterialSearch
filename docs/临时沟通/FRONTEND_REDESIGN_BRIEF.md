# 前端重构需求 - 瑞士国际主义风格

> ⚠️ **核心要求**：必须基于现有 `index_workspace.html` 修改，保留所有现有功能！
> 不要创建新的静态页面！

---

## 现有前端文件（必须基于这些修改）

| 文件 | 说明 |
|-----|------|
| `static/index_workspace.html` | **主文件** - 包含完整 Vue 模板和内联 CSS |
| `static/assets/workspace.js` | **Vue 逻辑** - 所有功能实现，不要修改 |
| `static/assets/materialsearch_theme_2.css` | 原主题 CSS 变量 |

**设计参考**：`.superdesign/design_iterations/superdesign_master_v2.html`

---

## ❌ 错误做法（上次的问题）

- 创建独立静态页面 `index_workspace_swiss.html` - 没有连接后端
- 删除原文件 - 破坏了功能
- 使用硬编码数据 - 失去动态功能

## ✅ 正确做法

1. **直接修改** `static/index_workspace.html`
2. **保留所有 Vue 绑定**（`v-model`, `v-for`, `@click` 等）
3. **保留 `workspace.js` 引用**，不修改 JS 逻辑
4. 只修改 **HTML 结构** 和 **CSS 样式**

---

## 品牌要求

- **Logo**: SA ARCHITECTS
- **副标题**: ASSET MANAGEMENT SYS.

## 配色方案

| 用途 | 颜色 |
|-----|------|
| 侧边栏背景 | #111111 |
| 主内容背景 | #F4F4F4 |
| 强调色 | #FF3300 |

## 布局要求

```
┌──────────────────────────────────────────────┐
│ [深色侧边栏 320px] │ [浅色主内容区]           │
│ 从顶到底完整显示   │ 网格背景纹理             │
└──────────────────────────────────────────────┘
```

**关键**：侧边栏必须从页面**最顶部**延伸到**最底部**！

## 必须保留的功能

- ✅ 搜索（文字搜图、以图搜图）
- ✅ 瀑布流/网格切换
- ✅ 永久库/项目库切换
- ✅ 上传索引流程
- ✅ 所有 Vue 响应式绑定

## 字体

```css
font-family: 'Inter', 'PingFang SC', sans-serif;
```

## 无圆角

```css
border-radius: 0 !important;
```

---

## 验收标准

1. ✅ 所有原有功能正常工作（点击按钮有响应）
2. ✅ 侧边栏深色、从顶到底
3. ✅ 无紫色/蓝色残留
4. ✅ 修改的是 `index_workspace.html`，不是新文件
