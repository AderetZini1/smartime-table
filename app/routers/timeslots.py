from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.timeslot import Timeslot
from app.models.teacher import Teacher
from app.schemas.timeslot import TimeslotCreate, TimeslotResponse
from app.auth import get_current_teacher, get_current_admin

router = APIRouter(prefix="/timeslots", tags=["timeslots"])


@router.get("/", response_model=List[TimeslotResponse])
async def list_timeslots(
    db: AsyncSession = Depends(get_db),
    _: Teacher = Depends(get_current_teacher),
):
    result = await db.execute(select(Timeslot).order_by(Timeslot.day_of_week, Timeslot.hour_of_day))
    return result.scalars().all()


@router.get("/{timeslot_id}", response_model=TimeslotResponse)
async def get_timeslot(
    timeslot_id: int,
    db: AsyncSession = Depends(get_db),
    _: Teacher = Depends(get_current_teacher),
):
    return await _get_or_404(db, timeslot_id)


@router.post("/", response_model=TimeslotResponse, status_code=status.HTTP_201_CREATED)
async def create_timeslot(
    data: TimeslotCreate,
    db: AsyncSession = Depends(get_db),
    _: Teacher = Depends(get_current_admin),
):
    timeslot = Timeslot(day_of_week=data.day_of_week, hour_of_day=data.hour_of_day)
    db.add(timeslot)
    await db.commit()
    await db.refresh(timeslot)
    return timeslot


@router.delete("/{timeslot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_timeslot(
    timeslot_id: int,
    db: AsyncSession = Depends(get_db),
    _: Teacher = Depends(get_current_admin),
):
    timeslot = await _get_or_404(db, timeslot_id)
    await db.delete(timeslot)
    await db.commit()


async def _get_or_404(db: AsyncSession, timeslot_id: int) -> Timeslot:
    result = await db.execute(select(Timeslot).where(Timeslot.id == timeslot_id))
    timeslot = result.scalar_one_or_none()
    if timeslot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Timeslot not found")
    return timeslot
