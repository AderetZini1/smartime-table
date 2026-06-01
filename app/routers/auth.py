from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.teacher import Teacher
from app.schemas.teacher import TeacherResponse
from app.auth import verify_password, create_access_token, get_current_teacher

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    # מאפשר התחברות עם teacher_identity או email
    result = await db.execute(
        select(Teacher).where(
            (Teacher.teacher_identity == form_data.username)
            | (Teacher.email == form_data.username)
        )
    )
    teacher = result.scalar_one_or_none()

    if not teacher or not verify_password(form_data.password, teacher.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": teacher.id})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=TeacherResponse)
async def get_me(current_teacher: Teacher = Depends(get_current_teacher)):
    return current_teacher
