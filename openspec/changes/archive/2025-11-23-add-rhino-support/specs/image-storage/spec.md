## ADDED Requirements

### Requirement: 复杂格式预览图提取
系统 SHALL 能够从非标准图片格式的容器文件中提取预览图像。

#### Scenario: Rhino 预览图提取
- **GIVEN** 一个有效的 Rhino (.3dm) 文件
- **WHEN** 系统处理该文件时
- **THEN** 尝试读取文件头部的二进制数据
- **AND** 识别并提取内嵌的 BMP 或 PNG 格式预览图
- **AND** 如果提取成功，使用该预览图进行后续的特征计算和缩略图生成
- **AND** 如果提取失败，记录错误并使用默认占位符

## MODIFIED Requirements

### Requirement: 图片宽高比计算
系统 SHALL 自动计算并存储图片的宽高比信息，用于 AI 自动排版。

#### Scenario: 计算精确宽高比
- **WHEN** 系统扫描图片时
- **THEN** 计算 `aspect_ratio = width / height`
- **AND** 对于 `.3dm` 等容器格式，使用提取出的预览图尺寸进行计算
- **AND** 精确到小数点后 3 位（如 1.778）
- **AND** 存储到 `aspect_ratio` 字段

#### Scenario: 识别标准宽高比
- **WHEN** 计算出精确宽高比后
- **THEN** 系统匹配标准比例（容差 ±5%）
- **AND** 识别常见比例：
  - 1:1（正方形）
  - 4:3（传统横向）
  - 16:9（宽屏横向）
  - 21:9（超宽屏）
  - 3:4（传统竖向）
  - 9:16（宽屏竖向）
  - √2:1（A4 横向）
  - 1:√2（A4 竖向）
- **AND** 存储到 `aspect_ratio_standard` 字段
- **AND** 非标准比例存储为计算值（如"1.85:1"）

#### Scenario: 按宽高比筛选图片
- **WHEN** 用户查询特定宽高比的图片
- **THEN** 系统可按 `aspect_ratio_standard` 精确匹配（如"16:9"）
- **OR** 按 `aspect_ratio` 范围查询（如 1.7 ~ 1.8 之间）
