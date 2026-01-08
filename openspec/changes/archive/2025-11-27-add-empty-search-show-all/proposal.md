# Change: 空搜索显示全部素材

## Why
当前项目库/永久库无法通过空搜索查看全部素材，运营需要“一键查看所有”。

## What Changes
- 允许空搜索触发全量列表（按库类型）
- 后端接受 top_n<=0 视为全量返回
- 前端 workspace/classic 支持空搜索并自动放宽 top_n

## Impact
- search API
- 前端 workspace/classic
- specs/search（新增空搜索场景）
