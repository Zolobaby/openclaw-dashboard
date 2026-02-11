# OpenClaw Dashboard Monitor

<div align="center">

![OpenClaw Dashboard](https://img.shields.io/badge/OpenClaw-Dashboard-blue?style=for-the-badge)
![Python 3.10+](https://img.shields.io/badge/Python-3.10+-green?style=for-the-badge)
![MIT License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**基于 OpenClaw 的企业级 AI Agent 监控系统**

[English](README.md) | [中文](README_CN.md)

</div>

---

## ✨ 特性

- 🖥️ **实时网关监控** - 端口、延迟、健康状态
- 💰 **成本追踪** - 7天/30天趋势、模型分布、预测
- 📡 **通道状态** - 多通道监控（飞书、Telegram、iMessage等）
- 🚨 **异常检测** - 自动识别错误爆发、频率异常
- 🔄 **自动恢复** - 服务故障自动重启
- 📊 **统一Dashboard** - 一站式监控面板

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/yourname/openclaw-dashboard.git
cd openclaw-dashboard
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置

```bash
cp config.example.yaml config.yaml
# 编辑配置文件
```

### 4. 启动

```bash
# 启动API服务器
python kuro_api_server.py

# 启动Dashboard
python kuro-dashboard-server.py

# 启动监控守护进程
python scripts/system_monitor.py daemon
```

---

## 📁 项目结构

```
openclaw-dashboard/
├── monitoring/              # 核心监控模块
│   ├── kuro_api_server.py   # API服务器
│   ├── kuro-dashboard-server.py  # Dashboard前端
│   ├── kuro_monitor_integration.py  # Kuro集成
│   └── *.db                 # SQLite数据库
├── scripts/                 # 监控脚本
│   ├── system_monitor.py    # 统一监控系统
│   ├── channel_monitor.py   # 通道监控
│   ├── system_recovery.py   # 自动恢复
│   └── fetch_gateway_costs.py  # 成本获取
├── dashboard/               # 前端页面
│   ├── index.html          # 主页面
│   ├── styles.css          # 样式
│   └── app.js              # 交互逻辑
├── config.yaml             # 配置文件
├── requirements.txt        # Python依赖
└── README.md              # 英文文档
```

---

## 📊 监控指标

### 网关状态
- 运行状态 (运行中/已停止)
- HTTP响应时间
- 端口连通性
- 进程信息

### 成本追踪
- 今日/本周/本月成本
- 7天成本趋势图
- 30天统计汇总
- 按模型成本分布
- 月度成本预测

### 通道监控
- 飞书 (Feishu)
- Telegram
- BlueBubbles
- iMessage

### 异常检测
- 总异常数
- 按严重程度分布 (Critical/Error/Warning)
- 按类型分布
- 最近10条异常记录

---

## 🔧 配置说明

### config.yaml

```yaml
gateway:
  port: 18789
  api_port: 18789

monitoring:
  check_interval: 60      # 检查间隔(秒)
  alert_threshold: 3      # 告警阈值

channels:
  feishu:
    name: "飞书"
    enabled: true
  telegram:
    name: "Telegram"
    enabled: true
```

---

## 📦 Python依赖

```
flask>=2.0.0
requests>=2.25.0
sqlite3
json
datetime
```

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

---

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

## 🙏 致谢

- [OpenClaw](https://github.com/openclaw/openclaw) - 底层框架
- [Kuro](https://github.com/yourname/kuro) - 战略助手

---

<div align="center">

**用 ❤️ 制作 by Kuro**

</div>
