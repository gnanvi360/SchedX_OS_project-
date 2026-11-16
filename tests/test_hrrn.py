"""
test_hrrn.py
------------
Test suite for the HRRN (Highest Response Ratio Next) scheduling algorithm.

Formulas:
  W   = Waiting time so far in ready queue = clock - arrival_time
  B   = Burst time
  RR  = (W + B) / B = 1 + W / B

Output Metrics:
  CT  = Completion Time
  TAT = Turnaround Time = CT - AT
  WT  = Waiting Time    = TAT - BT
  RT  = Response Time   = ST - AT
"""

import pytest
from schedulers.process import Process
from schedulers.hrrn import run_hrrn


# =========================================================================== #
# Test 1: All processes arrive at time zero                                    #
# =========================================================================== #
#
# Processes:
#   P1: AT=0, BT=3
#   P2: AT=0, BT=6
#   P3: AT=0, BT=1
#
# At t=0, for all processes: W = 0 -> RR = (0 + B) / B = 1.0.
# Tie-breaker 1: Arrival Time (all 0, tie)
# Tie-breaker 2: Shorter Burst Time -> P3(BT=1) < P1(BT=3) < P2(BT=6).
#
# Schedule:
#   P3 runs 0 -> 1.
#   At t=1:
#     P1: W = 1 - 0 = 1, B = 3 -> RR = (1 + 3) / 3 = 4/3 = 1.333
#     P2: W = 1 - 0 = 1, B = 6 -> RR = (1 + 6) / 6 = 7/6 = 1.167
#     P1 has higher RR (1.333 > 1.167) -> P1 runs 1 -> 4.
#   At t=4:
#     P2: runs 4 -> 10.
#
# Metrics:
#   P3: ST=0, CT=1,  TAT=1,  WT=0, RT=0
#   P1: ST=1, CT=4,  TAT=4,  WT=1, RT=1
#   P2: ST=4, CT=10, TAT=10, WT=4, RT=4
#
# =========================================================================== #
def test_all_arrive_at_zero():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=3),
        Process(pid="P2", arrival_time=0, burst_time=6),
        Process(pid="P3", arrival_time=0, burst_time=1),
    ]
    completed, timeline, decision_log = run_hrrn(processes)
    result = {p.pid: p for p in completed}

    assert result["P3"].completion_time == 1
    assert result["P3"].turnaround_time == 1
    assert result["P3"].waiting_time == 0
    assert result["P3"].response_time == 0

    assert result["P1"].completion_time == 4
    assert result["P1"].turnaround_time == 4
    assert result["P1"].waiting_time == 1
    assert result["P1"].response_time == 1

    assert result["P2"].completion_time == 10
    assert result["P2"].turnaround_time == 10
    assert result["P2"].waiting_time == 4
    assert result["P2"].response_time == 4

    pids_order = [p.pid for p in completed]
    assert pids_order == ["P3", "P1", "P2"]


# =========================================================================== #
# Test 2: Different arrival times                                              #
# =========================================================================== #
#
# Processes:
#   P1: AT=0, BT=4
#   P2: AT=2, BT=4
#   P3: AT=3, BT=2
#
# Trace:
#   t=0: Only P1 is ready. P1 runs 0 -> 4.
#   t=4: Ready: P2 (AT=2, BT=4), P3 (AT=3, BT=2)
#        P2: W = 4 - 2 = 2 -> RR = (2 + 4) / 4 = 6/4 = 1.5
#        P3: W = 4 - 3 = 1 -> RR = (1 + 2) / 2 = 3/2 = 1.5
#        Tie on RR (1.5 == 1.5)!
#        Tie-breaker 1: Arrival Time -> P2 (AT=2) < P3 (AT=3).
#        P2 runs 4 -> 8.
#   t=8: P3 runs 8 -> 10.
#
# Metrics:
#   P1: ST=0, CT=4,  TAT=4, WT=0, RT=0
#   P2: ST=4, CT=8,  TAT=6, WT=2, RT=2
#   P3: ST=8, CT=10, TAT=7, WT=5, RT=5
#
# =========================================================================== #
def test_different_arrival_times():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=4),
        Process(pid="P2", arrival_time=2, burst_time=4),
        Process(pid="P3", arrival_time=3, burst_time=2),
    ]
    completed, timeline, decision_log = run_hrrn(processes)
    result = {p.pid: p for p in completed}

    assert result["P1"].completion_time == 4
    assert result["P1"].turnaround_time == 4
    assert result["P1"].waiting_time == 0

    assert result["P2"].completion_time == 8
    assert result["P2"].turnaround_time == 6
    assert result["P2"].waiting_time == 2

    assert result["P3"].completion_time == 10
    assert result["P3"].turnaround_time == 7
    assert result["P3"].waiting_time == 5

    assert [p.pid for p in completed] == ["P1", "P2", "P3"]


# =========================================================================== #
# Test 3: Different burst times                                                #
# =========================================================================== #
#
# Processes:
#   P1: AT=0, BT=5
#   P2: AT=1, BT=2
#   P3: AT=1, BT=8
#
# Trace:
#   t=0: P1 runs 0 -> 5.
#   t=5: Ready: P2 (AT=1, BT=2), P3 (AT=1, BT=8)
#        P2: W = 5 - 1 = 4 -> RR = (4 + 2) / 2 = 3.0
#        P3: W = 5 - 1 = 4 -> RR = (4 + 8) / 8 = 12/8 = 1.5
#        P2 has higher RR (3.0 > 1.5) -> P2 runs 5 -> 7.
#   t=7: P3 runs 7 -> 15.
#
# =========================================================================== #
def test_different_burst_times():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=5),
        Process(pid="P2", arrival_time=1, burst_time=2),
        Process(pid="P3", arrival_time=1, burst_time=8),
    ]
    completed, timeline, decision_log = run_hrrn(processes)
    result = {p.pid: p for p in completed}

    assert result["P1"].completion_time == 5
    assert result["P2"].completion_time == 7
    assert result["P3"].completion_time == 15

    assert [p.pid for p in completed] == ["P1", "P2", "P3"]


# =========================================================================== #
# Test 4: Long-waiting process gaining priority over a newly arrived short job #
# =========================================================================== #
#
# Demonstrates starvation prevention:
# P1 (long) runs 0 -> 10.
# P2 (medium job, BT=5) arrives at t=1.
# P3 (short job, BT=2) arrives at t=10.
#
# Under SJF, P3 (BT=2) would beat P2 (BT=5).
# Under HRRN at t=10:
#   P2: W = 10 - 1 = 9, B = 5 -> RR = (9 + 5) / 5 = 14/5 = 2.8
#   P3: W = 10 - 10 = 0, B = 2 -> RR = (0 + 2) / 2 = 1.0
# Since 2.8 > 1.0, P2 WINS and runs first!
#
# P1: 0 -> 10
# P2: 10 -> 15 (CT=15, TAT=14, WT=9, RT=9)
# P3: 15 -> 17 (CT=17, TAT=7,  WT=5, RT=5)
#
# =========================================================================== #
def test_long_waiting_process_gains_priority():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=10),
        Process(pid="P2", arrival_time=1, burst_time=5),
        Process(pid="P3", arrival_time=10, burst_time=2),
    ]
    completed, timeline, decision_log = run_hrrn(processes)
    result = {p.pid: p for p in completed}

    # Verify P2 beats P3 despite P3 having a much shorter burst
    assert [p.pid for p in completed] == ["P1", "P2", "P3"]

    assert result["P2"].completion_time == 15
    assert result["P2"].waiting_time == 9

    assert result["P3"].completion_time == 17
    assert result["P3"].waiting_time == 5

    # Check decision log recorded at clock=10
    decision_at_10 = [d for d in decision_log if d["clock"] == 10][0]
    assert decision_at_10["selected"] == "P2"
    assert decision_at_10["ratios"]["P2"] == 2.8
    assert decision_at_10["ratios"]["P3"] == 1.0


# =========================================================================== #
# Test 5: Two processes with equal response ratios                             #
# =========================================================================== #
#
# Processes:
#   P0: AT=0, BT=6
#   P1: AT=2, BT=2
#   P2: AT=0, BT=3
#
# At t=6 (when P0 finishes):
#   P1: W = 6 - 2 = 4, B = 2 -> RR = (4 + 2) / 2 = 6/2 = 3.0
#   P2: W = 6 - 0 = 6, B = 3 -> RR = (6 + 3) / 3 = 9/3 = 3.0
#
# Equal RR = 3.0!
# Tie-breaker 1: Arrival Time -> P2 (AT=0) < P1 (AT=2).
# P2 must be selected first!
#
# Trace:
#   P0: 0 -> 6
#   P2: 6 -> 9
#   P1: 9 -> 11
#
# =========================================================================== #
def test_equal_response_ratio_tie_breaker():
    # P0 is the only process at t=0, so it runs 0 -> 6.
    # P2 arrives at t=2 (BT=4): at t=6, W = 6 - 2 = 4 -> RR = (4 + 4) / 4 = 2.0
    # P1 arrives at t=4 (BT=2): at t=6, W = 6 - 4 = 2 -> RR = (2 + 2) / 2 = 2.0
    # Both have RR = 2.0 at t=6!
    # Tie-breaker 1: Arrival time -> P2 (AT=2) < P1 (AT=4) -> P2 executes first.
    processes = [
        Process(pid="P0", arrival_time=0, burst_time=6),
        Process(pid="P2", arrival_time=2, burst_time=4),
        Process(pid="P1", arrival_time=4, burst_time=2),
    ]
    completed, timeline, decision_log = run_hrrn(processes)

    # P2 must execute before P1 due to earlier arrival time
    assert [p.pid for p in completed] == ["P0", "P2", "P1"]

    result = {p.pid: p for p in completed}
    assert result["P0"].completion_time == 6
    assert result["P2"].completion_time == 10
    assert result["P1"].completion_time == 12


# =========================================================================== #
# Test 6: CPU idle before the first process arrives                            #
# =========================================================================== #
#
# Processes:
#   P1: AT=5, BT=4
#
# CPU is idle 0 -> 5. P1 runs 5 -> 9.
#
# =========================================================================== #
def test_cpu_idle_before_first_arrival():
    processes = [
        Process(pid="P1", arrival_time=5, burst_time=4),
    ]
    completed, timeline, decision_log = run_hrrn(processes)
    result = {p.pid: p for p in completed}

    assert timeline[0] == {"pid": "IDLE", "start": 0, "end": 5}
    assert timeline[1] == {"pid": "P1",   "start": 5, "end": 9}

    assert result["P1"].start_time == 5
    assert result["P1"].completion_time == 9
    assert result["P1"].waiting_time == 0
    assert result["P1"].response_time == 0


# =========================================================================== #
# Test 7: Single process                                                       #
# =========================================================================== #
def test_single_process():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=7),
    ]
    completed, timeline, decision_log = run_hrrn(processes)
    result = {p.pid: p for p in completed}

    assert len(completed) == 1
    assert result["P1"].completion_time == 7
    assert result["P1"].turnaround_time == 7
    assert result["P1"].waiting_time == 0
    assert result["P1"].response_time == 0
    assert timeline == [{"pid": "P1", "start": 0, "end": 7}]


# =========================================================================== #
# Test 8: Multiple processes arriving during execution of a running process    #
# =========================================================================== #
#
# Processes:
#   P1: AT=0, BT=8
#   P2: AT=2, BT=4
#   P3: AT=4, BT=2
#   P4: AT=6, BT=6
#
# P1 runs 0 -> 8.
# At t=8:
#   P2: W = 8 - 2 = 6, B = 4 -> RR = 10/4 = 2.5
#   P3: W = 8 - 4 = 4, B = 2 -> RR = 6/2  = 3.0   <- HIGHEST
#   P4: W = 8 - 6 = 2, B = 6 -> RR = 8/6  = 1.333
#
# P3 is selected! Runs 8 -> 10.
#
# At t=10:
#   P2: W = 10 - 2 = 8, B = 4 -> RR = 12/4 = 3.0  <- HIGHEST
#   P4: W = 10 - 6 = 4, B = 6 -> RR = 10/6 = 1.667
#
# P2 is selected! Runs 10 -> 14.
#
# At t=14:
#   P4 runs 14 -> 20.
#
# Execution Order: P1 -> P3 -> P2 -> P4
#
# =========================================================================== #
def test_multiple_arrivals_during_execution():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=8),
        Process(pid="P2", arrival_time=2, burst_time=4),
        Process(pid="P3", arrival_time=4, burst_time=2),
        Process(pid="P4", arrival_time=6, burst_time=6),
    ]
    completed, timeline, decision_log = run_hrrn(processes)

    assert [p.pid for p in completed] == ["P1", "P3", "P2", "P4"]

    result = {p.pid: p for p in completed}
    assert result["P1"].completion_time == 8
    assert result["P3"].completion_time == 10
    assert result["P2"].completion_time == 14
    assert result["P4"].completion_time == 20


# =========================================================================== #
# Test 9: Original process list remains completely unchanged                   #
# =========================================================================== #
def test_originals_not_modified():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=5),
        Process(pid="P2", arrival_time=1, burst_time=3),
    ]
    orig_rem = [p.remaining_time for p in processes]
    orig_ct  = [p.completion_time for p in processes]
    orig_st  = [p.start_time for p in processes]

    run_hrrn(processes)

    for i, p in enumerate(processes):
        assert p.remaining_time == orig_rem[i]
        assert p.completion_time == orig_ct[i]
        assert p.start_time == orig_st[i]


# =========================================================================== #
# Test 10: Complete verification of all scheduling metrics                     #
# =========================================================================== #
#
# Hand-trace:
#   P1: AT=0, BT=4 -> ST=0,  CT=4,  TAT=4-0=4,  WT=4-4=0, RT=0-0=0
#   At t=4: P2(AT=1, BT=3, W=3, RR=6/3=2.0), P3(AT=2, BT=1, W=2, RR=3/1=3.0)
#   P3 runs 4 -> 5 -> ST=4,  CT=5,  TAT=5-2=3,  WT=3-1=2, RT=4-2=2
#   At t=5: P2(AT=1, BT=3, W=4, RR=7/3=2.333)
#   P2 runs 5 -> 8 -> ST=5,  CT=8,  TAT=8-1=7,  WT=7-3=4, RT=5-1=4
#
# Averages:
#   Avg TAT = (4 + 3 + 7) / 3 = 14 / 3 = 4.667
#   Avg WT  = (0 + 2 + 4) / 3 = 6 / 3  = 2.0
#   Avg RT  = (0 + 2 + 4) / 3 = 6 / 3  = 2.0
#
# =========================================================================== #
def test_all_metrics_verification():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=4),
        Process(pid="P2", arrival_time=1, burst_time=3),
        Process(pid="P3", arrival_time=2, burst_time=1),
    ]
    completed, timeline, decision_log = run_hrrn(processes)
    result = {p.pid: p for p in completed}

    assert result["P1"].start_time == 0
    assert result["P1"].completion_time == 4
    assert result["P1"].turnaround_time == 4
    assert result["P1"].waiting_time == 0
    assert result["P1"].response_time == 0

    assert result["P3"].start_time == 4
    assert result["P3"].completion_time == 5
    assert result["P3"].turnaround_time == 3
    assert result["P3"].waiting_time == 2
    assert result["P3"].response_time == 2

    assert result["P2"].start_time == 5
    assert result["P2"].completion_time == 8
    assert result["P2"].turnaround_time == 7
    assert result["P2"].waiting_time == 4
    assert result["P2"].response_time == 4

    n = len(completed)
    avg_tat = sum(p.turnaround_time for p in completed) / n
    avg_wt  = sum(p.waiting_time    for p in completed) / n
    avg_rt  = sum(p.response_time   for p in completed) / n

    assert abs(avg_tat - 14 / 3) < 1e-9
    assert abs(avg_wt  - 2.0)    < 1e-9
    assert abs(avg_rt  - 2.0)    < 1e-9
