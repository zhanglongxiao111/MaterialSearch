# 设计事务所数字资产分类体系 (Digital Asset Taxonomy)

本文档旨在定义设计事务所素材管理系统的分类逻辑。通过**“分库（Library Types）”**策略，将不同属性的数字资产在顶层进行物理或逻辑隔离，以实现精准的搜索与管理。

## 核心分类 (Library Types)

系统将资产划分为以下 7 大独立库。每个库拥有独立的元数据结构、预览方式和搜索逻辑。

| 库代码 | 名称 | 包含文件示例 | 核心用途 | 关键属性 (Key Attributes) |
| :--- | :--- | :--- | :--- | :--- |
| **REFERENCE** | 方案参考库 | 实景照片, 效果图, 分析图 | 寻找设计灵感, 案例研究 | 建筑类型, 风格, 空间功能 |
| **MATERIAL** | 材质贴图库 | .jpg (纹理), .tx, .sbsar | 渲染材质表现 | 材质种类, 表面处理, 通道类型 |
| **MODEL** | 3D模型库 | .3dm, .skp, .fbx, .obj | 建模与场景搭建 | 物体类别, 面数精度, 软件格式 |
| **GRAPHICS** | 平面素材库 | PNG(透明), PSD, AI, SVG | 后期P图, 文本排版, 分析图绘制 | 视角(顶/平/透), 风格(写实/插画) |
| **CAD** | 技术图纸库 | .dwg, .dxf, PDF图集 | 施工图绘制, 节点深化 | 图纸类型(平立剖), 比例, 构造对象 |
| **ENV** | 环境灯光库 | .hdr, .exr, .ies, .cube | 渲染环境设置, 灯光模拟 | 时间/天气(HDRI), 光斑形状(IES) |
| **SCRIPT** | 参数化脚本库 | .gh, .dyn, .py | 复杂逻辑生成, 性能分析 | 功能算法, 依赖插件, 宿主软件 |

---

## 详细分类定义

### 1. 方案参考库 (Reference Library)
*关注点：美学、空间关系、功能布局*

*   **一级分类 (Category)**
    *   **建筑 (Architecture)**: 外观, 鸟瞰, 局部
    *   **室内 (Interior)**: 大堂, 办公区, 居住空间
    *   **景观 (Landscape)**: 庭院, 铺装, 水景, 街道家具
    *   **规划/城市 (Urban)**: 总图, 城市肌理, 街道剖面
    *   **图纸/分析 (Drawings)**: 平面, 剖面, 爆炸图, 动线分析
*   **特有标签 (Tags)**
    *   **Mood**: 极简, 工业风, 赛博朋克, 传统中式
    *   **Component**: 楼梯, 坡道, 幕墙, 天窗, 双层皮
    *   **Lighting**: 夜景, 晨昏, 人工光

### 2. 材质贴图库 (Material Library)
*关注点：物理属性、纹理细节、PBR流程*

*   **一级分类 (Category)**
    *   **混凝土 (Concrete)**: 清水, 现浇, 预制板
    *   **木材 (Wood)**: 地板, 饰面, 原木, 软木
    *   **石材 (Stone)**: 大理石, 花岗岩, 洞石, 砖石
    *   **金属 (Metal)**: 钢, 铜, 铝板, 锈蚀金属
    *   **织物 (Fabric)**: 棉麻, 丝绒, 皮革, 地毯
    *   **透明/半透 (Translucent)**: 玻璃, 阳光板, 水, 亚克力
    *   **地面 (Ground)**: 沥青, 草地, 碎石, 土壤
*   **特有标签 (Tags)**
    *   **Property**: 无缝 (Seamless), 4K+, PBR套图
    *   **Finish**: 抛光 (Polished), 拉丝 (Brushed), 粗糙 (Rough)

### 3. 3D模型库 (Model Library)
*关注点：几何形态、拓扑结构、文件兼容性*

*   **一级分类 (Category)**
    *   **家具 (Furniture)**: 桌, 椅, 沙发, 柜, 床
    *   **植被 (Vegetation)**: 乔木, 灌木, 草, 室内绿植
    *   **人物 (People)**: 3D扫描人, 低模人
    *   **配景 (Accessories)**: 书籍, 餐具, 电子产品, 摆件
    *   **建筑构件 (Components)**: 门, 窗, 柱, 栏杆, 楼梯
    *   **交通 (Vehicles)**: 汽车, 自行车, 船
*   **特有标签 (Tags)**
    *   **Format**: Rhino, SketchUp, 3dsMax, Blender
    *   **Quality**: Low-poly, High-poly, 扫描级

### 4. 平面素材库 (Graphics Library)
*关注点：透明通道、平面设计、后期合成*

*   **一级分类 (Category)**
    *   **配景人 (Cutout People)**: 实景人, 插画人, 剪影
    *   **配景植物 (Cutout Plants)**: 树, 草丛, 盆栽
    *   **天空 (Skies)**: 蓝天, 晚霞, 阴天
    *   **纹理叠加 (Overlay)**: 污渍, 光效, 划痕, 纸纹
    *   **图标/标识 (Icons)**: 指北针, 比例尺, 功能图标, 箭头
*   **特有标签 (Tags)**
    *   **View**: 顶视 (Plan View), 平视 (Elevation View), 透视 (Perspective)
    *   **Type**: 栅格 (Raster), 矢量 (Vector)

### 5. 技术图纸库 (CAD Library)
*关注点：施工标准、节点构造、图块复用*

*   **一级分类 (Category)**
    *   **CAD图块 (Blocks)**: 家具, 洁具, 门窗, 植被符号
    *   **构造节点 (Details)**: 墙身, 地面, 屋面, 楼梯, 幕墙
    *   **标准图集 (Standards)**: 做法表, 通用详图
*   **特有标签 (Tags)**
    *   **Scale**: 1:10, 1:50, 1:100
    *   **Format**: DWG, DXF

### 6. 环境与灯光库 (Environment Library)
*关注点：光照模拟、渲染氛围*

*   **一级分类 (Category)**
    *   **HDRI**: 室内, 室外, 影棚
    *   **IES**: 射灯, 筒灯, 线条灯, 路灯
    *   **LUTs**: 电影感, 胶片感, 黑白
*   **特有标签 (Tags)**
    *   **Time**: Day, Night, Sunset, Overcast
    *   **Kelvin**: 3000K (Warm), 6000K (Cold)

### 7. 参数化脚本库 (Script Library)
*关注点：算法逻辑、生成器*

*   **一级分类 (Category)**
    *   **生成 (Generation)**: 造型, 纹理, 结构
    *   **分析 (Analysis)**: 日照, 视线, 排水, 结构优化
    *   **工具 (Utility)**: 批量改名, 导入导出, 图层管理
*   **特有标签 (Tags)**
    *   **Host**: Rhino(GH), Revit(Dynamo)
    *   **Plugin**: Kangaroo, Ladybug, Weaverbird

---

## 特殊文件处理策略 (Technical Strategy)

### CAD (.dwg/.dxf) 索引方案
CAD 图纸是线条数据，CLIP 视觉模型难以从原始图像中提取有效语义。采用 **“文本优先 + 智能预览”** 的混合策略。

1.  **元数据提取 (Metadata Extraction)**
    *   使用 `ezdxf` 或 `ODA` 解析文件。
    *   **提取对象**：图层名 (Layers), 块定义名 (Block Names), 文本标注 (MTEXT/TEXT)。
    *   **用途**：将提取的文本拼接后进行**文本嵌入 (Text Embedding)** 或全文检索，作为搜索的主要依据。

2.  **智能预览生成 (Smart Preview)**
    *   **转换**：利用转换工具生成高分辨率 PNG/PDF。
    *   **增强**：自动反色 (白底黑线)、线宽加粗、自动裁剪空白区域 (Zoom Extents)。
    *   **CLIP**：仅对增强后的预览图提取 CLIP 特征，但在搜索算法中降低其权重，优先信赖文本匹配。

---

## 前端交互设计 (Frontend UX)

### 侧边栏导航重构 (Sidebar Redesign)
利用 Workspace 现有的左侧栏结构，实现类似 IDE 或资源管理器的树状导航。

**逻辑层级：**
1.  **资源库根节点** (永久库 / 具体项目)
    *   点击后展开下级分类树。
2.  **分类子节点** (上述 7 大库)
    *   点击 `[🧱 材质贴图]`，右侧主视图切换为材质专用模式。
    *   点击 `[🛋️ 3D模型]`，右侧主视图切换为模型专用模式。

### 上下文感知 (Context-Aware)

**1. 动态筛选器 (Dynamic Filters)**
搜索栏下方的高级筛选区域将根据当前选中的“库类型”自动加载对应的控件：
*   **通用**: 路径搜索、排除词、时间范围。
*   **Reference 模式**: 增加 [建筑/室内/景观] 选项卡，[风格] 下拉框。
*   **Material 模式**: 增加 [材质类别] 图标阵列，[无缝] 开关。
*   **Model 模式**: 增加 [Rhino/SU] 格式复选框。

**2. 自适应视图 (Adaptive View)**
*   **瀑布流 (Masonry)**: 默认用于 Reference，保持图片原始比例，利于构图观察。
*   **正方形网格 (Grid)**: 默认用于 Material，便于纹理对比。
*   **列表/缩略图 (List)**: 默认用于 CAD/Script，强调文件名和元数据。

---

## 数据库实现建议 (Schema Proposal)

在 `Image` (或未来的 `Asset`) 表中增加以下字段以支持此分类体系：

```python
class Asset(Base):
    # ... 基础字段 ...

    # 1. 核心库类型划分
    library_type = Column(String(32), index=True) 
    # 枚举值: 'reference', 'material', 'model', 'graphics', 'cad', 'env', 'script'

    # 2. 分类层级
    category = Column(String(64), index=True)       # 一级分类 (如 'Concrete', 'Furniture')
    sub_category = Column(String(64), index=True)   # 二级分类 (如 'Polished', 'Chair')

    # 3. 扩展属性 (JSON)
    # 存储各库特有的非通用属性
    # 例 Material: {"seamless": true, "resolution": "4k"}
    # 例 Model: {"poly_count": 5000, "format": "3dm"}
    attributes = Column(JSON) 
```