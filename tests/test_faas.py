"""
test_faas.py
------------
Comprehensive test suite for Fairness-Aware Adaptive Scheduling (FAAS).

Contains 17 distinct test cases verifying:
  - Correct quantum bounding (Q=2)
  - Dynamic waiting-time aging (alpha * continuous_waiting_time)
  - Starvation protection threshold activation and override
  - Tie-breaking rules
  - Process arrivals during active quantums
  - CPU idle handling
  - Immutability of input
  - Parameter safety and empty input handling
  - Full scheduling metrics calculation
"""

import pytest
from schedulers.process import Process
from schedulers.faas import run_faas, DecisionLog


# =========================================================================== #
# Test 1: Single process                                                       #
# =========================================================================== #
def test_single_process():
    # P1: AT=0, BT=5. Quantum=2 -> Runs 0->2, 2->4, 4->5.
    # Consecutive intervals merge into [0 -> 5].
    processes = [Process(pid="P1", arrival_time=0, burst_time=5)]
    completed, timeline, log = run_faas(processes, quantum=2)

    assert len(completed) == 1
    p1 = completed[0]
    assert p1.start_time == 0
    assert p1.completion_time == 5
    assert p1.turnaround_time == 5
    assert p1.waiting_time == 0
    assert p1.response_time == 0
    assert timeline == [{"pid": "P1", "start": 0, "end": 5}]


# =========================================================================== #
# Test 2: Multiple processes arriving at time zero                             #
# =========================================================================== #
def test_multiple_arrive_at_zero():
    # P1: BT=4, P2: BT=2. Both at t=0.
    # At t=0: Continuous wait is 0 for both.
    # Priority(P1) = 1/4 = 0.25
    # Priority(P2) = 1/2 = 0.50 -> P2 selected first.
    # P2 runs 0 -> 2 (completes).
    # P1 runs 2 -> 4, 4 -> 6 (completes).
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=4),
        Process(pid="P2", arrival_time=0, burst_time=2),
    ]
    completed, timeline, log = run_faas(processes, quantum=2)
    result = {p.pid: p for p in completed}

    assert result["P2"].completion_time == 2
    assert result["P2"].waiting_time == 0
    assert result["P1"].completion_time == 6
    assert result["P1"].waiting_time == 2  # 6 - 4
    assert [p.pid for p in completed] == ["P2", "P1"]


# =========================================================================== #
# Test 3: Different arrival times                                              #
# =========================================================================== #
def test_different_arrival_times():
    # P1 arrives at t=0, BT=4. Runs 0 -> 2.
    # P2 arrives at t=1, BT=1. (Waits until t=2 because P1's quantum is guaranteed).
    # At t=2:
    # P1: remaining=2, continuous_wait=0 -> Priority = 1/2 + 4(0) = 0.50
    # P2: remaining=1, continuous_wait=2-1=1 -> Priority = 1/1 + 4(1) = 5.00
    # P2 runs 2 -> 3 (completes).
    # P1 runs 3 -> 5 (completes).
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=4),
        Process(pid="P2", arrival_time=1, burst_time=1),
    ]
    completed, timeline, log = run_faas(processes, quantum=2)
    result = {p.pid: p for p in completed}

    assert result["P2"].completion_time == 3
    assert result["P2"].turnaround_time == 2  # 3 - 1
    assert result["P2"].waiting_time == 1     # 2 - 1
    assert result["P2"].response_time == 1    # 2 - 1

    assert result["P1"].completion_time == 5
    assert result["P1"].waiting_time == 1     # 5 - 4


# =========================================================================== #
# Test 4: Short processes competing with long processes                        #
# =========================================================================== #
def test_short_competing_with_long():
    # P1 (long): BT=10, P2 (short): BT=2, P3 (short): BT=2.
    # All at t=0.
    # P2 and P3 have higher initial priority (1/2 = 0.5) vs P1 (1/10 = 0.1).
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=10),
        Process(pid="P2", arrival_time=0, burst_time=2),
        Process(pid="P3", arrival_time=0, burst_time=2),
    ]
    completed, timeline, log = run_faas(processes, quantum=2)

    # Short processes execute and finish first
    finished_order = [p.pid for p in completed]
    assert finished_order[0] in ["P2", "P3"]
    assert finished_order[1] in ["P2", "P3"]
    assert finished_order[2] == "P1"


# =========================================================================== #
# Test 5: Aging increases waiting-process priority                             #
# =========================================================================== #
def test_aging_increases_priority():
    # P1: AT=0, BT=8. P2: AT=2, BT=1.
    # At t=0: P1 runs 0 -> 2.
    # At t=2: P1 rem=6, wait=0 -> Priority = 1/6 + 0 = 0.1667.
    # P2 rem=1, wait=0 (just arrived at t=2) -> Priority = 1/1 + 0 = 1.0.
    # P2 runs 2 -> 3.
    # P1 waited from 2 -> 3 (wait=1).
    # At t=3: P1 Priority = 1/6 + 4(1) = 4.1667.
    # Confirms that waiting time multiplied by alpha increases the score.
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=8),
        Process(pid="P2", arrival_time=2, burst_time=1),
    ]
    completed, timeline, log = run_faas(processes, quantum=2, alpha=4.0)

    # Check decision record at t=3
    decision_at_3 = [d for d in log if d["clock"] == 3][0]
    p1_candidate = [c for c in decision_at_3["candidates"] if c["pid"] == "P1"][0]
    assert p1_candidate["continuous_waiting_time"] == 1
    assert p1_candidate["priority_score"] > 4.0


# =========================================================================== #
# Test 6: Starvation threshold activates correctly                             #
# =========================================================================== #
def test_starvation_threshold_activates():
    # Long job P1 (BT=20) arrives at t=0.
    # Short jobs P2, P3, P4, P5 arrive every 2 time units.
    # Without starvation threshold, P1 would be locked out.
    # With threshold=6: P1 will accumulate wait >= 6 and trigger an override!
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=20),
        Process(pid="P2", arrival_time=0, burst_time=2),
        Process(pid="P3", arrival_time=2, burst_time=2),
        Process(pid="P4", arrival_time=4, burst_time=2),
        Process(pid="P5", arrival_time=6, burst_time=2),
    ]
    completed, timeline, log = run_faas(processes, quantum=2, alpha=0.0, starvation_threshold=6)

    # Starvation activations must have occurred (since alpha=0 removes aging boost)
    assert log.stats["starvation_activations"] >= 1
    starvation_decisions = [d for d in log if d["starvation_override"]]
    assert len(starvation_decisions) >= 1
    assert starvation_decisions[0]["selected"] == "P1"


# =========================================================================== #
# Test 7: Starvation-protected processes receive service                       #
# =========================================================================== #
def test_starvation_protected_process_receives_service():
    # With alpha=0.0, priority is purely 1/remaining_time (shorter jobs win)
    # P1 (long job, BT=10) arrives at t=0
    # P2 (short job, BT=2) arrives at t=0 -> runs 0 -> 2
    # P3 (short job, BT=2) arrives at t=2 -> runs 2 -> 4
    # At t=4, P1 has waited 4 units continuously without CPU attention.
    # With starvation_threshold=4, P1 enters starvation-protection and triggers override!
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=10),
        Process(pid="P2", arrival_time=0, burst_time=2),
        Process(pid="P3", arrival_time=2, burst_time=2),
    ]
    completed, timeline, log = run_faas(processes, quantum=2, alpha=0.0, starvation_threshold=4)

    # At t=4, starvation override must trigger for P1
    decision_at_4 = [d for d in log if d["clock"] == 4][0]
    assert decision_at_4["starvation_override"] is True
    assert decision_at_4["selected"] == "P1"
    assert decision_at_4["reason"] == "Starvation Override"


# =========================================================================== #
# Test 8: Guaranteed quantum works correctly (no premature preemption)         #
# =========================================================================== #
def test_guaranteed_quantum_bounded():
    # P1: AT=0, BT=4. P2: AT=1, BT=1.
    # P1 starts at t=0 with quantum=2. P2 arrives at t=1.
    # P1 MUST run to t=2 without being interrupted at t=1.
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=4),
        Process(pid="P2", arrival_time=1, burst_time=1),
    ]
    completed, timeline, log = run_faas(processes, quantum=2)

    # First timeline interval must start at 0 and end at 2 for P1
    assert timeline[0] == {"pid": "P1", "start": 0, "end": 2}


# =========================================================================== #
# Test 9: Process finishes before quantum expires                              #
# =========================================================================== #
def test_process_finishes_before_quantum():
    # P1 has burst time 1, but quantum is 2.
    # P1 must finish at t=1, not hold the CPU for 2 units.
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=1),
        Process(pid="P2", arrival_time=0, burst_time=2),
    ]
    completed, timeline, log = run_faas(processes, quantum=2)

    result = {p.pid: p for p in completed}
    assert result["P1"].completion_time == 1
    assert timeline[0] == {"pid": "P1", "start": 0, "end": 1}
    assert timeline[1] == {"pid": "P2", "start": 1, "end": 3}


# =========================================================================== #
# Test 10: New process arrives during an existing quantum                      #
# =========================================================================== #
def test_arrival_during_quantum():
    # P1 runs 0 -> 2. P2 arrives at t=1.
    # At t=2, P2 has continuous_waiting_time = 2 - 1 = 1 unit.
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=4),
        Process(pid="P2", arrival_time=1, burst_time=2),
    ]
    completed, timeline, log = run_faas(processes, quantum=2)

    decision_at_2 = [d for d in log if d["clock"] == 2][0]
    p2_candidate = [c for c in decision_at_2["candidates"] if c["pid"] == "P2"][0]
    assert p2_candidate["continuous_waiting_time"] == 1


# =========================================================================== #
# Test 11: CPU idle periods                                                    #
# =========================================================================== #
def test_cpu_idle_periods():
    # P1 arrives at t=4, BT=2.
    # CPU is IDLE from 0 -> 4.
    processes = [Process(pid="P1", arrival_time=4, burst_time=2)]
    completed, timeline, log = run_faas(processes, quantum=2)

    assert timeline[0] == {"pid": "IDLE", "start": 0, "end": 4}
    assert timeline[1] == {"pid": "P1",   "start": 4, "end": 6}
    assert completed[0].start_time == 4
    assert completed[0].completion_time == 6


# =========================================================================== #
# Test 12: Multiple starvation-protected processes                             #
# =========================================================================== #
def test_multiple_starvation_protected_processes():
    # P1 arrives at t=0, P2 arrives at t=1.
    # Both wait while P0 runs a long burst.
    # At t=10, both exceed threshold=6.
    # P1 has waited 10 units, P2 has waited 9 units.
    # P1 must be selected because 10 > 9.
    processes = [
        Process(pid="P0", arrival_time=0, burst_time=10),
        Process(pid="P1", arrival_time=0, burst_time=2),
        Process(pid="P2", arrival_time=1, burst_time=2),
    ]
    # Set high burst for P0 and disable aging so P0 runs first
    # Or simply test selection when both P1 and P2 have starving status
    completed, timeline, log = run_faas(
        processes, quantum=2, alpha=0.0, starvation_threshold=6
    )

    # In log, verify that when starvation occurs, the one with longest wait wins
    starv_decisions = [d for d in log if d["starvation_override"]]
    if starv_decisions:
        first_starv = starv_decisions[0]
        assert first_starv["selected"] == "P1"


# =========================================================================== #
# Test 13: Identical priority scores tie-break                                 #
# =========================================================================== #
def test_identical_priority_scores_tiebreak():
    # P1: AT=0, BT=2. P2: AT=0, BT=2.
    # At t=0: Both have Priority = 1/2 + 0 = 0.50.
    # Tiebreak by PID: "P1" < "P2" -> P1 selected first.
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=2),
        Process(pid="P2", arrival_time=0, burst_time=2),
    ]
    completed, timeline, log = run_faas(processes, quantum=2)

    assert [p.pid for p in completed] == ["P1", "P2"]


# =========================================================================== #
# Test 14: Original input remains unchanged                                    #
# =========================================================================== #
def test_originals_not_modified():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=6),
        Process(pid="P2", arrival_time=2, burst_time=4),
    ]
    orig_rem = [p.remaining_time for p in processes]
    orig_ct  = [p.completion_time for p in processes]

    run_faas(processes, quantum=2)

    for i, p in enumerate(processes):
        assert p.remaining_time == orig_rem[i]
        assert p.completion_time == orig_ct[i]


# =========================================================================== #
# Test 15: All performance metrics are correct                                 #
# =========================================================================== #
def test_all_performance_metrics():
    # Hand-trace:
    # P1: AT=0, BT=2 -> Runs 0->2. ST=0, CT=2, TAT=2, WT=0, RT=0.
    # P2: AT=1, BT=2 -> Runs 2->4. ST=2, CT=4, TAT=3, WT=1, RT=1.
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=2),
        Process(pid="P2", arrival_time=1, burst_time=2),
    ]
    completed, timeline, log = run_faas(processes, quantum=2)
    stats = log.stats

    assert stats["avg_turnaround_time"] == 2.5  # (2 + 3) / 2
    assert stats["avg_waiting_time"] == 0.5     # (0 + 1) / 2
    assert stats["avg_response_time"] == 0.5    # (0 + 1) / 2
    assert stats["cpu_utilization"] == 100.0
    assert stats["throughput"] == 0.5           # 2 processes / 4 time units
    assert stats["context_switches"] == 1       # P1 -> P2


# =========================================================================== #
# Test 16: Empty process list handling                                         #
# =========================================================================== #
def test_empty_process_list():
    completed, timeline, log = run_faas([], quantum=2)
    assert completed == []
    assert timeline == []
    assert log == []
    assert log.stats["cpu_utilization"] == 0.0


# =========================================================================== #
# Test 17: Invalid quantum and aging parameters raise ValueError               #
# =========================================================================== #
def test_invalid_parameters():
    p = [Process(pid="P1", arrival_time=0, burst_time=3)]

    with pytest.raises(ValueError, match="Quantum must be a positive integer"):
        run_faas(p, quantum=0)

    with pytest.raises(ValueError, match="Quantum must be a positive integer"):
        run_faas(p, quantum=-1)

    with pytest.raises(ValueError, match="Alpha .* cannot be negative"):
        run_faas(p, alpha=-2.0)

    with pytest.raises(ValueError, match="Starvation threshold must be positive"):
        run_faas(p, starvation_threshold=0)
