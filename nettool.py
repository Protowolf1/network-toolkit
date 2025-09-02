import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import platform
import csv

print("Running:", __file__)


HOSTS_DB = Path("hosts.json")
RESULTS_DB = Path("results.json")

# ---------- Storage helpers ----------
def load_hosts():
    if not HOSTS_DB.exists(): return []
    with HOSTS_DB.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_hosts(hosts):
    with HOSTS_DB.open("w", encoding="utf-8") as f:
        json.dump(hosts, f, indent=2)

def load_results():
    if not RESULTS_DB.exists(): return []
    with RESULTS_DB.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_results(results):
    with RESULTS_DB.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

# ---------- Ping logic ----------
def _ping_command(host: str):
    system = platform.system().lower()
    if "windows" in system:
        # One echo, 1s timeout: -n 1 -w 1000
        return ["ping", "-n", "1", "-w", "1000", host]
    else:
        # Linux/mac: one packet, 1s timeout
        # mac uses -W in ms? On mac, -W is in ms with recent versions; to be safe use 1 second timeout via -W 1000 if supported; -t for TTL on mac not needed.
        # Most reliably: -c 1 -W 1 (seconds) works on Linux; mac's ping uses -W (ms) only in newer versions.
        # We'll still try -W 1; if it fails, the call will just time out by default.
        return ["ping", "-c", "1", "-W", "1", host]

_LATENCY_RE = re.compile(r"time[=<]?\s*(\d+(?:\.\d+)?)\s*ms", re.IGNORECASE)

def ping_once(host: str, timeout_ms: int = 1000):
    """
    Run a single ping attempt to host with a timeout (ms).
    Returns tuple: (reachable: bool, latency_ms: float|None, returncode: int, stdout+stderr: str)
    """
    # Build command based on OS
    system = platform.system().lower()
    if "windows" in system:
        # -n 1 => one echo; -w => timeout in ms
        cmd = ["ping", "-n", "1", "-w", str(timeout_ms), host]
    else:
        # Linux/mac: -c 1 => one packet; -W => timeout (Linux: seconds; mac: varies by version)
        # Use seconds for Linux; convert ms->s (ceil to 1 second minimum)
        sec = max(1, int(round(timeout_ms / 1000)))
        cmd = ["ping", "-c", "1", "-W", str(sec), host]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=max(1, timeout_ms/1000 + 1))
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        reachable = proc.returncode == 0

        # Try to parse "time=XX ms" or "time<1 ms"
        latency = None
        m = _LATENCY_RE.search(out)
        if m:
            try:
                latency = float(m.group(1))
            except ValueError:
                latency = None

        return reachable, latency, proc.returncode, out
    except subprocess.TimeoutExpired:
        return False, None, 124, ""  # 124 commonly used as timeout code
      
    """""
    Returns dict: {'host': str, 'reachable': bool, 'latency_ms': float|None, 'timestamp': iso}
    """""
    cmd = _ping_command(host)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        reachable = proc.returncode == 0

        latency = None
        m = _LATENCY_RE.search(out)
        if m:
            try:
                latency = float(m.group(1))
            except ValueError:
                latency = None

        return {
            "host": host,
            "reachable": bool(reachable),
            "latency_ms": latency,
            "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "raw_exit": proc.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "host": host,
            "reachable": False,
            "latency_ms": None,
            "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "raw_exit": "timeout"
        }

# ---------- Commands ----------
def cmd_add(args):
    hosts = load_hosts()
    new_hosts = []
    for h in args.hosts:
        h = h.strip()
        if h and h not in hosts:
            hosts.append(h)
            new_hosts.append(h)
    save_hosts(hosts)
    if new_hosts:
        print("Added:", ", ".join(new_hosts))
    else:
        print("No new hosts added (maybe they already exist).")

def cmd_remove(args):
    hosts = load_hosts()
    before = set(hosts)
    for h in args.hosts:
        if h in hosts:
            hosts.remove(h)
    save_hosts(hosts)
    removed = before - set(hosts)
    if removed:
        print("Removed:", ", ".join(sorted(removed)))
    else:
        print("Nothing removed.")

def cmd_list(args):
    hosts = load_hosts()
    if not hosts:
        print("No hosts saved. Add some with: python nettool.py add 8.8.8.8 example.com")
        return
    print("Saved hosts:")
    for i, h in enumerate(hosts, start=1):
        print(f"{i:2d}. {h}")
        import platform, subprocess, re
from datetime import datetime

# Parse "time=XX ms" or "time<1 ms"
_LATENCY_RE = re.compile(r"time[=<]?\s*(\d+(?:\.\d+)?)\s*ms", re.IGNORECASE)

def print_result(r):
    reach = "UP" if r["reachable"] else "DOWN"
    lat = f"{r['latency_ms']:.2f} ms" if r["latency_ms"] is not None else "-"
    print(f"{r['host']:<28} {reach:<5} {lat:>10}  ({r['timestamp']})")

def ping_once(host: str, timeout_ms: int = 1000):
    """Run a single ping attempt."""
    sysname = platform.system().lower()
    if "windows" in sysname:
        cmd = ["ping", "-n", "1", "-w", str(timeout_ms), host]       # Windows
        proc_timeout = max(1, timeout_ms/1000 + 1)
    else:
        sec = max(1, int(round(timeout_ms / 1000)))
        cmd = ["ping", "-c", "1", "-W", str(sec), host]              # Linux/mac
        proc_timeout = sec + 1
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=proc_timeout)
        out = (p.stdout or "") + "\n" + (p.stderr or "")
        reachable = (p.returncode == 0)
        latency = None
        m = _LATENCY_RE.search(out)
        if m:
            try:
                latency = float(m.group(1))
            except ValueError:
                pass
        return reachable, latency, p.returncode
    except subprocess.TimeoutExpired:
        return False, None, 124  # timeout

def ping_host(host: str, retries: int = 3, timeout_ms: int = 1000):
    """Try up to `retries`; keep best (lowest) latency if any succeed."""
    best = None
    successes = 0
    last_rc = None
    for _ in range(max(1, retries)):
        ok, lat, rc = ping_once(host, timeout_ms=timeout_ms)
        last_rc = rc
        if ok:
            successes += 1
            if lat is not None and (best is None or lat < best):
                best = lat
    return {
        "host": host,
        "reachable": successes > 0,
        "latency_ms": best,
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "raw_exit": last_rc,
        "attempts": max(1, retries),
        "successes": successes,
    }


def cmd_ping(args):
    result = ping_host(args.host, retries=args.retries, timeout_ms=args.timeout_ms)
    print_result(result)

def cmd_scan(args):
    hosts = load_hosts()
    if not hosts:
        print("No hosts saved.")
        return
    print(f"Scanning {len(hosts)} host(s)… (retries={args.retries}, timeout={args.timeout_ms}ms)\n")

    results = load_results()
    batch = []
    up = 0
    for h in hosts:
        r = ping_host(h, retries=args.retries, timeout_ms=args.timeout_ms)
        batch.append(r)
        if r["reachable"]:
            up += 1
        print_result(r)

    results.extend(batch)
    save_results(results)
    print("\nSummary:", f"{up}/{len(hosts)} reachable")

def cmd_report(args):
    # Build report from the most recent results for each host
    results = load_results()
    if not results:
        print("No results yet. Run: python nettool.py scan")
        return
    # Keep latest per host
    latest = {}
    for r in results:
        host = r["host"]
        ts = r.get("timestamp") or ""
        if host not in latest or ts > latest[host].get("timestamp", ""):
            latest[host] = r

    rows = list(latest.values())
    rows.sort(key=lambda r: (not r["reachable"], r["latency_ms"] if r["latency_ms"] is not None else 1e9, r["host"]))

    print("=== Network Report (latest per host) ===")
    print(f"Generated: {datetime.utcnow().isoformat(timespec='seconds')}Z")
    print("-" * 56)
    print(f"{'Host':<28} {'Reachable':<10} {'Latency (ms)':>12}")
    print("-" * 56)
    up = 0
    for r in rows:
        reach = "UP" if r["reachable"] else "DOWN"
        if r["reachable"]:
            up += 1
        lat = f"{r['latency_ms']:.2f}" if r["latency_ms"] is not None else "-"
        print(f"{r['host']:<28} {reach:<10} {lat:>12}")
    print("-" * 56)
    print(f"Total: {len(rows)}  |  UP: {up}  |  DOWN: {len(rows)-up}")

def cmd_export(args):
    results = load_results()
    if not results:
        print("No results to export. Run a scan first.")
        return

    rows = results
    if args.latest:
        latest = {}
        for r in results:
            host = r["host"]
            ts = r.get("timestamp") or ""
            if host not in latest or ts > latest[host].get("timestamp", ""):
                latest[host] = r
        rows = list(latest.values())

    out = Path(args.file)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Build fieldnames dynamically so new keys (attempts/successes) are included if present
    base_fields = ["host", "reachable", "latency_ms", "timestamp", "raw_exit"]
    extra_fields = set()
    for r in rows:
        extra_fields.update(r.keys())
    # Keep order: base fields first, then any extras not already included
    fieldnames = base_fields + [k for k in sorted(extra_fields) if k not in base_fields]

    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"Exported {len(rows)} row(s) to {out}")

# ---------- CLI ----------
def build_parser():
    p = argparse.ArgumentParser(description="Network Utility Toolkit")
    sub = p.add_subparsers(dest="cmd")
   
    a = sub.add_parser("add", help="Add one or more hosts")
    a.add_argument("hosts", nargs="+", help="Hostnames or IPs")
    a.set_defaults(func=cmd_add)

    r = sub.add_parser("remove", help="Remove one or more hosts")
    r.add_argument("hosts", nargs="+")
    r.set_defaults(func=cmd_remove)

    l = sub.add_parser("list", help="List saved hosts")
    l.set_defaults(func=cmd_list)

    # ping
    p1 = sub.add_parser("ping", help="Ping a single host immediately")
    p1.add_argument("host")
    p1.add_argument("--retries", type=int, default=3)
    p1.add_argument("--timeout-ms", type=int, default=1000)
    p1.set_defaults(func=cmd_ping)

    # scan
    s = sub.add_parser("scan", help="Ping all saved hosts and store results")
    s.add_argument("--retries", type=int, default=3)
    s.add_argument("--timeout-ms", type=int, default=1000)
    s.set_defaults(func=cmd_scan)

    rep = sub.add_parser("report", help="Show latest reachability/latency per host")
    rep.set_defaults(func=cmd_report)

    ex = sub.add_parser("export", help="Export results to CSV")
    ex.add_argument("--file", required=True, help="Output CSV path")
    ex.add_argument("--latest", action="store_true")
    ex.set_defaults(func=cmd_export)

    p.set_defaults(func=lambda _args: p.print_help())

    return p


def main():
    parser = build_parser()
       # TEMP: print the help your parser thinks it has
    print("\n--- DEBUG: parser help dump ---")
    print(parser.format_help())
    print("--- END DEBUG ---\n")

    if len(sys.argv) == 1:
        # no args: just show help and exit cleanly
        return
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
