## ADDED Requirements

### Requirement: 支持 Rhino 模型文件
系统 SHALL 支持扫描和索引 Rhino (.3dm) 模型文件。

#### Scenario: 识别 Rhino 预览
- **WHEN** 扫描器遍历目录时
- **THEN** 识别 `.3dm` 文件
- **AND** 将其视为可视化的图片素材进行处理
- **AND** 提取其内置预览图用于索引和展示
