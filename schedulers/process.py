"""
process.py
----------
Defines the Process dataclass used by ALL scheduling algorithms in SchedX.

Every process that enters the CPU scheduler is represented as one instance
of this class. All algorithms read from and write to the same fields,
ensuring consistent metric calculations.

Viva tip: A dataclass is just a regular Python class where __init__,
__repr__, and __eq__ are auto-generated based on the field annotations.
"""

from dataclasses import dataclass, field


@dataclass
class Process:
    """
    Represents a single process in the CPU scheduling simulation.

    Fields set BEFORE simulation (inputs):
        pid           : Unique process identifier, e.g. "P1".
        arrival_time  : The clock time at which this process enters the
                        ready queue. The CPU cannot schedule it before this.
        burst_time    : Total CPU time (in time units) needed to finish.

    Fields managed DURING simulation (internal state):
        remaining_time: How much burst time is left. Starts equal to
                        burst_time, counts down to 0 as the CPU runs it.
        waiting_time_so_far: Accumulates how long this process has been in
                        the ready queue without running. Used by FAAS for
                        aging and starvation detection.

    Fields set AFTER process completes (outputs / metrics):
        start_time    : Clock time of the FIRST CPU tick this process ran.
                        Used to compute response_time.
        completion_time: Clock time when remaining_time reaches 0.
        turnaround_time: completion_time - arrival_time.
                        Total time from submission to finish.
        waiting_time  : turnaround_time - burst_time.
                        Time spent NOT running (idle in the queue).
        response_time : start_time - arrival_time.
                        How quickly the process got its first CPU slot.

    Sentinel value -1: fields that have not been computed yet are stored
    as -1. This makes bugs obvious — a negative time is clearly wrong.
    """

    # --- Input fields (must be provided when creating a Process) ---
    pid: str
    arrival_time: int
    burst_time: int

    # --- Internal simulation state (managed by the scheduler) ---
    remaining_time: int = field(init=False)
    waiting_time_so_far: int = field(default=0, init=False)

    # --- Output / metric fields (filled in after simulation completes) ---
    start_time: int = field(default=-1, init=False)
    completion_time: int = field(default=-1, init=False)
    turnaround_time: int = field(default=-1, init=False)
    waiting_time: int = field(default=-1, init=False)
    response_time: int = field(default=-1, init=False)

    def __post_init__(self):
        """
        Called automatically by Python right after __init__.
        We use it to set remaining_time = burst_time, since remaining_time
        is not an __init__ parameter (the user doesn't supply it — it
        always starts equal to burst_time).
        """
        self.remaining_time = self.burst_time

    def reset(self):
        """
        Resets all simulation-state and output fields back to their
        initial values. Called before running each scheduling algorithm
        so that a fresh copy starts from a clean state.

        This is necessary because we run 4 different algorithms on the
        same set of processes — without reset(), the output of algorithm
        A would corrupt the input to algorithm B.
        """
        self.remaining_time = self.burst_time
        self.waiting_time_so_far = 0
        self.start_time = -1
        self.completion_time = -1
        self.turnaround_time = -1
        self.waiting_time = -1
        self.response_time = -1

    def copy(self):
        """
        Creates and returns a brand-new Process instance with the same
        pid, arrival_time, and burst_time, then calls reset() on it.

        We call copy() to give each scheduling algorithm its own
        independent list of Process objects. Modifying a copy does NOT
        affect the original or any other algorithm's copy.

        Returns:
            Process: A fresh, reset copy of this process.
        """
        new_process = Process(
            pid=self.pid,
            arrival_time=self.arrival_time,
            burst_time=self.burst_time,
        )
        new_process.reset()
        return new_process

    def finalize(self, current_time: int):
        """
        Called by a scheduling algorithm at the moment a process finishes
        (i.e., remaining_time reaches 0). Computes and stores all three
        output metrics.

        Parameters:
            current_time (int): The clock tick at which the process
                                completed its last CPU burst.

        Formulas:
            turnaround_time = completion_time - arrival_time
            waiting_time    = turnaround_time - burst_time
            response_time   = start_time - arrival_time
        """
        self.completion_time = current_time
        self.turnaround_time = self.completion_time - self.arrival_time
        self.waiting_time = self.turnaround_time - self.burst_time
        self.response_time = self.start_time - self.arrival_time

    def __repr__(self):
        """
        Human-readable string representation of the process.
        Shown when you print() a Process or inspect it in a test.
        """
        return (
            f"Process(pid={self.pid}, arrival={self.arrival_time}, "
            f"burst={self.burst_time}, remaining={self.remaining_time}, "
            f"ct={self.completion_time}, tat={self.turnaround_time}, "
            f"wt={self.waiting_time}, rt={self.response_time})"
        )
