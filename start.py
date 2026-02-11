#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenClaw Dashboard Monitor - 快速启动脚本

使用方法:
  python start.py api       # 启动API服务器
  python start.py dashboard # 启动Dashboard
  python start.py monitor   # 启动监控守护进程
  python start.py all       # 启动所有服务
  python start.py status    # 查看状态
  python start.py stop      # 停止所有服务

作者: Kuro
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

# 配置
PROJECT_DIR = Path(__file__).parent
PROCESSES = []


def print_banner():
    """打印横幅"""
    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║   🖥️  OpenClaw Dashboard Monitor                          ║
║                                                            ║
║   企业级 AI Agent 监控系统                                 ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
""")


def start_api():
    """启动API服务器"""
    print("🚀 启动 API 服务器...")
    api_script = PROJECT_DIR / "kuro_api_server.py"
    
    if not api_script.exists():
        print("❌ API服务器脚本不存在")
        return False
    
    proc = subprocess.Popen(
        [sys.executable, str(api_script)],
        cwd=str(PROJECT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    PROCESSES.append(("API", proc))
    print(f"✅ API服务器已启动 (PID: {proc.pid})")
    
    # 等待启动
    time.sleep(3)
    
    # 检查是否成功
    try:
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:18889/api/status")
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                print("✅ API服务器运行正常")
                return True
    except:
        pass
    
    print("⚠️  API服务器启动中...")
    return True


def start_dashboard():
    """启动Dashboard"""
    print("🌐 启动 Dashboard...")
    dash_script = PROJECT_DIR / "kuro-dashboard-server.py"
    
    if not dash_script.exists():
        print("⚠️  Dashboard脚本不存在，跳过")
        return True
    
    proc = subprocess.Popen(
        [sys.executable, str(dash_script)],
        cwd=str(PROJECT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    PROCESSES.append(("Dashboard", proc))
    print(f"✅ Dashboard已启动 (PID: {proc.pid})")
    print(f"   访问地址: http://localhost:8888/")
    
    return True


def start_monitor():
    """启动监控守护进程"""
    print("📡 启动监控守护进程...")
    monitor_script = PROJECT_DIR / "scripts" / "system_monitor.py"
    
    if not monitor_script.exists():
        print("❌ 监控脚本不存在")
        return False
    
    proc = subprocess.Popen(
        [sys.executable, str(monitor_script), "daemon"],
        cwd=str(PROJECT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    PROCESSES.append(("Monitor", proc))
    print(f"✅ 监控守护进程已启动 (PID: {proc.pid})")
    
    return True


def stop_all():
    """停止所有服务"""
    print("\n🛑 停止所有服务...")
    
    for name, proc in PROCESSES:
        if proc.poll() is None:  # 仍在运行
            print(f"   停止 {name} (PID: {proc.pid})...")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    
    # 清理残留进程
    try:
        subprocess.run(["pkill", "-f", "kuro_api_server"], capture_output=True)
        subprocess.run(["pkill", "-f", "kuro-dashboard"], capture_output=True)
        subprocess.run(["pkill", "-f", "system_monitor"], capture_output=True)
    except:
        pass
    
    print("✅ 所有服务已停止")
    PROCESSES.clear()


def check_status():
    """检查状态"""
    print("\n📊 服务状态:")
    
    # 检查API
    try:
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:18889/api/status")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            print(f"  ✅ API服务器: 运行中")
            print(f"     时间: {data.get('timestamp', 'N/A')[:19]}")
    except:
        print(f"  ❌ API服务器: 未运行")
    
    # 检查端口
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', 8888))
        sock.close()
        if result == 0:
            print(f"  ✅ Dashboard: 运行中 (端口 8888)")
        else:
            print(f"  ❌ Dashboard: 未运行")
    except:
        print(f"  ❌ Dashboard: 未运行")
    
    print("")


def show_help():
    """显示帮助"""
    print("""
📖 使用方法:
    
    python start.py api       - 启动API服务器
    python start.py dashboard - 启动Dashboard
    python start.py monitor   - 启动监控守护进程
    python start.py all       - 启动所有服务
    python start.py status    - 查看服务状态
    python start.py stop      - 停止所有服务
    python start.py help      - 显示此帮助
    
🔗 访问地址:
    
    Dashboard: http://localhost:8888/
    API:       http://localhost:18889/api/
    
📝 注意事项:
    
    - 确保 OpenClaw Gateway 已启动 (默认端口 18789)
    - API服务器使用端口 18889
    - Dashboard使用端口 8888
    - Windows用户可能需要安装 Visual C++ Build Tools
    """)


def main():
    """主函数"""
    print_banner()
    
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    # 导入json（start_api需要）
    import json
    
    if command == "api":
        start_api()
        
    elif command == "dashboard":
        start_dashboard()
        
    elif command == "monitor":
        start_monitor()
        
    elif command == "all":
        print("🚀 启动所有服务...\n")
        start_api()
        start_dashboard()
        start_monitor()
        print("\n✅ 所有服务已启动!")
        print("   访问 http://localhost:8888/ 查看Dashboard")
        
    elif command == "status":
        check_status()
        
    elif command == "stop":
        stop_all()
        
    elif command == "help" or command == "--help" or command == "-h":
        show_help()
        
    else:
        print(f"❌ 未知命令: {command}")
        print("   使用 'python start.py help' 查看帮助")
    
    # 注册信号处理
    def signal_handler(sig, frame):
        print("\n🛑 收到中断信号...")
        stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 如果是all命令，保持运行
    if command == "all":
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            stop_all()


if __name__ == "__main__":
    main()
