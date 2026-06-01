from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.student_group import StudentGroup
from app.models.teacher import Teacher
from app.schemas.student_group import StudentGroupCreate, StudentGroupUpdate, StudentGroupResponse
from app.auth import get_current_teacher, get_current_admin

router = APIRouter(prefix="/student-groups", tags=["student-groups"])


@router.get("/", response_model=List[StudentGroupResponse])
async def list_student_groups(
    db: AsyncSession = Depends(get_db),
    _: Teacher = Depends(get_current_teacher),
):
    result = await db.execute(select(StudentGroup).order_by(StudentGroup.group_name))
    return result.scalars().all()


@router.get("/{group_id}", response_model=StudentGroupResponse)
async def get_student_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    _: Teacher = Depends(get_current_teacher),
):
    return await _get_or_404(db, group_id)


@router.post("/", response_model=StudentGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_student_group(
    data: StudentGroupCreate,
    db: AsyncSession = Depends(get_db),
    _: Teacher = Depends(get_current_admin),
):
    group = StudentGroup(
        group_name=data.group_name,
        student_count=data.student_count,
        home_room_id=data.home_room_id,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


@router.patch("/{group_id}", response_model=StudentGroupResponse)
async def update_student_group(
    group_id: int,
    data: StudentGroupUpdate,
    db: AsyncSession = Depends(get_db),
    _: Teacher = Depends(get_current_admin),
):
    group = await _get_or_404(db, group_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(group, field, value)
    await db.commit()
    await db.refresh(group)
    return group


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    _: Teacher = Depends(get_current_admin),
):
    group = await _get_or_404(db, group_id)
    await db.delete(group)
    await db.commit()


async def _get_or_404(db: AsyncSession, group_id: int) -> StudentGroup:
    result = await db.execute(select(StudentGroup).where(StudentGroup.id == group_id))
    group = result.scalar_one_or_none()
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student group not found")
    return group
