from fastapi import HTTPException

from app.models.resume import ResumeEvaluation
from app.services.ai_providers import get_ai_provider


async def evaluate_resume_text(resume_text: str, target_role: str | None) -> ResumeEvaluation:
    provider = get_ai_provider()
    try:
        raw = await provider.evaluate(resume_text, target_role)
        return ResumeEvaluation(**raw)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Erro ao avaliar currículo com o provedor '{provider.name}': {exc}",
        ) from exc
    