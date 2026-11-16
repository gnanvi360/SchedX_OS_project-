"""
metrics.py
----------
Common performance metrics engine for SchedX.

Evaluates any scheduling algorithm's results (SJF, SRTF, HRRN, FAAS)
using consistent mathematical formulas and standard OS definitions.

Viva Tip:
  - CPU Utilization measures the fraction of simulation time the CPU spent
    doing useful process work (excluding IDLE time).
  - Throughput measures completed processes per unit time (N / total_time).
  - Context switches count process-to-process transitions.
  - Preemptions count instances where an unfinished job was interrupted.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import pandas as pd
from schedulers.process import Process


@dataclass
class PerformanceMetrics:
    """
    Structured container for all calculated performance metrics of a single scheduler run.
    """
    algorithm_name: str
    process_count: int
    total_simulation_time: int
    total_busy_time: int
    total_idle_time: int
    cpu_utilization: float
    throughput: float
    avg_waiting_time: float
    avg_turnaround_time: float
    avg_response_time: float
    max_waiting_time: int
    max_turnaround_time: int
    max_response_time: int
    context_switches: int
    preemptions: int

    def to_dict(self) -> Dict[str, Any]:
        """Converts metrics to a standard Python dictionary."""
        return asdict(self)


def calculate_metrics(
    completed_processes: List[Process],
    timeline: List[Dict[str, Any]],
    algorithm_name: str = "Algorithm"
) -> PerformanceMetrics:
    """
    Computes all standard performance metrics for a completed scheduler execution.

    Parameters:
        completed_processes (list[Process]): List of processes with finalized metrics.
        timeline (list[dict]): Execution timeline intervals (including IDLE).
        algorithm_name (str): Name of the scheduling algorithm.

    Returns:
        PerformanceMetrics: Standardized metrics object.
    """

    # ------------------------------------------------------------------ #
    # 1. Edge Case: Empty process list or empty timeline                 #
    # ------------------------------------------------------------------ #
    if not completed_processes or not timeline:
        return PerformanceMetrics(
            algorithm_name=algorithm_name,
            process_count=0,
            total_simulation_time=0,
            total_busy_time=0,
            total_idle_time=0,
            cpu_utilization=0.0,
            throughput=0.0,
            avg_waiting_time=0.0,
            avg_turnaround_time=0.0,
            avg_response_time=0.0,
            max_waiting_time=0,
            max_turnaround_time=0,
            max_response_time=0,
            context_switches=0,
            preemptions=0,
        )

    # ------------------------------------------------------------------ #
    # 2. Time Totals from Timeline                                       #
    # ------------------------------------------------------------------ #
    total_simulation_time = max(interval["end"] for interval in timeline)
    total_busy_time = 0
    total_idle_time = 0

    for interval in timeline:
        duration = interval["end"] - interval["start"]
        if interval["pid"] == "IDLE":
            total_idle_time += duration
        else:
            total_busy_time += duration

    # ------------------------------------------------------------------ #
    # 3. CPU Utilization and Throughput                                   #
    # ------------------------------------------------------------------ #
    if total_simulation_time > 0:
        cpu_utilization = round((total_busy_time / total_simulation_time) * 100.0, 2)
        throughput = round(len(completed_processes) / total_simulation_time, 4)
    else:
        cpu_utilization = 0.0
        throughput = 0.0

    # ------------------------------------------------------------------ #
    # 4. Process-Level Averages and Extremes                             #
    # ------------------------------------------------------------------ #
    n = len(completed_processes)
    total_wt = sum(p.waiting_time for p in completed_processes)
    total_tat = sum(p.turnaround_time for p in completed_processes)
    total_rt = sum(p.response_time for p in completed_processes)

    avg_waiting_time = round(total_wt / n, 4) if n > 0 else 0.0
    avg_turnaround_time = round(total_tat / n, 4) if n > 0 else 0.0
    avg_response_time = round(total_rt / n, 4) if n > 0 else 0.0

    max_waiting_time = max(p.waiting_time for p in completed_processes) if n > 0 else 0
    max_turnaround_time = max(p.turnaround_time for p in completed_processes) if n > 0 else 0
    max_response_time = max(p.response_time for p in completed_processes) if n > 0 else 0

    # ------------------------------------------------------------------ #
    # 5. Context Switch Counting                                         #
    # ------------------------------------------------------------------ #
    # Rule: A context switch occurs whenever execution switches from one #
    # running process to a different process. Transitions to/from IDLE    #
    # are handled consistently: if process A runs, then IDLE, then B,    #
    # the transition from A to B is a context switch. Initial start at   #
    # t=0 does not count as a switch since no prior process state existed#
    # ------------------------------------------------------------------ #
    context_switches = 0
    last_process_pid = None

    for interval in timeline:
        current_pid = interval["pid"]
        if current_pid != "IDLE":
            if last_process_pid is not None and last_process_pid != current_pid:
                context_switches += 1
            last_process_pid = current_pid

    # ------------------------------------------------------------------ #
    # 6. Preemption Counting                                             #
    # ------------------------------------------------------------------ #
    # Rule: An executing process is preempted if its interval ends       #
    # BEFORE its final completion time, and execution yields to another   #
    # process or IDLE.                                                   #
    # ------------------------------------------------------------------ #
    completion_map = {p.pid: p.completion_time for p in completed_processes}
    preemptions = 0

    for i in range(len(timeline) - 1):
        interval = timeline[i]
        pid = interval["pid"]
        if pid == "IDLE":
            continue

        end_time = interval["end"]
        # If the interval ends strictly before the process's completion time,
        # and the next interval is a different entity, it was preempted!
        if end_time < completion_map.get(pid, end_time):
            next_pid = timeline[i + 1]["pid"]
            if next_pid != pid:
                preemptions += 1

    return PerformanceMetrics(
        algorithm_name=algorithm_name,
        process_count=n,
        total_simulation_time=total_simulation_time,
        total_busy_time=total_busy_time,
        total_idle_time=total_idle_time,
        cpu_utilization=cpu_utilization,
        throughput=throughput,
        avg_waiting_time=avg_waiting_time,
        avg_turnaround_time=avg_turnaround_time,
        avg_response_time=avg_response_time,
        max_waiting_time=max_waiting_time,
        max_turnaround_time=max_turnaround_time,
        max_response_time=max_response_time,
        context_switches=context_switches,
        preemptions=preemptions,
    )


def compare_metrics(
    results_map: Dict[str, tuple]
) -> Dict[str, PerformanceMetrics]:
    """
    Computes performance metrics across multiple scheduling algorithm outputs.

    Parameters:
        results_map (dict): Mapping from algorithm name to scheduler return tuple:
                            {"SJF": (completed, timeline), ...}

    Returns:
        dict: Mapping from algorithm name to PerformanceMetrics.
    """
    metrics_map = {}
    for name, result in results_map.items():
        completed = result[0]
        timeline = result[1]
        metrics_map[name] = calculate_metrics(completed, timeline, algorithm_name=name)
    return metrics_map


def metrics_to_dataframe(metrics_dict: Dict[str, PerformanceMetrics]) -> pd.DataFrame:
    """
    Converts a dictionary of PerformanceMetrics into a clean pandas DataFrame
    for comparative display and Streamlit rendering.

    Columns include:
      - Algorithm
      - Avg Waiting Time
      - Avg Turnaround Time
      - Avg Response Time
      - Max Waiting Time
      - CPU Utilization (%)
      - Throughput
      - Context Switches
      - Preemptions
    """
    rows = []
    for name, m in metrics_dict.items():
        rows.append({
            "Algorithm": m.algorithm_name,
            "Avg Waiting Time": m.avg_waiting_time,
            "Avg Turnaround Time": m.avg_turnaround_time,
            "Avg Response Time": m.avg_response_time,
            "Max Waiting Time": m.max_waiting_time,
            "CPU Utilization (%)": m.cpu_utilization,
            "Throughput": m.throughput,
            "Context Switches": m.context_switches,
            "Preemptions": m.preemptions,
        })
    return pd.DataFrame(rows)
