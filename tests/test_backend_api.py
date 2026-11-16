"""
test_backend_api.py
-------------------
Integration and unit test suite for the FastAPI backend route handlers and models.

Tests:
  - Health check endpoint logic
  - Presets listing endpoint
  - Workload distributions listing endpoint
  - Random generator endpoint logic and seed reproducibility
  - Multi-algorithm simulation execution and numerical metric validation
  - Pydantic input models validation and error rejection
  - FAAS decision inspector endpoint with component decomposition
"""

import pytest
from pydantic import ValidationError
from backend.main import (
    health_check,
    list_presets,
    list_distributions,
    generate_workload,
    simulate,
    faas_inspector,
    ProcessInput,
    SimulateRequest,
    GenerateRequest,
)


def test_health_endpoint():
    res = health_check()
    assert res == {"status": "ok", "version": "1.0.0"}


def test_presets_endpoint():
    res = list_presets()
    assert "presets" in res
    presets = res["presets"]
    assert "Benchmark Dataset (P1-P4)" in presets
    assert len(presets["Benchmark Dataset (P1-P4)"]) == 4


def test_distributions_endpoint():
    res = list_distributions()
    assert "distributions" in res
    assert "Uniform Distribution" in res["distributions"]
    assert "Mixed Workload" in res["distributions"]


def test_generate_endpoint_valid():
    req = GenerateRequest(
        num_processes=6,
        min_arrival=0,
        max_arrival=5,
        min_burst=2,
        max_burst=8,
        distribution="Uniform Distribution",
        seed=42,
    )
    res = generate_workload(req)
    assert len(res["processes"]) == 6
    assert res["summary"]["total_processes"] == 6

    # Verify seed reproducibility: identical seed yields identical processes
    res2 = generate_workload(req)
    assert res["processes"] == res2["processes"]


def test_generate_endpoint_invalid_pydantic():
    # num_processes = 0 (violates ge=1)
    with pytest.raises(ValidationError):
        GenerateRequest(num_processes=0)

    # Invalid distribution name
    with pytest.raises(ValidationError):
        GenerateRequest(distribution="Invalid Nonexistent Distribution")


def test_simulate_endpoint_benchmark_dataset():
    req = SimulateRequest(
        processes=[
            ProcessInput(pid="P1", arrival_time=0, burst_time=6),
            ProcessInput(pid="P2", arrival_time=1, burst_time=2),
            ProcessInput(pid="P3", arrival_time=2, burst_time=4),
            ProcessInput(pid="P4", arrival_time=4, burst_time=3),
        ],
        faas_quantum=2,
        faas_alpha=4.0,
        faas_starvation_threshold=8,
    )
    res = simulate(req)

    assert "algorithms" in res
    assert "comparison" in res

    # Verify all four algorithms executed
    for alg in ["SJF", "SRTF", "HRRN", "FAAS"]:
        assert alg in res["algorithms"]
        assert len(res["algorithms"][alg]["processes"]) == 4
        assert len(res["algorithms"][alg]["timeline"]) > 0

    # Verify exact benchmark metrics
    sjf_metrics = res["algorithms"]["SJF"]["metrics"]
    assert sjf_metrics["avg_turnaround_time"] == 8.25
    assert sjf_metrics["avg_waiting_time"] == 4.50

    srtf_metrics = res["algorithms"]["SRTF"]["metrics"]
    assert srtf_metrics["avg_turnaround_time"] == 7.00
    assert srtf_metrics["avg_waiting_time"] == 3.25

    hrrn_metrics = res["algorithms"]["HRRN"]["metrics"]
    assert hrrn_metrics["avg_turnaround_time"] == 8.50
    assert hrrn_metrics["avg_waiting_time"] == 4.75

    faas_metrics = res["algorithms"]["FAAS"]["metrics"]
    assert faas_metrics["avg_turnaround_time"] == 9.50
    assert faas_metrics["avg_waiting_time"] == 5.75


def test_simulate_validation_errors():
    # 1. Non-positive burst time (violates ge=1)
    with pytest.raises(ValidationError):
        ProcessInput(pid="P1", arrival_time=0, burst_time=0)

    # 2. Negative arrival time (violates ge=0)
    with pytest.raises(ValidationError):
        ProcessInput(pid="P1", arrival_time=-1, burst_time=4)

    # 3. Empty PID string
    with pytest.raises(ValidationError):
        ProcessInput(pid="   ", arrival_time=0, burst_time=4)

    # 4. Duplicate PID in simulation list
    req_dup = SimulateRequest(
        processes=[
            ProcessInput(pid="P1", arrival_time=0, burst_time=4),
            ProcessInput(pid="P1", arrival_time=1, burst_time=2),
        ]
    )
    with pytest.raises(Exception):
        simulate(req_dup)


def test_faas_inspector_endpoint():
    req = SimulateRequest(
        processes=[
            ProcessInput(pid="P1", arrival_time=0, burst_time=6),
            ProcessInput(pid="P2", arrival_time=1, burst_time=2),
            ProcessInput(pid="P3", arrival_time=2, burst_time=4),
            ProcessInput(pid="P4", arrival_time=4, burst_time=3),
        ],
        faas_quantum=2,
        faas_alpha=4.0,
        faas_starvation_threshold=8,
    )
    res = faas_inspector(req)

    assert "steps" in res
    assert len(res["steps"]) > 0

    first_step = res["steps"][0]
    assert first_step["step_index"] == 1
    assert first_step["clock"] == 0
    assert first_step["selected_pid"] == "P1"
    assert "candidates" in first_step
    assert "explanation" in first_step
