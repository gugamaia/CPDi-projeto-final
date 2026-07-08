from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.config import settings
from app.models.resume import Resume, ResumeOut, ResumeTextIn
from app.models.user import User
from app.services.evaluator import evaluate_resume_text
from app.services.resume_parser import extract_text_from_upload
from app.services.security import get_current_user

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


@router.post("/evaluate/text", response_model=ResumeOut)
async def evaluate_from_text(
    payload: ResumeTextIn,
    current_user: User = Depends(get_current_user),
):
    """Avalia um currículo enviado como texto colado e salva no histórico do usuário logado."""
    evaluation = await evaluate_resume_text(payload.text, payload.target_role)
    doc = Resume(
        owner_id=str(current_user.id),
        candidate_name=payload.candidate_name or current_user.name,
        target_role=payload.target_role,
        raw_text=payload.text,
        evaluation=evaluation,
        ai_provider=settings.ai_provider,
    )
    await doc.insert()
    return ResumeOut.from_document(doc)


@router.post("/evaluate/file", response_model=ResumeOut)
async def evaluate_from_file(
    file: UploadFile = File(...),
    candidate_name: str | None = Form(default=None),
    target_role: str | None = Form(default=None),
    current_user: User = Depends(get_current_user),
):
    """Avalia um currículo enviado como arquivo (.pdf, .docx ou .txt) e salva no histórico."""
    text = await extract_text_from_upload(file)
    if len(text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Texto extraído é curto demais para avaliar.")

    evaluation = await evaluate_resume_text(text, target_role)
    doc = Resume(
        owner_id=str(current_user.id),
        candidate_name=candidate_name or current_user.name,
        target_role=target_role,
        raw_text=text,
        evaluation=evaluation,
        ai_provider=settings.ai_provider,
    )
    await doc.insert()
    return ResumeOut.from_document(doc)


@router.get("/me/history", response_model=list[ResumeOut])
async def my_history(limit: int = 50, current_user: User = Depends(get_current_user)):
    """Histórico de avaliações (feedbacks) do usuário logado, mais recentes primeiro."""
    docs = (
        await Resume.find(Resume.owner_id == str(current_user.id))
        .sort("-created_at")
        .limit(limit)
        .to_list()
    )
    return [ResumeOut.from_document(d) for d in docs]


@router.get("/{resume_id}", response_model=ResumeOut)
async def get_resume(resume_id: str, current_user: User = Depends(get_current_user)):
    doc = await Resume.get(resume_id)
    if not doc or doc.owner_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Currículo não encontrado.")
    return ResumeOut.from_document(doc)


@router.delete("/{resume_id}", status_code=204)
async def delete_resume(resume_id: str, current_user: User = Depends(get_current_user)):
    doc = await Resume.get(resume_id)
    if not doc or doc.owner_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Currículo não encontrado.")
    await doc.delete()
    