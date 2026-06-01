from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.teacher_constraint import TeacherConstraint
from app.models.teacher import Teacher
from app.schemas.teacher_constraint import (
    TeacherConstraintCreate,
    TeacherConstraintUpdate,
    TeacherConstraintResponse,
)
from app.auth import get_current_teacher

router = APIRouter(prefix="/teacher-constraints", tags=["teacher-constraints"])


@router.get("/", response_model=List[TeacherConstraintResponse])
async def list_constraints(
    db: AsyncSession = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    if current_teacher.is_admin:
        result = await db.execute(select(TeacherConstraint))
    else:
        result = await db.execute(
            select(TeacherConstraint).where(TeacherConstraint.teacher_id == current_teacher.id)
        )
    return result.scalars().all()


@router.get("/{constraint_id}", response_model=TeacherConstraintResponse)
async def get_constraint(
    constraint_id: int,
    db: AsyncSession = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    constraint = await _get_or_404(db, constraint_id)
    _check_ownership(constraint, current_teacher)
    return constraint


@router.post("/", response_model=TeacherConstraintResponse, status_code=status.HTTP_201_CREATED)
async def create_constraint(
    data: TeacherConstraintCreate,
    db: AsyncSession = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    if not current_teacher.is_admin and data.teacher_id != current_teacher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create constraints for yourself",
        )
    constraint = TeacherConstraint(
        teacher_id=data.teacher_id,
        timeslot_id=data.timeslot_id,
        weight=data.weight,
    )
    db.add(constraint)
    await db.commit()
    await db.refresh(constraint)
    return constraint


@router.patch("/{constraint_id}", response_model=TeacherConstraintResponse)
async def update_constraint(
    constraint_id: int,
    data: TeacherConstraintUpdate,
    db: AsyncSession = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    constraint = await _get_or_404(db, constraint_id)
    _check_ownership(constraint, current_teacher)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(constraint, field, value)
    await db.commit()
    await db.refresh(constraint)
    return constraint


@router.delete("/{constraint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_constraint(
    constraint_id: int,
    db: AsyncSession = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    constraint = await _get_or_404(db, constraint_id)
    _check_ownership(constraint, current_teacher)
    await db.delete(constraint)
    await db.commit()


def _check_ownership(constraint: TeacherConstraint, current_teacher: Teacher) -> None:
    if not current_teacher.is_admin and constraint.teacher_id != current_teacher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage your own constraints",
        )


async def _get_or_404(db: AsyncSession, constraint_id: int) -> TeacherConstraint:
    result = await db.execute(
        select(TeacherConstraint).where(TeacherConstraint.id == constraint_id)
    )
    constraint = result.scalar_one_or_none()
    if constraint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Teacher constraint not found"
        )
    return constraint
