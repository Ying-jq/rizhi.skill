#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志保存与分析 - Git自动提交脚本
自动执行git add和git commit操作

特性：
- 自动检测Git是否安装
- 从配置文件读取是否启用自动提交
- 无Git时优雅降级，不影响正常使用
"""

import subprocess
import sys
import os
import json
from pathlib import Path
from datetime import datetime

def load_config():
    """加载配置文件，获取Git设置"""
    config_path = Path(__file__).parent.parent / "journal_config.json"
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('preferences', {}).get('git_auto_commit', True)
        except Exception:
            pass
    return True  # 默认启用

def check_git_installed():
    """检测Git是否已安装"""
    try:
        result = subprocess.run(
            ['git', '--version'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=5
        )
        if result.returncode == 0:
            return True
    except Exception:
        pass
    return False

def run_git_command(args, cwd=None):
    """执行git命令"""
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=30
        )
        if result.returncode != 0:
            print(f"Git命令执行失败: {result.stderr}", file=sys.stderr)
            return False
        return True
    except subprocess.TimeoutExpired:
        print("Git命令执行超时", file=sys.stderr)
        return False
    except FileNotFoundError:
        # Git未安装
        return None
    except Exception as e:
        print(f"执行git命令时出错: {e}", file=sys.stderr)
        return False

def auto_commit(root_path, message):
    """
    自动提交git

    Args:
        root_path: 日志保存根目录
        message: 提交信息（如"保存日志"）

    Returns:
        tuple: (success: bool, skipped: bool, reason: str)
    """
    # 检查配置
    if not load_config():
        return True, True, "Git自动提交已在配置中关闭"

    # 检查Git是否安装
    if not check_git_installed():
        return True, True, "未检测到Git安装，已跳过自动提交。如需启用Git版本控制，请前往 https://git-scm.com/download 下载安装"

    if not os.path.exists(root_path):
        return False, False, f"路径不存在: {root_path}"

    # 确保在git仓库中执行
    git_dir = os.path.join(root_path, '.git')
    if not os.path.exists(git_dir):
        # 尝试初始化
        init_result = run_git_command(['git', 'init'], cwd=root_path)
        if init_result is None:
            return True, True, "Git未安装，已跳过自动提交"
        if not init_result:
            return False, False, "Git初始化失败"

        # 初始提交
        if not run_git_command(['git', 'add', '.'], cwd=root_path):
            return False, False, "Git add失败"
        if not run_git_command(['git', 'commit', '-m', 'chore: 初始化日志仓库'], cwd=root_path):
            return False, False, "Git初始提交失败"
        print("已初始化Git仓库并完成首次提交")

    # git add
    add_result = run_git_command(['git', 'add', '.'], cwd=root_path)
    if add_result is None:
        return True, True, "Git未安装，已跳过自动提交"
    if not add_result:
        return False, False, "Git add失败"

    # 检查是否有变更
    result = subprocess.run(
        ['git', 'status', '--porcelain'],
        cwd=root_path,
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=10
    )

    if not result.stdout.strip():
        return True, False, "没有变更需要提交"

    # git commit
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"auto: [{timestamp}] {message}"

    commit_result = run_git_command(['git', 'commit', '-m', full_message], cwd=root_path)
    if commit_result is None:
        return True, True, "Git未安装，已跳过自动提交"
    if not commit_result:
        return False, False, "Git commit失败"

    print(f"已自动提交: {full_message}")
    return True, False, "提交成功"

def main():
    """命令行入口"""
    if len(sys.argv) < 3:
        print("用法: python auto_commit.py <根目录> <提交信息>")
        print("示例: python auto_commit.py D:\\日志 \"保存日志\"")
        sys.exit(1)

    root_path = sys.argv[1]
    message = sys.argv[2]

    success, skipped, reason = auto_commit(root_path, message)

    # 只在非跳过且失败时退出
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
