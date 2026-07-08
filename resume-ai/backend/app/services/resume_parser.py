"""Extrai texto de arquivos de currículo enviados (PDF ou DOCX)."""

import io

from docx import Document as DocxDocument
from fastapi import HTTPException, UploadFile
from pypdf import PdfReader


async def extract_text_from_upload(file: UploadFile) -> str:
    filename = (file.filename or "").lower()
    content = await file.read()

    if filename.endswith(".pdf"):
        return _extract_pdf(content)
    if filename.endswith(".docx"):
        return _extract_docx(content)
    if filename.endswith(".txt"):
        return content.decode("utf-8", errors="ignore")

    raise HTTPException(
        status_code=400,
        detail="Formato não suportado. Envie um arquivo .pdf, .docx ou .txt.",
    )


def _extract_pdf(content: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Falha ao ler PDF: {exc}") from exc

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="Não foi possível extrair texto do PDF (pode ser um PDF escaneado/imagem).",
        )
    return text


def _extract_docx(content: bytes) -> str:
    try:
        doc = DocxDocument(io.BytesIO(content))
        text = "\n".join(p.text for p in doc.paragraphs)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Falha ao ler DOCX: {exc}") from exc

    if not text.strip():
        raise HTTPException(status_code=400, detail="O documento DOCX parece estar vazio.")
    return text
