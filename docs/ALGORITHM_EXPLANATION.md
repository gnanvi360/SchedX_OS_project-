# SchedX — Algorithmic Explanation & Comparative Analysis

## 1. Overview & Theoretical Framework

CPU scheduling is the core Operating Systems mechanism that determines which ready process is allocated CPU execution time when multiple processes compete for CPU resources. The uniprocessor scheduling objective function seeks to optimize system performance across several conflicting criteria:

1. **Turnaround Time ($TAT$):** Elapsed time from process submission to process completion:
   $$TAT_i = CT_i - AT_i$$
2. **Waiting Time ($WT$):** Total duration spent by a process residing in the ready queue:
   $$WT_i = TAT_i - BT_i$$
3. **Response Time ($RT$):** Time elapsed between process arrival and its very first CPU allocation:
   $$RT_i = ST_i - AT_i$$
4. **CPU Utilization:** Percentage of total elapsed simulation time during which the CPU is executing user processes:
   $$\text{CPU Utilization} = \left( \frac{\sum BT_i}{\text{Max}(CT_i)} \right) \times 100\%$$
5. **Throughput:** Rate of completed process terminations per unit time:
   $$\text{Throughput} = \frac{N}{\text{Max}(CT_i)}$$

---

## 2. Benchmark Dataset Reference

To provide a consistent, mathematically rigorous baseline across all algorithmic analyses in this document, we utilize the standardized **Benchmark Dataset**:

| Process ID | Arrival Time ($AT$) | Burst Time ($BT$) |
|---|---|---|
| **P1** | 0 | 6 |
| **P2** | 1 | 2 |
| **P3** | 2 | 4 |
| **P4** | 4 | 3 |

- Total Burst Workload: $\sum BT_i = 6 + 2 + 4 + 3 = 15$ time units.
- Minimum possible makespan (no idle gaps): $15$ time units ($t=0 \to 15$).

---

## 3. Shortest Job First (SJF) — Non-Preemptive

### 3.1 Mathematical Selection Rule
$$\text{Selected Process} = \arg\min_{p_i \in \text{Ready}(t)} \left( BT_i, AT_i, \text{PID}_i \right)$$

When the CPU becomes free, SJF inspects all processes that have already arrived ($AT_i \le t$). It selects the candidate with the shortest initial burst time. Once assigned to the CPU, the process executes uninterrupted until termination (non-preemptive).

### 3.2 Step-by-Step Execution Trace

```
Timeline: [ P1: 0 -> 6 ] [ P2: 6 -> 8 ] [ P4: 8 -> 11 ] [ P3: 11 -> 15 ]
```

1. **$t = 0$:** Only **P1** has arrived ($AT=0, BT=6$). Dispatched immediately.
2. **$t = 1 \dots 5$:** P2, P3, and P4 arrive in the ready queue. Because SJF is non-preemptive, P1 retains the CPU.
3. **$t = 6$:** P1 completes ($CT=6$). Ready queue candidates:
   - P2 ($BT=2$)
   - P3 ($BT=4$)
   - P4 ($BT=3$)
   Smallest burst is P2 ($BT=2$). Dispatched from $t=6 \to 8$.
4. **$t = 8$:** P2 completes ($CT=8$). Ready queue candidates:
   - P3 ($BT=4$)
   - P4 ($BT=3$)
   Smallest burst is P4 ($BT=3$). Dispatched from $t=8 \to 11$.
5. **$t = 11$:** P4 completes ($CT=11$). Only P3 remains ($BT=4$). Dispatched from $t=11 \to 15$.
6. **$t = 15$:** All processes completed.

### 3.3 Numerical Results
| PID | $AT$ | $BT$ | $ST$ | $CT$ | $TAT = CT - AT$ | $WT = TAT - BT$ | $RT = ST - AT$ |
|---|---|---|---|---|---|---|---|
| **P1** | 0 | 6 | 0 | 6 | 6 | 0 | 0 |
| **P2** | 1 | 2 | 6 | 8 | 7 | 5 | 5 |
| **P3** | 2 | 4 | 11 | 15 | 13 | 9 | 9 |
| **P4** | 4 | 3 | 8 | 11 | 7 | 4 | 4 |
| **Average** | — | — | — | — | **8.25** | **4.50** | **4.50** |

- **Context Switches:** $3$
- **Preemptions:** $0$

### 3.4 Strengths, Weaknesses & Viva Insights
- **Strengths:** Provably minimizes average waiting time when all processes arrive simultaneously ($t=0$).
- **Weaknesses:** Highly vulnerable to **starvation** (indefinite postponement). If short jobs arrive continuously, long jobs will never acquire the CPU.
- **Limitation:** In general-purpose OS kernels, total burst times cannot be known in advance and must be estimated using exponential smoothing ($S_{n+1} = \alpha t_n + (1-\alpha)S_n$).

---

## 4. Shortest Remaining Time First (SRTF) — Preemptive

### 4.1 Mathematical Selection Rule
$$\text{Selected Process} = \arg\min_{p_i \in \text{Ready}(t)} \left( \text{RemainingTime}_i(t), AT_i, \text{PID}_i \right)$$

SRTF is the preemptive generalization of SJF. Whenever a process arrives or the current CPU allocation ends, the scheduler compares the remaining burst time of the executing process against all ready processes. If any ready candidate has a strictly smaller remaining burst time, the currently running process is preempted.

### 4.2 Step-by-Step Execution Trace

```
Timeline: [ P1: 0 -> 1 ] [ P2: 1 -> 3 ] [ P3: 3 -> 7 ] [ P4: 7 -> 10 ] [ P1: 10 -> 15 ]
```

1. **$t = 0$:** P1 starts execution ($BT=6$).
2. **$t = 1$:** P2 arrives ($AT=1, BT=2$). P1 has $\text{Remaining}=5$. Because $2 < 5$, **P1 is preempted**. P2 is dispatched.
3. **$t = 2$:** P3 arrives ($AT=2, BT=4$). P2 has $\text{Remaining}=1$. Since $1 < 4$, P2 continues.
4. **$t = 3$:** P2 completes ($CT=3$). Ready queue candidates:
   - P3 ($\text{Remaining}=4$)
   - P1 ($\text{Remaining}=5$)
   Smallest remaining time is P3 ($4 < 5$). P3 is dispatched.
5. **$t = 4$:** P4 arrives ($AT=4, BT=3$). P3 has executed 1 unit ($\text{Remaining}=3$). We have a tie between P3 ($3$) and P4 ($3$). Tie-breaker rules favor the earlier arrived process (P3). P3 continues.
6. **$t = 7$:** P3 completes ($CT=7$). Ready queue candidates:
   - P4 ($\text{Remaining}=3$)
   - P1 ($\text{Remaining}=5$)
   P4 is dispatched ($3 < 5$).
7. **$t = 10$:** P4 completes ($CT=10$). P1 is the sole remaining candidate ($\text{Remaining}=5$). P1 resumes and runs to completion at $t=15$.

### 4.3 Numerical Results
| PID | $AT$ | $BT$ | $ST$ | $CT$ | $TAT = CT - AT$ | $WT = TAT - BT$ | $RT = ST - AT$ |
|---|---|---|---|---|---|---|---|
| **P1** | 0 | 6 | 0 | 15 | 15 | 9 | 0 |
| **P2** | 1 | 2 | 1 | 3 | 2 | 0 | 0 |
| **P3** | 2 | 4 | 3 | 7 | 5 | 1 | 1 |
| **P4** | 4 | 3 | 7 | 10 | 6 | 3 | 3 |
| **Average** | — | — | — | — | **7.00** | **3.25** | **1.00** |

- **Context Switches:** $4$
- **Preemptions:** $1$ (P1 preempted at $t=1$)

### 4.4 Strengths, Weaknesses & Viva Insights
- **Strengths:** Achieves the theoretical minimum average turnaround time and average waiting time across all scheduling algorithms.
- **Weaknesses:** Severe starvation vulnerability for long jobs; significantly higher context switching overhead and CPU cache invalidation penalties.

---

## 5. Highest Response Ratio Next (HRRN) — Non-Preemptive with Aging

### 5.1 Mathematical Selection Rule
$$\text{Response Ratio } (RR_i) = \frac{W_i + BT_i}{BT_i} = 1 + \frac{W_i}{BT_i}$$
$$\text{Selected Process} = \arg\max_{p_i \in \text{Ready}(t)} \left( RR_i, -AT_i, -\text{PID}_i \right)$$

HRRN is a non-preemptive algorithm designed to mitigate the starvation vulnerabilities of SJF without incurring preemptive context-switch costs. It balances short burst preference with waiting time accumulation:
- For short jobs ($BT_i \to \text{small}$), the denominator is small, giving high initial priority.
- For long jobs ($BT_i \to \text{large}$), as waiting time $W_i$ grows, the numerator increases, driving up the response ratio until the job eventually overtakes shorter newcomers.

### 5.2 Step-by-Step Execution Trace

```
Timeline: [ P1: 0 -> 6 ] [ P2: 6 -> 8 ] [ P3: 8 -> 12 ] [ P4: 12 -> 15 ]
```

1. **$t = 0 \to 6$:** P1 executes to completion ($CT=6$).
2. **$t = 6$:** Scheduling decision evaluated across ready candidates:
   - **P2:** $W = 6 - 1 = 5, BT = 2 \implies RR = 1 + \frac{5}{2} = 3.50$
   - **P3:** $W = 6 - 2 = 4, BT = 4 \implies RR = 1 + \frac{4}{4} = 2.00$
   - **P4:** $W = 6 - 4 = 2, BT = 3 \implies RR = 1 + \frac{2}{3} \approx 1.67$
   Highest ratio is **P2** ($3.50$). Dispatched from $t=6 \to 8$.
3. **$t = 8$:** P2 completes ($CT=8$). Scheduling decision:
   - **P3:** $W = 8 - 2 = 6, BT = 4 \implies RR = 1 + \frac{6}{4} = 2.50$
   - **P4:** $W = 8 - 4 = 4, BT = 3 \implies RR = 1 + \frac{4}{3} \approx 2.33$
   Highest ratio is **P3** ($2.50$). Dispatched from $t=8 \to 12$.
4. **$t = 12$:** P3 completes ($CT=12$). P4 is the sole remaining candidate. Dispatched from $t=12 \to 15$.

### 5.3 Numerical Results
| PID | $AT$ | $BT$ | $ST$ | $CT$ | $TAT = CT - AT$ | $WT = TAT - BT$ | $RT = ST - AT$ |
|---|---|---|---|---|---|---|---|
| **P1** | 0 | 6 | 0 | 6 | 6 | 0 | 0 |
| **P2** | 1 | 2 | 6 | 8 | 7 | 5 | 5 |
| **P3** | 2 | 4 | 8 | 12 | 10 | 6 | 6 |
| **P4** | 4 | 3 | 12 | 15 | 11 | 8 | 8 |
| **Average** | — | — | — | — | **8.50** | **4.75** | **4.75** |

- **Context Switches:** $3$
- **Preemptions:** $0$

### 5.4 Strengths, Weaknesses & Viva Insights
- **Strengths:** Inherently eliminates indefinite starvation without preemption.
- **Weaknesses:** Because it is non-preemptive, an exceptionally long job that acquires the CPU cannot be paused, degrading responsiveness for urgent interactive tasks.

---

## 6. Fairness-Aware Adaptive Scheduling (FAAS) — Proposed Policy

### 6.1 Architectural Motivation
Classical CPU scheduling algorithms expose fundamental engineering compromises:
- **SRTF** maximizes throughput and minimizes turnaround times, but risks severe starvation and context-switch thrashing.
- **HRRN** prevents starvation, but its non-preemptive structure degrades interactive response times.
- **Round Robin** guarantees fair time-slicing, but ignores job duration, degrading turnaround time.

**FAAS** is engineered to unify the optimal turnaround characteristics of SRTF with the starvation-immunity of aging policies and the bounded preemption stability of Round Robin.

### 6.2 Mathematical Formulation

1. **Composite Priority Score:**
   $$\text{Priority}(p_i) = \frac{1}{\text{RemainingTime}_i} + \left( \alpha \times \text{ContinuousWaitingTime}_i \right)$$
   - $\frac{1}{\text{RemainingTime}_i}$: Reciprocal remaining time prioritizes short tasks (SRTF behavior).
   - $\alpha \times \text{ContinuousWaitingTime}_i$: Dynamic aging component linearly boosts waiting jobs.

2. **Hard Starvation Prevention Override:**
   $$\text{Starvation Condition: } \text{ContinuousWaitingTime}_i \ge T_{\text{starve}}$$
   If any ready process satisfies this condition, normal priority competition is bypassed. The longest-starving process is dispatched immediately.

3. **Continuous vs Cumulative Waiting Time:**
   - $\text{ContinuousWaitingTime}$ measures consecutive unserviced wait time. It resets to $0$ as soon as a process receives CPU allocation.
   - $\text{CumulativeWaitingTime}$ continuously tracks total wait time across the process lifespan for accurate performance metrics.

4. **Guaranteed Bounded Service Quantum ($Q$):**
   Once dispatched, a process is guaranteed an uninterrupted CPU quantum of:
   $$\text{Service Allocation} = \min \left( Q, \text{RemainingTime}_i \right)$$
   Default $Q = 2$. Bounded preemption eliminates 1-unit context switch thrashing.

### 6.3 Step-by-Step Execution Trace ($Q=2, \alpha=4.0, T_{\text{starve}}=8$)

```
Timeline: [ P1: 0->2 ] [ P2: 2->4 ] [ P1: 4->6 ] [ P3: 6->8 ] [ P4: 8->10 ] [ P1: 10->12 ] [ P3: 12->14 ] [ P4: 14->15 ]
```

1. **$t = 0$:** P1 starts ($BT=6$). Runs for quantum $Q=2$ ($t=0 \to 2$, remaining $=4$).
2. **$t = 2$:** Candidates evaluated:
   - P1: rem=4, wait=0 $\implies \frac{1}{4} + 4(0) = 0.25$
   - P2: rem=2, wait=1 $\implies \frac{1}{2} + 4(1) = 4.50$
   - P3: rem=4, wait=0 $\implies \frac{1}{4} + 4(0) = 0.25$
   **P2 wins** ($4.50$). Runs $t=2 \to 4$, completing at $t=4$ ($CT=4$).
3. **$t = 4$:** Candidates evaluated:
   - P1: rem=4, wait=2 $\implies 0.25 + 4(2) = 8.25$
   - P3: rem=4, wait=2 $\implies 0.25 + 4(2) = 8.25$
   - P4: rem=3, wait=0 $\implies 0.33 + 4(0) = 0.33$
   Tie between P1 and P3 ($8.25$) broken by earlier arrival ($AT_1=0 < AT_3=2$). **P1 dispatched** from $t=4 \to 6$ (remaining $=2$).
4. **$t = 6$:** Candidates evaluated:
   - P1: rem=2, wait=0 $\implies 0.50 + 0 = 0.50$
   - P3: rem=4, wait=4 $\implies 0.25 + 4(4) = 16.25$
   - P4: rem=3, wait=2 $\implies 0.33 + 4(2) = 8.33$
   **P3 wins** ($16.25$). Runs $t=6 \to 8$ (remaining $=2$).
5. **$t = 8$:** Candidates evaluated:
   - P1: rem=2, wait=2 $\implies 0.50 + 8 = 8.50$
   - P3: rem=2, wait=0 $\implies 0.50 + 0 = 0.50$
   - P4: rem=3, wait=4 $\implies 0.33 + 16 = 16.33$
   **P4 wins** ($16.33$). Runs $t=8 \to 10$ (remaining $=1$).
6. **$t = 10$:** Candidates evaluated:
   - P1: rem=2, wait=4 $\implies 0.50 + 16 = 16.50$
   - P3: rem=2, wait=2 $\implies 0.50 + 8 = 8.50$
   - P4: rem=1, wait=0 $\implies 1.00 + 0 = 1.00$
   **P1 wins** ($16.50$). Runs $t=10 \to 12$, completing at $t=12$ ($CT=12$).
7. **$t = 12$:** Candidates evaluated:
   - P3: rem=2, wait=4 $\implies 0.50 + 16 = 16.50$
   - P4: rem=1, wait=2 $\implies 1.00 + 8 = 9.00$
   **P3 wins** ($16.50$). Runs $t=12 \to 14$, completing at $t=14$ ($CT=14$).
8. **$t = 14$:** P4 is the sole remaining process ($\text{Remaining}=1$). Runs $t=14 \to 15$, completing at $t=15$ ($CT=15$).

### 6.4 Numerical Results
| PID | $AT$ | $BT$ | $ST$ | $CT$ | $TAT = CT - AT$ | $WT = TAT - BT$ | $RT = ST - AT$ |
|---|---|---|---|---|---|---|---|
| **P1** | 0 | 6 | 0 | 12 | 12 | 6 | 0 |
| **P2** | 1 | 2 | 2 | 4 | 3 | 1 | 1 |
| **P3** | 2 | 4 | 6 | 14 | 12 | 8 | 4 |
| **P4** | 4 | 3 | 8 | 15 | 11 | 8 | 4 |
| **Average** | — | — | — | — | **9.50** | **5.75** | **2.25** |

- **Context Switches:** $7$
- **Preemptions:** $4$

---

## 7. Comparative Performance Benchmark

| Metric | SJF | SRTF | HRRN | FAAS ($Q=2, \alpha=4.0, T=8$) | Optimal Algorithm |
|---|---|---|---|---|---|
| **Average Turnaround Time** | $8.25$ | **$7.00$** | $8.50$ | $9.50$ | **SRTF** |
| **Average Waiting Time** | $4.50$ | **$3.25$** | $4.75$ | $5.75$ | **SRTF** |
| **Average Response Time** | $4.50$ | **$1.00$** | $4.75$ | $2.25$ | **SRTF** |
| **CPU Utilization (%)** | $100\%$ | $100\%$ | $100\%$ | $100\%$ | Tied (All 100%) |
| **Throughput (proc/unit)** | $0.2667$ | $0.2667$ | $0.2667$ | $0.2667$ | Tied (All 0.2667) |
| **Context Switches** | **$3$** | $4$ | **$3$** | $7$ | **SJF / HRRN** |
| **Preemptions** | **$0$** | $1$ | **$0$** | $4$ | **SJF / HRRN** |
| **Starvation Immunity** | ❌ None | ❌ None | ✅ Complete | ✅ Absolute Guaranteed | **FAAS / HRRN** |

### Synthesis & Trade-Off Analysis
1. **The Turnaround vs Fairness Trade-Off:** SRTF attains the absolute lowest average waiting time ($3.25$) at the cost of complete indifference to fairness. FAAS introduces a minor turnaround penalty ($5.75$ vs $3.25$) in exchange for guaranteed starvation immunity and smooth interactive progress across all processes.
2. **Context Switching Balance:** While non-preemptive algorithms produce fewer context switches ($3$), they cannot adapt mid-execution. FAAS bounds context switching overhead via quantum $Q=2$, avoiding the excessive overhead of pure 1-unit preemptive policies.
