"""
AI Analyst Chat Module.
"""

try:
    from chat.analyst_chat import AnalystChatService
except ImportError:
    from backend.chat.analyst_chat import AnalystChatService

__all__ = ["AnalystChatService"]
