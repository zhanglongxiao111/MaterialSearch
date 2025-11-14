#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
后端API测试脚本 - 测试库类型选择功能
"""

import requests
import json

BASE_URL = "http://localhost:5000"


def test_scan_with_target():
    """测试支持目标库选择的扫描API"""
    print("\n=== 测试扫描API ===")

    # 测试扫描到永久库
    print("测试1: 扫描到永久库 (target=permanent)")
    try:
        response = requests.get(f"{BASE_URL}/api/scan", params={"target": "permanent"}, timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"错误: {e}")

    # 测试扫描到项目库
    print("\n测试2: 扫描到项目库 (target=proj_test)")
    try:
        response = requests.get(f"{BASE_URL}/api/scan", params={"target": "proj_test"}, timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"错误: {e}")


def test_search_with_library_type():
    """测试支持库类型选择的搜索API"""
    print("\n=== 测试搜索API ===")

    # 测试搜索永久库
    print("测试1: 文字搜索图片 (library_type=permanent)")
    payload = {
        "positive": "测试",
        "negative": "",
        "positive_threshold": 15,
        "negative_threshold": 30,
        "image_threshold": 20,
        "top_n": 20,
        "search_type": 0,
        "img_id": None,
        "path": "",
        "start_time": None,
        "end_time": None,
        "library_type": "permanent",
        "project_id": None
    }
    try:
        response = requests.post(f"{BASE_URL}/api/match", json=payload, timeout=10)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            results = response.json()
            print(f"结果数量: {len(results)}")
            if results:
                print(f"第一个结果: {json.dumps(results[0], ensure_ascii=False, indent=2)}")
        else:
            print(f"错误响应: {response.text}")
    except Exception as e:
        print(f"错误: {e}")

    # 测试搜索项目库
    print("\n测试2: 文字搜索项目库图片 (library_type=project)")
    payload["library_type"] = "project"
    payload["project_id"] = "proj_test"
    try:
        response = requests.post(f"{BASE_URL}/api/match", json=payload, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"错误: {e}")


def test_project_apis():
    """测试项目管理API"""
    print("\n=== 测试项目管理API ===")

    # 测试获取项目列表
    print("测试1: 获取项目列表")
    try:
        response = requests.get(f"{BASE_URL}/api/projects", timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"错误: {e}")

    # 测试获取项目统计
    print("\n测试2: 获取项目统计")
    try:
        response = requests.get(f"{BASE_URL}/api/projects/proj_test/stats", timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    print("="*60)
    print("后端API测试脚本")
    print("请先确保应用已在运行 (python main.py)")
    print("="*60)

    # 等待用户确认
    input("\n按回车键开始测试...")

    try:
        test_project_apis()
        test_scan_with_target()
        test_search_with_library_type()

        print("\n" + "="*60)
        print("所有测试完成!")
        print("="*60)
    except KeyboardInterrupt:
        print("\n\n测试已取消")
