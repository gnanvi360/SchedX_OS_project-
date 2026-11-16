"""
test_faas_explainer.py
----------------------
Unit and regression tests for core/faas_explainer.py.

Verifies:
  1. Parsing raw FAAS decision records into structured FAASDecisionStep objects.
  2. Mathematical correctness of decomposed components (1/Rem and alpha*Wait).
  3. Starvation override detection and logging.
  4. Guaranteed quantum tracking.
  5. Contrast detection with pure SRTF preferred candidates.
  6. Empty decision log handling.
  7. Plotly priority decomposition chart generation.
  8. Candidate comparison table DataFrame generation.
  9. Strict regression: proving the explainer does NOT alter FAAS scheduling behavior.
"""

import pytest
import pandas as pd
import plotly.graph_objects as go

from schedulers.process import Process
from schedulers.faas import run_faas
from core.runner import run_all_schedulers
from core.faas_explainer import (
    parse_faas_decision_history,
    create_candidate_comparison_df,
    create_priority_component_chart,
    FAASDecisionStep,
)


# =========================================================================== #
# Test 1 & 2: Parse Decision Log & Component Verification                      #
# =========================================================================== #
def test_parse_decision_history_components():
    # P1: AT=0, BT=4
    # P2: AT=1, BT=2
    # Run with alpha=4.0, quantum=2, threshold=8
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=4),
        Process(pid="P2", arrival_time=1, burst_time=2),
    ]
    completed, timeline, log = run_faas(processes, quantum=2, alpha=4.0, starvation_threshold=8)
    steps = parse_faas_decision_history(log, alpha=4.0, starvation_threshold=8, quantum=2)

    assert len(steps) == len(log)
    assert all(isinstance(s, FAASDecisionStep) for s in steps)

    # Step 1 at clock=0
    step1 = steps[0]
    assert step1.clock == 0
    assert step1.selected_pid == "P1"
    assert step1.quantum_granted == 2

    # Step 2 at clock=2
    step2 = steps[1]
    assert step2.clock == 2
    # At t=2: P2 arrived at t=1, waited 1 unit -> wait priority = 4.0 * 1 = 4.0
    p2_cand = next(c for c in step2.candidates if c.pid == "P2")
    assert p2_cand.continuous_waiting_time == 1
    assert p2_cand.remaining_priority == round(1.0 / 2, 4)
    assert p2_cand.waiting_priority == 4.0
    assert p2_cand.final_score == round(0.5 + 4.0, 4)


# =========================================================================== #
# Test 3: Starvation Override Detection and Alert Reporting                   #
# =========================================================================== #
def test_starvation_override_reporting():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=10),
        Process(pid="P2", arrival_time=0, burst_time=2),
        Process(pid="P3", arrival_time=2, burst_time=2),
    ]
    # Set threshold=4, alpha=0 so P1 starves to t=4
    completed, timeline, log = run_faas(processes, quantum=2, alpha=0.0, starvation_threshold=4)
    steps = parse_faas_decision_history(log, alpha=0.0, starvation_threshold=4, quantum=2)

    starv_steps = [s for s in steps if s.starvation_override]
    assert len(starv_steps) >= 1
    assert starv_steps[0].selected_pid == "P1"
    assert "Starvation Prevention Override" in starv_steps[0].explanation


# =========================================================================== #
# Test 4: Divergence from SRTF Detection                                      #
# =========================================================================== #
def test_divergence_from_srtf():
    # Dataset where aging causes FAAS to pick a longer job over a shorter job
    # Benchmark dataset: P1: AT=0, BT=6, P2: AT=1, BT=2, P3: AT=2, BT=4, P4: AT=4, BT=3
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=6),
        Process(pid="P2", arrival_time=1, burst_time=2),
        Process(pid="P3", arrival_time=2, burst_time=4),
        Process(pid="P4", arrival_time=4, burst_time=3),
    ]
    completed, timeline, log = run_faas(processes, quantum=2, alpha=4.0, starvation_threshold=8)
    steps = parse_faas_decision_history(log, alpha=4.0, starvation_threshold=8, quantum=2)

    # At clock=6: P3 has remaining=4, wait=4 (score 16.25); P1 has remaining=2, wait=0 (score 0.5); P4 has remaining=3, wait=2 (score 8.33)
    # SRTF would pick P1 (remaining 2). FAAS picks P3 (score 16.25).
    step_at_6 = next(s for s in steps if s.clock == 6)
    assert step_at_6.selected_pid == "P3"
    assert step_at_6.srtf_preferred_pid == "P1"
    assert "Divergence from SRTF" in step_at_6.explanation


# =========================================================================== #
# Test 5: Candidate Comparison DataFrame Generation                            #
# =========================================================================== #
def test_candidate_comparison_dataframe():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=3),
        Process(pid="P2", arrival_time=0, burst_time=5),
    ]
    completed, timeline, log = run_faas(processes, quantum=2)
    steps = parse_faas_decision_history(log)

    df = create_candidate_comparison_df(steps[0])
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "PID" in df.columns
    assert "Total Priority Score" in df.columns
    assert df.loc[0, "Selected"] == "✓ YES"


# =========================================================================== #
# Test 6: Priority Component Plotly Chart Generation                           #
# =========================================================================== #
def test_priority_component_chart():
    processes = [
        Process(pid="P1", arrival_time=0, burst_time=4),
        Process(pid="P2", arrival_time=0, burst_time=2),
    ]
    completed, timeline, log = run_faas(processes, quantum=2)
    steps = parse_faas_decision_history(log)

    fig = create_priority_component_chart(steps[0])
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2  # Remaining-time bar + Waiting-time bar
    assert len(fig.layout.annotations) == 1  # Selected annotation arrow


# =========================================================================== #
# Test 7: Empty Decision Log Handling                                          #
# =========================================================================== #
def test_empty_decision_log():
    steps = parse_faas_decision_history([])
    assert steps == []

    df_empty = create_candidate_comparison_df(None)
    assert df_empty.empty

    fig_empty = create_priority_component_chart(None)
    assert isinstance(fig_empty, go.Figure)


# =========================================================================== #
# Test 8: Non-Interference Regression Proof                                     #
# =========================================================================== #
def test_explainer_does_not_modify_faas_output():
    # Proves running parse_faas_decision_history does not alter any scheduling metrics
    procs = [
        Process(pid="P1", arrival_time=0, burst_time=6),
        Process(pid="P2", arrival_time=1, burst_time=2),
    ]
    comp1, time1, log1 = run_faas([p.copy() for p in procs], quantum=2, alpha=4.0)
    steps = parse_faas_decision_history(log1, alpha=4.0)

    comp2, time2, log2 = run_faas([p.copy() for p in procs], quantum=2, alpha=4.0)

    assert [p.completion_time for p in comp1] == [p.completion_time for p in comp2]
    assert time1 == time2
    assert [d["clock"] for d in log1] == [d["clock"] for d in log2]
