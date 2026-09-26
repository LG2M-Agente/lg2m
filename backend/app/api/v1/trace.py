"""
lg2m/backend/app/api/v1/trace.py
Endpoint WebSocket para o Visualizador Agêntico em tempo real.
Conecte o visualizador em: ws://localhost:8000/api/v1/trace/ws
"""

import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from app.core.agent_tracer import tracer

router = APIRouter(prefix="/trace", tags=["Observabilidade Agêntica"])


@router.websocket("/ws")
async def agent_trace_websocket(websocket: WebSocket):
    """
    WebSocket que transmite em tempo real cada evento do grafo LangGraph:
    - node_start / node_end: ativação e conclusão de cada agente
    - edge: transição entre agentes
    - tool_call: chamada de ferramenta dentro de um agente
    - guardrail_event: resultado da auditoria do Guardrail
    - graph_start / graph_end: início e fim de uma execução completa
    """
    await websocket.accept()

    # Envia replay dos últimos eventos ao conectar (para não perder o contexto)
    recent = tracer.get_recent_events()
    if recent:
        await websocket.send_text(json.dumps({
            "type": "replay",
            "events": recent
        }, ensure_ascii=False))

    # Inscreve na fila de eventos
    q = tracer.subscribe()

    try:
        await websocket.send_text(json.dumps({
            "type": "connected",
            "message": "LG2M Agent Tracer conectado. Aguardando execuções do grafo...",
        }))

        while True:
            # Aguarda próximo evento (com timeout para keepalive)
            try:
                event = await asyncio.wait_for(q.get(), timeout=15.0)
                await websocket.send_text(json.dumps(event, ensure_ascii=False, default=str))
            except asyncio.TimeoutError:
                # Keepalive ping
                await websocket.send_text(json.dumps({"type": "ping"}))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        except Exception:
            pass
    finally:
        tracer.unsubscribe(q)


@router.get("/events")
def get_recent_events():
    """Retorna os últimos 100 eventos de trace (útil para debug via HTTP)."""
    return JSONResponse(content={"events": tracer.get_recent_events()})


@router.get("/health")
def trace_health():
    return {"status": "ok", "subscribers": len(tracer._queues)}
