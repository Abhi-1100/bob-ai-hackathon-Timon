"""
Realistic Enterprise Threat Intelligence Alerts Dataset Generator.

Generates realistic CSV alert feeds adhering strictly to the schema:
    timestamp, src_ip, dst_ip, event, severity

Features:
- Realistic threat actor public IPs (bulletproof hosters, Tor exit nodes, APT infrastructure)
- Realistic corporate enterprise subnet architecture (DMZ, App tier, DB tier, Domain Controllers, Endpoints)
- Multi-stage MITRE ATT&CK kill-chains (Ransomware, APT C2, SQLi exfiltration, Lateral Movement, Credential Access)
- Realistic SOC background noise & port scans
- Exact record count support (default: 1000 rows)
- Chronologically sorted timestamps
"""

import argparse
import csv
from datetime import datetime, timedelta
from pathlib import Path
import random
from typing import List, Dict, Tuple


# Realistic public IP pools simulating external threat actors / botnets / APTs
THREAT_ACTOR_IPS = [
    # Known bulletproof hosts / Tor exit nodes / VPS ranges
    "185.220.101.45", "185.220.101.78", "194.26.29.112", "194.26.29.115",
    "91.240.118.52", "91.240.118.99", "45.154.255.84", "45.154.255.12",
    "103.152.220.14", "103.152.220.89", "185.191.171.33", "185.191.171.76",
    "193.142.146.21", "193.142.146.88", "89.248.165.110", "89.248.165.145",
    "195.123.246.60", "195.123.246.92", "45.143.203.18", "45.143.203.54",
    "141.98.11.89", "141.98.11.104", "194.38.20.11", "194.38.20.45",
    "193.32.162.77", "193.32.162.90", "79.137.198.12", "79.137.198.56",
    "85.209.11.120", "85.209.11.205", "176.119.25.33", "176.119.25.88",
    "45.95.169.14", "45.95.169.87", "185.156.73.44", "185.156.73.120",
]

# Background scanner IPs (Shodan, Censys, mass scanning bots)
SCANNER_IPS = [
    "71.6.135.131", "71.6.165.200", "198.199.98.246", "162.243.128.91",
    "167.94.138.35", "167.94.138.52", "167.94.145.96", "167.94.146.10",
    "198.235.24.10", "198.235.24.50", "205.210.31.8", "205.210.31.25",
    "64.62.197.100", "64.62.197.105", "92.118.160.17", "92.118.160.45",
]

# Internal Enterprise Subnets
DMZ_WEB_SERVERS = ["10.0.1.10", "10.0.1.11", "10.0.1.12", "10.0.1.20", "10.0.1.25"]
APP_SERVERS = ["10.0.2.15", "10.0.2.16", "10.0.2.20", "10.0.2.22", "10.0.2.30"]
DATABASE_SERVERS = ["10.0.3.10", "10.0.3.11", "10.0.3.15"]
DOMAIN_CONTROLLERS = ["10.0.0.5", "10.0.0.6"]
WORKSTATIONS = [f"10.0.10.{i}" for i in range(10, 80)]
VPN_GATEWAYS = ["10.0.5.1", "10.0.5.2"]

# Multi-Stage Realistic Attack Campaigns
# Format: List of (event, severity, target_tier, delay_minutes)
ATTACK_CAMPAIGNS: List[Dict[str, any]] = [
    {
        "name": "APT Ransomware Deployment (LockBit / BlackCat style)",
        "steps": [
            ("PortScan", "Low", DMZ_WEB_SERVERS, (1, 5)),
            ("Enumeration", "Low", DMZ_WEB_SERVERS, (2, 6)),
            ("BruteForce", "Medium", DMZ_WEB_SERVERS, (3, 8)),
            ("BruteForce", "High", DMZ_WEB_SERVERS, (2, 5)),
            ("UnauthorizedAccess", "High", DMZ_WEB_SERVERS, (1, 4)),
            ("PowerShell", "High", DMZ_WEB_SERVERS, (2, 5)),
            ("PrivilegeEscalation", "High", DMZ_WEB_SERVERS, (3, 8)),
            ("CredentialDumping", "Critical", DOMAIN_CONTROLLERS, (4, 10)),
            ("LateralMovement", "High", APP_SERVERS, (5, 12)),
            ("LateralMovement", "Critical", DATABASE_SERVERS, (3, 8)),
            ("Malware", "Critical", APP_SERVERS, (2, 6)),
            ("DataExfiltration", "Critical", DATABASE_SERVERS, (5, 15)),
        ],
    },
    {
        "name": "SQL Injection & Database Exfiltration Breach",
        "steps": [
            ("Reconnaissance", "Low", DMZ_WEB_SERVERS, (2, 7)),
            ("PortScan", "Low", DMZ_WEB_SERVERS, (1, 4)),
            ("SQLInjection", "Medium", DMZ_WEB_SERVERS, (3, 8)),
            ("SQLInjection", "High", DMZ_WEB_SERVERS, (2, 6)),
            ("CommandExecution", "High", DMZ_WEB_SERVERS, (2, 5)),
            ("PrivilegeEscalation", "Critical", DMZ_WEB_SERVERS, (3, 10)),
            ("LateralMovement", "High", DATABASE_SERVERS, (4, 9)),
            ("DataExfiltration", "Critical", DATABASE_SERVERS, (6, 18)),
        ],
    },
    {
        "name": "Targeted Spearphishing & C2 Infiltration (APT29 / CozyBear style)",
        "steps": [
            ("Phishing", "Low", WORKSTATIONS, (5, 15)),
            ("Phishing", "Medium", WORKSTATIONS, (2, 6)),
            ("Malware", "High", WORKSTATIONS, (1, 5)),
            ("PowerShell", "High", WORKSTATIONS, (2, 6)),
            ("MalwareDownload", "High", WORKSTATIONS, (2, 8)),
            ("C2Beacon", "High", WORKSTATIONS, (3, 10)),
            ("CredentialAccess", "High", WORKSTATIONS, (4, 12)),
            ("LateralMovement", "High", DOMAIN_CONTROLLERS, (5, 15)),
            ("C2Beacon", "Critical", DOMAIN_CONTROLLERS, (4, 10)),
            ("DataExfiltration", "Critical", DOMAIN_CONTROLLERS, (8, 20)),
        ],
    },
    {
        "name": "VPN / SSH Credential Stuffing & Domain Takeover",
        "steps": [
            ("PortScan", "Low", VPN_GATEWAYS, (1, 4)),
            ("BruteForce", "Medium", VPN_GATEWAYS, (2, 6)),
            ("BruteForce", "High", VPN_GATEWAYS, (1, 4)),
            ("UnauthorizedAccess", "High", VPN_GATEWAYS, (2, 5)),
            ("LateralMovement", "High", DOMAIN_CONTROLLERS, (3, 9)),
            ("CredentialDumping", "Critical", DOMAIN_CONTROLLERS, (2, 6)),
            ("PrivilegeEscalation", "Critical", DOMAIN_CONTROLLERS, (3, 8)),
            ("CommandExecution", "Critical", DOMAIN_CONTROLLERS, (2, 5)),
        ],
    },
    {
        "name": "Remote Code Execution & Cryptomining / Lateral Movement",
        "steps": [
            ("PortScan", "Low", APP_SERVERS, (1, 3)),
            ("Enumeration", "Low", APP_SERVERS, (2, 5)),
            ("RemoteCodeExecution", "Critical", APP_SERVERS, (2, 6)),
            ("CommandExecution", "High", APP_SERVERS, (1, 4)),
            ("MalwareDownload", "High", APP_SERVERS, (2, 7)),
            ("Malware", "High", APP_SERVERS, (1, 4)),
            ("LateralMovement", "High", APP_SERVERS, (3, 8)),
            ("C2Beacon", "High", APP_SERVERS, (4, 10)),
        ],
    },
    {
        "name": "Distributed Denial of Service (DDoS) Volumetric Attack",
        "steps": [
            ("Reconnaissance", "Low", DMZ_WEB_SERVERS, (1, 3)),
            ("PortScan", "Low", DMZ_WEB_SERVERS, (1, 2)),
            ("DoS", "Medium", DMZ_WEB_SERVERS, (1, 3)),
            ("DDoS", "High", DMZ_WEB_SERVERS, (1, 2)),
            ("DDoS", "Critical", DMZ_WEB_SERVERS, (1, 2)),
        ],
    },
]

# Isolated noise / background scanner events
BACKGROUND_NOISE_EVENTS = [
    ("PortScan", "Low", DMZ_WEB_SERVERS),
    ("Enumeration", "Low", DMZ_WEB_SERVERS),
    ("PortScan", "Low", VPN_GATEWAYS),
    ("BruteForce", "Low", DMZ_WEB_SERVERS),
    ("BruteForce", "Medium", VPN_GATEWAYS),
    ("Reconnaissance", "Low", DMZ_WEB_SERVERS),
    ("Reconnaissance", "Low", APP_SERVERS),
    ("DoS", "Low", DMZ_WEB_SERVERS),
]


def generate_alerts(total_alerts: int = 1000) -> List[Dict[str, str]]:
    """
    Generate exactly `total_alerts` realistic threat alerts.
    
    Distributes approximately 70% of alerts into multi-stage attack chains
    and 30% into realistic background reconnaissance and botnet noise.
    """
    random.seed(42)  # Reproducible dataset
    base_time = datetime(2026, 9, 12, 6, 0, 0)
    alerts: List[Dict[str, str]] = []

    target_campaign_alerts = int(total_alerts * 0.72)
    campaign_alerts_count = 0

    # 1. Generate multi-stage attack chains
    while campaign_alerts_count < target_campaign_alerts:
        campaign = random.choice(ATTACK_CAMPAIGNS)
        steps = campaign["steps"]
        
        # Check if adding this campaign exceeds target
        if campaign_alerts_count + len(steps) > target_campaign_alerts:
            # truncate steps to fit exactly
            steps = steps[: target_campaign_alerts - campaign_alerts_count]

        src_ip = random.choice(THREAT_ACTOR_IPS)
        # Random start time across a 36-hour campaign window
        campaign_start = base_time + timedelta(
            hours=random.randint(0, 30),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )
        curr_time = campaign_start

        for event, severity, target_pool, (min_delay, max_delay) in steps:
            curr_time += timedelta(
                minutes=random.randint(min_delay, max_delay),
                seconds=random.randint(5, 55)
            )
            dst_ip = random.choice(target_pool)
            alerts.append({
                "timestamp": curr_time.strftime("%Y-%m-%d %H:%M:%S"),
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "event": event,
                "severity": severity,
            })
            campaign_alerts_count += 1

    # 2. Fill remaining rows with realistic background internet scanning / noise
    remaining = total_alerts - len(alerts)
    for _ in range(remaining):
        src_ip = random.choice(SCANNER_IPS)
        event, severity, target_pool = random.choice(BACKGROUND_NOISE_EVENTS)
        dst_ip = random.choice(target_pool)
        
        # Spread background alerts evenly across the 36-hour monitoring window
        noise_time = base_time + timedelta(
            hours=random.randint(0, 36),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )
        alerts.append({
            "timestamp": noise_time.strftime("%Y-%m-%d %H:%M:%S"),
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "event": event,
            "severity": severity,
        })

    # Sort strictly chronologically
    alerts.sort(key=lambda r: r["timestamp"])
    return alerts


def generate_dataset(total_alerts: int = 1000, output_file: str = "enterprise_threat_alerts_1000.csv") -> Path:
    """Generate and write alerts to CSV file."""
    alerts = generate_alerts(total_alerts=total_alerts)

    out_path = Path(__file__).resolve().parent / output_file
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["timestamp", "src_ip", "dst_ip", "event", "severity"]
        )
        writer.writeheader()
        writer.writerows(alerts)

    # Calculate summary statistics
    severities = {}
    events = {}
    unique_src = set()
    unique_dst = set()
    for a in alerts:
        severities[a["severity"]] = severities.get(a["severity"], 0) + 1
        events[a["event"]] = events.get(a["event"], 0) + 1
        unique_src.add(a["src_ip"])
        unique_dst.add(a["dst_ip"])

    print("=" * 65)
    print(f"Dataset successfully created: {out_path}")
    print(f"Total alert count: {len(alerts)}")
    print(f"Time span: {alerts[0]['timestamp']} -> {alerts[-1]['timestamp']}")
    print(f"Unique Source IPs: {len(unique_src)} | Unique Target IPs: {len(unique_dst)}")
    print(f"Severity Breakdown: {severities}")
    print(f"Top 5 Events: {sorted(events.items(), key=lambda x: x[1], reverse=True)[:5]}")
    print("=" * 65)
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate realistic threat alert datasets.")
    parser.add_argument("--count", type=int, default=1000, help="Total number of alert rows (default: 1000)")
    parser.add_argument("--output", type=str, default="enterprise_threat_alerts_1000.csv", help="Output CSV filename")
    args = parser.parse_args()

    generate_dataset(total_alerts=args.count, output_file=args.output)
