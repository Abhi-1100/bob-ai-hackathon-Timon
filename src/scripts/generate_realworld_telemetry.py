"""
Script to generate 1,000 realistic enterprise security alert events.
Simulates real-world threat campaigns (APT29, Lazarus, LockBit 3.0, Volt Typhoon, DDoS, and background noise).
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

# Base timestamp
base_time = datetime(2026, 9, 14, 2, 15, 0)

# Real-world Threat Actor / Suspicious External IP Pools
CAMPAIGNS = [
    {
        "name": "APT29_CozyBear",
        "actor": "APT29 (Nobelium)",
        "src_ips": ["185.220.101.5", "185.220.101.19", "194.26.29.112"],
        "targets": ["10.0.1.15", "10.0.4.5", "10.0.4.6", "10.0.2.10", "10.0.3.10"],
        "stages": [
            ("Reconnaissance", "Low"),
            ("PortScan", "Low"),
            ("BruteForce", "Medium"),
            ("UnauthorizedAccess", "High"),
            ("PowerShell", "High"),
            ("CredentialDumping", "Critical"),
            ("PrivilegeEscalation", "Critical"),
            ("LateralMovement", "Critical"),
            ("C2Beacon", "High"),
            ("DataExfiltration", "Critical"),
        ],
        "weight": 220,
    },
    {
        "name": "Lazarus_FinancialHeist",
        "actor": "Lazarus Group (HIDDEN COBRA)",
        "src_ips": ["175.45.176.8", "103.251.167.22", "210.180.12.89"],
        "targets": ["10.0.1.10", "10.0.1.20", "10.0.2.15", "10.0.3.20"],
        "stages": [
            ("PortScan", "Low"),
            ("SQLInjection", "High"),
            ("RemoteCodeExecution", "Critical"),
            ("CommandExecution", "High"),
            ("MalwareDownload", "High"),
            ("Malware", "Critical"),
            ("CredentialAccess", "High"),
            ("LateralMovement", "High"),
            ("DataExfiltration", "Critical"),
        ],
        "weight": 200,
    },
    {
        "name": "LockBit3_Ransomware",
        "actor": "LockBit 3.0 Affiliate",
        "src_ips": ["45.154.255.89", "91.240.118.140", "193.142.59.33"],
        "targets": ["10.0.1.25", "10.0.5.12", "10.0.5.44", "10.0.4.5", "10.0.3.10"],
        "stages": [
            ("Phishing", "Medium"),
            ("UnauthorizedAccess", "High"),
            ("PrivilegeEscalation", "Critical"),
            ("CredentialDumping", "Critical"),
            ("LateralMovement", "Critical"),
            ("CommandExecution", "High"),
            ("DataExfiltration", "Critical"),
            ("Persistence", "High"),
        ],
        "weight": 180,
    },
    {
        "name": "VoltTyphoon_CriticalInfra",
        "actor": "Volt Typhoon (Living-off-the-Land)",
        "src_ips": ["198.51.100.24", "198.51.100.77", "203.0.113.88"],
        "targets": ["10.0.6.1", "10.0.6.50", "10.0.4.5", "10.0.2.30"],
        "stages": [
            ("Reconnaissance", "Low"),
            ("Enumeration", "Low"),
            ("BruteForce", "Medium"),
            ("UnauthorizedAccess", "High"),
            ("PowerShell", "High"),
            ("CommandExecution", "High"),
            ("LateralMovement", "Critical"),
            ("C2Beacon", "High"),
        ],
        "weight": 160,
    },
    {
        "name": "Mirai_DDoS_Botnet",
        "actor": "Mirai / IoT Botnet Swarm",
        "src_ips": ["92.118.160.45", "185.156.73.120", "167.94.145.96", "162.243.128.91", "198.235.24.50"],
        "targets": ["10.0.1.10", "10.0.1.20", "10.0.1.15", "10.0.6.1"],
        "stages": [
            ("PortScan", "Low"),
            ("DoS", "Medium"),
            ("DoS", "High"),
            ("DDoS", "High"),
            ("DDoS", "Critical"),
        ],
        "weight": 120,
    },
    {
        "name": "Background_OSINT_Scanning",
        "actor": "Internet Background Noise / Shodan / Shadowserver",
        "src_ips": ["71.6.135.131", "198.199.98.246", "64.62.197.93", "89.248.165.74", "194.38.20.10"],
        "targets": ["10.0.1.10", "10.0.1.12", "10.0.1.25", "10.0.1.50"],
        "stages": [
            ("PortScan", "Low"),
            ("Reconnaissance", "Low"),
            ("Enumeration", "Low"),
            ("BruteForce", "Low"),
        ],
        "weight": 120,
    },
]

def generate_alerts(total_count: int = 1000) -> list:
    alerts = []
    current_time = base_time

    # Generate alerts per campaign with realistic temporal progression
    for camp in CAMPAIGNS:
        quota = camp["weight"]
        camp_time = base_time + timedelta(minutes=random.randint(0, 180))

        # Generate sequenced chains
        chains_needed = max(1, quota // len(camp["stages"]))
        for c_idx in range(chains_needed):
            src_ip = random.choice(camp["src_ips"])
            chain_start = camp_time + timedelta(minutes=c_idx * random.randint(15, 35))
            
            for s_idx, (event, sev) in enumerate(camp["stages"]):
                if len(alerts) >= total_count:
                    break
                # Advance 1 to 5 minutes between attack stages in the same chain
                event_time = chain_start + timedelta(minutes=s_idx * random.randint(2, 6), seconds=random.randint(5, 55))
                dst_ip = random.choice(camp["targets"])
                alerts.append({
                    "timestamp": event_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "src_ip": src_ip,
                    "dst_ip": dst_ip,
                    "event": event,
                    "severity": sev,
                })

    # Fill remaining up to 1000 with mixed threat telemetry
    remaining = total_count - len(alerts)
    for _ in range(remaining):
        camp = random.choice(CAMPAIGNS)
        src_ip = random.choice(camp["src_ips"])
        dst_ip = random.choice(camp["targets"])
        stage = random.choice(camp["stages"])
        event_time = base_time + timedelta(minutes=random.randint(10, 720), seconds=random.randint(0, 59))
        alerts.append({
            "timestamp": event_time.strftime("%Y-%m-%d %H:%M:%S"),
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "event": stage[0],
            "severity": stage[1],
        })

    # Sort strictly by timestamp for chronologically realistic log ingestion
    alerts.sort(key=lambda x: x["timestamp"])
    return alerts[:total_count]

def main():
    alerts = generate_alerts(1000)
    print(f"Generated {len(alerts)} alerts.")

    # Paths to output
    base_dir = Path(__file__).resolve().parent.parent.parent
    out_paths = [
        base_dir / "src" / "backend" / "sample_data" / "enterprise_threat_alerts_1000.csv",
        base_dir / "src" / "backend" / "sample_data" / "realworld_threat_alerts_1000.csv",
        base_dir / "src" / "frontend" / "public" / "sample_data" / "enterprise_threat_alerts_1000.csv",
        base_dir / "src" / "frontend" / "public" / "sample_data" / "realworld_threat_alerts_1000.csv",
    ]

    for p in out_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["timestamp", "src_ip", "dst_ip", "event", "severity"])
            writer.writeheader()
            writer.writerows(alerts)
        print(f"Written to {p} ({p.stat().st_size} bytes)")

if __name__ == "__main__":
    main()
