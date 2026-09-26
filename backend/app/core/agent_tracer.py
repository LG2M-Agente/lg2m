"""
lg2m/backend/app/core/agent_tracer.py
Bus de eventos de observabilidade para o grafo multiagente LG2M.
Transmite em tempo real via WebSocket para o Visualizador Agêntico.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional
from datetime import datetime


class AgentEventBus:
    """
    Singleton que mantém uma fila de eventos de rastreamento dos agentes.
    Cada execução do LangGraph publica eventos aqui; o endpoint WebSocket
    os consome e transmite ao visualizador.
    """

    def __init__(self):
        # Lista de asyncio.Queue — uma por cliente WebSocket conectado
        self._queues: List[asyncio.Queue] = []
        # Últimos N eventos para replay ao conectar
        self._recent_events: List[Dict] = []
        self._MAX_RECENT = 100

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._queues.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self._queues:
            self._queues.remove(q)

    def get_recent_events(self) -> List[Dict]:
        return list(self._recent_events)

    def publish(self, event: Dict):
        """Publica evento de forma síncrona (chamado de dentro dos nós do LangGraph)."""
        event.setdefault("ts", datetime.utcnow().isoformat() + "Z")
        self._recent_events.append(event)
        if len(self._recent_events) > self._MAX_RECENT:
            self._recent_events.pop(0)

        for q in self._queues:
            # Coloca na fila de forma thread-safe
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.call_soon_threadsafe(q.put_nowait, event)
                else:
                    q.put_nowait(event)
            except Exception:
                pass

    def emit_node_start(
        self,
        node: str,
        label: str,
        state_snapshot: Optional[Dict] = None,
        tools: Optional[List[str]] = None,
        inputs: Optional[Dict] = None,
    ):
        self.publish({
            "type": "node_start",
            "node": node,
            "label": label,
            "state": state_snapshot or {},
            "tools": tools or [],
            "inputs": inputs or {},
            "ts": datetime.utcnow().isoformat() + "Z",
        })

    def emit_node_end(
        self,
        node: str,
        label: str,
        duration_ms: float,
        output_summary: Optional[str] = None,
        state_snapshot: Optional[Dict] = None,
        status: str = "done",  # "done" | "rejected"
        outputs: Optional[Dict] = None,
    ):
        self.publish({
            "type": "node_end",
            "node": node,
            "label": label,
            "duration_ms": round(duration_ms, 1),
            "output_summary": output_summary or "",
            "state": state_snapshot or {},
            "status": status,
            "outputs": outputs or {},
            "ts": datetime.utcnow().isoformat() + "Z",
        })

    def emit_edge(self, from_node: str, to_node: str, label: str = ""):
        self.publish({
            "type": "edge",
            "from": from_node,
            "to": to_node,
            "label": label,
            "ts": datetime.utcnow().isoformat() + "Z",
        })

    def emit_graph_start(
        self,
        intent: str,
        certame: str = "",
        estilo: str = "",
        # Contexto rico do trigger (o que o usuário fez no frontend)
        trigger_action: str = "",      # "RESPOSTA_MARCADA" | "CHAT_PERGUNTA" | "BUSCA_SEMANTICA" | "STREAM_MENTORIA"
        trigger_detail: str = "",      # Descrição legível: "Alternativa (C) marcada"
        question_id: str = "",
        question_discipline: str = "",
        question_subject: str = "",
        question_preview: str = "",    # Primeiros ~80 chars do enunciado
        user_message: str = "",        # Mensagem do usuário no chat
        alternative_selected: str = "",
    ):
        self.publish({
            "type": "graph_start",
            "intent": intent,
            "certame": certame,
            "estilo": estilo,
            "trigger_action": trigger_action,
            "trigger_detail": trigger_detail,
            "question_id": question_id,
            "question_discipline": question_discipline,
            "question_subject": question_subject,
            "question_preview": question_preview,
            "user_message": user_message,
            "alternative_selected": alternative_selected,
            "ts": datetime.utcnow().isoformat() + "Z",
        })

    def emit_graph_end(self, total_ms: float, guardrail_status: str = "APPROVED"):
        self.publish({
            "type": "graph_end",
            "total_ms": round(total_ms, 1),
            "guardrail_status": guardrail_status,
            "ts": datetime.utcnow().isoformat() + "Z",
        })

    def emit_tool_call(self, node: str, tool_name: str, args_summary: str = ""):
        self.publish({
            "type": "tool_call",
            "node": node,
            "tool": tool_name,
            "args": args_summary,
            "ts": datetime.utcnow().isoformat() + "Z",
        })

    def emit_guardrail_event(self, status: str, reason: str = "", attempt: int = 1):
        self.publish({
            "type": "guardrail_event",
            "status": status,          # PENDING | APPROVED | REJECTED
            "reason": reason,
            "attempt": attempt,
            "ts": datetime.utcnow().isoformat() + "Z",
        })


# Singleton global
tracer = AgentEventBus()
