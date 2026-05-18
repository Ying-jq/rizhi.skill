#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志搜索脚本
支持关键词搜索、日期范围过滤
"""

import os
import re
import json
from datetime import datetime, timedelta
from pathlib import Path

def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent.parent / "journal_config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_date(date_str):
    """解析各种日期格式"""
    # 尝试多种日期格式
    formats = [
        r'(\d{4})[.-](\d{1,2})[.-](\d{1,2})',  # YYYY-MM-DD or YYYY.M.D
        r'(\d{1,2})[.-](\d{1,2})',               # M.D or M.DD
    ]

    for fmt in formats:
        match = re.match(fmt, date_str.strip())
        if match:
            groups = match.groups()
            if len(groups) == 3:
                return int(groups[0]), int(groups[1]), int(groups[2])
            elif len(groups) == 2:
                current_year = datetime.now().year
                return current_year, int(groups[0]), int(groups[1])
    return None

def search_logs(root_path, keyword=None, start_date=None, end_date=None, search_total=True):
    """
    搜索日志

    Args:
        root_path: 日志根目录
        keyword: 搜索关键词
        start_date: 开始日期 (datetime对象)
        end_date: 结束日期 (datetime对象)
        search_total: 是否搜索总日志
    """
    root = Path(root_path)
    results = []

    # 搜索总日志
    if search_total and (root / "总日志.md").exists():
        with open(root / "总日志.md", 'r', encoding='utf-8') as f:
            content = f.read()
            if keyword and keyword in content:
                results.append({
                    'file': '总日志.md',
                    'path': str(root / "总日志.md"),
                    'snippet': extract_snippet(content, keyword)
                })

    # 搜索各年月的日志文件
    for year_dir in sorted(root.glob("*")):
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue

        year = int(year_dir.name)

        for month_dir in sorted(year_dir.glob("*月份日志")):
            for log_file in sorted(month_dir.glob("*.md")):
                # 解析日志日期
                date_match = re.match(r'(\d{1,2})\.(\d{1,2})\.md', log_file.name)
                if not date_match:
                    continue

                month, day = int(date_match.group(1)), int(date_match.group(2))
                log_date = datetime(year, month, day)

                # 日期过滤
                if start_date and log_date < start_date:
                    continue
                if end_date and log_date > end_date:
                    continue

                # 读取文件内容
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 关键词过滤
                if keyword and keyword not in content:
                    continue

                results.append({
                    'file': log_file.name,
                    'path': str(log_file),
                    'date': log_date.strftime('%Y-%m-%d'),
                    'snippet': extract_snippet(content, keyword) if keyword else content[:200]
                })

    return results

def extract_snippet(content, keyword, context=100):
    """提取包含关键词的片段"""
    idx = content.find(keyword)
    if idx == -1:
        return ""

    start = max(0, idx - context)
    end = min(len(content), idx + len(keyword) + context)

    snippet = content[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(content):
        snippet = snippet + "..."

    return snippet

def print_results(results):
    """打印搜索结果"""
    if not results:
        print("未找到匹配的日志")
        return

    print(f"\n找到 {len(results)} 条匹配的日志：\n")
    print("=" * 80)

    for i, result in enumerate(results, 1):
        print(f"\n【{i}】 {result.get('date', '')} - {result['file']}")
        print(f"路径: {result['path']}")
        if 'snippet' in result:
            print(f"\n片段:\n{result['snippet']}")
        print("-" * 80)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='搜索日志')
    parser.add_argument('-k', '--keyword', help='搜索关键词')
    parser.add_argument('-s', '--start', help='开始日期 (格式: YYYY-MM-DD 或 M.D)')
    parser.add_argument('-e', '--end', help='结束日期 (格式: YYYY-MM-DD 或 M.D)')
    parser.add_argument('-t', '--total', action='store_true', default=True, help='搜索总日志')

    args = parser.parse_args()

    # 加载配置
    config = load_config()
    root_path = config['root_path']

    # 解析日期
    start_date = None
    end_date = None

    if args.start:
        parsed = parse_date(args.start)
        if parsed:
            start_date = datetime(*parsed)

    if args.end:
        parsed = parse_date(args.end)
        if parsed:
            end_date = datetime(*parsed)

    # 执行搜索
    results = search_logs(root_path, args.keyword, start_date, end_date, args.total)

    # 打印结果
    print_results(results)
