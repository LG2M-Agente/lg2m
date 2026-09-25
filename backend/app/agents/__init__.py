"""
lg2m/backend/app/agents/__init__.py
Exportação do motor multiagente e tipos de estado da LG2M.
"""

from app.agents.state import AgentState
from app.agents.graph import multiagent_engine, build_lg2m_graph

__all__ = ["AgentState", "multiagent_engine", "build_lg2m_graph"]
