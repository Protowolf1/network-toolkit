hosts.json
results.json
__pycache__/
*.pyc
# 🌐 Network Utility Toolkit (CLI)

A Python-based command-line toolkit to manage and monitor hosts.  
It can save host lists, ping hosts with retries, scan multiple hosts, generate reports, and export results to CSV.  

This is a learning project to practice **Python CLI development**, **file I/O**, **argparse**, and **Git/GitHub workflows**.

---

## ✨ Features
- Add, remove, and list saved hosts
- Ping a single host with configurable retries and timeouts
- Scan all saved hosts (results saved to JSON)
- Retry logic: keeps the **best latency** across attempts
- Generate a report showing latest reachability/latency per host
- Export all results or latest results to CSV
- Data stored locally in `hosts.json` and `results.json` (ignored by Git)

---

## 🚀 Usage

### Add hosts
```bash
python nettool.py add 8.8.8.8 1.1.1.1 example.com

## Author
**Dreon**
- GitHub:[@Protowolf1](https://github.com/Protowolf1)
- Portfolio: _Coming soon_