"""
test_metrics.py
---------------
Unit tests for the common performance metrics engine (core/metrics.py).

Verifies:
  1. Average waiting time calculation.
  2. Average turnaround time calculation.
  3. Average response time calculation.
  4. CPU utilization with no idle periods.
  5. CPU utilization with idle periods.
  6. Throughput calculation.
  7. Context-switch counting.
  8. Preemption counting.
  9. Total busy and idle time.
  10. Empty process list.
  11. Single process.
  12. Multiple processes with different arrival times.
  13. Zero division protection.
  14. Verify consistency across all four algorithms on the required benchmark dataset.
  15. Verify original scheduling results remain unchanged.
"""

import pytest
import pandas as pd
from schedulers.process import Process
from schedulers.sjf import run_sjf
from schedulers.srtf import run_srtf
from schedulers.hrrn import run_hrrn
from schedulers.faas import run_faas
from core.metrics import calculate_metrics, compare_metrics, metrics_to_dataframe


# =========================================================================== #
# Test 1, 2, 3: Average WT, TAT, and RT Calculations                         #
# =========================================================================== #
def test_average_metrics_calculation():
    # Setup 3 dummy completed processes
    # P1: TAT=10, WT=4, RT=0
    # P2: TAT=4,  WT=1, RT=1
    # P3: TAT=6,  WT=3, RT=2
    p1 = Process(pid="P1", arrival_time=0, burst_time=6)
    p1.start_time = 0
    p1.finalize(10)  # TAT=10, WT=4, RT=0

    p2 = Process(pid="P2", arrival_time=1, burst_time=3)
    p2.start_time = 2
    p2.finalize(5)   # TAT=4, WT=1, RT=1

    p3 = Process(pid="P3", arrival_time=2, burst_time=3)
    p3.start_time = 4
    p3.finalize(8)   # TAT=6, WT=3, RT=2

    timeline = [{"pid": "P1", "start": 0, "end": 10}]
    m = calculate_metrics([p1, p2, p3], timeline, "TestAlgo")

    assert m.avg_turnaround_time == round((10 + 4 + 6) / 3, 4)  # 6.6667
    assert m.avg_waiting_time == round((4 + 1 + 3) / 3, 4)      # 2.6667
    assert m.avg_response_time == round((0 + 1 + 2) / 3, 4)     # 1.0
    assert m.max_turnaround_time == 10
    assert m.max_waiting_time == 4
    assert m.max_response_time == 2


# =========================================================================== #
# Test 4: CPU Utilization with NO idle periods                                 #
# =========================================================================== #
def test_cpu_utilization_no_idle():
    p1 = Process(pid="P1", arrival_time=0, burst_time=5)
    p1.start_time = 0
    p1.finalize(5)

    timeline = [{"pid": "P1", "start": 0, "end": 5}]
    m = calculate_metrics([p1], timeline, "NoIdle")

    assert m.total_busy_time == 5
    assert m.total_idle_time == 0
    assert m.total_simulation_time == 5
    assert m.cpu_utilization == 100.0


# =========================================================================== #
# Test 5: CPU Utilization WITH idle periods                                    #
# =========================================================================== #
def test_cpu_utilization_with_idle():
    p1 = Process(pid="P1", arrival_time=4, burst_time=6)
    p1.start_time = 4
    p1.finalize(10)

    # 4 units IDLE (0 to 4), 6 units BUSY (4 to 10)
    timeline = [
        {"pid": "IDLE", "start": 0, "end": 4},
        {"pid": "P1",   "start": 4, "end": 10},
    ]
    m = calculate_metrics([p1], timeline, "WithIdle")

    assert m.total_idle_time == 4
    assert m.total_busy_time == 6
    assert m.total_simulation_time == 10
    assert m.cpu_utilization == 60.0  # (6 / 10) * 100


# =========================================================================== #
# Test 6: Throughput Calculation                                               #
# =========================================================================== #
def test_throughput_calculation():
    # 4 processes completed in 20 time units -> Throughput = 4 / 20 = 0.20
    processes = []
    for i in range(4):
        p = Process(pid=f"P{i}", arrival_time=0, burst_time=5)
        p.start_time = i * 5
        p.finalize((i + 1) * 5)
        processes.append(p)

    timeline = [{"pid": f"P{i}", "start": i * 5, "end": (i + 1) * 5} for i in range(4)]
    m = calculate_metrics(processes, timeline, "ThroughputTest")

    assert m.total_simulation_time == 20
    assert m.process_count == 4
    assert m.throughput == 0.2


# =========================================================================== #
# Test 7: Context-Switch Counting                                              #
# =========================================================================== #
def test_context_switch_counting():
    # P1 -> P2 -> P3 -> P1: 3 context switches
    p1 = Process(pid="P1", arrival_time=0, burst_time=6)
    p1.start_time = 0
    p1.finalize(10)

    p2 = Process(pid="P2", arrival_time=0, burst_time=2)
    p2.start_time = 2
    p2.finalize(4)

    p3 = Process(pid="P3", arrival_time=0, burst_time=2)
    p3.start_time = 4
    p3.finalize(6)

    timeline = [
        {"pid": "P1", "start": 0, "end": 2},
        {"pid": "P2", "start": 2, "end": 4},
        {"pid": "P3", "start": 4, "end": 6},
        {"pid": "P1", "start": 6, "end": 10},
    ]
    m = calculate_metrics([p1, p2, p3], timeline, "CS")
    assert m.context_switches == 3


# =========================================================================== #
# Test 8: Preemption Counting                                                  #
# =========================================================================== #
def test_preemption_counting():
    # P1 runs 0->2 (CT=8, interrupted -> preemption 1)
    # P2 runs 2->4 (CT=4, normal finish)
    # P1 runs 4->6 (CT=8, interrupted -> preemption 2)
    # P3 runs 6->8 (CT=8, normal finish)
    # P1 runs 8->10 (CT=10, normal finish)
    p1 = Process(pid="P1", arrival_time=0, burst_time=6)
    p1.start_time = 0
    p1.finalize(10)

    p2 = Process(pid="P2", arrival_time=0, burst_time=2)
    p2.start_time = 2
    p2.finalize(4)

    p3 = Process(pid="P3", arrival_time=0, burst_time=2)
    p3.start_time = 6
    p3.finalize(8)

    timeline = [
        {"pid": "P1", "start": 0, "end": 2},
        {"pid": "P2", "start": 2, "end": 4},
        {"pid": "P1", "start": 4, "end": 6},
        {"pid": "P3", "start": 6, "end": 8},
        {"pid": "P1", "start": 8, "end": 10},
    ]
    m = calculate_metrics([p1, p2, p3], timeline, "Preempt")
    assert m.preemptions == 2


# =========================================================================== #
# Test 9: Total Busy and Idle Time                                             #
# =========================================================================== #
def test_total_busy_and_idle_time():
    p1 = Process(pid="P1", arrival_time=2, burst_time=3)
    p1.start_time = 2
    p1.finalize(5)

    p2 = Process(pid="P2", arrival_time=8, burst_time=2)
    p2.start_time = 8
    p2.finalize(10)

    timeline = [
        {"pid": "IDLE", "start": 0, "end": 2},
        {"pid": "P1",   "start": 2, "end": 5},
        {"pid": "IDLE", "start": 5, "end": 8},
        {"pid": "P2",   "start": 8, "end": 10},
    ]
    m = calculate_metrics([p1, p2], timeline, "BusyIdle")
    assert m.total_idle_time == 5  # (2 - 0) + (8 - 5)
    assert m.total_busy_time == 5  # (5 - 2) + (10 - 8)
    assert m.total_simulation_time == 10
    assert m.cpu_utilization == 50.0


# =========================================================================== #
# Test 10 & 13: Empty List and Zero Division Protection                        #
# =========================================================================== #
def test_empty_and_zero_division():
    m = calculate_metrics([], [], "Empty")
    assert m.process_count == 0
    assert m.total_simulation_time == 0
    assert m.cpu_utilization == 0.0
    assert m.throughput == 0.0
    assert m.avg_waiting_time == 0.0


# =========================================================================== #
# Test 11: Single Process                                                      #
# =========================================================================== #
def test_single_process():
    p1 = Process(pid="P1", arrival_time=0, burst_time=7)
    p1.start_time = 0
    p1.finalize(7)
    timeline = [{"pid": "P1", "start": 0, "end": 7}]

    m = calculate_metrics([p1], timeline, "Single")
    assert m.process_count == 1
    assert m.avg_waiting_time == 0.0
    assert m.avg_turnaround_time == 7.0
    assert m.cpu_utilization == 100.0
    assert m.context_switches == 0
    assert m.preemptions == 0


# =========================================================================== #
# Test 12: Multiple Processes with Different Arrival Times                     #
# =========================================================================== #
def test_multiple_arrivals():
    # P1: AT=0, BT=4, ST=0, CT=4 (WT=0, TAT=4, RT=0)
    # P2: AT=2, BT=3, ST=4, CT=7 (WT=2, TAT=5, RT=2)
    p1 = Process(pid="P1", arrival_time=0, burst_time=4)
    p1.start_time = 0
    p1.finalize(4)

    p2 = Process(pid="P2", arrival_time=2, burst_time=3)
    p2.start_time = 4
    p2.finalize(7)

    timeline = [
        {"pid": "P1", "start": 0, "end": 4},
        {"pid": "P2", "start": 4, "end": 7},
    ]
    m = calculate_metrics([p1, p2], timeline, "MultiArrival")
    assert m.avg_waiting_time == 1.0     # (0 + 2) / 2
    assert m.avg_turnaround_time == 4.5  # (4 + 5) / 2
    assert m.avg_response_time == 1.0    # (0 + 2) / 2
    assert m.context_switches == 1
    assert m.preemptions == 0


# =========================================================================== #
# Test 14: Benchmark Dataset Verification Across All 4 Algorithms              #
# =========================================================================== #
# Required validation dataset:
#   P1: AT=0, BT=6
#   P2: AT=1, BT=2
#   P3: AT=2, BT=4
#   P4: AT=4, BT=3
# =========================================================================== #
def test_benchmark_dataset_all_algorithms():
    base_processes = [
        Process(pid="P1", arrival_time=0, burst_time=6),
        Process(pid="P2", arrival_time=1, burst_time=2),
        Process(pid="P3", arrival_time=2, burst_time=4),
        Process(pid="P4", arrival_time=4, burst_time=3),
    ]

    # Run all 4 algorithms on identical dataset copies
    sjf_res  = run_sjf(base_processes)
    srtf_res = run_srtf(base_processes)
    hrrn_res = run_hrrn(base_processes)
    faas_res = run_faas(base_processes, quantum=2, alpha=4.0, starvation_threshold=8)

    results_map = {
        "SJF": sjf_res,
        "SRTF": srtf_res,
        "HRRN": hrrn_res,
        "FAAS": faas_res,
    }

    metrics = compare_metrics(results_map)

    # 1. SJF Verification
    # Order: P1 (0->6), P2 (6->8), P4 (8->11), P3 (11->15)
    sjf_m = metrics["SJF"]
    assert sjf_m.total_simulation_time == 15
    assert sjf_m.cpu_utilization == 100.0
    assert sjf_m.avg_turnaround_time == 8.25
    assert sjf_m.avg_waiting_time == 4.5
    assert sjf_m.avg_response_time == 4.5
    assert sjf_m.context_switches == 3
    assert sjf_m.preemptions == 0

    # 2. SRTF Verification
    # Order: P1 (0->1), P2 (1->3), P3 (3->7), P4 (7->10), P1 (10->15)
    srtf_m = metrics["SRTF"]
    assert srtf_m.total_simulation_time == 15
    assert srtf_m.cpu_utilization == 100.0
    assert srtf_m.avg_turnaround_time == 7.00
    assert srtf_m.avg_waiting_time == 3.25
    assert srtf_m.avg_response_time == 1.00
    assert srtf_m.context_switches == 4
    assert srtf_m.preemptions == 1

    # 3. HRRN Verification
    # Order: P1 (0->6), P2 (6->8), P3 (8->12), P4 (12->15)
    hrrn_m = metrics["HRRN"]
    assert hrrn_m.total_simulation_time == 15
    assert hrrn_m.cpu_utilization == 100.0
    assert hrrn_m.avg_turnaround_time == 8.50
    assert hrrn_m.avg_waiting_time == 4.75
    assert hrrn_m.avg_response_time == 4.75
    assert hrrn_m.context_switches == 3
    assert hrrn_m.preemptions == 0

    # 4. FAAS Verification
    # Order: P1 (0->2), P2 (2->4), P1 (4->6), P3 (6->8), P4 (8->10), P1 (10->12), P3 (12->14), P4 (14->15)
    faas_m = metrics["FAAS"]
    assert faas_m.total_simulation_time == 15
    assert faas_m.cpu_utilization == 100.0
    assert faas_m.avg_turnaround_time == 9.50
    assert faas_m.avg_waiting_time == 5.75
    assert faas_m.avg_response_time == 2.25
    assert faas_m.context_switches == 7
    assert faas_m.preemptions == 4

    # DataFrame conversion test
    df = metrics_to_dataframe(metrics)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 4
    assert "Avg Waiting Time" in df.columns


# =========================================================================== #
# Test 15: Immutability of Original Inputs                                     #
# =========================================================================== #
def test_originals_unchanged():
    procs = [
        Process(pid="P1", arrival_time=0, burst_time=5),
        Process(pid="P2", arrival_time=2, burst_time=3),
    ]
    orig_rem = [p.remaining_time for p in procs]
    orig_ct  = [p.completion_time for p in procs]

    # Run compare_metrics with dummy results
    compare_metrics({"Test": run_sjf(procs)})

    for i, p in enumerate(procs):
        assert p.remaining_time == orig_rem[i]
        assert p.completion_time == orig_ct[i]
