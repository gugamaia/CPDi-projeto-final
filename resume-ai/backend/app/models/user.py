from datetime import datetime, timezone

from beanie import Document, Indexed
from pydantic import BaseModel, EmailStr, Field


class User(Document):
    """Usuário da plataforma. Cada avaliação de currículo fica vinculada a um user_id."""

    name: str
    email: Indexed(EmailStr, unique=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"


# ---------- Schemas de request/response ----------

class UserCreate(BaseModel):
    name: str = Field(min_length=2)
    email: EmailStr
    password: str = Field(min_length=6, description="Mínimo de 6 caracteres")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    created_at: datetime

    @classmethod
    def from_document(cls, doc: User) -> "UserOut":
        return cls(id=str(doc.id), name=doc.name, email=doc.email, created_at=doc.created_at)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
    