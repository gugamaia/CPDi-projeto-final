"""
Camada de abstração de provedores de IA.

Ideia: o resto do app (evaluator.py) só conhece `get_ai_provider()`.
Trocar de provedor = mudar AI_PROVIDER no .env, nada de código muda.
"""

import json
from abc import ABC, abstractmethod

import httpx

from app.config import settings


SYSTEM_PROMPT = """Você é um recrutador técnico sênior e especialista em RH.
Analise o currículo enviado e devolva SOMENTE um JSON válido (sem markdown,
sem ```json, sem texto antes ou depois), no seguinte formato exato:

{
  "score": <inteiro de 0 a 100>,
  "strengths": ["ponto forte 1", "ponto forte 2", ...],
  "weaknesses": ["ponto fraco 1", "ponto fraco 2", ...],
  "missing_keywords": ["palavra-chave 1", "palavra-chave 2", ...],
  "improvement_tips": ["dica 1", "dica 2", ...],
  "summary": "resumo geral em até 2 frases"
}

Seja específico e construtivo. Se uma vaga/área alvo for informada, avalie a
aderência do currículo a essa vaga e sugira palavras-chave da área que estão
faltando. Se não houver vaga alvo, avalie de forma geral (clareza, impacto,
estrutura, quantificação de resultados, erros comuns)."""


def _build_user_prompt(resume_text: str, target_role: str | None) -> str:
    role_line = f"\nVaga/área alvo informada: {target_role}\n" if target_role else ""
    return f"{role_line}\nCurrículo a ser avaliado:\n---\n{resume_text}\n---"


def _extract_json(raw: str) -> dict:
    """IAs às vezes envolvem o JSON em ```json ... ``` mesmo quando pedimos pra não fazer isso."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()
    return json.loads(cleaned)


class AIProvider(ABC):
    name: str

    @abstractmethod
    async def evaluate(self, resume_text: str, target_role: str | None) -> dict:
        ...


class OpenAIProvider(AIProvider):
    name = "openai"

    async def evaluate(self, resume_text: str, target_role: str | None) -> dict:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={
                    "model": settings.openai_model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": _build_user_prompt(resume_text, target_role)},
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.3,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return _extract_json(content)


class GeminiProvider(AIProvider):
    name = "gemini"

    async def evaluate(self, resume_text: str, target_role: str | None) -> dict:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
        )
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                url,
                json={
                    "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                    "contents": [
                        {
                            "role": "user",
                            "parts": [{"text": _build_user_prompt(resume_text, target_role)}],
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.3,
                        "responseMimeType": "application/json",
                    },
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            return _extract_json(content)


class ClaudeProvider(AIProvider):
    name = "claude"

    async def evaluate(self, resume_text: str, target_role: str | None) -> dict:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": settings.anthropic_model,
                    "max_tokens": 1500,
                    "system": SYSTEM_PROMPT,
                    "messages": [
                        {"role": "user", "content": _build_user_prompt(resume_text, target_role)}
                    ],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["content"][0]["text"]
            return _extract_json(content)


_PROVIDERS: dict[str, type[AIProvider]] = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "claude": ClaudeProvider,
}


def get_ai_provider() -> AIProvider:
    provider_cls = _PROVIDERS.get(settings.ai_provider.lower())
    if not provider_cls:
        raise ValueError(
            f"AI_PROVIDER='{settings.ai_provider}' inválido. Use: openai, gemini ou claude."
        )
    return provider_cls()
