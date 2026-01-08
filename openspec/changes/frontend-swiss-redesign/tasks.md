# Tasks: Workspace 前端瑞士风格重构

## Phase 1: CSS 主题系统 (基础)

- [x] 1.1 创建新主题文件 `materialsearch_theme_swiss.css`
- [x] 1.2 定义 CSS 变量：配色方案（黑白灰+橙）
- [x] 1.3 定义 CSS 变量：字体（Inter + JetBrains Mono）
- [x] 1.4 全局重置圆角 (`border-radius: 0`)
- [x] 1.5 定义滚动条样式（4px 极简风格）

## Phase 2: 布局重构

- [x] 2.1 侧边栏宽度调整为 320px
- [x] 2.2 添加建筑网格背景纹理
- [x] 2.3 实现响应式侧边栏（窄屏滑动隐藏/显示）
- [ ] 2.4 添加汉堡菜单按钮（移动端）- 待测试

## Phase 3: 品牌标识

- [x] 3.1 修改左上角 Logo 为 "SA ARCHITECTS"
- [x] 3.2 添加副标题 "ASSET MANAGEMENT SYS."
- [x] 3.3 调整品牌区域样式（深色背景、白色文字）

## Phase 4: 组件样式更新

- [x] 4.1 侧边栏：深色背景、条目悬停效果
- [x] 4.2 顶部导航栏：浅色背景、面包屑样式
- [x] 4.3 搜索框：底线输入框样式
- [x] 4.4 过滤器：样式更新
- [x] 4.5 卡片/列表：方角边框、悬停强调色
- [x] 4.6 按钮：方角、UPPERCASE、宽字间距

## Phase 5: 上传流程界面

- [x] 5.1-5.5 上传步骤界面样式

## Phase 6: 装饰标签系统

- [ ] 6.3 在关键位置添加装饰标签（如搜索结果数）

## Phase 7: 验证

- [ ] 7.1 功能测试：搜索、上传、项目切换
- [ ] 7.2 响应式测试：不同屏幕宽度
- [ ] 7.3 浏览器兼容性：Chrome、Edge、Firefox

---

## 验证方式

### 自动化测试
```bash
pytest tests/test_core_functions.py -v
```

### 手动验证
1. 启动服务器 `python main.py`
2. 访问 http://localhost:58888/workspace
3. 检查以下功能：
   - [ ] 搜索功能正常
   - [ ] 以图搜图正常
   - [ ] 项目切换正常
   - [ ] 瀑布流/网格切换正常
   - [ ] 上传索引功能正常
   - [ ] 侧边栏响应式正常

### 视觉对照
- 对比设计稿 `.superdesign/design_iterations/superdesign_master_v2.html`
