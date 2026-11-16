"""
test_sjf.py
-----------
Test suite for the SJF (Shortest Job First) scheduling algorithm.

Each test case:
  1. Defines a set of processes.
  2. Runs run_sjf().
  3. Verifies EVERY metric independently with hand-traced expected values.

Hand-trace legend:
  AT  = Arrival Time
  BT  = Burst Time
  ST  = Start Time (first CPU grant)
  CT  = Completion Time
  TAT = Turnaround Time = CT - AT
  WT  = Waiting Time    = TAT - BT
  RT  = Response Time   = ST - AT
"""

import pytest
from schedulers.process import Process
from schedulers.sjf import run_sjf


# =========================================================================== #
# Test 1: Three processes with different burst times, all arriving at t=0      #
# =========================================================================== #
#
# Processes:
#   P1: AT=0, BT=6
#   P2: AT=0, BT=3   ← shortest
#   P3: AT=0, BT=8   ← longest
#
# SJF order: P2 → P1 → P3
#
# Timeline:
#   P2: 0  → 3    CT=3,  TAT=3-0=3,  WT=3-3=0,   RT=0-0=0
#   P1: 3  → 9    CT=9,  TAT=9-0=9,  WT=9-6=3,   RT=3-0=3
#   P3: 9  → 17   CT=17, TAT=17-0=17,WT=17-8=9,  RT=9-0=9
#
# =========================================================================== #
def test_different_burst_times():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=6),
        Process(pid="P2", arrival_time=0, burst_time=3),
        Process(pid="P3", arrival_time=0, burst_time=8),
    ]
    completed, timeline = run_sjf(processes)

    # Build a lookup dict: pid → process
    result = {p.pid: p for p in completed}

    # --- P2 (shortest, runs first) ---
    assert result["P2"].completion_time == 3
    assert result["P2"].turnaround_time == 3   # 3 - 0
    assert result["P2"].waiting_time == 0      # 3 - 3
    assert result["P2"].response_time == 0     # 0 - 0

    # --- P1 (runs second) ---
    assert result["P1"].completion_time == 9
    assert result["P1"].turnaround_time == 9   # 9 - 0
    assert result["P1"].waiting_time == 3      # 9 - 6
    assert result["P1"].response_time == 3     # 3 - 0

    # --- P3 (longest, runs last) ---
    assert result["P3"].completion_time == 17
    assert result["P3"].turnaround_time == 17  # 17 - 0
    assert result["P3"].waiting_time == 9      # 17 - 8
    assert result["P3"].response_time == 9     # 9 - 0

    # Gantt timeline: exactly 3 entries, no IDLE
    assert len(timeline) == 3
    assert timeline[0] == {"pid": "P2", "start": 0, "end": 3}
    assert timeline[1] == {"pid": "P1", "start": 3, "end": 9}
    assert timeline[2] == {"pid": "P3", "start": 9, "end": 17}


# =========================================================================== #
# Test 2: Processes arriving at different times                                #
# =========================================================================== #
#
# Processes:
#   P1: AT=0, BT=7
#   P2: AT=2, BT=4
#   P3: AT=4, BT=1   ← arrives mid-P1-run
#   P4: AT=5, BT=4
#
# P1 is the only process at t=0 → starts immediately.
# While P1 runs (0→7): P2 arrives at t=2, P3 at t=4, P4 at t=5.
# At t=7, ready_queue = [P2(BT=4), P3(BT=1), P4(BT=4)]
# SJF picks P3 (BT=1). Runs 7→8.
# At t=8, ready_queue = [P2(BT=4), P4(BT=4)]. Tie: AT=2 vs AT=5 → P2 first.
# P2 runs 8→12. P4 runs 12→16.
#
# Metrics:
#   P1: ST=0,  CT=7,  TAT=7-0=7,   WT=7-7=0,   RT=0-0=0
#   P3: ST=7,  CT=8,  TAT=8-4=4,   WT=4-1=3,   RT=7-4=3
#   P2: ST=8,  CT=12, TAT=12-2=10, WT=10-4=6,  RT=8-2=6
#   P4: ST=12, CT=16, TAT=16-5=11, WT=11-4=7,  RT=12-5=7
#
# =========================================================================== #
def test_different_arrival_times():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=7),
        Process(pid="P2", arrival_time=2, burst_time=4),
        Process(pid="P3", arrival_time=4, burst_time=1),
        Process(pid="P4", arrival_time=5, burst_time=4),
    ]
    completed, timeline = run_sjf(processes)
    result = {p.pid: p for p in completed}

    assert result["P1"].completion_time == 7
    assert result["P1"].turnaround_time == 7
    assert result["P1"].waiting_time == 0
    assert result["P1"].response_time == 0

    assert result["P3"].completion_time == 8
    assert result["P3"].turnaround_time == 4   # 8 - 4
    assert result["P3"].waiting_time == 3      # 4 - 1
    assert result["P3"].response_time == 3     # 7 - 4

    assert result["P2"].completion_time == 12
    assert result["P2"].turnaround_time == 10  # 12 - 2
    assert result["P2"].waiting_time == 6      # 10 - 4
    assert result["P2"].response_time == 6     # 8 - 2

    assert result["P4"].completion_time == 16
    assert result["P4"].turnaround_time == 11  # 16 - 5
    assert result["P4"].waiting_time == 7      # 11 - 4
    assert result["P4"].response_time == 7     # 12 - 5


# =========================================================================== #
# Test 3: Two processes with IDENTICAL burst times (tie-breaking by AT then PID)
# =========================================================================== #
#
# Processes:
#   P1: AT=0, BT=4
#   P2: AT=0, BT=4   ← same burst AND same arrival → tiebreak by pid
#
# pid tiebreak: "P1" < "P2" → P1 runs first.
#
# Timeline: P1: 0→4,  P2: 4→8
#
# P1: CT=4, TAT=4, WT=0, RT=0
# P2: CT=8, TAT=8, WT=4, RT=4
#
# =========================================================================== #
def test_identical_burst_times():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=4),
        Process(pid="P2", arrival_time=0, burst_time=4),
    ]
    completed, timeline = run_sjf(processes)
    result = {p.pid: p for p in completed}

    # Confirm execution order via completion times
    assert result["P1"].completion_time == 4
    assert result["P1"].turnaround_time == 4
    assert result["P1"].waiting_time == 0
    assert result["P1"].response_time == 0

    assert result["P2"].completion_time == 8
    assert result["P2"].turnaround_time == 8
    assert result["P2"].waiting_time == 4
    assert result["P2"].response_time == 4

    # P1 must appear before P2 in timeline
    pids_in_order = [entry["pid"] for entry in timeline]
    assert pids_in_order == ["P1", "P2"]


# =========================================================================== #
# Test 4: CPU idle time before first arrival                                   #
# =========================================================================== #
#
# Processes:
#   P1: AT=5, BT=3
#
# Clock starts at 0. No process at t=0.
# CPU is IDLE from 0→5. P1 runs 5→8.
#
# P1: ST=5, CT=8, TAT=8-5=3, WT=3-3=0, RT=5-5=0
#
# =========================================================================== #
def test_cpu_idle_before_first_arrival():
    processes = [
        Process(pid="P1", arrival_time=5, burst_time=3),
    ]
    completed, timeline = run_sjf(processes)
    result = {p.pid: p for p in completed}

    # Verify IDLE entry appears in Gantt
    assert timeline[0] == {"pid": "IDLE", "start": 0, "end": 5}
    assert timeline[1] == {"pid": "P1",   "start": 5, "end": 8}

    assert result["P1"].completion_time == 8
    assert result["P1"].turnaround_time == 3   # 8 - 5
    assert result["P1"].waiting_time == 0      # 3 - 3
    assert result["P1"].response_time == 0     # 5 - 5


# =========================================================================== #
# Test 5: All processes arriving at time zero                                  #
# =========================================================================== #
#
# Processes:
#   P1: AT=0, BT=5
#   P2: AT=0, BT=2   ← shortest
#   P3: AT=0, BT=4
#
# SJF order: P2(2) → P3(4) → P1(5)
#
# P2: 0→2:   CT=2,  TAT=2,  WT=0,  RT=0
# P3: 2→6:   CT=6,  TAT=6,  WT=2,  RT=2
# P1: 6→11:  CT=11, TAT=11, WT=6,  RT=6
#
# =========================================================================== #
def test_all_arrive_at_zero():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=5),
        Process(pid="P2", arrival_time=0, burst_time=2),
        Process(pid="P3", arrival_time=0, burst_time=4),
    ]
    completed, timeline = run_sjf(processes)
    result = {p.pid: p for p in completed}

    assert result["P2"].completion_time == 2
    assert result["P2"].waiting_time == 0
    assert result["P2"].response_time == 0

    assert result["P3"].completion_time == 6
    assert result["P3"].turnaround_time == 6
    assert result["P3"].waiting_time == 2
    assert result["P3"].response_time == 2

    assert result["P1"].completion_time == 11
    assert result["P1"].turnaround_time == 11
    assert result["P1"].waiting_time == 6
    assert result["P1"].response_time == 6

    pids_in_order = [entry["pid"] for entry in timeline]
    assert pids_in_order == ["P2", "P3", "P1"]


# =========================================================================== #
# Test 6: Long process arrives first, short processes queue up behind it       #
# =========================================================================== #
#
# This tests that SJF is truly non-preemptive:
# P1 (long) must run to completion before short processes are served.
#
# Processes:
#   P1: AT=0, BT=10   ← starts immediately (only process at t=0)
#   P2: AT=1, BT=2
#   P3: AT=2, BT=1    ← shortest, but P1 cannot be interrupted
#
# P1 runs 0→10 uninterrupted.
# At t=10, ready_queue = [P2(BT=2), P3(BT=1)] → pick P3
# P3 runs 10→11. P2 runs 11→13.
#
# P1: ST=0,  CT=10, TAT=10,  WT=0,  RT=0
# P3: ST=10, CT=11, TAT=9,   WT=8,  RT=8
# P2: ST=11, CT=13, TAT=12,  WT=10, RT=10
#
# =========================================================================== #
def test_long_process_first_nonpreemptive():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=10),
        Process(pid="P2", arrival_time=1, burst_time=2),
        Process(pid="P3", arrival_time=2, burst_time=1),
    ]
    completed, timeline = run_sjf(processes)
    result = {p.pid: p for p in completed}

    # P1 must run completely first (non-preemptive proof)
    assert timeline[0] == {"pid": "P1", "start": 0, "end": 10}

    assert result["P1"].completion_time == 10
    assert result["P1"].turnaround_time == 10
    assert result["P1"].waiting_time == 0
    assert result["P1"].response_time == 0

    # P3 (shorter) beats P2 when queue is evaluated at t=10
    assert timeline[1] == {"pid": "P3", "start": 10, "end": 11}
    assert result["P3"].completion_time == 11
    assert result["P3"].turnaround_time == 9    # 11 - 2
    assert result["P3"].waiting_time == 8       # 9 - 1
    assert result["P3"].response_time == 8      # 10 - 2

    assert timeline[2] == {"pid": "P2", "start": 11, "end": 13}
    assert result["P2"].completion_time == 13
    assert result["P2"].turnaround_time == 12   # 13 - 1
    assert result["P2"].waiting_time == 10      # 12 - 2
    assert result["P2"].response_time == 10     # 11 - 1


# =========================================================================== #
# Extra guard: verify originals are NOT modified by run_sjf                   #
# =========================================================================== #
def test_originals_not_modified():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=5),
        Process(pid="P2", arrival_time=1, burst_time=3),
    ]
    # Snapshot original state
    original_remaining = [p.remaining_time for p in processes]
    original_ct        = [p.completion_time for p in processes]

    run_sjf(processes)

    # Originals must be unchanged
    for i, p in enumerate(processes):
        assert p.remaining_time == original_remaining[i], \
            f"{p.pid}: original remaining_time was modified!"
        assert p.completion_time == original_ct[i], \
            f"{p.pid}: original completion_time was modified!"
