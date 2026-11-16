"""
test_runner.py
--------------
Test suite for the unified scheduler runner (core/runner.py).

Verifies:
  1. All four algorithms execute successfully.
  2. All algorithms receive identical input datasets.
  3. Input process lists remain unchanged.
  4. Independent process copies are maintained.
  5. Metrics are calculated correctly.
  6. Empty inputs are handled safely.
  7. Invalid inputs are rejected appropriately.
  8. Different arrival times work correctly.
  9. FAAS configuration is passed correctly.
  10. Existing algorithms remain functional.
  11. Benchmark numerical validation on the required dataset.
"""

import pytest
import pandas as pd
from schedulers.process import Process
from core.runner import run_all_schedulers, validate_processes, SimulationResults


# =========================================================================== #
# Test 1 & 2: All four algorithms execute and produce results                 #
# =========================================================================== #
def test_all_four_algorithms_execute():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=5),
        Process(pid="P2", arrival_time=1, burst_time=3),
    ]
    sim = run_all_schedulers(processes)

    assert isinstance(sim, SimulationResults)
    assert set(sim.algorithms.keys()) == {"SJF", "SRTF", "HRRN", "FAAS"}

    for name in ["SJF", "SRTF", "HRRN", "FAAS"]:
        res = sim.get_algorithm(name)
        assert res is not None
        assert len(res.completed_processes) == 2
        assert len(res.timeline) >= 2
        assert res.metrics.process_count == 2
        assert res.metrics.cpu_utilization == 100.0


# =========================================================================== #
# Test 3 & 4: Immutability and Independent Copies                              #
# =========================================================================== #
def test_immutability_and_independence():
    p1 = Process(pid="P1", arrival_time=0, burst_time=6)
    p2 = Process(pid="P2", arrival_time=2, burst_time=4)
    processes = [p1, p2]

    # Run simulation
    sim = run_all_schedulers(processes)

    # Verify input process objects were not altered
    assert p1.remaining_time == 6
    assert p1.completion_time == -1
    assert p1.turnaround_time == -1
    assert p1.waiting_time == -1
    assert p1.response_time == -1

    assert p2.remaining_time == 4
    assert p2.completion_time == -1

    # Verify that each algorithm got separate copies with independent IDs in memory
    p1_sjf = sim.get_algorithm("SJF").completed_processes[0]
    p1_srtf = sim.get_algorithm("SRTF").completed_processes[0]
    assert p1_sjf is not p1_srtf
    assert p1_sjf is not p1


# =========================================================================== #
# Test 5: Metrics and Comparison DataFrame Generation                          #
# =========================================================================== #
def test_metrics_dataframe_generation():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=4),
        Process(pid="P2", arrival_time=1, burst_time=2),
    ]
    sim = run_all_schedulers(processes)

    df = sim.comparison_df
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 4
    assert set(df["Algorithm"]) == {"SJF", "SRTF", "HRRN", "FAAS"}
    assert "Avg Turnaround Time" in df.columns
    assert "Avg Waiting Time" in df.columns
    assert "CPU Utilization (%)" in df.columns


# =========================================================================== #
# Test 6: Empty Inputs Handled Safely                                          #
# =========================================================================== #
def test_empty_input_handling():
    sim = run_all_schedulers([])
    assert isinstance(sim, SimulationResults)
    assert len(sim.algorithms) == 0
    assert len(sim.comparison_df) == 0


# =========================================================================== #
# Test 7: Invalid Inputs Rejected                                              #
# =========================================================================== #
def test_invalid_inputs_rejected():
    # Not a list
    with pytest.raises(TypeError, match="Expected a list"):
        run_all_schedulers("invalid")

    # Non-Process element
    with pytest.raises(TypeError, match="is not a Process instance"):
        run_all_schedulers([Process("P1", 0, 5), "not_a_proc"])

    # Negative arrival time
    with pytest.raises(ValueError, match="negative arrival time"):
        run_all_schedulers([Process("P1", -1, 5)])

    # Zero or negative burst time
    with pytest.raises(ValueError, match="non-positive burst time"):
        run_all_schedulers([Process("P1", 0, 0)])

    # Duplicate PID
    with pytest.raises(ValueError, match="Duplicate PID"):
        run_all_schedulers([Process("P1", 0, 5), Process("P1", 1, 3)])

    # Invalid FAAS parameters
    valid_proc = [Process("P1", 0, 5)]
    with pytest.raises(ValueError, match="FAAS quantum must be > 0"):
        run_all_schedulers(valid_proc, faas_quantum=0)

    with pytest.raises(ValueError, match="FAAS alpha must be >= 0"):
        run_all_schedulers(valid_proc, faas_alpha=-1.0)

    with pytest.raises(ValueError, match="FAAS starvation threshold must be > 0"):
        run_all_schedulers(valid_proc, faas_starvation_threshold=0)


# =========================================================================== #
# Test 8: Different Arrival Times & CPU Idle Handling                          #
# =========================================================================== #
def test_different_arrivals_and_idle():
    # P1 arrives at t=3, BT=2. Idle from 0 to 3.
    processes = [Process(pid="P1", arrival_time=3, burst_time=2)]
    sim = run_all_schedulers(processes)

    for name in ["SJF", "SRTF", "HRRN", "FAAS"]:
        res = sim.get_algorithm(name)
        assert res.metrics.total_idle_time == 3
        assert res.metrics.total_busy_time == 2
        assert res.metrics.total_simulation_time == 5
        assert res.metrics.cpu_utilization == 40.0


# =========================================================================== #
# Test 9: FAAS Configuration Propagated Correctly                              #
# =========================================================================== #
def test_faas_configuration_propagation():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=10),
        Process(pid="P2", arrival_time=0, burst_time=2),
    ]
    # Configure custom quantum=3
    sim = run_all_schedulers(processes, faas_quantum=3, faas_alpha=2.0, faas_starvation_threshold=5)
    faas_res = sim.get_algorithm("FAAS")

    # In decision log, quantum granted should be min(3, remaining)
    assert faas_res.decision_log is not None
    assert faas_res.decision_log[0]["quantum_granted"] == 2  # P2 has BT=2
    # P1 should receive up to 3 units when dispatched
    assert any(d["quantum_granted"] == 3 for d in faas_res.decision_log)


# =========================================================================== #
# Test 10: Process Detail Table Export (Streamlit Preparation)                 #
# =========================================================================== #
def test_process_dataframe_export():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=4),
        Process(pid="P2", arrival_time=1, burst_time=2),
    ]
    sim = run_all_schedulers(processes)
    sjf_df = sim.get_algorithm("SJF").process_dataframe

    assert isinstance(sjf_df, pd.DataFrame)
    assert len(sjf_df) == 2
    assert "PID" in sjf_df.columns
    assert "Completion Time" in sjf_df.columns
    assert "Waiting Time" in sjf_df.columns


# =========================================================================== #
# Test 11: Benchmark Dataset Numerical Validation                              #
# =========================================================================== #
def test_benchmark_numerical_validation():
    benchmark_dataset = [
        Process(pid="P1", arrival_time=0, burst_time=6),
        Process(pid="P2", arrival_time=1, burst_time=2),
        Process(pid="P3", arrival_time=2, burst_time=4),
        Process(pid="P4", arrival_time=4, burst_time=3),
    ]

    sim = run_all_schedulers(benchmark_dataset, faas_quantum=2, faas_alpha=4.0, faas_starvation_threshold=8)

    # 1. SJF verification
    sjf = sim.get_algorithm("SJF").metrics
    assert sjf.avg_turnaround_time == 8.25
    assert sjf.avg_waiting_time == 4.50
    assert sjf.avg_response_time == 4.50
    assert sjf.context_switches == 3
    assert sjf.preemptions == 0

    # 2. SRTF verification
    srtf = sim.get_algorithm("SRTF").metrics
    assert srtf.avg_turnaround_time == 7.00
    assert srtf.avg_waiting_time == 3.25
    assert srtf.avg_response_time == 1.00
    assert srtf.context_switches == 4
    assert srtf.preemptions == 1

    # 3. HRRN verification
    hrrn = sim.get_algorithm("HRRN").metrics
    assert hrrn.avg_turnaround_time == 8.50
    assert hrrn.avg_waiting_time == 4.75
    assert hrrn.avg_response_time == 4.75
    assert hrrn.context_switches == 3
    assert hrrn.preemptions == 0

    # 4. FAAS verification
    faas = sim.get_algorithm("FAAS").metrics
    assert faas.avg_turnaround_time == 9.50
    assert faas.avg_waiting_time == 5.75
    assert faas.avg_response_time == 2.25
    assert faas.context_switches == 7
    assert faas.preemptions == 4
