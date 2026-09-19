from .state import ThreatWorkflowState

__all__ = [
    "ThreatWorkflowState",
    "compiled_threat_workflow",
    "create_threat_workflow",
    "ThreatWorkflowRunner",
]

def __getattr__(name):
    if name in ("compiled_threat_workflow", "create_threat_workflow", "ThreatWorkflowRunner"):
        from .threat_workflow import (
            compiled_threat_workflow,
            create_threat_workflow,
            ThreatWorkflowRunner,
        )
        return locals()[name]
    raise AttributeError(f"module 'graph' has no attribute '{name}'")
