"""
lg2m/backend/app/services/llm_client.py
Cliente unificado e resiliente para inferência em LLMs (Google Gemini, Groq, OpenAI).
Executa chamadas HTTP com timeout rígido e fallback gracioso sem quebrar o sistema.
"""

import json
import logging
from typing import Optional, Dict, Any
import httpx

from app.core.config import settings

logger = logging.getLogger("lg2m.llm")


def call_llm(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 1500,
    timeout_seconds: float = 25.0
) -> Optional[str]:
    """
    Executa chamada a um dos provedores de LLM configurados, seguindo a prioridade:
    1. Google Gemini API (gemini-flash-lite-latest / gemini-3.8-flash)
    2. Groq (llama-3.1-70b-versatile ou llama-3.3-70b)
    3. OpenAI (gpt-4o-mini)
    
    Retorna None se nenhuma chave estiver configurada ou se houver falha de rede.
    """
    # 1. Provedor Google Gemini (com fallback entre modelos para tolerar picos de demanda 503)
    if settings.GEMINI_API_KEY:
        gemini_models = [
            "gemini-flash-lite-latest",
            "gemini-3.8-flash",
            "gemini-flash-latest",
            "gemini-3.1-flash-lite",
        ]
        for model_name in gemini_models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={settings.GEMINI_API_KEY}"
                payload = {
                    "system_instruction": {
                        "parts": [{"text": system_prompt}]
                    },
                    "contents": [
                        {
                            "role": "user",
                            "parts": [{"text": user_prompt}]
                        }
                    ],
                    "generationConfig": {
                        "temperature": temperature,
                        "maxOutputTokens": max_tokens,
                    }
                }
                with httpx.Client(timeout=timeout_seconds) as client:
                    res = client.post(url, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            text_parts = [p.get("text", "") for p in parts if p.get("text")]
                            full_text = "".join(text_parts).strip()
                            if full_text:
                                logger.info(f"[LLM] Resposta gerada com sucesso via Gemini ({model_name})")
                                return full_text
                    elif res.status_code in (503, 429):
                        logger.warning(f"[Gemini {model_name}] Pico de demanda ({res.status_code}), tentando modelo alternativo...")
                        continue
                    else:
                        logger.warning(f"[Gemini {model_name}] HTTP {res.status_code}: {res.text[:120]}")
            except httpx.TimeoutException:
                logger.warning(f"[Gemini {model_name} Timeout ({timeout_seconds}s)], tentando modelo alternativo...")
                continue
            except Exception as e:
                logger.warning(f"[Gemini {model_name} Call Failed]: {e}")
                continue

    # 2. Provedor Groq Cloud (Altíssima velocidade)
    if settings.GROQ_API_KEY:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.1-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            with httpx.Client(timeout=timeout_seconds) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.warning(f"[Groq API Call Failed]: {e}")

    # 3. Provedor OpenAI
    if settings.OPENAI_API_KEY:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            with httpx.Client(timeout=timeout_seconds) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.warning(f"[OpenAI API Call Failed]: {e}")

    return None
