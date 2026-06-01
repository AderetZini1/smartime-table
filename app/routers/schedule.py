from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.schedule import Schedule
from app.models.teacher import Teacher
from app.schemas.schedule import ScheduleCreate, ScheduleResponse
from app.auth import get_current_teacher, get_current_admin

router = APIRouter(prefix="/schedule", tags=["schedule"])


@router.get("/", response_model=List[ScheduleResponse])
async def list_entries(
    db: AsyncSession = Depends(get_db),
    _: Teacher = Depends(get_current_teacher),
):
    result = await db.execute(select(Schedule))
    return result.scalars().all()


@router.get("/by-run/{run_id}", response_model=List[ScheduleResponse])
async def get_entries_by_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    _: Teacher = Depends(get_current_teacher),
):
    result = await db.execute(select(Schedule).where(Schedule.run_id == run_id))
    return result.scalars().all()


@router.get("/{entry_id}", response_model=ScheduleResponse)
async def get_entry(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
    _: Teacher = Depends(get_current_teacher),
):
    return await _get_or_404(db, entry_id)


@router.post("/", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_entry(
    data: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
    _: Teacher = Depends(get_current_admin),
):
    entry = Schedule(
        timeslot_id=data.timeslot_id,
        tea_assignment_id=data.tea_assignment_id,
        room_id=data.room_id,
        run_id=data.run_id,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
    _: Teacher = Depends(get_current_admin),
):
    entry = await _get_or_404(db, entry_id)
    await db.delete(entry)
    await db.commit()


async def _get_or_404(db: AsyncSession, entry_id: int) -> Schedule:
    result = await db.execute(select(Schedule).where(Schedule.id == entry_id))
    entry = result.scalar_one_or_none()
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule entry not found")
    return entry
