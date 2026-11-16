"""
backend/main.py
---------------
FastAPI backend for the CPU Scheduling Simulator website.

Wraps the existing Python scheduling engine (schedulers/, core/) and
exposes REST API endpoints consumed by the React frontend.

All scheduling logic is reused unchanged from the existing modules.
No algorithm code is duplicated or rewritten here.
"""

import sys
import os

# Add the project root to the Python path so scheduler imports resolve
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any

from schedulers.process import Process
from core.runner import run_all_schedulers, validate_processes
from core.generator import (
    generate_processes,
    calculate_workload_summary,
    DISTRIBUTION_PRESETS,
)
from core.faas_explainer import (
    parse_faas_decision_history,
    create_candidate_comparison_df,
)


# =========================================================================== #
# App Initialisation                                                           #
# =========================================================================== #

app = FastAPI(
    title="CPU Scheduling Simulator API",
    description="REST API for SJF, SRTF, HRRN and FAAS scheduling algorithms.",
    version="1.0.0",
)

# Allow requests from the React dev server and any local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================================== #
# Pydantic Request / Response Models                                           #
# =========================================================================== #

class ProcessInput(BaseModel):
    pid: str = Field(..., min_length=1)
    arrival_time: int = Field(..., ge=0)
    burst_time: int = Field(..., ge=1)

    @field_validator("pid")
    @classmethod
    def pid_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("PID cannot be blank.")
        return v.strip()


class SimulateRequest(BaseModel):
    processes: List[ProcessInput] = Field(..., min_length=1)
    faas_quantum: int = Field(default=2, ge=1)
    faas_alpha: float = Field(default=4.0, ge=0.0)
    faas_starvation_threshold: int = Field(default=8, ge=1)


class GenerateRequest(BaseModel):
    num_processes: int = Field(default=5, ge=1, le=100)
    min_arrival: int = Field(default=0, ge=0)
    max_arrival: int = Field(default=10, ge=0)
    min_burst: int = Field(default=1, ge=1)
    max_burst: int = Field(default=10, ge=1)
    distribution: str = Field(default="Uniform Distribution")
    seed: Optional[int] = Field(default=None)

    @field_validator("distribution")
    @classmethod
    def distribution_must_be_valid(cls, v: str) -> str:
        if v not in DISTRIBUTION_PRESETS:
            raise ValueError(f"Invalid distribution. Choose from: {DISTRIBUTION_PRESETS}")
        return v


# =========================================================================== #
# Helper: convert PerformanceMetrics dataclass → plain dict                   #
# =========================================================================== #

def _metrics_to_dict(m) -> Dict[str, Any]:
    return {
        "algorithm_name": m.algorithm_name,
        "process_count": m.process_count,
        "total_simulation_time": m.total_simulation_time,
        "total_busy_time": m.total_busy_time,
        "total_idle_time": m.total_idle_time,
        "cpu_utilization": m.cpu_utilization,
        "throughput": m.throughput,
        "avg_waiting_time": m.avg_waiting_time,
        "avg_turnaround_time": m.avg_turnaround_time,
        "avg_response_time": m.avg_response_time,
        "max_waiting_time": m.max_waiting_time,
        "max_turnaround_time": m.max_turnaround_time,
        "max_response_time": m.max_response_time,
        "context_switches": m.context_switches,
        "preemptions": m.preemptions,
    }


def _process_to_dict(p: Process) -> Dict[str, Any]:
    return {
        "pid": p.pid,
        "arrival_time": p.arrival_time,
        "burst_time": p.burst_time,
        "start_time": p.start_time,
        "completion_time": p.completion_time,
        "turnaround_time": p.turnaround_time,
        "waiting_time": p.waiting_time,
        "response_time": p.response_time,
    }


# =========================================================================== #
# Routes                                                                       #
# =========================================================================== #

router = APIRouter()

@router.get("/health")
def health_check():
    """Simple health probe used by the frontend on startup."""
    return {"status": "ok", "version": "1.0.0"}


@router.get("/distributions")
def list_distributions():
    """Returns available workload distribution names for the random generator."""
    return {"distributions": DISTRIBUTION_PRESETS}


@router.get("/presets")
def list_presets():
    """Returns the built-in sample process datasets."""
    presets = {
        "Benchmark Dataset (P1-P4)": [
            {"pid": "P1", "arrival_time": 0, "burst_time": 6},
            {"pid": "P2", "arrival_time": 1, "burst_time": 2},
            {"pid": "P3", "arrival_time": 2, "burst_time": 4},
            {"pid": "P4", "arrival_time": 4, "burst_time": 3},
        ],
        "Simultaneous Arrivals (t=0)": [
            {"pid": "P1", "arrival_time": 0, "burst_time": 8},
            {"pid": "P2", "arrival_time": 0, "burst_time": 4},
            {"pid": "P3", "arrival_time": 0, "burst_time": 2},
            {"pid": "P4", "arrival_time": 0, "burst_time": 6},
        ],
        "Starvation Risk Trace": [
            {"pid": "P1", "arrival_time": 0, "burst_time": 16},
            {"pid": "P2", "arrival_time": 1, "burst_time": 2},
            {"pid": "P3", "arrival_time": 3, "burst_time": 2},
            {"pid": "P4", "arrival_time": 5, "burst_time": 2},
            {"pid": "P5", "arrival_time": 7, "burst_time": 2},
        ],
        "Idle CPU Intervals Trace": [
            {"pid": "P1", "arrival_time": 3, "burst_time": 4},
            {"pid": "P2", "arrival_time": 9, "burst_time": 3},
            {"pid": "P3", "arrival_time": 15, "burst_time": 2},
        ],
    }
    return {"presets": presets}


@router.post("/generate")
def generate_workload(req: GenerateRequest):
    """
    Generates a random process list using the existing core/generator.py engine.
    Returns process dictionaries ready to populate the frontend table.
    """
    try:
        processes = generate_processes(
            num_processes=req.num_processes,
            arrival_range=(req.min_arrival, req.max_arrival),
            burst_range=(req.min_burst, req.max_burst),
            distribution=req.distribution,
            seed=req.seed,
        )
        summary = calculate_workload_summary(processes)
        return {
            "processes": [
                {"pid": p.pid, "arrival_time": p.arrival_time, "burst_time": p.burst_time}
                for p in processes
            ],
            "summary": summary,
        }
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/simulate")
def simulate(req: SimulateRequest):
    """
    Runs all four scheduling algorithms (SJF, SRTF, HRRN, FAAS) on the
    provided process list and returns timelines, per-process metrics, and
    aggregate statistics for all algorithms.
    """
    # Build Process objects from request payload
    processes = [
        Process(pid=p.pid, arrival_time=p.arrival_time, burst_time=p.burst_time)
        for p in req.processes
    ]

    # Validate (raises ValueError/TypeError on bad input)
    try:
        validate_processes(processes)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Run all schedulers — reuses existing runner.py unchanged
    try:
        sim = run_all_schedulers(
            processes,
            faas_quantum=req.faas_quantum,
            faas_alpha=req.faas_alpha,
            faas_starvation_threshold=req.faas_starvation_threshold,
        )
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Serialise results
    results = {}
    for alg_name, alg_res in sim.algorithms.items():
        results[alg_name] = {
            "timeline": alg_res.timeline,
            "processes": [_process_to_dict(p) for p in alg_res.completed_processes],
            "metrics": _metrics_to_dict(alg_res.metrics),
            "decision_log": alg_res.decision_log or [],
        }

    # Comparison table as list of rows
    comparison_rows = sim.comparison_df.to_dict(orient="records") if not sim.comparison_df.empty else []

    return {
        "algorithms": results,
        "comparison": comparison_rows,
    }


@router.post("/faas-inspector")
def faas_inspector(req: SimulateRequest):
    """
    Runs FAAS on the provided processes and returns the full parsed
    decision history for the interactive FAAS inspector panel.
    """
    processes = [
        Process(pid=p.pid, arrival_time=p.arrival_time, burst_time=p.burst_time)
        for p in req.processes
    ]

    try:
        validate_processes(processes)
        sim = run_all_schedulers(
            processes,
            faas_quantum=req.faas_quantum,
            faas_alpha=req.faas_alpha,
            faas_starvation_threshold=req.faas_starvation_threshold,
        )
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    faas_res = sim.algorithms.get("FAAS")
    if not faas_res or not faas_res.decision_log:
        return {"steps": []}

    steps = parse_faas_decision_history(
        faas_res.decision_log,
        alpha=req.faas_alpha,
        starvation_threshold=req.faas_starvation_threshold,
        quantum=req.faas_quantum,
    )

    # Serialise steps to plain dicts
    serialised_steps = []
    for step in steps:
        candidates = [
            {
                "pid": c.pid,
                "remaining_time": c.remaining_time,
                "continuous_waiting_time": c.continuous_waiting_time,
                "remaining_priority": c.remaining_priority,
                "waiting_priority": c.waiting_priority,
                "final_score": c.final_score,
                "is_starving": c.is_starving,
                "is_selected": c.is_selected,
            }
            for c in step.candidates
        ]
        serialised_steps.append({
            "step_index": step.step_index,
            "clock": step.clock,
            "selected_pid": step.selected_pid,
            "selected_priority": step.selected_priority,
            "quantum_granted": step.quantum_granted,
            "starvation_override": step.starvation_override,
            "reason": step.reason,
            "starvation_threshold": step.starvation_threshold,
            "configured_quantum": step.configured_quantum,
            "alpha": step.alpha,
            "candidates": candidates,
            "srtf_preferred_pid": step.srtf_preferred_pid,
            "explanation": step.explanation,
        })

    return {"steps": serialised_steps}


# Register routes for both /api/path (from Vite dev proxy & frontend) and /path
app.include_router(router, prefix="/api")
app.include_router(router)


# =========================================================================== #
# Static File Hosting: Mount Production React Build                           #
# =========================================================================== #
frontend_dist_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
if os.path.exists(frontend_dist_path):
    app.mount("/", StaticFiles(directory=frontend_dist_path, html=True), name="frontend")

