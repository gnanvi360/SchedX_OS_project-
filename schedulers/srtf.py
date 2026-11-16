"""
srtf.py
-------
Implements the Shortest Remaining Time First (SRTF) CPU scheduling algorithm.

SRTF is PREEMPTIVE:
  - At every scheduling event (new arrival or process completion), the process
    with the smallest remaining_time is selected.
  - If a newly arrived process has a shorter remaining time than the currently
    running process, the running process is PREEMPTED — stopped immediately,
    put back into the ready queue, and the shorter process gets the CPU.

Key difference from SJF:
  - SJF makes one decision per process (when CPU is free, never preempts).
  - SRTF re-evaluates at EVERY arrival event and can preempt at any moment.

This module exposes a single public function: run_srtf()

Viva tip: SRTF is theoretically optimal for minimising average waiting time
(even better than SJF). However, it causes more context switches and can
starve long processes if short processes keep arriving.
"""

from schedulers.process import Process


def run_srtf(processes: list) -> tuple:
    """
    Runs the SRTF (preemptive) scheduling algorithm on a list of processes.

    Strategy: Event-driven simulation.
    Instead of simulating every clock tick (slow), we jump between events:
      - Next process arrival
      - Current process completion
    whichever comes first.

    Parameters:
        processes (list[Process]): The original list of Process objects.
                                   This function does NOT modify the originals —
                                   it works on deep copies.

    Returns:
        tuple: A pair (completed_processes, timeline)

            completed_processes (list[Process]):
                Each Process has all metrics filled:
                start_time, completion_time, turnaround_time,
                waiting_time, response_time.
                Ordered by completion sequence.

            timeline (list[dict]):
                Each entry records one continuous CPU interval:
                  {"pid": "P1", "start": 2, "end": 5}   ← process ran
                  {"pid": "IDLE", "start": 0, "end": 3} ← CPU was idle
                Consecutive intervals of the same process are MERGED
                (e.g., P1 runs 3→4 then 4→5 → stored as P1[3→5]).
                Used to draw the Gantt chart.

    Interface note:
        Return format is identical to run_sjf() — both return
        (list[Process], list[dict]) — making them interchangeable
        in the runner and UI code.
    """

    # ------------------------------------------------------------------ #
    # Step 1: Make independent copies of every process.                   #
    # We NEVER modify the caller's list. Each algorithm needs its own     #
    # copies so SJF/SRTF/HRRN/FAAS don't interfere with each other.      #
    # ------------------------------------------------------------------ #
    process_copies = [p.copy() for p in processes]

    # Sort by arrival_time (then pid for stability) so we can efficiently
    # find the next arriving process at any point in the simulation.
    not_arrived = sorted(process_copies, key=lambda p: (p.arrival_time, p.pid))

    ready_queue = []        # Processes that have arrived, waiting for CPU
    completed = []          # Processes that have finished execution
    timeline = []           # Gantt chart intervals (merged same-process runs)
    clock = 0               # Current simulation time
    current_process = None  # The process currently holding the CPU (or None)

    # ------------------------------------------------------------------ #
    # Helper: collect_arrived()                                            #
    # Moves all processes whose arrival_time <= clock into ready_queue.   #
    # Called every time the clock advances.                                #
    # ------------------------------------------------------------------ #
    def collect_arrived():
        """
        Scans not_arrived and moves every process with arrival_time <= clock
        into ready_queue. Removes moved processes from not_arrived.
        """
        nonlocal not_arrived
        arrived_now = [p for p in not_arrived if p.arrival_time <= clock]
        not_arrived  = [p for p in not_arrived if p.arrival_time > clock]
        ready_queue.extend(arrived_now)

    # ------------------------------------------------------------------ #
    # Helper: pick_shortest()                                              #
    # Finds the process with the smallest remaining_time from ALL          #
    # candidates: ready_queue PLUS the currently running process.          #
    # Including current_process ensures we correctly decide whether to     #
    # preempt it or let it continue.                                       #
    # ------------------------------------------------------------------ #
    def pick_shortest():
        """
        Returns the process with the minimum remaining_time among all
        currently available processes (ready queue + currently running).

        Tie-breaking order:
          1. remaining_time  (smallest first — core SRTF criterion)
          2. arrival_time    (earlier arrival wins a tie)
          3. pid             (alphabetical — deterministic tiebreak)

        Returns None if no candidates exist (should only occur during idle).
        """
        candidates = list(ready_queue)         # copy to avoid mutation
        if current_process is not None:
            candidates.append(current_process) # include running process

        if not candidates:
            return None

        return min(candidates, key=lambda p: (p.remaining_time, p.arrival_time, p.pid))

    # ------------------------------------------------------------------ #
    # Helper: record_timeline(pid, start, end)                            #
    # Adds or extends a Gantt chart interval.                              #
    # If the last interval belongs to the SAME process, we simply extend  #
    # its end time instead of creating a new entry. This prevents the     #
    # timeline from fragmenting when a process is interrupted by an       #
    # arrival event but wins re-evaluation and continues running.          #
    # ------------------------------------------------------------------ #
    def record_timeline(pid: str, start: int, end: int):
        """
        Appends a Gantt timeline entry. If the most recent entry already
        belongs to the same pid, extends it instead of adding a new one.
        """
        if timeline and timeline[-1]["pid"] == pid:
            # Same process continues — extend the existing interval
            timeline[-1]["end"] = end
        else:
            # Different process (or first entry) — start a new interval
            timeline.append({"pid": pid, "start": start, "end": end})

    # ------------------------------------------------------------------ #
    # Main scheduling loop: runs until every process is completed.        #
    # ------------------------------------------------------------------ #
    while len(completed) < len(process_copies):

        # Collect any processes that have arrived by the current clock.
        collect_arrived()

        # ---------------------------------------------------------------- #
        # Case 1: Nothing in queue AND nothing running → CPU is IDLE.      #
        # Jump clock forward to the next process arrival.                   #
        # ---------------------------------------------------------------- #
        if not ready_queue and current_process is None:
            # not_arrived is sorted by arrival_time, so [0] is soonest
            next_arrival = not_arrived[0].arrival_time
            record_timeline("IDLE", clock, next_arrival)
            clock = next_arrival
            collect_arrived()   # bring the just-arrived process into queue
            continue

        # ---------------------------------------------------------------- #
        # Step 2: Identify the best process to run (SRTF selection).       #
        # ---------------------------------------------------------------- #
        best = pick_shortest()

        # ---------------------------------------------------------------- #
        # Step 3: Preemption check.                                         #
        # If `best` is NOT the currently running process, we must preempt. #
        # ---------------------------------------------------------------- #
        if best is not current_process:
            # --- Preemption occurs ---
            if current_process is not None:
                # Push the interrupted process back into the ready queue.
                # Its remaining_time has already been decremented to reflect
                # how much it ran before being preempted.
                ready_queue.append(current_process)

            # Remove the new winner from the ready queue
            # (safe because PIDs are unique — no duplicate objects)
            ready_queue.remove(best)

            # Switch to the new process
            current_process = best

            # Record the very first CPU grant for response_time calculation.
            # Only set once — subsequent runs don't overwrite start_time.
            if current_process.start_time == -1:
                current_process.start_time = clock

        # ---------------------------------------------------------------- #
        # Step 4: Determine how long to run before the next event.         #
        #                                                                   #
        # We run until either:                                              #
        #   (a) The next unscheduled process arrives — we must re-evaluate #
        #       in case it should preempt the current process.             #
        #   (b) The current process finishes.                               #
        # whichever comes first.                                            #
        # ---------------------------------------------------------------- #
        if not_arrived:
            next_arrival_time = not_arrived[0].arrival_time
        else:
            next_arrival_time = float('inf')   # no more arrivals

        process_finish_time = clock + current_process.remaining_time
        run_until = min(next_arrival_time, process_finish_time)
        duration = run_until - clock

        # ---------------------------------------------------------------- #
        # Step 5: Record this execution interval in the Gantt timeline.    #
        # ---------------------------------------------------------------- #
        record_timeline(current_process.pid, clock, run_until)

        # ---------------------------------------------------------------- #
        # Step 6: Advance simulation — decrement remaining time and clock. #
        # ---------------------------------------------------------------- #
        current_process.remaining_time -= duration
        clock = run_until

        # ---------------------------------------------------------------- #
        # Step 7: Check if the current process has finished.               #
        # ---------------------------------------------------------------- #
        if current_process.remaining_time == 0:
            # Compute completion_time, turnaround_time, waiting_time,
            # response_time using the Process.finalize() method
            current_process.finalize(clock)
            completed.append(current_process)
            current_process = None   # CPU is now free

    return completed, timeline
