"""
sjf.py
------
Implements the Shortest Job First (SJF) CPU scheduling algorithm.

SJF is NON-PREEMPTIVE:
  - At each scheduling decision, the process with the smallest burst_time
    is selected from the ready queue.
  - Once a process starts, it runs until completion. No interruptions.

This module exposes a single public function: run_sjf()

Viva tip: SJF minimises average waiting time among all non-preemptive
algorithms when all jobs arrive simultaneously. However, it can cause
starvation for long processes if short processes keep arriving.
"""

from schedulers.process import Process


def run_sjf(processes: list) -> tuple:
    """
    Runs the SJF (non-preemptive) scheduling algorithm on a list of processes.

    Parameters:
        processes (list[Process]): The original list of Process objects.
                                   This function does NOT modify the originals —
                                   it works on deep copies.

    Returns:
        tuple: A pair (completed_processes, timeline)

            completed_processes (list[Process]):
                Each Process has its metrics filled in:
                start_time, completion_time, turnaround_time,
                waiting_time, response_time.
                Ordered by completion sequence.

            timeline (list[dict]):
                Each entry records one continuous CPU interval:
                  {"pid": "P1", "start": 0, "end": 5}   ← process ran
                  {"pid": "IDLE", "start": 0, "end": 3} ← CPU was idle
                Used to draw the Gantt chart.
    """

    # ------------------------------------------------------------------ #
    # Step 1: Make independent copies of every process.                   #
    # ------------------------------------------------------------------ #
    # We NEVER modify the caller's list. Each algorithm gets its own      #
    # copies so that running SJF does not corrupt the data for SRTF etc.  #
    # ------------------------------------------------------------------ #
    process_copies = [p.copy() for p in processes]

    # Sort by arrival_time so we can efficiently find the next arrival.
    # For equal arrival times, sort by pid as a stable secondary key.
    not_arrived = sorted(process_copies, key=lambda p: (p.arrival_time, p.pid))

    ready_queue = []     # Processes that have arrived and are waiting for CPU
    completed = []       # Processes that have finished execution
    timeline = []        # Gantt chart intervals
    clock = 0            # Simulation clock (current time unit)

    # ------------------------------------------------------------------ #
    # Helper: move all newly arrived processes into the ready queue.      #
    # ------------------------------------------------------------------ #
    # We call this whenever the clock advances, so the ready queue stays  #
    # up-to-date with what has actually arrived by the current time.      #
    # ------------------------------------------------------------------ #
    def collect_arrived():
        """
        Scans not_arrived and moves every process with arrival_time <= clock
        into ready_queue. Updates not_arrived in place (removes moved ones).
        """
        # nonlocal lets us modify variables from the enclosing function scope
        nonlocal not_arrived
        arrived_now = [p for p in not_arrived if p.arrival_time <= clock]
        not_arrived = [p for p in not_arrived if p.arrival_time > clock]
        ready_queue.extend(arrived_now)

    # ------------------------------------------------------------------ #
    # Main scheduling loop: runs until every process is completed.        #
    # ------------------------------------------------------------------ #
    while len(completed) < len(process_copies):

        # Collect any processes that have arrived by the current clock.
        collect_arrived()

        # ---------------------------------------------------------------- #
        # Case 1: Ready queue is empty → CPU is IDLE.                      #
        # This happens when no process has arrived yet.                     #
        # We skip forward to the arrival time of the very next process.    #
        # ---------------------------------------------------------------- #
        if not ready_queue:
            # not_arrived is sorted by arrival_time, so [0] is the soonest
            next_arrival = not_arrived[0].arrival_time
            timeline.append({
                "pid": "IDLE",
                "start": clock,
                "end": next_arrival
            })
            clock = next_arrival
            # After advancing the clock, immediately collect newly arrived
            collect_arrived()
            continue   # Re-enter the loop to pick from the now-populated queue

        # ---------------------------------------------------------------- #
        # Case 2: Ready queue has processes → apply SJF selection.         #
        # ---------------------------------------------------------------- #
        # Tie-breaking order:
        #   1st: burst_time  (primary — shortest job first)
        #   2nd: arrival_time (earlier arrival wins a tie)
        #   3rd: pid          (alphabetical, for deterministic results)
        # ---------------------------------------------------------------- #
        ready_queue.sort(key=lambda p: (p.burst_time, p.arrival_time, p.pid))

        # Select and remove the shortest job from the front of the queue
        selected = ready_queue.pop(0)

        # Record the moment this process first touched the CPU.
        # In SJF (non-preemptive), a process runs at most once,
        # so start_time == the moment it's selected.
        selected.start_time = clock

        # ---------------------------------------------------------------- #
        # Non-preemptive execution: run selected process to completion.    #
        # end_time = current clock + full burst time (no interruption).    #
        # ---------------------------------------------------------------- #
        end_time = clock + selected.burst_time

        # Record this interval in the Gantt timeline
        timeline.append({
            "pid": selected.pid,
            "start": clock,
            "end": end_time
        })

        # Advance the clock to when this process finishes
        clock = end_time

        # Compute and store completion_time, turnaround_time,
        # waiting_time, response_time using the Process.finalize() method
        selected.finalize(clock)

        # Mark this process as done
        completed.append(selected)

    return completed, timeline
