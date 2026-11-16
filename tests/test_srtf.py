"""
test_srtf.py
------------
Test suite for the SRTF (Shortest Remaining Time First) scheduling algorithm.

Each test case:
  1. Defines a process set.
  2. Runs run_srtf().
  3. Verifies EVERY metric with hand-traced expected values.

Hand-trace legend:
  AT   = Arrival Time
  BT   = Burst Time (original, full)
  ST   = Start Time (clock when process FIRST got the CPU)
  CT   = Completion Time
  TAT  = Turnaround Time = CT - AT
  WT   = Waiting Time    = TAT - BT
  RT   = Response Time   = ST - AT
"""

import pytest
from schedulers.process import Process
from schedulers.srtf import run_srtf


# =========================================================================== #
# Test 1: All processes arrive at t=0 (SRTF behaves identically to SJF here) #
# =========================================================================== #
#
# When all processes arrive simultaneously, there is no preemption possible.
# SRTF and SJF produce the same schedule in this case.
#
# Processes:
#   P1: AT=0, BT=5
#   P2: AT=0, BT=3
#   P3: AT=0, BT=1   ← shortest
#
# SRTF order: P3(1) → P2(3) → P1(5)
#
# P3: ST=0, CT=1,  TAT=1-0=1,  WT=1-1=0,  RT=0-0=0
# P2: ST=1, CT=4,  TAT=4-0=4,  WT=4-3=1,  RT=1-0=1
# P1: ST=4, CT=9,  TAT=9-0=9,  WT=9-5=4,  RT=4-0=4
#
# =========================================================================== #
def test_all_arrive_at_zero():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=5),
        Process(pid="P2", arrival_time=0, burst_time=3),
        Process(pid="P3", arrival_time=0, burst_time=1),
    ]
    completed, timeline = run_srtf(processes)
    result = {p.pid: p for p in completed}

    assert result["P3"].completion_time == 1
    assert result["P3"].turnaround_time == 1
    assert result["P3"].waiting_time == 0
    assert result["P3"].response_time == 0

    assert result["P2"].completion_time == 4
    assert result["P2"].turnaround_time == 4
    assert result["P2"].waiting_time == 1
    assert result["P2"].response_time == 1

    assert result["P1"].completion_time == 9
    assert result["P1"].turnaround_time == 9
    assert result["P1"].waiting_time == 4
    assert result["P1"].response_time == 4

    # Gantt: P3[0→1], P2[1→4], P1[4→9]
    assert timeline == [
        {"pid": "P3", "start": 0, "end": 1},
        {"pid": "P2", "start": 1, "end": 4},
        {"pid": "P1", "start": 4, "end": 9},
    ]


# =========================================================================== #
# Test 2: Shorter process arrives while a longer process is executing          #
# =========================================================================== #
#
# This is the fundamental SRTF behaviour: a new arrival triggers preemption.
#
# Processes:
#   P1: AT=0, BT=8    ← starts immediately, but gets preempted at t=1
#   P2: AT=1, BT=4    ← arrives with remaining=4 < P1's remaining=7 → preempts
#
# Trace:
#   t=0:  P1 starts. Run until min(next_arrival=1, P1_done=8) = 1.
#         P1 remaining: 8 → 7. Timeline: P1[0→1]. clock=1.
#   t=1:  P2 arrives. Candidates: P1(7), P2(4). Best=P2(4). PREEMPT P1.
#         P2.start_time=1. Run until min(inf, 1+4=5) = 5.
#         P2 remaining: 4 → 0. Timeline: P2[1→5]. clock=5. P2 DONE.
#         CT=5, TAT=5-1=4, WT=4-4=0, RT=1-1=0.
#   t=5:  Ready=[P1(7)]. P1 runs. Run until min(inf, 5+7=12) = 12.
#         P1 remaining: 7 → 0. Timeline: P1[5→12]. clock=12. P1 DONE.
#         CT=12, TAT=12-0=12, WT=12-8=4, RT=0-0=0.
#
# =========================================================================== #
def test_preemption_on_arrival():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=8),
        Process(pid="P2", arrival_time=1, burst_time=4),
    ]
    completed, timeline = run_srtf(processes)
    result = {p.pid: p for p in completed}

    # P2 finishes first despite arriving later (preempted P1)
    assert result["P2"].completion_time == 5
    assert result["P2"].turnaround_time == 4   # 5 - 1
    assert result["P2"].waiting_time == 0      # 4 - 4
    assert result["P2"].response_time == 0     # 1 - 1

    # P1 finishes last (was preempted, resumed after P2)
    assert result["P1"].completion_time == 12
    assert result["P1"].turnaround_time == 12  # 12 - 0
    assert result["P1"].waiting_time == 4      # 12 - 8
    assert result["P1"].response_time == 0     # 0 - 0

    # Gantt timeline: exactly 3 entries
    assert timeline == [
        {"pid": "P1", "start": 0, "end": 1},
        {"pid": "P2", "start": 1, "end": 5},
        {"pid": "P1", "start": 5, "end": 12},
    ]


# =========================================================================== #
# Test 3: Multiple preemptions                                                 #
# =========================================================================== #
#
# P1 is preempted by P2, then P2 is preempted by P3.
#
# Processes:
#   P1: AT=0, BT=9
#   P2: AT=1, BT=4
#   P3: AT=2, BT=2
#
# Trace:
#   t=0:  P1 starts. Run until min(1, 9)=1. P1 rem=8. Timeline: P1[0→1].
#   t=1:  P2 arrives. P2(4)<P1(8). PREEMPT P1. P2.start=1.
#         Run until min(2, 1+4=5)=2. P2 rem=3. Timeline: P2[1→2].
#   t=2:  P3 arrives. P3(2)<P2(3). PREEMPT P2. P3.start=2.
#         Run until min(inf, 2+2=4)=4. P3 rem=0. Timeline: P3[2→4]. P3 DONE.
#         CT=4, TAT=2, WT=0, RT=0.
#   t=4:  Ready=[P1(8), P2(3)]. Best=P2(3). P2 runs.
#         Run until min(inf, 4+3=7)=7. P2 rem=0. Timeline: P2[4→7]. P2 DONE.
#         CT=7, TAT=6, WT=2, RT=0.
#   t=7:  Ready=[P1(8)]. P1 runs.
#         Run until min(inf, 7+8=15)=15. P1 rem=0. Timeline: P1[7→15]. P1 DONE.
#         CT=15, TAT=15, WT=6, RT=0.
#
# =========================================================================== #
def test_multiple_preemptions():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=9),
        Process(pid="P2", arrival_time=1, burst_time=4),
        Process(pid="P3", arrival_time=2, burst_time=2),
    ]
    completed, timeline = run_srtf(processes)
    result = {p.pid: p for p in completed}

    assert result["P1"].completion_time == 15
    assert result["P1"].turnaround_time == 15
    assert result["P1"].waiting_time == 6
    assert result["P1"].response_time == 0

    assert result["P2"].completion_time == 7
    assert result["P2"].turnaround_time == 6   # 7 - 1
    assert result["P2"].waiting_time == 2      # 6 - 4
    assert result["P2"].response_time == 0     # 1 - 1

    assert result["P3"].completion_time == 4
    assert result["P3"].turnaround_time == 2   # 4 - 2
    assert result["P3"].waiting_time == 0      # 2 - 2
    assert result["P3"].response_time == 0     # 2 - 2

    assert timeline == [
        {"pid": "P1", "start": 0,  "end": 1},
        {"pid": "P2", "start": 1,  "end": 2},
        {"pid": "P3", "start": 2,  "end": 4},
        {"pid": "P2", "start": 4,  "end": 7},
        {"pid": "P1", "start": 7,  "end": 15},
    ]


# =========================================================================== #
# Test 4: Equal remaining times — no preemption (earlier arrival wins)         #
# =========================================================================== #
#
# When P2 arrives, P1's remaining time equals P2's remaining time.
# Tiebreak: earlier arrival_time → P1 (arrived at 0) keeps the CPU.
# This confirms NO unnecessary preemption occurs on a tie.
#
# Processes:
#   P1: AT=0, BT=5
#   P2: AT=1, BT=4   ← arrives when P1 has 4 remaining (a tie!)
#
# Trace:
#   t=0:  P1 starts. Run until min(1, 5)=1. P1 rem=4. Timeline: P1[0→1].
#   t=1:  P2 arrives. Candidates: P1(rem=4), P2(rem=4). TIE on remaining.
#         Tiebreak: arrival P1(0) < P2(1). P1 wins → NO PREEMPTION.
#         Run until min(inf, 1+4=5)=5. P1 rem=0. Timeline: P1[0→5] (merged). P1 DONE.
#         CT=5, TAT=5, WT=0, RT=0.
#   t=5:  Ready=[P2(4)]. P2 runs. Run until min(inf, 9)=9. P2 DONE.
#         CT=9, TAT=8, WT=4, RT=4.
#
# =========================================================================== #
def test_equal_remaining_no_preemption():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=5),
        Process(pid="P2", arrival_time=1, burst_time=4),
    ]
    completed, timeline = run_srtf(processes)
    result = {p.pid: p for p in completed}

    # P1 must complete first (kept CPU despite tie)
    assert result["P1"].completion_time == 5
    assert result["P1"].turnaround_time == 5
    assert result["P1"].waiting_time == 0
    assert result["P1"].response_time == 0

    assert result["P2"].completion_time == 9
    assert result["P2"].turnaround_time == 8   # 9 - 1
    assert result["P2"].waiting_time == 4      # 8 - 4
    assert result["P2"].response_time == 4     # 5 - 1

    # Timeline must be only 2 entries (P1 merged, no fragmentation)
    assert timeline == [
        {"pid": "P1", "start": 0, "end": 5},
        {"pid": "P2", "start": 5, "end": 9},
    ]


# =========================================================================== #
# Test 5: CPU idle time before first arrival                                   #
# =========================================================================== #
#
# Clock starts at 0. P1 doesn't arrive until t=4.
# CPU must be IDLE from 0→4, then run P1 from 4→7.
#
# Processes:
#   P1: AT=4, BT=3
#
# P1: ST=4, CT=7, TAT=3, WT=0, RT=0
#
# =========================================================================== #
def test_cpu_idle_before_first_arrival():
    processes = [
        Process(pid="P1", arrival_time=4, burst_time=3),
    ]
    completed, timeline = run_srtf(processes)
    result = {p.pid: p for p in completed}

    assert timeline[0] == {"pid": "IDLE", "start": 0, "end": 4}
    assert timeline[1] == {"pid": "P1",   "start": 4, "end": 7}

    assert result["P1"].completion_time == 7
    assert result["P1"].turnaround_time == 3   # 7 - 4
    assert result["P1"].waiting_time == 0      # 3 - 3
    assert result["P1"].response_time == 0     # 4 - 4


# =========================================================================== #
# Test 6: Identical arrival times — tiebreak by PID                           #
# =========================================================================== #
#
# Two processes arrive simultaneously with equal burst times.
# No preemption possible. PID order decides who runs first.
#
# Processes:
#   P1: AT=0, BT=4
#   P2: AT=0, BT=4
#
# Tiebreak: burst=4 (tie), arrival=0 (tie), PID: "P1" < "P2" → P1 first.
#
# P1: 0→4, CT=4, TAT=4, WT=0, RT=0
# P2: 4→8, CT=8, TAT=8, WT=4, RT=4
#
# =========================================================================== #
def test_identical_arrivals_tiebreak_pid():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=4),
        Process(pid="P2", arrival_time=0, burst_time=4),
    ]
    completed, timeline = run_srtf(processes)
    result = {p.pid: p for p in completed}

    # P1 must run before P2
    pids_in_order = [entry["pid"] for entry in timeline]
    assert pids_in_order == ["P1", "P2"]

    assert result["P1"].completion_time == 4
    assert result["P1"].waiting_time == 0
    assert result["P1"].response_time == 0

    assert result["P2"].completion_time == 8
    assert result["P2"].turnaround_time == 8
    assert result["P2"].waiting_time == 4
    assert result["P2"].response_time == 4


# =========================================================================== #
# Test 7: Single process                                                       #
# =========================================================================== #
#
# Simplest possible case — one process, no decisions needed.
#
# P1: AT=0, BT=5 → runs 0→5, CT=5, TAT=5, WT=0, RT=0
#
# =========================================================================== #
def test_single_process():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=5),
    ]
    completed, timeline = run_srtf(processes)
    result = {p.pid: p for p in completed}

    assert len(completed) == 1
    assert result["P1"].completion_time == 5
    assert result["P1"].turnaround_time == 5
    assert result["P1"].waiting_time == 0
    assert result["P1"].response_time == 0

    assert timeline == [{"pid": "P1", "start": 0, "end": 5}]


# =========================================================================== #
# Test 8: Long process with several short arrivals                             #
# =========================================================================== #
#
# A long process starts, then gets repeatedly preempted by shorter arrivals.
# Also tests TIMELINE MERGING: P2 runs in two separate windows (3→5 merged).
#
# Processes:
#   P1: AT=0, BT=15
#   P2: AT=1, BT=3
#   P3: AT=2, BT=1
#   P4: AT=4, BT=2
#
# Trace:
#   t=0:  P1 starts. Run until min(1, 15)=1. P1 rem=14. Timeline: P1[0→1].
#   t=1:  P2 arrives. P2(3)<P1(14). PREEMPT P1. P2.start=1.
#         Run until min(2, 1+3=4)=2. P2 rem=2. Timeline: P2[1→2].
#   t=2:  P3 arrives. P3(1)<P2(2). PREEMPT P2. P3.start=2.
#         Run until min(4, 2+1=3)=3. P3 rem=0. Timeline: P3[2→3]. P3 DONE.
#         CT=3, TAT=3-2=1, WT=0, RT=0.
#   t=3:  Ready=[P1(14), P2(2)]. Best=P2(2). P2 runs.
#         Run until min(4, 3+2=5)=4. P2 rem=1. Timeline: P2[3→4].
#   t=4:  P4 arrives. Ready=[P1(14), P4(2)]. Current=P2(1). 
#         All: P1(14), P4(2), P2(1). Best=P2(1). NO PREEMPTION (P2 shortest).
#         Run until min(inf, 4+1=5)=5. P2 rem=0. 
#         Merge P2: P2[3→4] extends to P2[3→5]. P2 DONE.
#         CT=5, TAT=5-1=4, WT=4-3=1, RT=1-1=0.
#   t=5:  Ready=[P1(14), P4(2)]. Best=P4(2). P4.start=5.
#         Run until min(inf, 5+2=7)=7. P4 rem=0. Timeline: P4[5→7]. P4 DONE.
#         CT=7, TAT=7-4=3, WT=3-2=1, RT=5-4=1.
#   t=7:  Ready=[P1(14)]. P1 runs.
#         Run until min(inf, 7+14=21)=21. P1 rem=0. Timeline: P1[7→21]. P1 DONE.
#         CT=21, TAT=21-0=21, WT=21-15=6, RT=0-0=0.
#
# =========================================================================== #
def test_long_process_with_short_arrivals():
    processes = [
        Process(pid="P1", arrival_time=0,  burst_time=15),
        Process(pid="P2", arrival_time=1,  burst_time=3),
        Process(pid="P3", arrival_time=2,  burst_time=1),
        Process(pid="P4", arrival_time=4,  burst_time=2),
    ]
    completed, timeline = run_srtf(processes)
    result = {p.pid: p for p in completed}

    assert result["P1"].completion_time == 21
    assert result["P1"].turnaround_time == 21
    assert result["P1"].waiting_time == 6
    assert result["P1"].response_time == 0

    assert result["P2"].completion_time == 5
    assert result["P2"].turnaround_time == 4   # 5 - 1
    assert result["P2"].waiting_time == 1      # 4 - 3
    assert result["P2"].response_time == 0     # 1 - 1

    assert result["P3"].completion_time == 3
    assert result["P3"].turnaround_time == 1   # 3 - 2
    assert result["P3"].waiting_time == 0      # 1 - 1
    assert result["P3"].response_time == 0     # 2 - 2

    assert result["P4"].completion_time == 7
    assert result["P4"].turnaround_time == 3   # 7 - 4
    assert result["P4"].waiting_time == 1      # 3 - 2
    assert result["P4"].response_time == 1     # 5 - 4

    # Verify merged timeline (P2 appears in one merged block 3→5)
    assert timeline == [
        {"pid": "P1", "start": 0,  "end": 1},
        {"pid": "P2", "start": 1,  "end": 2},
        {"pid": "P3", "start": 2,  "end": 3},
        {"pid": "P2", "start": 3,  "end": 5},  # merged from [3→4] + [4→5]
        {"pid": "P4", "start": 5,  "end": 7},
        {"pid": "P1", "start": 7,  "end": 21},
    ]


# =========================================================================== #
# Test 9: Original process list must NOT be modified                           #
# =========================================================================== #
#
# SRTF must work on copies. The original objects passed in must remain exactly
# as they were created.
#
# =========================================================================== #
def test_originals_not_modified():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=6),
        Process(pid="P2", arrival_time=2, burst_time=3),
    ]
    # Snapshot original state
    original_remaining = [p.remaining_time  for p in processes]
    original_ct        = [p.completion_time for p in processes]
    original_start     = [p.start_time      for p in processes]

    run_srtf(processes)

    for i, p in enumerate(processes):
        assert p.remaining_time  == original_remaining[i], \
            f"{p.pid}: remaining_time was modified!"
        assert p.completion_time == original_ct[i], \
            f"{p.pid}: completion_time was modified!"
        assert p.start_time      == original_start[i], \
            f"{p.pid}: start_time was modified!"


# =========================================================================== #
# Test 10: Comprehensive manual verification of all metrics                    #
# =========================================================================== #
#
# A three-process scenario with preemptions. All four metrics verified,
# plus average metrics calculated.
#
# Processes:
#   P1: AT=0, BT=6
#   P2: AT=1, BT=3
#   P3: AT=2, BT=1
#
# Trace:
#   t=0:  P1 starts. Run until min(1, 6)=1. P1 rem=5. Timeline: P1[0→1].
#   t=1:  P2 arrives. P2(3)<P1(5). PREEMPT P1. P2.start=1.
#         Run until min(2, 1+3=4)=2. P2 rem=2. Timeline: P2[1→2].
#   t=2:  P3 arrives. P3(1)<P2(2). PREEMPT P2. P3.start=2.
#         Run until min(inf, 2+1=3)=3. P3 rem=0. Timeline: P3[2→3]. P3 DONE.
#         CT=3, TAT=3-2=1, WT=1-1=0, RT=2-2=0.
#   t=3:  Ready=[P1(5), P2(2)]. Best=P2(2). P2 runs.
#         Run until min(inf, 3+2=5)=5. P2 rem=0. Timeline: P2[3→5]. P2 DONE.
#         CT=5, TAT=5-1=4, WT=4-3=1, RT=1-1=0.
#   t=5:  Ready=[P1(5)]. P1 runs.
#         Run until min(inf, 5+5=10)=10. P1 rem=0. Timeline: P1[5→10]. P1 DONE.
#         CT=10, TAT=10-0=10, WT=10-6=4, RT=0-0=0.
#
# Average metrics:
#   Avg TAT = (10 + 4 + 1) / 3 = 5.0
#   Avg WT  = (4  + 1 + 0) / 3 = 1.667
#   Avg RT  = (0  + 0 + 0) / 3 = 0.0
#
# =========================================================================== #
def test_all_metrics_manual_verification():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=6),
        Process(pid="P2", arrival_time=1, burst_time=3),
        Process(pid="P3", arrival_time=2, burst_time=1),
    ]
    completed, timeline = run_srtf(processes)
    result = {p.pid: p for p in completed}

    # --- Individual metrics ---
    assert result["P1"].completion_time == 10
    assert result["P1"].turnaround_time == 10   # 10 - 0
    assert result["P1"].waiting_time == 4       # 10 - 6
    assert result["P1"].response_time == 0      # 0 - 0

    assert result["P2"].completion_time == 5
    assert result["P2"].turnaround_time == 4    # 5 - 1
    assert result["P2"].waiting_time == 1       # 4 - 3
    assert result["P2"].response_time == 0      # 1 - 1

    assert result["P3"].completion_time == 3
    assert result["P3"].turnaround_time == 1    # 3 - 2
    assert result["P3"].waiting_time == 0       # 1 - 1
    assert result["P3"].response_time == 0      # 2 - 2

    # --- Average metrics (computed from results) ---
    n = len(completed)
    avg_tat = sum(p.turnaround_time for p in completed) / n
    avg_wt  = sum(p.waiting_time    for p in completed) / n
    avg_rt  = sum(p.response_time   for p in completed) / n

    assert abs(avg_tat - 5.0)   < 1e-9
    assert abs(avg_wt  - (5/3)) < 1e-9
    assert abs(avg_rt  - 0.0)   < 1e-9

    # --- Gantt timeline ---
    assert timeline == [
        {"pid": "P1", "start": 0, "end": 1},
        {"pid": "P2", "start": 1, "end": 2},
        {"pid": "P3", "start": 2, "end": 3},
        {"pid": "P2", "start": 3, "end": 5},
        {"pid": "P1", "start": 5, "end": 10},
    ]


# =========================================================================== #
# Regression: SJF tests must still pass unmodified                            #
# (run via: pytest tests/ -v to include both test files)                      #
# =========================================================================== #
# No code needed here — running "pytest tests/" automatically picks up
# both test_sjf.py and test_srtf.py and runs them together.
