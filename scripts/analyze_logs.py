#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志统计分析脚本
统计写作频率、情绪趋势、内容主题等
"""

import os
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter, defaultdict

def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent.parent / "journal_config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_original_content(markdown_content):
    """提取用户原文内容（跳过分析框架部分）"""
    # 找到"---"分隔符，之后是分析框架内容
    parts = markdown_content.split('---')
    if len(parts) >= 2:
        # 第一部分是标题+原文内容
        original = parts[0]
        # 移除标题行
        lines = original.split('\n')
        if lines and lines[0].startswith('#'):
            lines = lines[2:]  # 跳过标题和空行
        return '\n'.join(lines).strip()
    return markdown_content

def analyze_writing_frequency(root_path, year=None):
    """分析写作频率"""
    root = Path(root_path)

    if year is None:
        year = datetime.now().year

    year_dir = root / str(year)
    if not year_dir.exists():
        return None

    stats = {
        'total_logs': 0,
        'total_words': 0,
        'by_month': defaultdict(lambda: {'count': 0, 'words': 0}),
        'by_weekday': defaultdict(int),
        'streak': 0,
        'max_gap': 0,
    }

    dates = []

    for month_dir in sorted(year_dir.glob("*月份日志")):
        month_match = re.search(r'(\d{1,2})月份日志', month_dir.name)
        if not month_match:
            continue
        month = int(month_match.group(1))

        for log_file in sorted(month_dir.glob("*.md")):
            # 跳过月志和年报
            if '月日志' in log_file.name or '年报' in log_file.name:
                continue

            date_match = re.match(r'(\d{1,2})\.(\d{1,2})\.md', log_file.name)
            if not date_match:
                continue

            day = int(date_match.group(1))
            log_date = datetime(year, month, day)
            dates.append(log_date)

            # 读取文件
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取原文计算字数
            original = extract_original_content(content)
            word_count = len(original)

            stats['total_logs'] += 1
            stats['total_words'] += word_count
            stats['by_month'][month]['count'] += 1
            stats['by_month'][month]['words'] += word_count
            stats['by_weekday'][log_date.weekday()] += 1

    # 计算连续写作天数和最大间隔
    if dates:
        dates.sort()
        stats['streak'] = calculate_streak(dates)
        stats['max_gap'] = calculate_max_gap(dates)

    return stats

def calculate_streak(dates):
    """计算当前连续写作天数"""
    if not dates:
        return 0

    today = datetime.now().date()
    streak = 0

    for i in range(len(dates)-1, -1, -1):
        date = dates[i].date()
        if (today - date).days <= 1 or streak == 0:
            streak += 1
            today = date
        else:
            break

    return streak

def calculate_max_gap(dates):
    """计算最大间隔天数"""
    if len(dates) < 2:
        return 0

    max_gap = 0
    for i in range(1, len(dates)):
        gap = (dates[i] - dates[i-1]).days
        if gap > max_gap:
            max_gap = gap

    return max_gap

def extract_emotion_trend(root_path, year=None):
    """提取用户原文中的情绪趋势"""
    root = Path(root_path)

    if year is None:
        year = datetime.now().year

    year_dir = root / str(year)
    if not year_dir.exists():
        return None

    # 情绪关键词（用户原文中的真实情绪表达）
    emotion_keywords = {
        'positive': {
            '开心': ['开心', '快乐', '高兴', '兴奋', '愉悦', '满足', '幸福', '美好', '棒', '赞', '哈哈'],
            'grateful': ['感谢', '感恩', '谢谢', '感激', '幸运', '福气'],
            'motivated': ['充实', '收获', '进步', '成长', '完成', '达成', '突破', '进展'],
            'connected': ['陪伴', '聊天', '朋友', '相聚', '热闹'],
        },
        'negative': {
            '焦虑': ['焦虑', '焦虑', '担心', '忧虑', '不安', '紧张'],
            'sad': ['难过', '伤心', '失落', '沮丧', '郁闷', '压抑'],
            'lonely': ['孤独', '寂寞', '孤单', '没人', '一个人'],
            'confused': ['迷茫', '困惑', '迷茫', '不知道', '不确定', '纠结'],
            'tired': ['累', '疲惫', '疲倦', '困', '想睡觉'],
            'stressed': ['压力', '压力', '压抑', '喘不过气', '崩溃'],
        }
    }

    monthly_emotions = defaultdict(lambda: defaultdict(int))
    emotion_timeline = []

    for month_dir in sorted(year_dir.glob("*月份日志")):
        month_match = re.search(r'(\d{1,2})月份日志', month_dir.name)
        if not month_match:
            continue
        month = int(month_match.group(1))

        for log_file in sorted(month_dir.glob("*.md")):
            # 跳过月志和年报
            if '月日志' in log_file.name or '年报' in log_file.name:
                continue

            date_match = re.match(r'(\d{1,2})\.(\d{1,2})\.md', log_file.name)
            if not date_match:
                continue

            day = int(date_match.group(1))
            log_date = datetime(year, month, day)

            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 只分析原文内容
            original = extract_original_content(content)

            # 统计情绪
            daily_emotions = {'positive': 0, 'negative': 0, 'detail': {}}
            for category, keywords in emotion_keywords['positive'].items():
                for keyword in keywords:
                    count = original.count(keyword)
                    if count > 0:
                        daily_emotions['positive'] += count
                        daily_emotions['detail'][category] = daily_emotions['detail'].get(category, 0) + count
                        monthly_emotions[month][category] += count

            for category, keywords in emotion_keywords['negative'].items():
                for keyword in keywords:
                    count = original.count(keyword)
                    if count > 0:
                        daily_emotions['negative'] += count
                        daily_emotions['detail'][category] = daily_emotions['detail'].get(category, 0) + count
                        monthly_emotions[month][category] += count

            if daily_emotions['positive'] > 0 or daily_emotions['negative'] > 0:
                emotion_timeline.append({
                    'date': log_date.strftime('%Y-%m-%d'),
                    'month': month,
                    'day': day,
                    **daily_emotions
                })

    return monthly_emotions, emotion_timeline

def extract_content_themes(root_path, year=None, top_n=10):
    """提取内容主题/高频词"""
    root = Path(root_path)

    if year is None:
        year = datetime.now().year

    year_dir = root / str(year)
    if not year_dir.exists():
        return None

    # 停用词（更全面的列表）
    stopwords = {
        # 常见虚词
        '的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
        '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
        '自己', '这', '那', '个', '们', '来', '还', '这个', '那个', '什么', '怎么',
        '可以', '因为', '所以', '但是', '如果', '虽然', '然后', '还是', '或者', '而且',
        # 日志框架词（避免统计这些）
        '今天', '今天我', '今天让', '让我', '让我开', '让我充', '让我感', '让我感',
        '我在今', '值得我', '需要改', '改进的', '开心的', '充实的', '感谢的', '思考的',
        '分析', '分析原', '原文', '提取', '本日志', '本分析', '日期',
    }

    word_counter = Counter()

    for month_dir in sorted(year_dir.glob("*月份日志")):
        for log_file in sorted(month_dir.glob("*.md")):
            # 跳过月志和年报
            if '月日志' in log_file.name or '年报' in log_file.name:
                continue

            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 只分析原文
            original = extract_original_content(content)

            # 分词（简单按标点和空格分）
            words = re.findall(r'[\u4e00-\u9fff]+', original)
            for word in words:
                if word not in stopwords and len(word) >= 2:
                    word_counter[word] += 1

    return word_counter.most_common(top_n)

def print_analysis(root_path, year=None):
    """打印统计分析结果"""
    if year is None:
        year = datetime.now().year

    print(f"\n{'='*80}")
    print(f"{year}年日志统计分析报告")
    print(f"{'='*80}\n")

    # 1. 写作频率分析
    freq_stats = analyze_writing_frequency(root_path, year)
    if freq_stats:
        print("【一、写作频率统计】")
        print(f"  总日志数: {freq_stats['total_logs']} 篇")
        print(f"  总字数: {freq_stats['total_words']} 字")
        print(f"  平均每篇: {freq_stats['total_words']//max(1, freq_stats['total_logs'])} 字")
        print(f"  当前连续写作: {freq_stats['streak']} 天")
        print(f"  最大间隔: {freq_stats['max_gap']} 天")

        print("\n  按月统计:")
        for month in sorted(freq_stats['by_month'].keys()):
            info = freq_stats['by_month'][month]
            print(f"    {month}月: {info['count']} 篇, {info['words']} 字")

        print("\n  按星期统计:")
        weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        for wd in range(7):
            count = freq_stats['by_weekday'][wd]
            print(f"    {weekdays[wd]}: {count} 篇")
        print()

    # 2. 情绪趋势分析（基于用户原文）
    emotion_result = extract_emotion_trend(root_path, year)
    if emotion_result:
        monthly_emotions, timeline = emotion_result
        print("【二、情绪趋势分析】(基于用户原文内容)")
        print("  ※ 以下数据仅供参考，实际情况请以原文为准\n")

        if timeline:
            print("  近期待关注的日子:")
            for entry in timeline[-5:]:  # 最近5条
                pos = entry['positive']
                neg = entry['negative']
                detail = entry['detail']
                if neg > pos:  # 负面情绪较多的日子
                    top_emotion = max(detail.items(), key=lambda x: x[1])[0] if detail else '未知'
                    print(f"    {entry['date']}: 负面情绪偏多 ({top_emotion})")
            print()

        print("  按月统计情绪关键词出现次数:")
        all_emotions = set()
        for month in monthly_emotions:
            all_emotions.update(monthly_emotions[month].keys())

        for emotion in all_emotions:
            print(f"\n    【{emotion}】")
            for month in sorted(monthly_emotions.keys()):
                if emotion in monthly_emotions[month]:
                    print(f"      {month}月: {monthly_emotions[month][emotion]} 次")
        print()
    else:
        print("【二、情绪趋势分析】")
        print("  暂无数据\n")

    # 3. 内容主题/高频词
    themes = extract_content_themes(root_path, year)
    if themes:
        print("【三、内容主题 TOP 10】")
        for i, (word, count) in enumerate(themes, 1):
            print(f"  {i}. {word} ({count} 次)")
        print()

    print(f"{'='*80}\n")
    print("※ 以上数据仅供参考，实际情况请以日志原文为准\n")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='统计分析日志')
    parser.add_argument('-y', '--year', type=int, help='分析指定年份 (默认当前年)')
    parser.add_argument('-f', '--frequency', action='store_true', help='仅显示写作频率')
    parser.add_argument('-e', '--emotion', action='store_true', help='仅显示情绪趋势')
    parser.add_argument('-t', '--theme', action='store_true', help='仅显示内容主题')

    args = parser.parse_args()

    # 加载配置
    config = load_config()
    root_path = config['root_path']

    # 解析年份
    year = args.year if args.year else datetime.now().year

    print_analysis(root_path, year)
