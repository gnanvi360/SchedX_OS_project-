# SchedX — Comprehensive Test Suite & Regression Verification Specification

This document details the complete automated test suite powering SchedX. The test suite comprises **99 unit, integration, and mathematical regression tests** implemented with `pytest`.

---

## 1. Test Suite Architecture & Summary

| Test Module | Component Tested | Test Count | Key Focus Areas | Status |
|---|---|---|---|---|
| `tests/test_sjf.py` | Non-Preemptive SJF | 7 | Burst comparison, tie-breaks, idle periods, immutability | **PASSED** |
| `tests/test_srtf.py` | Preemptive SRTF | 10 | Mid-burst preemption, remaining time ties, metrics | **PASSED** |
| `tests/test_hrrn.py` | Non-Preemptive HRRN | 10 | Response ratio aging, tie-breaks, idle CPU handling | **PASSED** |
| `tests/test_faas.py` | Proposed FAAS Scheduler | 16 | Priority formula, aging, starvation override, bounded quantum | **PASSED** |
| `tests/test_metrics.py` | Metrics Engine | 12 | TAT, WT, RT, utilization, context switches, preemptions | **PASSED** |
| `tests/test_runner.py` | Unified Scheduler Runner | 10 | Cross-algorithm execution, input validation, immutability | **PASSED** |
| `tests/test_charts.py` | Visualization Engine | 9 | Gantt generation, idle rendering, color determinism | **PASSED** |
| `tests/test_generator.py` | Workload Generator | 10 | Presets, boundary checks, seed reproducibility | **PASSED** |
| `tests/test_faas_explainer.py` | FAAS Decision Inspector | 7 | Component decomposition, starvation alert, SRTF divergence | **PASSED** |
| `tests/test_backend_api.py` | FastAPI Backend & REST API | 8 | Health check, presets, generator, multi-algorithm simulation, FAAS inspector | **PASSED** |
| **TOTAL** | **Entire Application** | **99** | **Comprehensive Full System Verification** | **100% PASSED** |

---

## 2. Module-by-Module Test Specifications

### 2.1 `tests/test_sjf.py` (Shortest Job First — 7 Tests)
1. `test_different_burst_times`: Verifies that processes arriving simultaneously at $t=0$ are dispatched strictly in order of shortest burst time.
2. `test_different_arrival_times`: Verifies that a process arriving earlier executes first even if a later process has a shorter burst (non-preemptive property).
3. `test_identical_burst_times`: Verifies that ties in burst times are broken deterministically by earliest arrival time, then by PID.
4. `test_cpu_idle_before_first_arrival`: Verifies that when the first process arrives at $t > 0$, the scheduler correctly inserts an IDLE interval from $0 \to AT_1$.
5. `test_all_arrive_at_zero`: Verifies correct makespan and metrics when all jobs arrive at $t=0$.
6. `test_long_process_first_nonpreemptive`: Verifies that once a long process begins execution, incoming short processes cannot preempt it.
7. `test_originals_not_modified`: Asserts that the original input list of `Process` objects is unmodified post-execution.

### 2.2 `tests/test_srtf.py` (Shortest Remaining Time First — 10 Tests)
1. `test_all_arrive_at_zero`: Validates that SRTF behaves identically to SJF when all jobs arrive at $t=0$.
2. `test_preemption_on_arrival`: Verifies that when a newly arrived job has a remaining burst strictly smaller than the executing job, preemption occurs immediately at the arrival timestamp.
3. `test_multiple_preemptions`: Verifies cascading preemptions where successive arrivals each preempt the executing process.
4. `test_equal_remaining_no_preemption`: Verifies that if an arriving process has remaining time equal to the running process, preemption does NOT occur (favoring the currently running job).
5. `test_cpu_idle_before_first_arrival`: Validates idle gap handling when $AT_1 > 0$.
6. `test_identical_arrivals_tiebreak_pid`: Verifies deterministic tie-breaking by Process ID for identical arrival and burst times.
7. `test_single_process`: Verifies baseline execution and metric calculation for $N=1$.
8. `test_long_process_with_short_arrivals`: Verifies that a long process interrupted by short arrivals is correctly suspended and resumed later.
9. `test_originals_not_modified`: Validates process object immutability.
10. `test_all_metrics_manual_verification`: Step-by-step manual numerical check of TAT, WT, RT against textbook calculations.

### 2.3 `tests/test_hrrn.py` (Highest Response Ratio Next — 10 Tests)
1. `test_all_arrive_at_zero`: Verifies that at $t=0$ when $W=0$, HRRN selects the shortest burst job first.
2. `test_different_arrival_times`: Verifies selection when arrival times stagger.
3. `test_different_burst_times`: Verifies correct response ratio sorting across varying burst lengths.
4. `test_long_waiting_process_gains_priority`: Validates aging by showing that a long job waiting in the queue eventually surpasses a newly arrived shorter job:
   $$RR = 1 + \frac{W}{B}$$
5. `test_equal_response_ratio_tie_breaker`: Verifies deterministic tie-breaking when two ready processes have identical response ratios.
6. `test_cpu_idle_before_first_arrival`: Validates IDLE block insertion from $0 \to AT_1$.
7. `test_single_process`: Baseline single-job execution.
8. `test_multiple_arrivals_during_execution`: Verifies ready queue accumulation while a long process occupies the CPU.
9. `test_originals_not_modified`: Validates input immutability.
10. `test_all_metrics_verification`: Full numerical assertion of TAT, WT, RT, and completion times.

### 2.4 `tests/test_faas.py` (Fairness-Aware Adaptive Scheduling — 16 Tests)
1. `test_single_process`: Verifies that a single process runs in slices bounded by quantum $Q$.
2. `test_multiple_arrive_at_zero`: Verifies initial priority computation when $W_{\text{cont}} = 0$.
3. `test_different_arrival_times`: Verifies ready queue dynamic updates at arrival events.
4. `test_short_competing_with_long`: Verifies that short jobs initially take precedence due to the reciprocal term $\frac{1}{\text{RemainingTime}}$.
5. `test_aging_increases_priority`: Verifies that unserviced continuous wait time increases priority score via $\alpha \times W_{\text{cont}}$.
6. `test_starvation_threshold_activates`: Verifies that when $W_{\text{cont}} \ge T_{\text{starve}}$, the starvation flag is raised in the candidate log.
7. `test_starvation_protected_process_receives_service`: Verifies that an emergency starvation override bypasses normal priority competition and forces dispatch.
8. `test_guaranteed_quantum_bounded`: Verifies that dispatch intervals never exceed the configured quantum $Q$.
9. `test_process_finishes_before_quantum`: Verifies that if a process has remaining time $R < Q$, it yields the CPU immediately upon completion without wasting time.
10. `test_arrival_during_quantum`: Verifies that arrivals occurring during an ongoing quantum slice are queued and evaluated at the slice boundary.
11. `test_cpu_idle_periods`: Verifies IDLE interval recording when no processes are ready.
12. `test_multiple_starvation_protected_processes`: Verifies priority arbitration among multiple starving processes (longest wait first, then arrival time).
13. `test_identical_priority_scores_tiebreak`: Verifies deterministic tie-breaking for equal priority scores.
14. `test_originals_not_modified`: Validates process immutability.
15. `test_all_performance_metrics`: Validates accurate TAT, WT, RT, and utilization calculations.
16. `test_empty_process_list` & `test_invalid_parameters`: Validates exception raising for invalid configurations ($Q \le 0$, $\alpha < 0$, $T_{\text{starve}} \le 0$).

### 2.5 `tests/test_metrics.py` (Metrics Engine — 12 Tests)
1. `test_average_metrics_calculation`: Mathematical checks for mean Turnaround, Waiting, and Response Times.
2. `test_cpu_utilization_no_idle`: Confirms $100\%$ utilization when no idle gaps exist.
3. `test_cpu_utilization_with_idle`: Validates utilization formula when idle intervals are present:
   $$\text{Util} = \frac{\text{Busy}}{\text{Busy} + \text{Idle}} \times 100\%$$
4. `test_throughput_calculation`: Validates $N / T_{\text{total}}$ throughput computation.
5. `test_context_switch_counting`: Validates exact context switch transitions across multi-segment schedules.
6. `test_preemption_counting`: Verifies that interrupted, non-completing process intervals increment the preemption counter.
7. `test_total_busy_and_idle_time`: Validates time accounting across complex timelines.
8. `test_empty_and_zero_division`: Asserts graceful zero-handling when process count is zero.
9. `test_single_process`: Baseline verification for $N=1$.
10. `test_multiple_arrivals`: Numerical verification for staggered arrivals.
11. `test_benchmark_dataset_all_algorithms`: **Gold Standard Regression Test** comparing all 4 algorithms on the benchmark dataset against precomputed theoretical values.
12. `test_originals_unchanged`: Asserts process immutability during metrics evaluation.

### 2.6 `tests/test_runner.py` (Unified Scheduler Runner — 10 Tests)
1. `test_all_four_algorithms_execute`: Verifies that `run_all_schedulers` successfully returns outputs for SJF, SRTF, HRRN, and FAAS.
2. `test_immutability_and_independence`: Asserts that running all schedulers does not cross-contaminate state between algorithms.
3. `test_metrics_dataframe_generation`: Verifies that comparative summary DataFrames are properly structured.
4. `test_empty_input_handling`: Asserts that empty process lists raise descriptive `ValueError` exceptions.
5. `test_invalid_inputs_rejected`: Asserts validation rejections for negative burst times, duplicate PIDs, or negative arrival times.
6. `test_different_arrivals_and_idle`: Validates idle handling consistency across all four schedulers.
7. `test_faas_configuration_propagation`: Verifies that custom $Q$, $\alpha$, and $T_{\text{starve}}$ values are correctly passed into `run_faas`.
8. `test_process_dataframe_export`: Confirms tabular export formatting for per-process completion statistics.
9. `test_benchmark_numerical_validation`: Full numerical assertion of all benchmark metric values.
10. `test_invalid_faas_parameters`: Confirms boundary parameter validation for FAAS.

### 2.7 `tests/test_charts.py` (Visualization Engine — 9 Tests)
1. `test_color_map_determinism_and_idle`: Verifies that identical PIDs receive consistent colors across all charts and that IDLE is mapped to grey.
2. `test_gantt_chart_generation`: Verifies that Gantt figures are valid Plotly `go.Figure` instances containing correct bar traces.
3. `test_gantt_chart_with_idle`: Confirms IDLE intervals are visually rendered.
4. `test_preemptive_timeline_gantt`: Verifies segmented Gantt chart rendering for preemptive executions.
5. `test_empty_and_zero_duration_timeline`: Validates graceful empty figure generation without crashes.
6. `test_metric_bar_chart`: Verifies single-metric comparative bar chart generation.
7. `test_create_all_comparison_charts`: Verifies batch creation of all 6 comparative bar charts.
8. `test_faas_decision_visualization`: Verifies FAAS priority score trajectory chart generation.
9. `test_benchmark_dataset_visualization`: End-to-end chart rendering on the benchmark dataset.

### 2.8 `tests/test_generator.py` (Random Workload Generator — 10 Tests)
1. `test_process_count_and_unique_pids`: Confirms exact requested process count and unique PID generation.
2. `test_valid_arrival_and_burst_times`: Asserts generated arrival and burst times respect configured bounds $[min, max]$.
3. `test_uniform_distribution`: Confirms statistical bounds for uniform sampling.
4. `test_short_vs_long_job_distributions`: Validates skew in short-heavy and long-heavy presets.
5. `test_mixed_workload`: Validates distribution mixing in multimodal presets.
6. `test_seed_reproducibility`: Confirms identical seeds yield bit-for-bit identical process lists.
7. `test_invalid_inputs`: Asserts parameter validation for $N \le 0$ or $min > max$.
8. `test_boundary_values`: Tests boundary limits ($N=1$, $min=max$).
9. `test_workload_summary`: Validates statistical calculation of workload metrics.
10. `test_runner_integration_and_immutability`: Verifies synthetic workloads execute seamlessly in `run_all_schedulers`.

### 2.9 `tests/test_faas_explainer.py` (FAAS Decision Inspector — 7 Tests)
1. `test_parse_decision_history_components`: Verifies accurate mathematical decomposition of priority into reciprocal remaining time and continuous wait aging.
2. `test_starvation_override_reporting`: Verifies that starvation override events are identified and highlighted in the decision step record.
3. `test_divergence_from_srtf`: Confirms detection when FAAS selects a job different from what pure SRTF would have chosen.
4. `test_candidate_comparison_dataframe`: Verifies tabular formatting of candidate processes at any given decision step.
5. `test_priority_component_chart`: Verifies stacked Plotly bar chart generation and annotations.
6. `test_empty_decision_log`: Confirms graceful empty handling when decision log is empty.
7. `test_explainer_does_not_modify_faas_output`: Confirms strict read-only immutability.

### 2.10 `tests/test_backend_api.py` (FastAPI Backend & REST Integration — 8 Tests)
1. `test_health_endpoint`: Verifies API operational status probe and version return.
2. `test_presets_endpoint`: Validates retrieval of built-in benchmark datasets.
3. `test_distributions_endpoint`: Validates available workload distribution names.
4. `test_generate_endpoint_valid`: Verifies synthetic workload generation adhering to bounds, and validates deterministic seed reproducibility.
5. `test_generate_endpoint_invalid_pydantic`: Validates parameter boundary rejections.
6. `test_simulate_endpoint_benchmark_dataset`: Full end-to-end simulation across all 4 algorithms verifying exact benchmark metrics.
7. `test_simulate_validation_errors`: Validates rejection of non-positive bursts, negative arrival times, empty PIDs, and duplicate PIDs.
8. `test_faas_inspector_endpoint`: Verifies decision history extraction, candidate decomposition, and explanation generation.

---

## 3. How to Run the Automated Test Suite

### Full Test Suite Execution:
```powershell
python -m pytest -p no:anyio -v
```

### Module-Specific Execution:
```powershell
# Run backend API integration tests
python -m pytest tests/test_backend_api.py -v

# Run only FAAS algorithm tests
python -m pytest tests/test_faas.py -v

# Run only FAAS explainer tests
python -m pytest tests/test_faas_explainer.py -v

# Run only benchmark validation tests
python -m pytest tests/test_metrics.py -k "test_benchmark" -v
```

### Expected Output:
```
============================= 99 passed in 1.03s ==============================
```
