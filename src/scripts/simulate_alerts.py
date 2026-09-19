#!/usr/bin/env python3
"""
TimonTrack — Alert Simulation & Ingestion Script
=================================================

A demo/training script that reads security alerts from a local CSV or JSON
file and pushes them one-by-one to the TimonTrack Ingestion API using your
personal Bearer token.

Usage:
------
  python simulate_alerts.py --api-key tt_live_<your-key>
  python simulate_alerts.py --api-key tt_live_<your-key> --source data/alerts.json --format json
  python simulate_alerts.py --api-key tt_live_<your-key> --url http://localhost:8000 --delay 0.5

Arguments:
----------
  --api-key   (required) Your TimonTrack Ingestion API key (copy from Settings > Profile)
  --source    Path to CSV or JSON file (default: data/alerts.csv)
  --format    File format: csv or json (default: auto-detect from extension)
  --url       TimonTrack backend URL (default: http://localhost:8000)
  --delay     Seconds between each alert push (default: 0.3)
  --batch     Push all alerts in one batch request instead of one by one
"""

import argparse
import csv
import json
import sys
import time
from pathlib import Path

# ── Terminal colors ──────────────────────────────────────────────────────────
RESET   = "\033[0m"
BOLD    = "\033[1m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
RED     = "\033[91m"
CYAN    = "\033[96m"
MAGENTA = "\033[95m"
BLUE    = "\033[94m"
GRAY    = "\033[90m"

def c(color: str, text: str) -> str:
    return f"{color}{text}{RESET}"


def banner():
    print()
    print(c(BLUE, "╔══════════════════════════════════════════════════════════╗"))
    print(c(BLUE, "║") + c(BOLD, "   🛡️  TimonTrack — Alert Simulation Engine              ") + c(BLUE, "║"))
    print(c(BLUE, "║") + c(GRAY,  "   IBM BoB AI Hackathon 2026 · Real-Time Log Feeder       ") + c(BLUE, "║"))
    print(c(BLUE, "╚══════════════════════════════════════════════════════════╝"))
    print()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Push security alerts to TimonTrack via the Ingestion API."
    )
    p.add_argument("--api-key",  required=True,  help="Your TimonTrack Bearer API key (copy from Settings → Profile)")
    p.add_argument("--source",   default="data/alerts.csv", help="Path to alerts CSV or JSON file")
    p.add_argument("--format",   default=None,   choices=["csv", "json"], help="File format override (auto-detected by default)")
    p.add_argument("--url",      default="http://localhost:8000", help="TimonTrack backend base URL")
    p.add_argument("--delay",    default=0.3,    type=float, help="Seconds between each alert push")
    p.add_argument("--batch",    action="store_true", help="Push all alerts in a single batch request")
    return p.parse_args()


# ── Load Alerts ──────────────────────────────────────────────────────────────

def load_csv(path: Path) -> list[dict]:
    alerts = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Strip whitespace from keys and values
            clean = {k.strip(): v.strip() for k, v in row.items() if k}
            if clean:
                alerts.append(clean)
    return alerts


def load_json(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # Support {"alerts": [...]} or plain list
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("alerts", "data", "events", "items", "results"):
            if isinstance(data.get(key), list):
                return data[key]
    raise ValueError(f"Cannot parse JSON: expected a list or {{'alerts': [...]}}. Got keys: {list(data.keys())}")


def load_alerts(source: str, fmt: str | None) -> tuple[list[dict], str]:
    path = Path(source)
    if not path.exists():
        print(c(RED, f"  ✗ File not found: {path}"))
        sys.exit(1)

    detected_fmt = fmt or ("json" if path.suffix.lower() == ".json" else "csv")
    try:
        if detected_fmt == "json":
            alerts = load_json(path)
        else:
            alerts = load_csv(path)
    except Exception as e:
        print(c(RED, f"  ✗ Failed to load {path}: {e}"))
        sys.exit(1)

    return alerts, detected_fmt


# ── Normalize Alert ──────────────────────────────────────────────────────────

# Maps common field aliases to canonical names
FIELD_ALIASES = {
    "event_type": "event",
    "alert_type": "event",
    "type":       "event",
    "source_ip":  "src_ip",
    "src":        "src_ip",
    "dest_ip":    "dst_ip",
    "dst":        "dst_ip",
    "destination_ip": "dst_ip",
    "time":       "timestamp",
    "date":       "timestamp",
    "level":      "severity",
    "priority":   "severity",
}

REQUIRED = {"timestamp", "src_ip", "dst_ip", "event", "severity"}


def normalize_alert(raw: dict) -> dict | None:
    """Map aliases and validate required fields."""
    alert = {}
    for k, v in raw.items():
        canonical = FIELD_ALIASES.get(k.lower().strip(), k.lower().strip())
        alert[canonical] = v
    missing = REQUIRED - alert.keys()
    if missing:
        return None   # Skip rows missing critical fields
    return alert


# ── HTTP Ingestion ────────────────────────────────────────────────────────────

def push_alert(alert: dict, base_url: str, api_key: str, session) -> dict:
    """POST a single alert to /api/v1/ingest."""
    resp = session.post(
        f"{base_url}/api/v1/ingest",
        json={"alerts": [alert]},
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def push_batch(alerts: list[dict], base_url: str, api_key: str, session) -> dict:
    """POST all alerts in a single request."""
    resp = session.post(
        f"{base_url}/api/v1/ingest",
        json={"alerts": alerts},
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


# ── Health Check ─────────────────────────────────────────────────────────────

def check_backend(base_url: str, session) -> bool:
    try:
        r = session.get(f"{base_url}/", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    try:
        import requests
    except ImportError:
        print(c(RED, "\n  ✗ 'requests' library not found. Install it with:"))
        print(c(YELLOW, "    pip install requests\n"))
        sys.exit(1)

    args = parse_args()
    banner()

    print(c(CYAN, "  Configuration"))
    print(f"  {c(GRAY, 'Source File :')} {args.source}")
    print(f"  {c(GRAY, 'Backend URL :')} {args.url}")
    print(f"  {c(GRAY, 'API Key     :')} tt_live_{'*' * (len(args.api_key) - 8)}{args.api_key[-4:]}")
    print(f"  {c(GRAY, 'Mode        :')} {'Batch (single request)' if args.batch else f'Sequential (delay={args.delay}s)'}")
    print()

    # Load alerts
    print(c(CYAN, "  Loading Alerts..."))
    raw_alerts, fmt = load_alerts(args.source, args.format)
    print(f"  {c(GREEN, '✓')} Loaded {c(BOLD, str(len(raw_alerts)))} raw events from {c(BOLD, args.source)} [{fmt.upper()}]")

    # Normalize
    alerts = []
    skipped = 0
    for raw in raw_alerts:
        a = normalize_alert(raw)
        if a:
            alerts.append(a)
        else:
            skipped += 1

    print(f"  {c(GREEN, '✓')} Normalized {c(BOLD, str(len(alerts)))} valid alerts ({c(YELLOW, str(skipped))} skipped — missing required fields)")
    print()

    if not alerts:
        print(c(RED, "  ✗ No valid alerts to push. Check your file and required columns: timestamp, src_ip, dst_ip, event, severity"))
        sys.exit(1)

    # Session setup
    session = requests.Session()

    # Backend health check
    print(c(CYAN, "  Checking TimonTrack backend..."))
    if check_backend(args.url, session):
        print(f"  {c(GREEN, '✓')} Backend is {c(GREEN, 'ONLINE')} at {args.url}")
    else:
        print(f"  {c(YELLOW, '⚠')} Backend health check failed — attempting anyway...")
    print()

    # Push alerts
    print(c(CYAN, f"  Ingesting {len(alerts)} alerts {'(batch mode)' if args.batch else '(sequential mode)'}..."))
    print(c(GRAY, "  " + "─" * 56))

    success_count = 0
    fail_count    = 0
    total_chains  = 0

    if args.batch:
        try:
            result = push_batch(alerts, args.url, args.api_key, session)
            ingested = result.get("alerts_ingested", len(alerts))
            chains   = result.get("chains_formed", 0)
            total_chains += chains
            success_count = ingested
            print(f"  {c(GREEN, '✓')} Batch complete — {c(BOLD, str(ingested))} alerts ingested, {c(MAGENTA, str(chains))} chains formed")
        except Exception as e:
            fail_count = len(alerts)
            print(f"  {c(RED, '✗')} Batch failed: {e}")
    else:
        for i, alert in enumerate(alerts, 1):
            ts       = alert.get("timestamp", "")[:19]
            src      = alert.get("src_ip", "?")
            event    = alert.get("event", "?")
            severity = alert.get("severity", "?").upper()

            # Severity color
            sev_color = RED if severity in ("CRITICAL", "HIGH") else (YELLOW if severity == "MEDIUM" else GRAY)

            try:
                result = push_alert(alert, args.url, args.api_key, session)
                chains = result.get("chains_formed", 0)
                total_chains += chains
                success_count += 1
                chain_note = f" {c(MAGENTA, f'+{chains} chain')}" if chains > 0 else ""
                print(
                    f"  {c(GREEN, '✓')} [{i:>4}/{len(alerts)}] "
                    f"{c(GRAY, ts)}  {c(CYAN, src):<20} "
                    f"{c(BOLD, event):<22} "
                    f"{c(sev_color, severity):<10}"
                    f"{chain_note}"
                )
            except Exception as e:
                fail_count += 1
                print(
                    f"  {c(RED, '✗')} [{i:>4}/{len(alerts)}] "
                    f"{c(GRAY, ts)}  {c(CYAN, src):<20} "
                    f"{c(BOLD, event):<22} "
                    f"{c(RED, str(e)[:40])}"
                )

            if i < len(alerts):
                time.sleep(args.delay)

    # Summary
    print(c(GRAY, "  " + "─" * 56))
    print()
    print(c(CYAN, "  Simulation Complete"))
    print(f"  {c(GREEN, '✓')} Ingested   : {c(BOLD, str(success_count))} alerts")
    if fail_count:
        print(f"  {c(RED, '✗')} Failed     : {c(BOLD, str(fail_count))} alerts")
    print(f"  {c(MAGENTA, '⛓')} Attack Chains Formed: {c(BOLD, str(total_chains))}")
    print()
    print(c(GRAY, "  Open the TimonTrack dashboard to view correlated attack chains."))
    print(c(GRAY, f"  → http://localhost:5173/dashboard"))
    print()


if __name__ == "__main__":
    main()
