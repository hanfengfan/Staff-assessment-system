#!/usr/bin/env python
"""
快速启动开发服务器
"""
import os
import sys
import subprocess

def run_command(command, description):
    """执行命令并显示描述"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✓ 成功")
        if result.stdout:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"✗ 失败: {e}")
        if e.stderr:
            print(f"错误信息: {e.stderr}")
        return False
    return True

def main():
    print("=" * 50)
    print("轨道交通站务人员AI智能考核系统 - 后端启动")
    print("=" * 50)

    # 检查Django是否已安装
    try:
        import django
        print(f"✓ Django {django.get_version()} 已安装")
    except ImportError:
        print("✗ Django未安装，请先运行: pip install -r requirements.txt")
        return

    # 检查数据库文件是否存在
    if not os.path.exists('db.sqlite3'):
        print("\n数据库文件不存在，开始初始化...")
        if not run_command("python manage.py migrate", "执行数据库迁移"):
            return

        # 创建管理员用户
        if not run_command("python manage.py init_admin", "创建管理员用户"):
            return

        # 初始化示例数据
        if not run_command("python manage.py init_sample_data", "初始化示例数据"):
            return

    print("\n启动Django开发服务器...")
    print("访问地址: http://127.0.0.1:8000")
    print("管理界面: http://127.0.0.1:8000/admin/")
    print("API文档: http://127.0.0.1:8000/api/")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 50)

    # 启动开发服务器
    try:
        os.execvp(sys.executable, [sys.executable, "manage.py", "runserver"])
    except KeyboardInterrupt:
        print("\n\n服务器已停止")

if __name__ == "__main__":
    main()