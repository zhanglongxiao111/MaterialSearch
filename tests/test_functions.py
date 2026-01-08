#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接测试搜索函数 - 不依赖Flask服务器
"""

import sys
import os
import pytest
sys.path.insert(0, "D:\\AI\\materialsearch")

if os.getenv("RUN_INTEGRATION_TESTS") != "1":
    pytest.skip("Integration test requires prepared data.", allow_module_level=True)

from app.services.search_service import search_image_by_text_path_time, search_video_by_text_path_time
print("="*60)
print("测试搜索函数 - 直接调用")
print("="*60)

print("\n1. 测试搜索永久库 (library_type='permanent')")
try:
    results = search_image_by_text_path_time(
        positive_prompt="测试",
        negative_prompt="",
        library_type="permanent",
        project_id=None
    )
    print(f"✓ 搜索成功! 找到 {len(results)} 个结果")
    if results:
        print(f"  第一个结果: {results[0].get('path', 'N/A')}")
        print(f"  来源标注: {results[0].get('source', 'N/A')}")
except Exception as e:
    print(f"✗ 搜索失败: {e}")
    import traceback
    traceback.print_exc()

print("\n2. 测试搜索项目库 (library_type='project', project_id='proj_test')")
try:
    results = search_image_by_text_path_time(
        positive_prompt="测试",
        negative_prompt="",
        library_type="project",
        project_id="proj_test"
    )
    print(f"✓ 搜索成功! 找到 {len(results)} 个结果")
    if results:
        print(f"  第一个结果: {results[0].get('path', 'N/A')}")
        print(f"  来源标注: {results[0].get('source', 'N/A')}")
except Exception as e:
    print(f"✗ 搜索失败: {e}")
    import traceback
    traceback.print_exc()

print("\n3. 测试视频搜索")
try:
    results = search_video_by_text_path_time(
        positive_prompt="测试",
        negative_prompt="",
        library_type="permanent",
        project_id=None
    )
    print(f"✓ 视频搜索成功! 找到 {len(results)} 个结果")
    if results:
        print(f"  第一个结果: {results[0].get('path', 'N/A')}")
        print(f"  来源标注: {results[0].get('source', 'N/A')}")
except Exception as e:
    print(f"✗ 视频搜索失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("函数测试完成!")
print("="*60)
