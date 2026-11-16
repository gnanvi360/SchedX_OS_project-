"""
test_generator.py
-----------------
Automated test suite for the Random Process Generator (core/generator.py).

Covers:
  1. Correct process count generation.
  2. Unique PID generation (P1, P2, ...).
  3. Valid arrival time boundaries.
  4. Positive burst time boundaries.
  5. Uniform distribution generation.
  6. Short-job-heavy distribution characteristics.
  7. Long-job-heavy distribution characteristics.
  8. Mixed workload distribution characteristics.
  9. Reproducibility with identical random seeds.
  10. Differentiation with different random seeds.
  11. Invalid input handling and boundary assertions.
  12. Boundary values (N=1, N=100, min=max).
  13. Integration with the shared Process data model.
  14. Integration with the unified scheduler runner (run_all_schedulers).
  15. Immutability of original generated processes during execution.
"""

import pytest
from schedulers.process import Process
from core.generator import (
    generate_processes,
    calculate_workload_summary,
    DISTRIBUTION_PRESETS,
)
from core.runner import run_all_schedulers


# =========================================================================== #
# Test 1 & 2: Process Count & Unique PIDs                                     #
# =========================================================================== #
def test_process_count_and_unique_pids():
    n = 10
    procs = generate_processes(num_processes=n, seed=42)
    assert len(procs) == n

    pids = [p.pid for p in procs]
    assert len(set(pids)) == n
    assert pids == [f"P{i}" for i in range(1, n + 1)]


# =========================================================================== #
# Test 3 & 4: Valid Arrival and Positive Burst Times                           #
# =========================================================================== #
def test_valid_arrival_and_burst_times():
    procs = generate_processes(
        num_processes=20,
        arrival_range=(5, 15),
        burst_range=(2, 8),
        seed=123,
    )
    for p in procs:
        assert 5 <= p.arrival_time <= 15
        assert 2 <= p.burst_time <= 8
        assert p.remaining_time == p.burst_time
        assert p.completion_time == -1


# =========================================================================== #
# Test 5: Uniform Distribution Generation                                      #
# =========================================================================== #
def test_uniform_distribution():
    procs = generate_processes(
        num_processes=50,
        arrival_range=(0, 20),
        burst_range=(1, 10),
        distribution="Uniform Distribution",
        seed=999,
    )
    bursts = [p.burst_time for p in procs]
    assert min(bursts) >= 1
    assert max(bursts) <= 10
    # Over 50 samples, mean should reasonably be around the middle (3 to 8)
    avg_burst = sum(bursts) / len(bursts)
    assert 3.0 <= avg_burst <= 8.0


# =========================================================================== #
# Test 6 & 7: Short-Job Heavy vs Long-Job Heavy Distributions                  #
# =========================================================================== #
def test_short_vs_long_job_distributions():
    # Generate 100 processes under both strategies over range 1 to 30
    short_procs = generate_processes(
        num_processes=100,
        arrival_range=(0, 10),
        burst_range=(1, 30),
        distribution="Short-Job Heavy",
        seed=101,
    )
    long_procs = generate_processes(
        num_processes=100,
        arrival_range=(0, 10),
        burst_range=(1, 30),
        distribution="Long-Job Heavy",
        seed=101,
    )

    avg_short = sum(p.burst_time for p in short_procs) / 100
    avg_long = sum(p.burst_time for p in long_procs) / 100

    # Short-job heavy average MUST be strictly lower than long-job heavy average
    assert avg_short < avg_long
    assert avg_short < 15.0  # Range mid is ~15.5
    assert avg_long > 15.0


# =========================================================================== #
# Test 8: Mixed Workload Generation                                            #
# =========================================================================== #
def test_mixed_workload():
    procs = generate_processes(
        num_processes=50,
        arrival_range=(0, 10),
        burst_range=(1, 30),
        distribution="Mixed Workload",
        seed=202,
    )
    bursts = [p.burst_time for p in procs]
    assert any(b <= 10 for b in bursts)  # Has short jobs
    assert any(b >= 20 for b in bursts)  # Has long jobs


# =========================================================================== #
# Test 9 & 10: Seed Reproducibility vs Different Seeds                         #
# =========================================================================== #
def test_seed_reproducibility():
    procs_a = generate_processes(num_processes=8, seed=777)
    procs_b = generate_processes(num_processes=8, seed=777)
    procs_c = generate_processes(num_processes=8, seed=888)

    # Identical seeds must produce identical data
    for pa, pb in zip(procs_a, procs_b):
        assert pa.pid == pb.pid
        assert pa.arrival_time == pb.arrival_time
        assert pa.burst_time == pb.burst_time

    # Different seeds must produce different data
    data_a = [(p.arrival_time, p.burst_time) for p in procs_a]
    data_c = [(p.arrival_time, p.burst_time) for p in procs_c]
    assert data_a != data_c


# =========================================================================== #
# Test 11: Invalid Input Handling                                              #
# =========================================================================== #
def test_invalid_inputs():
    # Number of processes out of bounds
    with pytest.raises(ValueError, match="between 1 and 100"):
        generate_processes(num_processes=0)

    with pytest.raises(ValueError, match="between 1 and 100"):
        generate_processes(num_processes=101)

    with pytest.raises(TypeError):
        generate_processes(num_processes="five")

    # Invalid arrival range
    with pytest.raises(ValueError, match="cannot exceed maximum arrival"):
        generate_processes(arrival_range=(10, 5))

    with pytest.raises(ValueError, match="cannot be negative"):
        generate_processes(arrival_range=(-2, 5))

    # Invalid burst range
    with pytest.raises(ValueError, match="at least 1"):
        generate_processes(burst_range=(0, 5))

    with pytest.raises(ValueError, match="cannot exceed maximum burst"):
        generate_processes(burst_range=(8, 4))

    # Unknown distribution
    with pytest.raises(ValueError, match="Unknown distribution"):
        generate_processes(distribution="NonExistent")

    # Invalid seed type
    with pytest.raises(TypeError, match="integer or None"):
        generate_processes(seed="invalid_seed")


# =========================================================================== #
# Test 12: Boundary Values                                                     #
# =========================================================================== #
def test_boundary_values():
    # Minimum valid process count N=1
    p1 = generate_processes(num_processes=1, seed=1)
    assert len(p1) == 1
    assert p1[0].pid == "P1"

    # Maximum valid process count N=100
    p100 = generate_processes(num_processes=100, seed=1)
    assert len(p100) == 100
    assert p100[-1].pid == "P100"

    # Equal min and max bounds
    p_exact = generate_processes(
        num_processes=5,
        arrival_range=(3, 3),
        burst_range=(4, 4),
        seed=1,
    )
    for p in p_exact:
        assert p.arrival_time == 3
        assert p.burst_time == 4


# =========================================================================== #
# Test 13: Workload Summary Statistics Calculation                             #
# =========================================================================== #
def test_workload_summary():
    procs = [
        Process("P1", 0, 4),
        Process("P2", 2, 6),
        Process("P3", 4, 10),
    ]
    summary = calculate_workload_summary(procs)
    assert summary["total_processes"] == 3
    assert summary["total_burst_time"] == 20
    assert summary["avg_burst_time"] == round(20 / 3, 2)
    assert summary["avg_arrival_time"] == 2.0
    assert summary["min_burst_time"] == 4
    assert summary["max_burst_time"] == 10

    # Empty summary test
    empty_summary = calculate_workload_summary([])
    assert empty_summary["total_processes"] == 0
    assert empty_summary["avg_burst_time"] == 0.0


# =========================================================================== #
# Test 14 & 15: Integration with Runner & Immutability                         #
# =========================================================================== #
def test_runner_integration_and_immutability():
    generated_procs = generate_processes(
        num_processes=6,
        arrival_range=(0, 8),
        burst_range=(2, 6),
        seed=444,
    )

    # Snapshot original attributes
    orig_remaining = [p.remaining_time for p in generated_procs]
    orig_completion = [p.completion_time for p in generated_procs]
    orig_burst = [p.burst_time for p in generated_procs]

    # Execute all 4 algorithms on generated dataset
    sim = run_all_schedulers(generated_procs)

    # 1. All 4 algorithms executed successfully
    assert set(sim.algorithms.keys()) == {"SJF", "SRTF", "HRRN", "FAAS"}
    assert len(sim.comparison_df) == 4

    # 2. Verify that input objects were NOT mutated
    for i, p in enumerate(generated_procs):
        assert p.remaining_time == orig_remaining[i]
        assert p.completion_time == orig_completion[i]
        assert p.burst_time == orig_burst[i]
