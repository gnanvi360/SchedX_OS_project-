"""
faas.py
-------
Implements Fairness-Aware Adaptive Scheduling (FAAS).

FAAS is our proposed custom CPU scheduling algorithm for SchedX.
It is a PREEMPTIVE scheduling algorithm with bounded dispatch intervals
(guaranteed service quantums) that combines:
  1. Shortest remaining time efficiency: (1 / remaining_time)
  2. Dynamic waiting-time aging: (alpha * continuous_waiting_time)
  3. Hard starvation prevention: strict override when continuous_waiting_time >= starvation_threshold
  4. Guaranteed service quantum: non-interruptible execution window (default: 2 time units)

Mathematical Formula for normal candidates:
  Priority(P) = (1 / remaining_time) + (alpha * continuous_waiting_time)

Starvation Override:
  If any ready process has continuous_waiting_time >= starvation_threshold,
  it enters the starvation-protected category and bypasses the priority formula.
  Among starvation-protected processes, the one waiting longest is selected.

This module exposes:
  run_faas(processes, quantum=2, alpha=4.0, starvation_threshold=8)
"""

from schedulers.process import Process


class DecisionLog(list):
    """
    Custom list subclass that stores individual decision records while also
    exposing summary simulation statistics via the .stats attribute.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stats = {}


def run_faas(
    processes: list,
    quantum: int = 2,
    alpha: float = 4.0,
    starvation_threshold: int = 8,
) -> tuple:
    """
    Runs the FAAS scheduling algorithm on a list of processes.

    Parameters:
        processes (list[Process]): Original list of Process objects.
                                   Never modified in-place; deep copies are used.
        quantum (int): Maximum consecutive CPU time units granted per dispatch (default: 2).
        alpha (float): Aging factor multiplier for continuous waiting time (default: 4.0).
        starvation_threshold (int): Continuous waiting time threshold that triggers
                                    starvation override protection (default: 8).

    Returns:
        tuple: (completed_processes, timeline, decision_log)

            completed_processes (list[Process]):
                Processes sorted in completion order with CT, TAT, WT, RT finalized.

            timeline (list[dict]):
                Merged execution and idle intervals for Gantt chart rendering:
                  {"pid": "P1", "start": 0, "end": 4}
                  {"pid": "IDLE", "start": 4, "end": 6}

            decision_log (DecisionLog):
                List of detailed decision dictionaries at each scheduling event,
                with .stats containing aggregate metrics.
    """

    # ------------------------------------------------------------------ #
    # Parameter Validation (Safety & Robustness)                         #
    # ------------------------------------------------------------------ #
    if quantum <= 0:
        raise ValueError(f"Quantum must be a positive integer, got {quantum}.")
    if alpha < 0:
        raise ValueError(f"Alpha (aging coefficient) cannot be negative, got {alpha}.")
    if starvation_threshold <= 0:
        raise ValueError(f"Starvation threshold must be positive, got {starvation_threshold}.")

    # Empty input handling
    if not processes:
        empty_log = DecisionLog()
        empty_log.stats = {
            "avg_waiting_time": 0.0,
            "avg_turnaround_time": 0.0,
            "avg_response_time": 0.0,
            "cpu_utilization": 0.0,
            "throughput": 0.0,
            "context_switches": 0,
            "preemptions": 0,
            "starvation_activations": 0,
        }
        return [], [], empty_log

    # ------------------------------------------------------------------ #
    # Step 1: Deep copy and initialize internal tracking fields           #
    # ------------------------------------------------------------------ #
    process_copies = [p.copy() for p in processes]

    for p in process_copies:
        # last_service_time tracks when the process last ran (or arrived)
        p.last_service_time = p.arrival_time
        # continuous_waiting_time is reset when the process runs on the CPU
        p.continuous_waiting_time = 0

    # Sort not-arrived processes by arrival time, then pid for deterministic ordering
    not_arrived = sorted(process_copies, key=lambda p: (p.arrival_time, p.pid))

    ready_queue = []
    completed = []
    timeline = []
    decision_log = DecisionLog()

    clock = 0
    last_running_pid = None
    context_switches = 0
    preemptions = 0
    starvation_activations = 0
    busy_cpu_time = 0

    # ------------------------------------------------------------------ #
    # Helper: collect_arrived()                                            #
    # Moves all processes whose arrival_time <= clock into ready_queue.   #
    # ------------------------------------------------------------------ #
    def collect_arrived():
        nonlocal not_arrived
        arrived_now = [p for p in not_arrived if p.arrival_time <= clock]
        not_arrived = [p for p in not_arrived if p.arrival_time > clock]
        ready_queue.extend(arrived_now)

    # ------------------------------------------------------------------ #
    # Helper: update_waiting_times()                                       #
    # Recalculates continuous_waiting_time for all ready processes at clock#
    # ------------------------------------------------------------------ #
    def update_waiting_times():
        for p in ready_queue:
            p.continuous_waiting_time = max(0, clock - p.last_service_time)

    # ------------------------------------------------------------------ #
    # Helper: record_timeline(pid, start, end)                            #
    # Merges adjacent intervals of the same process for clean Gantt charts#
    # ------------------------------------------------------------------ #
    def record_timeline(pid: str, start: int, end: int):
        if timeline and timeline[-1]["pid"] == pid:
            timeline[-1]["end"] = end
        else:
            timeline.append({"pid": pid, "start": start, "end": end})

    # ------------------------------------------------------------------ #
    # Main Scheduling Loop                                                #
    # ------------------------------------------------------------------ #
    while len(completed) < len(process_copies):

        collect_arrived()

        # ---------------------------------------------------------------- #
        # Case 1: CPU is IDLE when ready queue is empty                     #
        # ---------------------------------------------------------------- #
        if not ready_queue:
            next_arrival = not_arrived[0].arrival_time
            record_timeline("IDLE", clock, next_arrival)

            if last_running_pid is not None and last_running_pid != "IDLE":
                context_switches += 1
            last_running_pid = "IDLE"

            clock = next_arrival
            collect_arrived()
            continue

        # Update continuous waiting times up to the current clock
        update_waiting_times()

        # ---------------------------------------------------------------- #
        # Case 2: Identify Starvation-Protected Candidates                 #
        # ---------------------------------------------------------------- #
        starving_candidates = [
            p for p in ready_queue if p.continuous_waiting_time >= starvation_threshold
        ]

        is_starvation_override = len(starving_candidates) > 0

        # Snapshot of candidate states for educational logging
        candidates_snapshot = []
        for p in ready_queue:
            rem_inv = (1.0 / p.remaining_time) if p.remaining_time > 0 else 0.0
            p_score = rem_inv + (alpha * p.continuous_waiting_time)
            candidates_snapshot.append({
                "pid": p.pid,
                "remaining_time": p.remaining_time,
                "continuous_waiting_time": p.continuous_waiting_time,
                "priority_score": round(p_score, 4),
                "is_starving": p.continuous_waiting_time >= starvation_threshold,
            })

        if is_starvation_override:
            # Starvation Override:
            # Select process waiting longest. Tiebreak by earlier arrival, then pid.
            selected = min(
                starving_candidates,
                key=lambda p: (-p.continuous_waiting_time, p.arrival_time, p.pid)
            )
            starvation_activations += 1
            decision_reason = "Starvation Override"
        else:
            # Normal FAAS Priority Formula:
            # Priority = (1 / remaining_time) + (alpha * continuous_waiting_time)
            # Tiebreak by earlier arrival, shorter remaining time, then pid.
            def priority_key(p: Process):
                rem_inv = (1.0 / p.remaining_time) if p.remaining_time > 0 else 0.0
                score = rem_inv + (alpha * p.continuous_waiting_time)
                # Negate score so min() picks the highest
                return (-score, p.arrival_time, p.remaining_time, p.pid)

            selected = min(ready_queue, key=priority_key)
            decision_reason = "Highest Priority Score"

        # Remove selected process from ready queue during execution
        ready_queue.remove(selected)

        # ---------------------------------------------------------------- #
        # Context Switch & First Start Time Tracking                       #
        # ---------------------------------------------------------------- #
        if last_running_pid is not None and last_running_pid != selected.pid:
            context_switches += 1
        last_running_pid = selected.pid

        if selected.start_time == -1:
            selected.start_time = clock

        # ---------------------------------------------------------------- #
        # Execute for Guaranteed Service Quantum                           #
        # (Runs for up to `quantum`, or until process completes)            #
        # ---------------------------------------------------------------- #
        service_duration = min(quantum, selected.remaining_time)
        start_time_of_quantum = clock
        end_time_of_quantum = clock + service_duration

        record_timeline(selected.pid, start_time_of_quantum, end_time_of_quantum)
        busy_cpu_time += service_duration

        # Compute selected priority score for the log
        sel_rem_inv = (1.0 / selected.remaining_time) if selected.remaining_time > 0 else 0.0
        sel_score = sel_rem_inv + (alpha * selected.continuous_waiting_time)

        # Record this decision for UI transparency and testing
        decision_log.append({
            "clock": clock,
            "selected": selected.pid,
            "selected_priority": round(sel_score, 4),
            "continuous_waiting_time": selected.continuous_waiting_time,
            "quantum_granted": service_duration,
            "starvation_override": is_starvation_override,
            "reason": decision_reason,
            "candidates": candidates_snapshot,
        })

        # Advance simulation clock
        clock = end_time_of_quantum
        selected.remaining_time -= service_duration

        # ---------------------------------------------------------------- #
        # Post-Quantum State Update                                        #
        # ---------------------------------------------------------------- #
        # Reset continuous waiting time since the process just received service
        selected.last_service_time = clock
        selected.continuous_waiting_time = 0

        # Collect any new arrivals that entered during this quantum
        collect_arrived()

        if selected.remaining_time == 0:
            # Process finished! Finalize CT, TAT, WT, RT
            selected.finalize(clock)
            completed.append(selected)
        else:
            # Process still has work left:
            # Check if it was preempted (i.e. someone else might run next or ready queue has candidates)
            # It returns to the ready queue for the next scheduling evaluation
            ready_queue.append(selected)
            # If there are other ready processes, this quantum transition counts as a preemption event
            if len(ready_queue) > 1:
                preemptions += 1

    # ------------------------------------------------------------------ #
    # Aggregate Performance Metrics Calculation                          #
    # ------------------------------------------------------------------ #
    n = len(completed)
    total_simulation_time = clock
    avg_wt = sum(p.waiting_time for p in completed) / n if n > 0 else 0.0
    avg_tat = sum(p.turnaround_time for p in completed) / n if n > 0 else 0.0
    avg_rt = sum(p.response_time for p in completed) / n if n > 0 else 0.0
    cpu_util = (busy_cpu_time / total_simulation_time * 100.0) if total_simulation_time > 0 else 0.0
    throughput = (n / total_simulation_time) if total_simulation_time > 0 else 0.0

    decision_log.stats = {
        "avg_waiting_time": round(avg_wt, 4),
        "avg_turnaround_time": round(avg_tat, 4),
        "avg_response_time": round(avg_rt, 4),
        "cpu_utilization": round(cpu_util, 2),
        "throughput": round(throughput, 4),
        "context_switches": context_switches,
        "preemptions": preemptions,
        "starvation_activations": starvation_activations,
    }

    return completed, timeline, decision_log
