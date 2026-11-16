"""
runner.py
---------
Unified CPU scheduler execution engine for SchedX.

Coordinates execution across all four scheduling algorithms:
  1. SJF  (Shortest Job First - Non-preemptive)
  2. SRTF (Shortest Remaining Time First - Preemptive)
  3. HRRN (Highest Response Ratio Next - Non-preemptive)
  4. FAAS (Fairness-Aware Adaptive Scheduling - Proposed Custom Algorithm)

Responsibilities:
  - Input validation and sanitization.
  - Generating independent, isolated process copies for each algorithm.
  - Executing each algorithm with appropriate parameters.
  - Passing execution timelines and completed processes to core/metrics.py.
  - Returning a unified, structured SimulationResults object suitable for Streamlit.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import pandas as pd

from schedulers.process import Process
from schedulers.sjf import run_sjf
from schedulers.srtf import run_srtf
from schedulers.hrrn import run_hrrn
from schedulers.faas import run_faas
from core.metrics import (
    PerformanceMetrics,
    calculate_metrics,
    compare_metrics,
    metrics_to_dataframe,
)


@dataclass
class AlgorithmRunResult:
    """
    Encapsulates the complete execution output of a single scheduling algorithm.
    """
    algorithm_name: str
    completed_processes: List[Process]
    timeline: List[Dict[str, Any]]
    metrics: PerformanceMetrics
    decision_log: Optional[List[Dict[str, Any]]] = None

    @property
    def process_dataframe(self) -> pd.DataFrame:
        """
        Returns a pandas DataFrame of process-level metrics (PID, AT, BT, ST, CT, TAT, WT, RT).
        Useful for rendering process detail tables in Streamlit.
        """
        if not self.completed_processes:
            return pd.DataFrame(columns=[
                "PID", "Arrival Time", "Burst Time", "Start Time",
                "Completion Time", "Turnaround Time", "Waiting Time", "Response Time"
            ])

        rows = []
        for p in self.completed_processes:
            rows.append({
                "PID": p.pid,
                "Arrival Time": p.arrival_time,
                "Burst Time": p.burst_time,
                "Start Time": p.start_time,
                "Completion Time": p.completion_time,
                "Turnaround Time": p.turnaround_time,
                "Waiting Time": p.waiting_time,
                "Response Time": p.response_time,
            })
        return pd.DataFrame(rows)


@dataclass
class SimulationResults:
    """
    Encapsulates the full multi-algorithm comparative simulation run.
    Contains individual results for SJF, SRTF, HRRN, FAAS, as well as
    a unified comparison DataFrame.
    """
    algorithms: Dict[str, AlgorithmRunResult] = field(default_factory=dict)
    comparison_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    metrics_summary: Dict[str, PerformanceMetrics] = field(default_factory=dict)

    def get_algorithm(self, name: str) -> Optional[AlgorithmRunResult]:
        """Retrieves results for a specific algorithm by name."""
        return self.algorithms.get(name)


def validate_processes(processes: List[Process]) -> None:
    """
    Validates process list integrity:
      - Must be a list or iterable of Process instances.
      - Burst times must be positive integers (> 0).
      - Arrival times must be non-negative integers (>= 0).
      - Process IDs must be non-empty strings.
    """
    if not isinstance(processes, list):
        raise TypeError(f"Expected a list of Process objects, got {type(processes).__name__}.")

    seen_pids = set()
    for i, p in enumerate(processes):
        if not isinstance(p, Process):
            raise TypeError(f"Item at index {i} is not a Process instance ({type(p).__name__}).")
        if not p.pid or not isinstance(p.pid, str):
            raise ValueError(f"Process at index {i} has an invalid PID: {p.pid!r}.")
        if p.arrival_time < 0:
            raise ValueError(f"Process {p.pid} has negative arrival time: {p.arrival_time}.")
        if p.burst_time <= 0:
            raise ValueError(f"Process {p.pid} has non-positive burst time: {p.burst_time}.")
        if p.pid in seen_pids:
            raise ValueError(f"Duplicate PID detected: {p.pid!r}. Each process must have a unique PID.")
        seen_pids.add(p.pid)


def run_all_schedulers(
    processes: List[Process],
    faas_quantum: int = 2,
    faas_alpha: float = 4.0,
    faas_starvation_threshold: int = 8,
) -> SimulationResults:
    """
    Executes SJF, SRTF, HRRN, and FAAS on independent copies of the input processes,
    computes unified performance metrics, and packages all results into a
    structured SimulationResults object.

    Parameters:
        processes (list[Process]): Input process dataset. Originals remain pristine.
        faas_quantum (int): Guaranteed service quantum for FAAS (default: 2).
        faas_alpha (float): Aging factor for FAAS (default: 4.0).
        faas_starvation_threshold (int): Starvation threshold for FAAS (default: 8).

    Returns:
        SimulationResults: Comparative simulation output containing individual algorithm
                           results, timelines, metrics, and a comparison DataFrame.
    """

    # ------------------------------------------------------------------ #
    # 1. Input Validation                                                #
    # ------------------------------------------------------------------ #
    validate_processes(processes)

    if faas_quantum <= 0:
        raise ValueError(f"FAAS quantum must be > 0, got {faas_quantum}.")
    if faas_alpha < 0:
        raise ValueError(f"FAAS alpha must be >= 0, got {faas_alpha}.")
    if faas_starvation_threshold <= 0:
        raise ValueError(f"FAAS starvation threshold must be > 0, got {faas_starvation_threshold}.")

    # Handle empty dataset edge case
    if not processes:
        empty_metrics_df = pd.DataFrame(columns=[
            "Algorithm", "Avg Waiting Time", "Avg Turnaround Time", "Avg Response Time",
            "Max Waiting Time", "CPU Utilization (%)", "Throughput", "Context Switches", "Preemptions"
        ])
        return SimulationResults(algorithms={}, comparison_df=empty_metrics_df, metrics_summary={})

    # ------------------------------------------------------------------ #
    # 2. Independent Execution of Each Algorithm                         #
    # ------------------------------------------------------------------ #
    # Each algorithm is dispatched with independent copies of processes  #
    # to guarantee zero state contamination across runs.                 #
    # ------------------------------------------------------------------ #

    # SJF (Non-preemptive)
    sjf_completed, sjf_timeline = run_sjf([p.copy() for p in processes])
    sjf_metrics = calculate_metrics(sjf_completed, sjf_timeline, algorithm_name="SJF")

    # SRTF (Preemptive)
    srtf_completed, srtf_timeline = run_srtf([p.copy() for p in processes])
    srtf_metrics = calculate_metrics(srtf_completed, srtf_timeline, algorithm_name="SRTF")

    # HRRN (Non-preemptive with aging)
    hrrn_completed, hrrn_timeline, hrrn_decisions = run_hrrn([p.copy() for p in processes])
    hrrn_metrics = calculate_metrics(hrrn_completed, hrrn_timeline, algorithm_name="HRRN")

    # FAAS (Our proposed algorithm)
    faas_completed, faas_timeline, faas_decisions = run_faas(
        [p.copy() for p in processes],
        quantum=faas_quantum,
        alpha=faas_alpha,
        starvation_threshold=faas_starvation_threshold,
    )
    faas_metrics = calculate_metrics(faas_completed, faas_timeline, algorithm_name="FAAS")

    # ------------------------------------------------------------------ #
    # 3. Assemble Unified Results                                        #
    # ------------------------------------------------------------------ #
    algorithms_map = {
        "SJF": AlgorithmRunResult(
            algorithm_name="SJF",
            completed_processes=sjf_completed,
            timeline=sjf_timeline,
            metrics=sjf_metrics,
            decision_log=None,
        ),
        "SRTF": AlgorithmRunResult(
            algorithm_name="SRTF",
            completed_processes=srtf_completed,
            timeline=srtf_timeline,
            metrics=srtf_metrics,
            decision_log=None,
        ),
        "HRRN": AlgorithmRunResult(
            algorithm_name="HRRN",
            completed_processes=hrrn_completed,
            timeline=hrrn_timeline,
            metrics=hrrn_metrics,
            decision_log=hrrn_decisions,
        ),
        "FAAS": AlgorithmRunResult(
            algorithm_name="FAAS",
            completed_processes=faas_completed,
            timeline=faas_timeline,
            metrics=faas_metrics,
            decision_log=faas_decisions,
        ),
    }

    metrics_map = {
        "SJF": sjf_metrics,
        "SRTF": srtf_metrics,
        "HRRN": hrrn_metrics,
        "FAAS": faas_metrics,
    }

    comparison_df = metrics_to_dataframe(metrics_map)

    return SimulationResults(
        algorithms=algorithms_map,
        comparison_df=comparison_df,
        metrics_summary=metrics_map,
    )
