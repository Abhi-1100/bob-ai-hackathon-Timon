/**
 * Sentinel Forge — Enterprise Threat Intelligence Fallback & Seed Data
 * Realistic SOC threat campaigns, MITRE matrix mappings, and BLUF summaries.
 */

export const MOCK_ATTACK_CHAINS = [
  {
    chain_id: 'AC001',
    source_ip: '198.51.100.24',
    dest_ips: ['10.0.4.12', '10.0.4.15', '10.0.2.8'],
    severity: 'Critical',
    risk_level: 'Critical',
    risk_score: 94,
    final_score: 94,
    alert_count: 14,
    status: 'Active',
    created_at: '2026-09-13 19:42:10 UTC',
    start_time: '2026-09-13 19:30:00 UTC',
    end_time: '2026-09-13 19:42:10 UTC',
    mitre_techniques: [
      { technique_id: 'T1595', name: 'Active Scanning', tactic: 'Reconnaissance', count: 4 },
      { technique_id: 'T1110', name: 'Brute Force', tactic: 'Credential Access', count: 6 },
      { technique_id: 'T1003', name: 'OS Credential Dumping', tactic: 'Credential Access', count: 2 },
      { technique_id: 'T1021', name: 'Remote Services (RDP/SSH)', tactic: 'Lateral Movement', count: 2 },
    ],
    events: [
      { timestamp: '2026-09-13 19:30:12', event: 'PortScan', severity: 'Low', src_ip: '198.51.100.24', dst_ip: '10.0.4.12', protocol: 'TCP/22' },
      { timestamp: '2026-09-13 19:33:45', event: 'SSH_BruteForce', severity: 'High', src_ip: '198.51.100.24', dst_ip: '10.0.4.12', protocol: 'SSH' },
      { timestamp: '2026-09-13 19:37:02', event: 'CredentialDumping', severity: 'Critical', src_ip: '10.0.4.12', dst_ip: '10.0.4.12', protocol: 'Host' },
      { timestamp: '2026-09-13 19:40:15', event: 'LateralMovement_SSH', severity: 'High', src_ip: '10.0.4.12', dst_ip: '10.0.4.15', protocol: 'SSH' },
      { timestamp: '2026-09-13 19:42:10', event: 'DataStaging', severity: 'Critical', src_ip: '10.0.4.15', dst_ip: '10.0.2.8', protocol: 'SMB' },
    ],
    score_breakdown: {
      base_event_score: 42,
      mitre_score: 28,
      kill_chain_bonus: 24,
      final_score: 94
    },
    recommendations: {
      immediate_actions: [
        'Immediately quarantine host 10.0.4.12 and 10.0.4.15 from the production VLAN.',
        'Null-route external attacker IP 198.51.100.24 on perimeter firewalls.',
        'Invalidate all active Kerberos TGTs and service tickets for root & service accounts.'
      ],
      containment_actions: [
        'Enforce micro-segmentation between subnet 10.0.4.0/24 and database tier 10.0.2.0/24.',
        'Terminate active SSH sessions originating from compromised jump host 10.0.4.12.'
      ],
      investigation_actions: [
        'Collect memory forensics dump from 10.0.4.12 to extract injected beacon binaries.',
        'Review authentication logs on 10.0.2.8 for unauthorized read queries on payroll DB.'
      ],
      prevention_actions: [
        'Implement Hardware MFA (FIDO2) on all jump host external bastion interfaces.',
        'Deploy behavioral LSASS memory protection rules on all Linux/Windows endpoints.'
      ]
    },
    report: {
      executive_summary: 'Critical cross-domain intrusion detected targeting internal database infrastructure via external SSH brute-force and rapid credential dumping.',
      attack_overview: 'Threat actor initiated automated port sweeps from 198.51.100.24, gained access via weak SSH credentials, dumped system hashes, and pivoted across internal subnets within 12 minutes.',
      affected_assets: 'Jump Host (10.0.4.12), App Server (10.0.4.15), Core Financial DB (10.0.2.8).',
      mitre_summary: 'Correlated across 4 ATT&CK stages: Reconnaissance (T1595), Credential Access (T1110, T1003), and Lateral Movement (T1021).',
      threat_level: 'Critical',
      conclusion: 'Immediate containment executed. No evidence of bulk data egress observed prior to isolation.'
    }
  },
  {
    chain_id: 'AC002',
    source_ip: '203.0.113.88',
    dest_ips: ['10.0.1.50'],
    severity: 'Critical',
    risk_level: 'Critical',
    risk_score: 91,
    final_score: 91,
    alert_count: 9,
    status: 'Investigating',
    created_at: '2026-09-13 18:15:30 UTC',
    start_time: '2026-09-13 18:02:00 UTC',
    end_time: '2026-09-13 18:15:30 UTC',
    mitre_techniques: [
      { technique_id: 'T1190', name: 'Exploit Public-Facing Application', tactic: 'Initial Access', count: 3 },
      { technique_id: 'T1059', name: 'Command & Scripting Interpreter', tactic: 'Execution', count: 4 },
      { technique_id: 'T1505', name: 'Server Software Component: Web Shell', tactic: 'Persistence', count: 2 },
    ],
    events: [
      { timestamp: '2026-09-13 18:02:11', event: 'Web_Exploit_Attempt', severity: 'High', src_ip: '203.0.113.88', dst_ip: '10.0.1.50', protocol: 'HTTPS' },
      { timestamp: '2026-09-13 18:07:33', event: 'WebShell_Dropped', severity: 'Critical', src_ip: '203.0.113.88', dst_ip: '10.0.1.50', protocol: 'HTTP' },
      { timestamp: '2026-09-13 18:15:30', event: 'Reverse_Shell_Spawned', severity: 'Critical', src_ip: '10.0.1.50', dst_ip: '203.0.113.88', protocol: 'TCP/4444' },
    ],
    score_breakdown: { base_event_score: 40, mitre_score: 26, kill_chain_bonus: 25, final_score: 91 },
    recommendations: {
      immediate_actions: ['Sever egress connection to 203.0.113.88 on port 4444.', 'Take web server 10.0.1.50 offline for forensic triage.'],
      containment_actions: ['Revoke web service service-account database tokens.'],
      investigation_actions: ['Analyze Apache access logs for URI patterns matching CVE-2024-4577.'],
      prevention_actions: ['Apply WAF virtual patch for remote code execution signatures.']
    }
  },
  {
    chain_id: 'AC003',
    source_ip: '185.220.101.5',
    dest_ips: ['10.0.3.100', '10.0.3.104'],
    severity: 'High',
    risk_level: 'High',
    risk_score: 84,
    final_score: 84,
    alert_count: 8,
    status: 'Investigating',
    created_at: '2026-09-13 17:05:00 UTC',
    start_time: '2026-09-13 16:50:00 UTC',
    end_time: '2026-09-13 17:05:00 UTC',
    mitre_techniques: [
      { technique_id: 'T1566', name: 'Phishing: Spearphishing Attachment', tactic: 'Initial Access', count: 2 },
      { technique_id: 'T1059', name: 'Command & Scripting Interpreter: PowerShell', tactic: 'Execution', count: 4 },
      { technique_id: 'T1071', name: 'Application Layer Protocol: C2', tactic: 'Command and Control', count: 2 },
    ],
    events: [
      { timestamp: '2026-09-13 16:50:20', event: 'Malicious_Email_Attachment', severity: 'High', src_ip: '185.220.101.5', dst_ip: '10.0.3.100', protocol: 'SMTP' },
      { timestamp: '2026-09-13 16:55:40', event: 'Suspicious_PowerShell_Execution', severity: 'High', src_ip: '10.0.3.100', dst_ip: '10.0.3.100', protocol: 'Host' },
      { timestamp: '2026-09-13 17:05:00', event: 'Outbound_Beacon_DNS_Tunnel', severity: 'Critical', src_ip: '10.0.3.100', dst_ip: '185.220.101.5', protocol: 'DNS' },
    ],
    score_breakdown: { base_event_score: 38, mitre_score: 24, kill_chain_bonus: 22, final_score: 84 },
    recommendations: {
      immediate_actions: ['Block DNS queries to malicious root domains at corporate resolvers.', 'Isolate workstation 10.0.3.100.'],
      containment_actions: ['Disable user Active Directory account associated with phishing click.'],
      investigation_actions: ['Identify all internal recipients of the malicious campaign.'],
      prevention_actions: ['Update secure email gateway attachment sandbox rules.']
    }
  },
  {
    chain_id: 'AC004',
    source_ip: '45.154.255.99',
    dest_ips: ['10.0.8.20'],
    severity: 'High',
    risk_level: 'High',
    risk_score: 79,
    final_score: 79,
    alert_count: 6,
    status: 'Active',
    created_at: '2026-09-13 16:10:00 UTC',
    start_time: '2026-09-13 16:00:00 UTC',
    end_time: '2026-09-13 16:10:00 UTC',
    mitre_techniques: [
      { technique_id: 'T1498', name: 'Network Denial of Service', tactic: 'Impact', count: 4 },
      { technique_id: 'T1046', name: 'Network Service Discovery', tactic: 'Discovery', count: 2 },
    ],
    events: [
      { timestamp: '2026-09-13 16:00:15', event: 'SynFlood_Detected', severity: 'High', src_ip: '45.154.255.99', dst_ip: '10.0.8.20', protocol: 'TCP/SYN' },
      { timestamp: '2026-09-13 16:10:00', event: 'Port_Scan_Telemetry', severity: 'Medium', src_ip: '45.154.255.99', dst_ip: '10.0.8.20', protocol: 'TCP' },
    ],
    score_breakdown: { base_event_score: 35, mitre_score: 24, kill_chain_bonus: 20, final_score: 79 },
    recommendations: {
      immediate_actions: ['Enable upstream ISP scrubbing for edge router 10.0.8.20.'],
      containment_actions: ['Rate limit incoming SYN packets to 500 pps.'],
      investigation_actions: ['Check BGP route telemetry for route hijacking indicators.'],
      prevention_actions: ['Deploy cloud DDoS protection shield.']
    }
  },
  {
    chain_id: 'AC005',
    source_ip: '192.0.2.144',
    dest_ips: ['10.0.5.88'],
    severity: 'Medium',
    risk_level: 'Medium',
    risk_score: 62,
    final_score: 62,
    alert_count: 5,
    status: 'Mitigated',
    created_at: '2026-09-13 14:20:00 UTC',
    start_time: '2026-09-13 14:10:00 UTC',
    end_time: '2026-09-13 14:20:00 UTC',
    mitre_techniques: [
      { technique_id: 'T1078', name: 'Valid Accounts', tactic: 'Defense Evasion', count: 3 },
      { technique_id: 'T1087', name: 'Account Discovery', tactic: 'Discovery', count: 2 },
    ],
    events: [
      { timestamp: '2026-09-13 14:10:05', event: 'Unusual_Geo_Login', severity: 'Medium', src_ip: '192.0.2.144', dst_ip: '10.0.5.88', protocol: 'VPN' },
      { timestamp: '2026-09-13 14:20:00', event: 'AD_Enumeration', severity: 'Medium', src_ip: '10.0.5.88', dst_ip: '10.0.5.88', protocol: 'LDAP' },
    ],
    score_breakdown: { base_event_score: 30, mitre_score: 20, kill_chain_bonus: 12, final_score: 62 },
    recommendations: {
      immediate_actions: ['Force password reset on compromised VPN user account.'],
      containment_actions: ['Revoke active session tokens.'],
      investigation_actions: ['Confirm whether user was traveling or if credentials were leaked.'],
      prevention_actions: ['Enforce conditional access policies blocking non-compliant regions.']
    }
  },
  {
    chain_id: 'AC006',
    source_ip: '198.51.100.9',
    dest_ips: ['10.0.6.14'],
    severity: 'Low',
    risk_level: 'Low',
    risk_score: 38,
    final_score: 38,
    alert_count: 3,
    status: 'Closed',
    created_at: '2026-09-13 12:00:00 UTC',
    start_time: '2026-09-13 11:50:00 UTC',
    end_time: '2026-09-13 12:00:00 UTC',
    mitre_techniques: [
      { technique_id: 'T1046', name: 'Network Service Discovery', tactic: 'Discovery', count: 3 }
    ],
    events: [
      { timestamp: '2026-09-13 11:50:00', event: 'ICMP_Ping_Sweep', severity: 'Low', src_ip: '198.51.100.9', dst_ip: '10.0.6.14', protocol: 'ICMP' }
    ],
    score_breakdown: { base_event_score: 20, mitre_score: 10, kill_chain_bonus: 8, final_score: 38 },
    recommendations: {
      immediate_actions: ['Monitor perimeter log alerts for secondary activity.'],
      containment_actions: ['No host isolation required at this tier.'],
      investigation_actions: ['Correlate IP reputation against public OSINT feeds.'],
      prevention_actions: ['Disable ICMP responses on edge routers.']
    }
  }
];

export const MOCK_KPIS = {
  total_alerts: '1,428',
  total_alerts_trend: '+14.2%',
  total_chains: '18',
  total_chains_trend: '+4 new',
  critical_incidents: '4',
  critical_trend: 'Urgent SLA',
  high_risk_incidents: '7',
  high_risk_trend: '+2 today',
  mitre_techniques: '24',
  mitre_tactics: '8 tactics',
  avg_risk_score: '74.8',
  avg_risk_trend: 'Elevated'
};

export const MOCK_RISK_DISTRIBUTION = {
  critical: 4,
  high: 7,
  medium: 5,
  low: 2
};

export const MOCK_TREND_DATA = [
  { day: 'Mon', alerts: 142, incidents: 2, score: 62 },
  { day: 'Tue', alerts: 210, incidents: 3, score: 68 },
  { day: 'Wed', alerts: 340, incidents: 5, score: 79 },
  { day: 'Thu', alerts: 280, incidents: 4, score: 71 },
  { day: 'Fri', alerts: 410, incidents: 7, score: 85 },
  { day: 'Sat', alerts: 320, incidents: 3, score: 74 },
  { day: 'Sun', alerts: 190, incidents: 2, score: 65 }
];

export const MOCK_MITRE_FREQUENCY = [
  { technique: 'T1110 (Brute Force)', count: 48, tactic: 'Credential Access', level: 'Critical' },
  { technique: 'T1595 (Active Scan)', count: 42, tactic: 'Reconnaissance', level: 'Medium' },
  { technique: 'T1190 (Exploit Public)', count: 35, tactic: 'Initial Access', level: 'Critical' },
  { technique: 'T1059 (Command Interp)', count: 29, tactic: 'Execution', level: 'High' },
  { technique: 'T1003 (OS Cred Dump)', count: 24, tactic: 'Credential Access', level: 'Critical' },
  { technique: 'T1021 (Remote Serv)', count: 19, tactic: 'Lateral Movement', level: 'High' },
  { technique: 'T1071 (App Layer C2)', count: 16, tactic: 'C2', level: 'High' },
  { technique: 'T1486 (Data Encrypted)', count: 8, tactic: 'Impact', level: 'Critical' }
];

export const MOCK_HOURLY_VOLUME = [
  { hour: '00:00', volume: 42 },
  { hour: '03:00', volume: 28 },
  { hour: '06:00', volume: 55 },
  { hour: '09:00', volume: 180 },
  { hour: '12:00', volume: 240 },
  { hour: '15:00', volume: 310 },
  { hour: '18:00', volume: 260 },
  { hour: '21:00', volume: 150 }
];

export const MOCK_MITRE_MATRIX = [
  {
    tactic: 'Reconnaissance',
    techniques: [
      { id: 'T1595', name: 'Active Scanning', count: 42, severity: 'medium' },
      { id: 'T1592', name: 'Gather Victim Host Info', count: 12, severity: 'low' },
      { id: 'T1590', name: 'Gather Network Info', count: 18, severity: 'medium' }
    ]
  },
  {
    tactic: 'Initial Access',
    techniques: [
      { id: 'T1190', name: 'Exploit Public App', count: 35, severity: 'critical' },
      { id: 'T1566', name: 'Phishing', count: 14, severity: 'high' },
      { id: 'T1078', name: 'Valid Accounts', count: 9, severity: 'high' }
    ]
  },
  {
    tactic: 'Execution',
    techniques: [
      { id: 'T1059', name: 'Command & Scripting', count: 29, severity: 'high' },
      { id: 'T1204', name: 'User Execution', count: 11, severity: 'medium' },
      { id: 'T1053', name: 'Scheduled Task', count: 6, severity: 'low' }
    ]
  },
  {
    tactic: 'Credential Access',
    techniques: [
      { id: 'T1110', name: 'Brute Force', count: 48, severity: 'critical' },
      { id: 'T1003', name: 'OS Credential Dumping', count: 24, severity: 'critical' },
      { id: 'T1555', name: 'Credentials from Password Stores', count: 7, severity: 'high' }
    ]
  },
  {
    tactic: 'Lateral Movement',
    techniques: [
      { id: 'T1021', name: 'Remote Services', count: 19, severity: 'high' },
      { id: 'T1550', name: 'Use Alternate Auth Material', count: 8, severity: 'critical' },
      { id: 'T1570', name: 'Lateral Tool Transfer', count: 15, severity: 'medium' }
    ]
  },
  {
    tactic: 'Command and Control',
    techniques: [
      { id: 'T1071', name: 'Application Layer Protocol', count: 16, severity: 'high' },
      { id: 'T1573', name: 'Encrypted Channel', count: 12, severity: 'medium' },
      { id: 'T1090', name: 'Proxy / Tunnel', count: 8, severity: 'medium' }
    ]
  },
  {
    tactic: 'Impact',
    techniques: [
      { id: 'T1486', name: 'Data Encrypted for Impact', count: 8, severity: 'critical' },
      { id: 'T1498', name: 'Network Denial of Service', count: 14, severity: 'high' },
      { id: 'T1565', name: 'Data Manipulation', count: 3, severity: 'critical' }
    ]
  }
];

export const MOCK_CHAT_SESSIONS = [
  { id: 'sess-01', title: 'Critical SSH Pivot Investigation (AC001)', time: '10 mins ago', count: 4 },
  { id: 'sess-02', title: 'Web Shell & RCE Vulnerability Scan', time: '1 hour ago', count: 6 },
  { id: 'sess-03', title: 'MITRE T1110 Campaign Correlation', time: '3 hours ago', count: 2 },
  { id: 'sess-04', title: 'Executive BLUF Summary Generator', time: 'Yesterday', count: 5 }
];
