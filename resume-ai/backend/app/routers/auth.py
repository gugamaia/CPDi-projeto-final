from fastapi import APIRouter, Depends, HTTPException, status

from app.models.user import Token, User, UserCreate, UserLogin, UserOut
from app.services.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate):
    existing = await User.find_one(User.email == payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Já existe uma conta com este e-mail.")

    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    await user.insert()

    token = create_access_token(str(user.id))
    return Token(access_token=token, user=UserOut.from_document(user))


@router.post("/login", response_model=Token)
async def login(payload: UserLogin):
    user = await User.find_one(User.email == payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")

    token = create_access_token(str(user.id))
    return Token(access_token=token, user=UserOut.from_document(user))


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return UserOut.from_document(current_user)
