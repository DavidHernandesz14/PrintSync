
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.scheduler import PrintScheduler


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="PrintSync API",
    description="3D Printer Management with SJF Scheduling",
    version="1.0.0",
)

app.mount(
    "/frontend",
    StaticFiles(directory=FRONTEND_DIR),
    name="frontend",
)

# The website uses persistent SQLite storage.
scheduler = PrintScheduler(persist=True)

controller_lock = threading.Lock()
scheduler_running = False


class PrintJobRequest(BaseModel):
    job_name: str = Field(
        min_length=1,
        max_length=100,
    )
    duration: float = Field(
        gt=0,
        allow_inf_nan=False,
        le=3600,
    )


@app.get("/")
def home():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/jobs", status_code=201)
def add_job(job: PrintJobRequest):
    with controller_lock:
        if scheduler_running:
            raise HTTPException(
                status_code=409,
                detail="Wait until the current batch finishes.",
            )

        scheduler.add_job(
            job.job_name,
            job.duration,
        )

    return {
        "message": "Job added successfully",
        "job_name": job.job_name,
        "estimated_duration": job.duration,
    }


def run_scheduler():
    global scheduler_running

    try:
        scheduler.run()
    finally:
        with controller_lock:
            scheduler_running = False


@app.post("/scheduler/start")
def start_scheduler():
    global scheduler_running

    with controller_lock:
        if scheduler_running:
            raise HTTPException(
                status_code=409,
                detail="Scheduler is already running.",
            )

        if scheduler.job_queue.empty():
            raise HTTPException(
                status_code=400,
                detail="No pending jobs to print.",
            )

        scheduler_running = True

        thread = threading.Thread(
            target=run_scheduler,
            daemon=True,
        )
        thread.start()

    return {
        "message": "SJF scheduler started",
        "status": "running",
    }


@app.get("/status")
def get_status():
    with controller_lock:
        running = scheduler_running

        with scheduler.lock:
            completed_jobs = [
                job.copy()
                for job in scheduler.completed_jobs
            ]

        with scheduler.job_queue.mutex:
            pending_jobs = sorted(
                list(scheduler.job_queue.queue)
            )

    printers = [
        {
            "printer_id": printer.printer_id,
            "name": printer.name,
            "status": printer.status,
            "progress": printer.progress,
            "current_job": printer.current_job,
        }
        for printer in scheduler.printers
    ]

    return {
        "algorithm": "SJF",
        "scheduler_running": running,
        "pending_jobs": [
            {
                "job_name": job[2],
                "duration": job[0],
            }
            for job in pending_jobs
        ],
        "printers": printers,
        "completed_jobs": completed_jobs,
    }
