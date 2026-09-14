"""
Production-Ready MITRE ATT&CK Mapping Service.

Deterministic, dictionary-based mapper that converts alert event names
from attack chains into MITRE ATT&CK technique identifiers.

This module does NOT use LLMs, LangGraph, or any AI.
Mapping is fully deterministic via a configurable knowledge base dictionary.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from database.models import AttackChainDB, MitreMappingDB
from repositories.mitre_repository import MitreRepository
from schemas.mitre import (
    MitreChainMapping,
    MitreTechnique,
    MitreMappingResponse,
    MitreBulkMappingResponse,
)

logger = logging.getLogger("mitre_mapping")


# ---------------------------------------------------------------------------
# MITRE ATT&CK Knowledge Base
# ---------------------------------------------------------------------------
# Extensible dictionary mapping normalized event names to MITRE techniques.
# To add new mappings, simply add entries to this dictionary.
# Format: "EventName": {"technique_id": "Txxxx", "name": "...", "tactic": "...", "description": "..."}

MITRE_KNOWLEDGE_BASE: Dict[str, Dict[str, str]] = {
    # Reconnaissance
    "PortScan": {
        "technique_id": "T1595",
        "name": "Active Scanning",
        "tactic": "Reconnaissance",
        "description": "Adversaries may scan victim IP blocks to gather information that can be used during targeting.",
    },
    "Reconnaissance": {
        "technique_id": "T1595",
        "name": "Active Scanning",
        "tactic": "Reconnaissance",
        "description": "Adversaries may scan victim IP blocks to gather information that can be used during targeting.",
    },
    "Enumeration": {
        "technique_id": "T1046",
        "name": "Network Service Discovery",
        "tactic": "Discovery",
        "description": "Adversaries may attempt to get a listing of services running on remote hosts.",
    },

    # Credential Access
    "BruteForce": {
        "technique_id": "T1110",
        "name": "Brute Force",
        "tactic": "Credential Access",
        "description": "Adversaries may use brute force techniques to gain access to accounts.",
    },
    "CredentialDumping": {
        "technique_id": "T1003",
        "name": "OS Credential Dumping",
        "tactic": "Credential Access",
        "description": "Adversaries may attempt to dump credentials to obtain account login information.",
    },
    "CredentialAccess": {
        "technique_id": "T1555",
        "name": "Credentials from Password Stores",
        "tactic": "Credential Access",
        "description": "Adversaries may search for common password storage locations to obtain user credentials.",
    },

    # Execution
    "CommandExecution": {
        "technique_id": "T1059",
        "name": "Command and Scripting Interpreter",
        "tactic": "Execution",
        "description": "Adversaries may abuse command and script interpreters to execute commands.",
    },
    "RemoteCodeExecution": {
        "technique_id": "T1059",
        "name": "Command and Scripting Interpreter",
        "tactic": "Execution",
        "description": "Adversaries may abuse command and script interpreters to execute commands.",
    },
    "PowerShell": {
        "technique_id": "T1059.001",
        "name": "PowerShell",
        "tactic": "Execution",
        "description": "Adversaries may abuse PowerShell commands and scripts for execution.",
    },

    # Persistence
    "Persistence": {
        "technique_id": "T1547",
        "name": "Boot or Logon Autostart Execution",
        "tactic": "Persistence",
        "description": "Adversaries may configure system settings to automatically execute a program during system boot or logon.",
    },
    "Malware": {
        "technique_id": "T1204",
        "name": "User Execution",
        "tactic": "Execution",
        "description": "Adversaries may rely upon specific actions by a user in order to gain execution.",
    },
    "MalwareDownload": {
        "technique_id": "T1105",
        "name": "Ingress Tool Transfer",
        "tactic": "Command and Control",
        "description": "Adversaries may transfer tools or other files from an external system into a compromised environment.",
    },

    # Privilege Escalation
    "PrivilegeEscalation": {
        "technique_id": "T1068",
        "name": "Exploitation for Privilege Escalation",
        "tactic": "Privilege Escalation",
        "description": "Adversaries may exploit software vulnerabilities in an attempt to elevate privileges.",
    },

    # Lateral Movement
    "LateralMovement": {
        "technique_id": "T1021",
        "name": "Remote Services",
        "tactic": "Lateral Movement",
        "description": "Adversaries may use valid accounts to log into a service for lateral movement.",
    },

    # Command and Control
    "C2Beacon": {
        "technique_id": "T1071",
        "name": "Application Layer Protocol",
        "tactic": "Command and Control",
        "description": "Adversaries may communicate using application layer protocols to avoid detection.",
    },

    # Exfiltration
    "DataExfiltration": {
        "technique_id": "T1041",
        "name": "Exfiltration Over C2 Channel",
        "tactic": "Exfiltration",
        "description": "Adversaries may steal data by exfiltrating it over an existing command and control channel.",
    },

    # Initial Access
    "Phishing": {
        "technique_id": "T1566",
        "name": "Phishing",
        "tactic": "Initial Access",
        "description": "Adversaries may send phishing messages to gain access to victim systems.",
    },
    "SQLInjection": {
        "technique_id": "T1190",
        "name": "Exploit Public-Facing Application",
        "tactic": "Initial Access",
        "description": "Adversaries may attempt to exploit weaknesses in internet-facing systems.",
    },
    "UnauthorizedAccess": {
        "technique_id": "T1078",
        "name": "Valid Accounts",
        "tactic": "Defense Evasion",
        "description": "Adversaries may obtain and abuse credentials of existing accounts.",
    },

    # Impact
    "DDoS": {
        "technique_id": "T1498",
        "name": "Network Denial of Service",
        "tactic": "Impact",
        "description": "Adversaries may perform network denial of service attacks to degrade availability.",
    },
    "DoS": {
        "technique_id": "T1499",
        "name": "Endpoint Denial of Service",
        "tactic": "Impact",
        "description": "Adversaries may perform endpoint denial of service attacks to degrade availability.",
    },
}


class MitreMappingError(Exception):
    """Raised when MITRE mapping encounters a fatal issue."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class MitreMappingService:
    """
    Deterministic MITRE ATT&CK mapping service.

    Converts alert event names from attack chains into structured MITRE technique
    references using an extensible dictionary-based knowledge base.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = MitreRepository(db)
        self.knowledge_base = MITRE_KNOWLEDGE_BASE

    # ------------------------------------------------------------------
    # Core mapping logic
    # ------------------------------------------------------------------
    def map_event(self, event_name: str) -> Optional[MitreTechnique]:
        """Map a single event name to a MITRE ATT&CK technique.

        Returns None if the event is not found in the knowledge base.
        """
        entry = self.knowledge_base.get(event_name)
        if entry:
            return MitreTechnique(
                technique_id=entry["technique_id"],
                name=entry["name"],
                tactic=entry.get("tactic", "Unknown"),
                description=entry.get("description", ""),
                event=event_name,
            )
        return None

    def map_attack_chain(self, chain: AttackChainDB) -> MitreChainMapping:
        """Map all events in an attack chain to MITRE ATT&CK techniques.

        Args:
            chain: An AttackChainDB ORM record with a comma-separated events field.

        Returns:
            MitreChainMapping with techniques and unmapped events.
        """
        events_str = chain.events or ""
        events = [e.strip() for e in events_str.split(",") if e.strip()]

        techniques: List[MitreTechnique] = []
        unmapped_events: List[str] = []
        seen_technique_ids: set = set()

        for event_name in events:
            technique = self.map_event(event_name)
            if technique:
                # Avoid duplicate technique entries per chain
                if technique.technique_id not in seen_technique_ids:
                    techniques.append(technique)
                    seen_technique_ids.add(technique.technique_id)
            else:
                unmapped_events.append(event_name)
                logger.warning(
                    f"Event '{event_name}' in chain '{chain.chain_id}' has no MITRE mapping"
                )

        return MitreChainMapping(
            chain_id=chain.chain_id,
            techniques=techniques,
            techniques_found=len(techniques),
            unmapped_events=unmapped_events,
        )

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def store_mappings(
        self,
        chain: AttackChainDB,
        mapping: MitreChainMapping,
    ) -> int:
        """Persist MITRE technique mappings to the database.

        Deletes existing mappings for the chain before inserting new ones.
        Returns the number of mapping rows inserted.
        """
        # Remove stale mappings
        self.repo.delete_chain_mappings(chain.id)

        if not mapping.techniques:
            return 0

        db_records = [
            MitreMappingDB(
                attack_chain_id=chain.id,
                technique_id=t.technique_id,
                technique_name=t.name,
                tactic=t.tactic,
                event=t.event,
            )
            for t in mapping.techniques
        ]
        count = self.repo.bulk_create_mappings(db_records)
        logger.info(
            f"Stored {count} MITRE mappings for chain '{chain.chain_id}'"
        )
        return count

    def get_chain_mappings(self, chain_id: str) -> MitreChainMapping:
        """Retrieve stored MITRE mappings for a chain by its human-readable ID.

        Raises:
            MitreMappingError: If the chain does not exist.
        """
        chain = (
            self.db.query(AttackChainDB)
            .filter(AttackChainDB.chain_id == chain_id)
            .first()
        )
        if not chain:
            raise MitreMappingError(f"Attack chain '{chain_id}' not found")

        db_mappings = self.repo.get_chain_mappings(chain.id)

        techniques = [
            MitreTechnique(
                technique_id=m.technique_id,
                name=m.technique_name,
                tactic=m.tactic or "Unknown",
                description="",
                event=m.event or "",
            )
            for m in db_mappings
        ]

        return MitreChainMapping(
            chain_id=chain_id,
            techniques=techniques,
            techniques_found=len(techniques),
            unmapped_events=[],
        )

    # ------------------------------------------------------------------
    # High-level orchestration
    # ------------------------------------------------------------------
    def map_single_chain(self, chain_id: str) -> MitreMappingResponse:
        """Map and persist MITRE techniques for a single attack chain.

        Raises:
            MitreMappingError: If the chain does not exist.
        """
        logger.info(f"MITRE mapping started for chain '{chain_id}'")

        chain = (
            self.db.query(AttackChainDB)
            .filter(AttackChainDB.chain_id == chain_id)
            .first()
        )
        if not chain:
            raise MitreMappingError(f"Attack chain '{chain_id}' not found")

        mapping = self.map_attack_chain(chain)
        self.store_mappings(chain, mapping)

        logger.info(
            f"MITRE mapping completed for chain '{chain_id}': "
            f"{mapping.techniques_found} techniques found"
        )

        return MitreMappingResponse(
            success=True,
            chain_id=chain_id,
            techniques_found=mapping.techniques_found,
            unmapped_events=mapping.unmapped_events,
            message="MITRE mapping completed successfully",
        )

    def map_all_chains(self, user_id: Optional[UUID] = None) -> MitreBulkMappingResponse:
        """Map and persist MITRE techniques for stored attack chains, optionally scoped to a user."""
        start_ts = time.perf_counter()
        logger.info(f"MITRE bulk mapping started for attack chains (user_id={user_id})")

        query = self.db.query(AttackChainDB)
        if user_id:
            query = query.filter(AttackChainDB.user_id == user_id)
        chains = query.order_by(AttackChainDB.chain_id).all()
        if not chains:
            raise MitreMappingError("No attack chains found in the database")

        # Clear existing mappings for these specific chains
        chain_ids = [c.id for c in chains]
        self.db.query(MitreMappingDB).filter(MitreMappingDB.attack_chain_id.in_(chain_ids)).delete(synchronize_session=False)

        all_mappings: List[MitreChainMapping] = []
        all_db_records: List[MitreMappingDB] = []

        for chain in chains:
            mapping = self.map_attack_chain(chain)
            for t in mapping.techniques:
                all_db_records.append(
                    MitreMappingDB(
                        attack_chain_id=chain.id,
                        technique_id=t.technique_id,
                        technique_name=t.name,
                        tactic=t.tactic,
                        event=t.event,
                    )
                )
            all_mappings.append(mapping)

        total_techniques = self.repo.bulk_create_mappings(all_db_records)

        elapsed_ms = (time.perf_counter() - start_ts) * 1000

        logger.info(
            f"MITRE bulk mapping completed: {len(chains)} chains, "
            f"{total_techniques} techniques, {elapsed_ms:.2f}ms"
        )

        return MitreBulkMappingResponse(
            success=True,
            chains_mapped=len(chains),
            total_techniques=total_techniques,
            execution_time_ms=round(elapsed_ms, 2),
            mappings=all_mappings,
        )
