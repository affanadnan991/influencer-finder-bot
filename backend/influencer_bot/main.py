"""FastAPI backend for Instagram Influencer Finder."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import jobs

app = FastAPI(
    title="Instagram Influencer Finder API",
    version="1.0.0",
    description="Find relevant Instagram influencers by scanning a target profile's followings",
)

# CORS — allow frontend (Next.js dev server on 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ─────────────────────────────────────


class SearchRequest(BaseModel):
    target: str = Field(..., description="Instagram username to scan", min_length=1)
    keywords: list[str] = Field(default=[], description="Keywords to match in bios (max 7)")
    max_following: int = Field(default=200, ge=1, le=1000, description="Max followings to check")


class SearchResponse(BaseModel):
    job_id: str
    message: str


class StatusResponse(BaseModel):
    job_id: str
    target: str
    keywords: list[str]
    status: str
    phase: str
    detail: str
    counters: dict
    result_count: int
    error: str
    created_at: str
    finished_at: Optional[str]


# ── API Routes ────────────────────────────────────────────────────


@app.post("/api/search", response_model=SearchResponse)
def start_search(req: SearchRequest):
    """Start a new influencer search job in the background."""
    keywords = req.keywords[:7]  # cap at 7
    job = jobs.start_search(
        target=req.target,
        keywords=keywords,
        max_following=req.max_following,
    )
    return SearchResponse(
        job_id=job.id,
        message=f"Search started for @{job.target}",
    )


@app.get("/api/status/{job_id}", response_model=StatusResponse)
def get_status(job_id: str):
    """Get the current status and progress of a search job."""
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    d = job.to_dict()
    return StatusResponse(
        job_id=d["job_id"],
        target=d["target"],
        keywords=d["keywords"],
        status=d["status"],
        phase=d["phase"],
        detail=d["detail"],
        counters=d["counters"],
        result_count=d["result_count"],
        error=d["error"],
        created_at=d["created_at"],
        finished_at=d["finished_at"],
    )


@app.get("/api/results/{job_id}")
def get_results(job_id: str):
    """Get the profiles matched so far — works while the job is still running too,
    since matches are saved and reported to the frontend as soon as they're found."""
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job.id,
        "status": job.status.value,
        "result_count": len(job.results),
        "results": [
            {
                "username": p.get("username", ""),
                "profile_url": p.get("profile_url", ""),
                "niche": p.get("niche", ""),
                "score": p.get("score", 0),
                "date_collected": p.get("date_collected", ""),
            }
            for p in job.results
        ],
    }


@app.get("/api/download/{job_id}")
def download_csv(job_id: str):
    """Download the CSV file for a job — available as soon as the first profile
    is matched, since each match is written to disk immediately, not just at the end."""
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.csv_path or not os.path.exists(job.csv_path):
        raise HTTPException(status_code=404, detail="CSV file not found")
    filename = f"influencers_{job.target}_{job.id}.csv"
    return FileResponse(
        path=job.csv_path,
        media_type="text/csv",
        filename=filename,
    )


@app.get("/api/jobs")
def list_all_jobs():
    """List all jobs (for dashboard view)."""
    return {"jobs": jobs.list_jobs()}


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "influencer-finder-api"}


# ── WebSocket ─────────────────────────────────────────────────────


@app.on_event("startup")
async def on_startup():
    """Register the asyncio event loop so background threads can push WS messages."""
    jobs.set_event_loop(asyncio.get_running_loop())


@app.websocket("/ws/progress/{job_id}")
async def ws_progress(websocket: WebSocket, job_id: str):
    """Real-time progress stream for a job.

    Client connects → receives JSON messages whenever job state changes.
    Connection closes automatically when job finishes (completed/failed).
    """
    job = jobs.get_job(job_id)
    if not job:
        await websocket.close(code=4004, reason="Job not found")
        return

    await websocket.accept()

    # Send current state immediately
    await websocket.send_json(job.to_dict())

    # If already finished, close right away
    if job.status in (jobs.JobStatus.COMPLETED, jobs.JobStatus.FAILED):
        await websocket.close()
        return

    # Queue for receiving updates from the background thread
    queue: asyncio.Queue = asyncio.Queue()

    async def on_update(data: dict):
        await queue.put(data)

    jobs.add_ws_listener(job_id, on_update)

    try:
        while True:
            data = await queue.get()
            await websocket.send_json(data)
            # Close when job is done
            if data.get("status") in ("completed", "failed"):
                await websocket.close()
                break
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        jobs.remove_ws_listener(job_id, on_update)
