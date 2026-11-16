# SchedX — Comprehensive Viva Voce Preparation Guide

This guide provides an exhaustive collection of academic questions, theoretical derivations, scenario analyses, and implementation insights designed for lab examinations, academic viva voces, and Operating Systems project defenses.

---

## SECTION 1: Operating Systems & CPU Scheduling Fundamentals

### Q1. What is the fundamental purpose of CPU scheduling in modern multiprogrammed operating systems?
**Answer:**
In a multiprogramming system, multiple processes reside in memory simultaneously. Whenever the currently running process must wait (e.g., for I/O completion, page faults, or synchronization locks), the Operating System switches the CPU away from that process and allocates it to another ready process. The core objectives are to maximize **CPU utilization**, maximize **throughput**, minimize **turnaround and waiting times**, and guarantee **bounded latency/response time** for interactive tasks.

### Q2. Distinguish between a Long-Term, Short-Term, and Medium-Term Scheduler.
**Answer:**
- **Long-Term Scheduler (Job Scheduler):** Determines which jobs from the mass-storage disk pool are admitted into main memory (Ready state), controlling the *degree of multiprogramming*.
- **Short-Term Scheduler (CPU Scheduler):** Executes frequently (every few milliseconds) to select which ready process in memory receives the CPU next.
- **Medium-Term Scheduler (Swapper):** Temporarily removes partially executed processes from main memory to disk (swapping out) to relieve memory pressure, and reintroduces them later (swapping in).

### Q3. What is the difference between the CPU Scheduler and the Dispatcher?
**Answer:**
- **Scheduler:** The decision-making algorithmic component that inspects the ready queue and selects the candidate process according to a specific policy (e.g., SJF, SRTF, HRRN, FAAS).
- **Dispatcher:** The low-level kernel module that gives physical control of the CPU to the selected process. Its duties include:
  1. Switching context (saving current CPU registers and restoring the incoming process's state).
  2. Switching from kernel mode to user mode.
  3. Jumping to the appropriate instruction address in the program to resume execution.
- **Dispatch Latency:** The elapsed time required for the dispatcher to stop one process and start another.

### Q4. What is a Process Control Block (PCB) and what state must be preserved during a context switch?
**Answer:**
The PCB is the kernel data structure representing a process. During a context switch, the kernel preserves:
- Program Counter ($PC$)
- General-purpose CPU register states
- Stack Pointer ($SP$)
- CPU Scheduling parameters (priority, remaining burst, waiting time)
- Memory-management state (page tables, base/limit registers)
- I/O status and open file descriptor tables

### Q5. What is the Convoy Effect?
**Answer:**
The Convoy Effect occurs when a CPU-bound process with a very long burst holds the CPU in a non-preemptive environment (like First-Come, First-Served), forcing numerous short I/O-bound processes to wait idly in the ready queue. This degrades CPU and device utilization because the I/O devices sit idle while the long process runs, and then the CPU sits idle when all the short processes rush to perform I/O at the same time.

---

## SECTION 2: Core Performance Metrics & Mathematical Formulations

### Q6. Define and mathematically state Turnaround Time ($TAT$), Waiting Time ($WT$), and Response Time ($RT$).
**Answer:**
Given process arrival time $AT$, burst time $BT$, first dispatch time $ST$, and final termination time $CT$:
1. **Turnaround Time ($TAT$):**
   $$TAT = CT - AT$$
   Total lifespan of the process from submission to completion.
2. **Waiting Time ($WT$):**
   $$WT = TAT - BT$$
   Total accumulated duration spent sitting in the ready queue without CPU allocation.
3. **Response Time ($RT$):**
   $$RT = ST - AT$$
   Elapsed latency before the process receives its very first CPU time slice. In non-preemptive schedulers without I/O, $RT \equiv WT$. In preemptive schedulers, $RT \le WT$.

### Q7. How are CPU Utilization and Throughput calculated over a simulation timeline?
**Answer:**
Given makespan $T_{\text{total}} = \max(CT_i)$ and total busy execution time $\sum BT_i$:
- **CPU Utilization:**
  $$\text{CPU Utilization} = \left( \frac{\text{Total Busy Time}}{T_{\text{total}}} \right) \times 100\% = \left( \frac{\sum BT_i}{T_{\text{total}}} \right) \times 100\%$$
- **Throughput:**
  $$\text{Throughput} = \frac{N}{T_{\text{total}}} \quad (\text{processes completed per unit time})$$

### Q8. What constitutes a Context Switch and a Preemption in our metrics engine?
**Answer:**
- **Context Switch:** Occurs whenever the CPU transitions execution from one process ID to a different process ID ($p_{\text{curr}} \ne p_{\text{next}}$, ignoring idle gaps).
- **Preemption:** Occurs specifically when a running process $p_{\text{curr}}$ is interrupted and descheduled before its burst has completed ($CT_i > t_{\text{interrupt}}$). A scheduled termination is a voluntary yield, not a preemption.

---

## SECTION 3: Classical Algorithms (SJF, SRTF, HRRN)

### Q9. Why is SJF mathematically optimal in minimizing average waiting time, and what is the proof intuition?
**Answer:**
**Proof Intuition:** Consider $n$ processes available at $t=0$ with burst times $b_1, b_2, \dots, b_n$.
The total waiting time is:
$$W_{\text{total}} = 0 + b_1 + (b_1 + b_2) + \dots + \sum_{k=1}^{n-1} b_k = \sum_{i=1}^{n} (n - i) b_i$$
To minimize this linear summation, the largest multiplier $(n-1)$ must be assigned to the smallest burst time, and the smallest multiplier $0$ to the largest burst time. Any inversion where $b_j > b_k$ for $j < k$ strictly increases total waiting time. Therefore, sorting bursts in monotonically non-decreasing order minimizes average waiting time.

### Q10. What is the fundamental fatal flaw of SJF and SRTF in production environments?
**Answer:**
**Starvation (Indefinite Postponement).** If there is a steady influx of short-burst processes into the ready queue, longer processes will perpetually have a higher remaining time and will never be selected for CPU allocation.

### Q11. How does exponential smoothing estimate future CPU burst times in real OS kernels?
**Answer:**
Since future CPU burst times cannot be known deterministically in general-purpose systems, kernels predict the next burst length $\tau_{n+1}$ using a weighted exponential moving average:
$$\tau_{n+1} = \alpha t_n + (1 - \alpha)\tau_n$$
where $t_n$ is the most recent actual burst, $\tau_n$ is the past predicted burst, and $\alpha \in [0, 1]$ controls the decay weight assigned to recent vs historical behavior.

### Q12. Explain how HRRN resolves starvation while remaining non-preemptive.
**Answer:**
HRRN calculates the **Response Ratio**:
$$RR_i = \frac{W_i + BT_i}{BT_i} = 1 + \frac{W_i}{BT_i}$$
- When a process first arrives, $W_i = 0 \implies RR_i = 1.0$.
- For short processes ($BT_i \to \text{small}$), $RR_i$ grows rapidly even for small waiting times.
- For long processes ($BT_i \to \text{large}$), although growth is slower, $W_i$ increases monotonically as it sits in the ready queue. Eventually, $W_i$ becomes so large that $RR_i$ surpasses the response ratio of newly arrived short jobs, guaranteeing execution without preemption.

---

## SECTION 4: Proposed Algorithm — FAAS (Fairness-Aware Adaptive Scheduling)

### Q13. What is FAAS and what are its four architectural pillars?
**Answer:**
FAAS is a hybrid, bounded-preemptive scheduling policy combining:
1. **Reciprocal Remaining-Time Efficiency:** Prioritizes shorter remaining tasks similarly to SRTF via $\frac{1}{\text{RemainingTime}}$.
2. **Dynamic Linear Waiting-Time Aging:** Escalates priority over time via $\alpha \times \text{ContinuousWaitingTime}$.
3. **Hard Starvation Prevention Override:** Guaranteed priority override when continuous wait meets or exceeds $T_{\text{starve}}$.
4. **Bounded Service Quantum ($Q=2$):** Bounded CPU dispatch intervals that eliminate 1-time-unit context switch thrashing.

### Q14. Explain the FAAS priority formula in detail.
**Answer:**
$$\text{Priority}(p_i) = \frac{1}{\text{RemainingTime}_i} + \left( \alpha \times \text{ContinuousWaitingTime}_i \right)$$
- **First Component ($\frac{1}{\text{RemainingTime}_i}$):** As remaining burst decreases, priority increases hyperbolicly. For example, a remaining burst of 1 yields $1.0$, while a remaining burst of 10 yields $0.1$.
- **Second Component ($\alpha \times \text{ContinuousWaitingTime}_i$):** Waiting time scales priority linearly. With aging factor $\alpha = 4.0$, waiting 2 units contributes $+8.0$ to priority, quickly dominating the reciprocal component and preventing starvation.

### Q15. Why does FAAS maintain separate Continuous Waiting Time and Cumulative Waiting Time?
**Answer:**
- **Continuous Waiting Time ($W_{\text{cont}}$):** Tracks consecutive waiting time since the process's *most recent* CPU service slice. When a process receives CPU allocation, $W_{\text{cont}}$ resets to $0$. This prevents a process that has already received service from "gaming" the starvation threshold.
- **Cumulative Waiting Time ($W_{\text{cumul}}$):** Monotonically accumulates the total time spent in the ready queue over the process's entire life cycle. This is preserved for calculating true system-wide performance metrics ($TAT$, $WT$).

### Q16. How does the FAAS Starvation Prevention Override work?
**Answer:**
At every scheduling decision point:
1. The scheduler checks if any ready candidate process satisfies $W_{\text{cont}} \ge T_{\text{starve}}$ (default $T_{\text{starve}} = 8$).
2. If one or more processes satisfy this condition:
   - The normal priority formula is **bypassed completely**.
   - The process with the highest continuous waiting time is declared starving and dispatched immediately.
   - Any ties among starving processes are broken by earliest arrival time, then by PID.

### Q17. Why is the service quantum bounded ($Q=2$) instead of checking preemption at every single time unit ($Q=1$)?
**Answer:**
Checking preemption at every single unit (pure continuous preemption) results in excessive context-switch frequency and cache thrashing. By enforcing a minimum service quantum $Q=2$, FAAS guarantees that a dispatched process can execute for at least 2 units (or until completion if remaining time $< 2$) before being preempted. This dramatically stabilizes context-switching costs while preserving interactive adaptability.

---

## SECTION 5: Benchmark Numerical Trace Questions

### Q18. Given the Benchmark Dataset (P1: 0, 6; P2: 1, 2; P3: 2, 4; P4: 4, 3), why does SRTF preempt P1 at $t=1$, but FAAS allows P1 to run until $t=2$?
**Answer:**
- **In SRTF:** At $t=1$, P2 arrives with burst $2$. P1 has remaining time $5$. Because $2 < 5$ and SRTF is continuously preemptive ($Q=1$), P1 is preempted immediately at $t=1$.
- **In FAAS:** P1 was dispatched at $t=0$ with guaranteed bounded quantum $Q=2$. Therefore, P1 is granted an uninterrupted execution slice from $t=0 \to 2$. P2's arrival at $t=1$ is registered in the ready queue, but scheduling evaluation is deferred until $t=2$, avoiding immediate context-switch overhead.

### Q19. Walk through the FAAS priority competition at $t=2$ on the benchmark dataset.
**Answer:**
At $t=2$:
- **P1:** $\text{Remaining} = 4, W_{\text{cont}} = 0 \implies \text{Priority} = \frac{1}{4} + 4(0) = 0.25$
- **P2:** $\text{Remaining} = 2, W_{\text{cont}} = 1 \implies \text{Priority} = \frac{1}{2} + 4(1) = 4.50$
- **P3:** $\text{Remaining} = 4, W_{\text{cont}} = 0 \implies \text{Priority} = \frac{1}{4} + 4(0) = 0.25$
P2 has the highest priority score ($4.50$) and is dispatched for quantum $\min(2, 2) = 2$ units from $t=2 \to 4$.

### Q20. What is the average waiting time for all 4 algorithms on the benchmark dataset?
**Answer:**
- **SRTF:** $3.25$ time units (optimal)
- **SJF:** $4.50$ time units
- **HRRN:** $4.75$ time units
- **FAAS:** $5.75$ time units (deliberate trade-off for guaranteed fairness and bounded preemption)

---

## SECTION 6: Project Architecture & Software Engineering

### Q21. Explain the directory structure and architectural separation of concerns in SchedX.
**Answer:**
The codebase follows strict layered decoupling:
1. `schedulers/process.py`: Shared domain model (`Process` dataclass with state transitions, immutability clones, and validation).
2. `schedulers/`: Individual, isolated algorithmic engines (`sjf.py`, `srtf.py`, `hrrn.py`, `faas.py`). Each algorithm takes independent process copies and returns execution timelines without external side effects.
3. `core/metrics.py`: Standardized performance evaluation engine calculating all 10 academic metrics uniformly.
4. `core/runner.py`: Unified orchestrator executing all schedulers concurrently on isolated copies, packaging outputs into a clean `SimulationResults` structure.
5. `core/charts.py`: Visualization engine generating interactive Plotly Gantt timelines and comparative bar charts.
6. `core/generator.py`: Synthetic workload generator implementing uniform, short-heavy, long-heavy, and mixed distributions.
7. `core/faas_explainer.py`: Read-only educational observer that parses FAAS decision logs, decomposes priority components, and detects SRTF divergence.
8. `app.py`: Streamlit presentation layer implementing horizontal top navigation and dark-themed analytics.

### Q22. Why are process instances cloned using deep copies before being passed to schedulers?
**Answer:**
If processes were passed by reference, mutable fields (such as `remaining_time`, `start_time`, `completion_time`, `is_completed`) modified during the execution of one scheduler (e.g., SJF) would corrupt the input for subsequent schedulers (e.g., SRTF). Cloning via `copy.deepcopy()` or `Process.from_dict()` guarantees absolute input immutability and mathematical independence across runs.

### Q23. Why is the FAAS Decision Explainer decoupled from the scheduling loop rather than embedded within it?
**Answer:**
Separation of concerns. The scheduling engine (`schedulers/faas.py`) must remain lean, performant, and focused strictly on CPU allocation mechanics. It emits an immutable event log (`decision_log`). The explainer (`core/faas_explainer.py`) is an external observer that consumes this log post-run to produce UI tables, explanations, and Plotly charts. This ensures that visualization logic never risks introducing bugs into the core scheduling mathematics.

---

## SECTION 7: Real-World OS Comparisons & Advanced Scenarios

### Q24. How does FAAS relate to the Linux Completely Fair Scheduler (CFS)?
**Answer:**
- **Linux CFS:** Uses a red-black tree indexed by `vruntime` (virtual runtime). Tasks with the smallest `vruntime` are scheduled next. Preemption occurs dynamically when a task's `vruntime` exceeds its peers.
- **FAAS Analogy:** FAAS uses continuous waiting time and dynamic aging to achieve fair progression. Like CFS's `latency_target`, FAAS uses bounded quantum $Q=2$ to balance time-slicing with context-switch penalties. Unlike CFS, FAAS explicitly provides a hard starvation prevention threshold ($T_{\text{starve}}$) that overrides priority when latency boundaries are breached.

### Q25. What happens when a long-burst process arrives at $t=0$ followed by continuous arrivals of short processes?
**Answer:**
- **SJF:** The long process runs first to completion because no other processes were present at $t=0$. The arriving short processes must wait in the queue.
- **SRTF:** The long process starts at $t=0$. As soon as the first short process arrives at $t=1$, the long process is preempted and starved indefinitely until all short processes finish.
- **HRRN:** The long process runs to completion. Once free, older short processes execute according to their response ratios.
- **FAAS:** The long process executes for $Q=2$ units. A short process is dispatched. As more short processes arrive, the long process's continuous waiting time accumulates. Either its aging score $(\alpha \times W_{\text{cont}})$ overtakes the short jobs, or it hits $T_{\text{starve}} = 8$, triggering an emergency override and guaranteeing CPU time.

---

## SECTION 8: Viva Quick-Fire Summary Table

| Question | Short Answer |
|---|---|
| Which algorithm minimizes average turnaround time? | **SRTF** |
| Which algorithm has zero context switches during process runs? | **SJF and HRRN** (non-preemptive) |
| Which algorithm prevents starvation without preemption? | **HRRN** |
| What triggers a starvation override in FAAS? | $\text{ContinuousWaitingTime} \ge T_{\text{starve}}$ |
| What is the default FAAS service quantum? | $Q = 2$ time units |
| What happens to continuous waiting time upon CPU dispatch? | Resets to $0$ |
| What is the tie-breaker rule across all algorithms in SchedX? | Earlier Arrival Time, then alphabetical Process ID |
| Total test cases in the automated test suite? | **91 tests** (100% passing) |
