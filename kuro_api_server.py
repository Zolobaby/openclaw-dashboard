#!/usr/bin/env python3
"""
Kuro监控API服务器
为Dashboard提供实时成本、性能和日志数据
"""

import json
import sqlite3
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import subprocess

# 确保导入kuro_monitor_integration
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from kuro_monitor_integration import KuroMonitorIntegration
except ImportError:
    KuroMonitorIntegration = None


class MonitoringAPI:
    """监控数据API"""

    def __init__(self):
        self.workspace = os.path.expanduser("~/.openclaw/workspace/monitoring")
        self.db_path = os.path.join(self.workspace, "cost_tracker.db")
        self.metrics_db_path = os.path.join(self.workspace, "system_metrics.db")
        self.log_db_path = os.path.join(self.workspace, "log_patterns.db")
        self.integration = None

        if KuroMonitorIntegration:
            try:
                self.integration = KuroMonitorIntegration()
            except Exception as e:
                print(f"Kuro集成初始化失败: {e}")

    def get_gateway_status(self) -> dict:
        """获取网关状态"""
        try:
            import urllib.request
            import urllib.error

            req = urllib.request.Request(
                "http://127.0.0.1:18789",
                method="HEAD",
                headers={"Host": "127.0.0.1:18789"}
            )

            start = datetime.now()
            try:
                response = urllib.request.urlopen(req, timeout=5)
                response_time = (datetime.now() - start).total_seconds() * 1000

                return {
                    "running": True,
                    "http_status": response.status,
                    "response_time_ms": round(response_time, 2),
                    "port_open": True,
                    "healthy": response.status == 200,
                    "timestamp": datetime.now().isoformat()
                }
            except urllib.error.HTTPError as e:
                return {
                    "running": True,
                    "http_status": e.code,
                    "response_time_ms": 0,
                    "port_open": True,
                    "healthy": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "running": False,
                "http_status": 0,
                "response_time_ms": 0,
                "port_open": False,
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def get_cost_data(self) -> dict:
        """获取成本数据"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "daily": 0,
            "weekly": 0,
            "monthly": 0,
            "by_model": {},
            "trend_7d": [],
            "prediction": {
                "predicted_monthly_cost": 0,
                "confidence": "low",
                "daily_average": 0,
                "trend": "stable",
                "based_on_days": 0
            },
            "stats": {
                "period_days": 30,
                "total_calls": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost_usd": 0,
                "avg_latency_ms": 0,
                "failed_calls": 0,
                "success_rate": 0
            }
        }

        # 从数据库获取
        if os.path.exists(self.db_path):
            try:
                with sqlite3.connect(self.db_path) as conn:
                    now = datetime.now()

                    # 日统计
                    daily_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    cursor = conn.execute(
                        "SELECT SUM(cost_usd), COUNT(*), SUM(input_tokens), SUM(output_tokens) FROM model_calls WHERE timestamp >= ?",
                        [daily_start.isoformat()]
                    )
                    row = cursor.fetchone()
                    if row and row[0]:
                        data["daily"] = round(row[0], 2)

                    # 周统计
                    weekly_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
                    cursor = conn.execute(
                        "SELECT SUM(cost_usd), COUNT(*), SUM(input_tokens), SUM(output_tokens) FROM model_calls WHERE timestamp >= ?",
                        [weekly_start.isoformat()]
                    )
                    row = cursor.fetchone()
                    data["weekly"] = round(row[0], 2) if row and row[0] else 0

                    # 月统计
                    monthly_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    cursor = conn.execute(
                        "SELECT SUM(cost_usd), COUNT(*), SUM(input_tokens), SUM(output_tokens) FROM model_calls WHERE timestamp >= ?",
                        [monthly_start.isoformat()]
                    )
                    row = cursor.fetchone()
                    data["monthly"] = round(row[0], 2) if row and row[0] else 0

                    # 按模型统计 (7天)
                    cursor = conn.execute(
                        """
                        SELECT model, provider, SUM(cost_usd), COUNT(*), SUM(input_tokens), SUM(output_tokens)
                        FROM model_calls
                        WHERE timestamp >= datetime('now', '-7 days')
                        GROUP BY model, provider
                        ORDER BY SUM(cost_usd) DESC
                        """
                    )
                    for row in cursor.fetchall():
                        model_key = f"{row[1]}/{row[0]}"
                        data["by_model"][model_key] = round(row[2], 2) if row[2] else 0

                    # 7日成本趋势
                    daily_costs = []
                    for i in range(7):
                        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0)
                        day_end = (now - timedelta(days=i-1)).replace(hour=0, minute=0, second=0)
                        cursor = conn.execute(
                            "SELECT SUM(cost_usd) FROM model_calls WHERE timestamp >= ? AND timestamp < ?",
                            [day_start.isoformat(), day_end.isoformat()]
                        )
                        row = cursor.fetchone()
                        daily_cost = round(row[0], 2) if row and row[0] else 0
                        daily_costs.append({
                            "date": day_start.strftime("%m-%d"),
                            "cost": daily_cost
                        })
                    data["trend_7d"] = daily_costs

                    # 30天统计
                    cursor = conn.execute(
                        """
                        SELECT COUNT(*), SUM(input_tokens), SUM(output_tokens), SUM(cost_usd), AVG(latency_ms)
                        FROM model_calls
                        WHERE timestamp >= datetime('now', '-30 days')
                        """
                    )
                    row = cursor.fetchone()
                    if row:
                        data["stats"]["total_calls"] = row[0] or 0
                        data["stats"]["total_input_tokens"] = row[1] or 0
                        data["stats"]["total_output_tokens"] = row[2] or 0
                        data["stats"]["total_cost_usd"] = round(row[3] or 0, 2)
                        data["stats"]["avg_latency_ms"] = round(row[4] or 0, 2)

                    # 预测
                    if data["monthly"] > 0:
                        days_used = now.day
                        daily_avg = data["monthly"] / max(days_used, 1)
                        predicted = daily_avg * 30
                        data["prediction"] = {
                            "predicted_monthly_cost": round(predicted, 2),
                            "confidence": "medium" if days_used > 10 else "low",
                            "daily_average": round(daily_avg, 2),
                            "trend": "increasing" if daily_avg > (data["daily"] or 1) else "stable",
                            "based_on_days": days_used
                        }

            except Exception as e:
                print(f"数据库查询失败: {e}")

        return data

    def get_performance_data(self) -> dict:
        """获取性能数据"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_percent": 0,
                "cpu_1h_avg": 0
            },
            "gateway": {
                "response_1h_avg": 0,
                "error_1h_avg": 0,
                "total_requests": 0
            }
        }

        # 从metrics数据库获取
        if os.path.exists(self.metrics_db_path):
            try:
                with sqlite3.connect(self.metrics_db_path) as conn:
                    # 最新系统指标
                    cursor = conn.execute(
                        "SELECT cpu_percent, memory_percent, disk_percent FROM metrics ORDER BY timestamp DESC LIMIT 1"
                    )
                    row = cursor.fetchone()
                    if row:
                        data["system"]["cpu_percent"] = row[0]
                        data["system"]["memory_percent"] = row[1]
                        data["system"]["disk_percent"] = row[2]

                    # 1小时平均CPU
                    one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
                    cursor = conn.execute(
                        "SELECT AVG(cpu_percent) FROM metrics WHERE timestamp >= ?",
                        [one_hour_ago]
                    )
                    row = cursor.fetchone()
                    if row and row[0]:
                        data["system"]["cpu_1h_avg"] = round(row[0], 2)

                    # 网关响应时间
                    cursor = conn.execute(
                        "SELECT AVG(response_time_ms), COUNT(*) FROM gateway_metrics WHERE timestamp >= datetime('now', '-1 hour')"
                    )
                    row = cursor.fetchone()
                    if row and row[0]:
                        data["gateway"]["response_1h_avg"] = round(row[0], 2)
                        data["gateway"]["total_requests"] = row[1]

            except Exception as e:
                print(f"性能数据查询失败: {e}")

        return data

    def get_log_analysis(self) -> dict:
        """获取日志分析"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "total_anomalies": 0,
            "by_severity": {"critical": 0, "error": 0, "warning": 0},
            "by_type": {},
            "recent_anomalies": []
        }

        if os.path.exists(self.log_db_path):
            try:
                with sqlite3.connect(self.log_db_path) as conn:
                    # 总异常数 (使用正确的表名 anomaly_events)
                    cursor = conn.execute("SELECT COUNT(*) FROM anomaly_events")
                    row = cursor.fetchone()
                    if row:
                        data["total_anomalies"] = row[0]

                    # 按严重程度统计
                    cursor = conn.execute(
                        "SELECT severity, COUNT(*) FROM anomaly_events GROUP BY severity"
                    )
                    for row in cursor.fetchall():
                        data["by_severity"][row[0]] = row[1]

                    # 按类型统计
                    cursor = conn.execute(
                        "SELECT anomaly_type, COUNT(*) FROM anomaly_events GROUP BY anomaly_type"
                    )
                    for row in cursor.fetchall():
                        data["by_type"][row[0]] = row[1]

                    # 最近异常 (7天内)
                    seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
                    cursor = conn.execute(
                        """
                        SELECT timestamp, anomaly_type, severity, description, suggested_action
                        FROM anomaly_events
                        WHERE timestamp >= ?
                        ORDER BY timestamp DESC
                        LIMIT 10
                        """,
                        [seven_days_ago]
                    )
                    for row in cursor.fetchall():
                        data["recent_anomalies"].append({
                            "timestamp": row[0],
                            "anomaly_type": row[1],
                            "severity": row[2],
                            "description": row[3],
                            "suggested_action": row[4]
                        })

            except Exception as e:
                print(f"日志分析查询失败: {e}")

        return data

    def get_channel_status(self) -> dict:
        """获取通道状态"""
        try:
            sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace"))
            from scripts.channel_monitor import ChannelMonitor
            monitor = ChannelMonitor()
            health = monitor.check_all_channels()
            return health
        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def get_all_data(self) -> dict:
        """获取所有监控数据"""
        return {
            "gateway": self.get_gateway_status(),
            "costs": self.get_cost_data(),
            "performance": self.get_performance_data(),
            "logs": self.get_log_analysis(),
            "channels": self.get_channel_status(),
            "timestamp": datetime.now().isoformat()
        }


class APIHandler(BaseHTTPRequestHandler):
    """API请求处理器"""

    api = MonitoringAPI()

    def log_message(self, format, *args):
        """简化日志输出"""
        pass

    def _send_json(self, data: dict, status=200):
        """发送JSON响应"""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        """处理GET请求"""
        path = self.path

        if path == "/api/status" or path == "/api/health":
            self._send_json({"status": "ok", "timestamp": datetime.now().isoformat()})

        elif path == "/api/full-status" or path == "/api/monitoring/all":
            # Dashboard兼容端点
            data = self.api.get_all_data()
            # 添加dashboard期望的字段
            data['resources'] = {
                'disk_usage_percent': data.get('performance', {}).get('system', {}).get('disk_percent', 0),
                'logs_human': '2 MB',
                'workspace_human': '31 MB'
            }
            self._send_json(data)

        elif path == "/api/monitoring/gateway":
            self._send_json(self.api.get_gateway_status())

        elif path == "/api/monitoring/costs":
            self._send_json(self.api.get_cost_data())

        elif path == "/api/monitoring/performance":
            self._send_json(self.api.get_performance_data())

        elif path == "/api/monitoring/logs":
            self._send_json(self.api.get_log_analysis())

        elif path == "/api/monitoring/channels":
            self._send_json(self.api.get_channel_status())

        else:
            self._send_json({"error": "Not found"}, 404)


class KuroAPIServer:
    """Kuro API服务器"""

    def __init__(self, port=18888):
        self.port = port
        self.server = None
        self.thread = None
        self.running = False

    def start(self):
        """启动服务器"""
        if self.running:
            return

        self.server = HTTPServer(("127.0.0.1", self.port), APIHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.running = True
        print(f"✅ Kuro API服务器已启动 (http://127.0.0.1:{self.port})")

    def stop(self):
        """停止服务器"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        self.running = False
        print("🛑 Kuro API服务器已停止")


if __name__ == "__main__":
    import time
    import socket

    # 尝试18888，如果被占用则用18889
    port = 18888
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', port))
        s.close()
    except OSError:
        port = 18889
        print(f"⚠️ 端口 18888 被占用，使用 {port}")

    server = KuroAPIServer(port=port)
    server.start()

    print("\n可用API端点:")
    print(f"  http://127.0.0.1:{port}/api/status")
    print(f"  http://127.0.0.1:{port}/api/monitoring/all")
    print(f"  http://127.0.0.1:{port}/api/monitoring/gateway")
    print(f"  http://127.0.0.1:{port}/api/monitoring/costs")
    print(f"  http://127.0.0.1:{port}/api/monitoring/performance")
    print(f"  http://127.0.0.1:{port}/api/monitoring/logs")
    print(f"  http://127.0.0.1:{port}/api/monitoring/channels")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
