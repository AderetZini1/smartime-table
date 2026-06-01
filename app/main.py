from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, teachers, rooms, timeslots, subjects, student_groups, teacher_constraints, teacher_assignments, curriculum_requirements, schedule_runs, schedule

app = FastAPI(
    title="Smartime API",
    description="Smart Timetable Scheduling System",
    version="1.0.0"
)

# מאפשר לFrontend לדבר עם השרת
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # בפרודקשן נגביל לכתובת הFrontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(teachers.router)
app.include_router(rooms.router)
app.include_router(timeslots.router)
app.include_router(subjects.router)
app.include_router(student_groups.router)
app.include_router(teacher_constraints.router)
app.include_router(teacher_assignments.router)
app.include_router(curriculum_requirements.router)
app.include_router(schedule_runs.router)
app.include_router(schedule.router)

@app.get("/")
async def root():
    return {"message": "Smartime API is running"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}