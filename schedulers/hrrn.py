"""
hrrn.py
-------
Implements the Highest Response Ratio Next (HRRN) CPU scheduling algorithm.

HRRN is NON-PREEMPTIVE:
  - At each scheduling decision point (when CPU is free), the Response Ratio (RR)
    is computed for every arrived, waiting process.
  - The process with the HIGHEST response ratio is selected to run to completion.
  - Once started, a process cannot be preempted.

Mathematical Formula:
  Response Ratio (RR) = (Waiting Time + Burst Time) / Burst Time
                      = 1 + (Waiting Time / Burst Time)

Where:
  Waiting Time (W) = current_time - arrival_time
  Burst Time (B)   = process.burst_time

Viva tip: HRRN eliminates the starvation problem of SJF. Even a very long
process will eventually gain a high response ratio as its waiting time increases,
allowing it to overtake newly arrived short processes.
"""

from fractions import Fraction
from schedulers.process import Process


def run_hrrn(processes: list) -> tuple:
    """
    Runs the HRRN (non-preemptive) scheduling algorithm on a list of processes.

    Parameters:
        processes (list[Process]): The original list of Process objects.
                                   This function does NOT modify the originals —
                                   it works on independent deep copies.

    Returns:
        tuple: (completed_processes, timeline, decision_log)

            completed_processes (list[Process]):
                Each Process has its metrics filled:
                start_time, completion_time, turnaround_time,
                waiting_time, response_time.
                Ordered by execution/completion sequence.

            timeline (list[dict]):
                Gantt chart intervals:
                  {"pid": "P1", "start": 0, "end": 5}
                  {"pid": "IDLE", "start": 5, "end": 8}

            decision_log (list[dict]):
                Detailed log of response ratios evaluated at each scheduling decision:
                  {
                    "clock": 10,
                    "ratios": {"P2": 2.8, "P3": 1.0},
                    "selected": "P2",
                    "selected_ratio": 2.8
                  }
                Useful for educational transparency and viva demonstration.
    """

    # ------------------------------------------------------------------ #
    # Step 1: Make independent copies of every process.                   #
    # We never mutate the input list passed by the caller.               #
    # ------------------------------------------------------------------ #
    process_copies = [p.copy() for p in processes]

    # Sort not-arrived processes by arrival_time, then pid for stability
    not_arrived = sorted(process_copies, key=lambda p: (p.arrival_time, p.pid))

    ready_queue = []     # Arrived processes waiting for the CPU
    completed = []       # Finished processes
    timeline = []        # Gantt chart execution intervals
    decision_log = []    # History of response ratio calculations
    clock = 0            # Current simulation clock

    # ------------------------------------------------------------------ #
    # Helper: collect_arrived()                                            #
    # Scans not_arrived and moves processes with arrival_time <= clock    #
    # into the ready_queue.                                                #
    # ------------------------------------------------------------------ #
    def collect_arrived():
        nonlocal not_arrived
        arrived_now = [p for p in not_arrived if p.arrival_time <= clock]
        not_arrived = [p for p in not_arrived if p.arrival_time > clock]
        ready_queue.extend(arrived_now)

    # ------------------------------------------------------------------ #
    # Helper: calculate_response_ratio(p, current_time)                    #
    # Computes (W + B) / B as an exact Fraction.                         #
    # ------------------------------------------------------------------ #
    def calculate_response_ratio(p: Process, current_time: int) -> Fraction:
        waiting_time = current_time - p.arrival_time
        return Fraction(waiting_time + p.burst_time, p.burst_time)

    # ------------------------------------------------------------------ #
    # Main scheduling loop: continues until all processes finish.        #
    # ------------------------------------------------------------------ #
    while len(completed) < len(process_copies):

        # Update ready queue with processes that have arrived by current clock
        collect_arrived()

        # ---------------------------------------------------------------- #
        # Case 1: CPU is IDLE when ready queue is empty.                   #
        # Jump the clock forward to the next process arrival.              #
        # ---------------------------------------------------------------- #
        if not ready_queue:
            next_arrival = not_arrived[0].arrival_time
            timeline.append({
                "pid": "IDLE",
                "start": clock,
                "end": next_arrival
            })
            clock = next_arrival
            collect_arrived()
            continue

        # ---------------------------------------------------------------- #
        # Case 2: Evaluate Response Ratios for all ready processes.        #
        # ---------------------------------------------------------------- #
        # Tie-breaking rules specified in requirements:
        #   1. Highest Response Ratio (largest fraction)
        #   2. Earlier Arrival Time (smaller arrival_time)
        #   3. Shorter Burst Time (smaller burst_time)
        #   4. Process ID (alphabetical, "P1" < "P2")
        # ---------------------------------------------------------------- #
        # To use Python's min(), we negate the response ratio:
        #   -larger ratio becomes smaller negative value -> selected first.
        # ---------------------------------------------------------------- #
        current_ratios = {}
        for p in ready_queue:
            rr_fraction = calculate_response_ratio(p, clock)
            current_ratios[p.pid] = float(rr_fraction)

        def selection_key(p: Process):
            rr = calculate_response_ratio(p, clock)
            return (-rr, p.arrival_time, p.burst_time, p.pid)

        # Select the process that optimizes the key
        selected = min(ready_queue, key=selection_key)
        ready_queue.remove(selected)

        selected_rr = current_ratios[selected.pid]

        # Record this decision for educational transparency
        decision_log.append({
            "clock": clock,
            "ratios": current_ratios,
            "selected": selected.pid,
            "selected_ratio": selected_rr
        })

        # ---------------------------------------------------------------- #
        # Execute the selected process to completion (Non-preemptive)      #
        # ---------------------------------------------------------------- #
        selected.start_time = clock
        end_time = clock + selected.burst_time

        timeline.append({
            "pid": selected.pid,
            "start": clock,
            "end": end_time
        })

        clock = end_time

        # Finalize metrics: CT, TAT, WT, RT
        selected.finalize(clock)
        completed.append(selected)

    return completed, timeline, decision_log
