from datetime import datetime, timezone
from typing import Optional

from beanie import Document
from pydantic import BaseModel, Field


class ResumeEvaluation(BaseModel):
    """Estrutura de saída da avaliação feita pela IA."""

    score: int = Field(ge=0, le=100, description="Nota geral do currículo (0-100)")
    strengths: list[str] = Field(default_factory=list, description="Pontos fortes")
    weaknesses: list[str] = Field(default_factory=list, description="Pontos fracos")
    missing_keywords: list[str] = Field(
        default_factory=list, description="Palavras-chave/skills que faltam"
    )
    improvement_tips: list[str] = Field(
        default_factory=list, description="Como melhorar o currículo"
    )
    summary: str = Field(default="", description="Resumo geral em 1-2 frases")


class Resume(Document):
    """Documento salvo no MongoDB via Beanie — é a 'tabela de feedbacks' /
    histórico de consultas. Cada registro fica vinculado ao usuário dono
    (owner_id) para que ninguém perca seu histórico."""

    owner_id: str  # str(User.id) do usuário logado que gerou a avaliação
    candidate_name: Optional[str] = None
    target_role: Optional[str] = None
    raw_text: str
    evaluation: ResumeEvaluation
    ai_provider: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "resumes"


# ---------- Schemas de request/response da API ----------

class ResumeTextIn(BaseModel):
    """Payload quando o usuário cola o texto do currículo diretamente."""

    text: str = Field(min_length=50, description="Texto do currículo")
    candidate_name: Optional[str] = None
    target_role: Optional[str] = Field(
        default=None, description="Vaga/área alvo, ex: 'Desenvolvedor Backend Python'"
    )


class ResumeOut(BaseModel):
    id: str
    owner_id: str
    candidate_name: Optional[str]
    target_role: Optional[str]
    evaluation: ResumeEvaluation
    ai_provider: str
    created_at: datetime

    @classmethod
    def from_document(cls, doc: Resume) -> "ResumeOut":
        return cls(
            id=str(doc.id),
            owner_id=doc.owner_id,
            candidate_name=doc.candidate_name,
            target_role=doc.target_role,
            evaluation=doc.evaluation,
            ai_provider=doc.ai_provider,
            created_at=doc.created_at,
        )
    