from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.curriculum_requirement import CurriculumRequirement
from app.models.teacher import Teacher
from app.schemas.curriculum_requirement import (
    CurriculumRequirementCreate,
    CurriculumRequirementUpdate,
    CurriculumRequirementResponse,
)
from app.auth import get_current_teacher, get_current_admin

router = APIRouter(prefix="/curriculum-requirements", tags=["curriculum-requirements"])


@router.get("/", response_model=List[CurriculumRequirementResponse])
async def list_requirements(
    db: AsyncSession = Depends(get_db),
    _: Teacher = Depends(get_current_teacher),
):
    result = await db.execute(select(CurriculumRequirement))
    return result.scalars().all()


@router.get("/{requirement_id}", response_model=CurriculumRequirementResponse)
async def get_requirement(
    requirement_id: int,
    db: AsyncSession = Depends(get_db),
    _: Teacher = Depends(get_current_teacher),
):
    return await _get_or_404(db, requirement_id)


@router.post("/", response_model=CurriculumRequirementResponse, status_code=status.HTTP_201_CREATED)
async def create_requirement(
    data: CurriculumRequirementCreate,
    db: AsyncSession = Depends(get_db),
    _: Teacher = Depends(get_current_admin),
):
    requirement = CurriculumRequirement(
        subject_id=data.subject_id,
        student_group_id=data.student_group_id,
        weekly_hours=data.weekly_hours,
        sync_block_identity=data.sync_block_identity,
    )
    db.add(requirement)
    await db.commit()
    await db.refresh(requirement)
    return requirement


@router.patch("/{requirement_id}", response_model=CurriculumRequirementResponse)
async def update_requirement(
    requirement_id: int,
    data: CurriculumRequirementUpdate,
    db: AsyncSession = Depends(get_db),
    _: Teacher = Depends(get_current_admin),
):
    requirement = await _get_or_404(db, requirement_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(requirement, field, value)
    await db.commit()
    await db.refresh(requirement)
    return requirement


@router.delete("/{requirement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_requirement(
    requirement_id: int,
    db: AsyncSession = Depends(get_db),
    _: Teacher = Depends(get_current_admin),
):
    requirement = await _get_or_404(db, requirement_id)
    await db.delete(requirement)
    await db.commit()


async def _get_or_404(db: AsyncSession, requirement_id: int) -> CurriculumRequirement:
    result = await db.execute(
        select(CurriculumRequirement).where(CurriculumRequirement.id == requirement_id)
    )
    requirement = result.scalar_one_or_none()
    if requirement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum requirement not found"
        )
    return requirement
