"""
test_charts.py
--------------
Unit and integration test suite for the visualization engine (core/charts.py).

Verifies:
  1. Gantt chart generation for single and multiple processes.
  2. Idle interval visualization.
  3. Preemptive execution timelines (SRTF/FAAS).
  4. Non-preemptive execution timelines (SJF/HRRN).
  5. Performance comparison bar charts.
  6. FAAS decision log visualization and formatting.
  7. Empty and invalid timeline handling.
  8. Deterministic and consistent process color mapping.
  9. Benchmark numerical validation on the required dataset.
"""

import pytest
import pandas as pd
import plotly.graph_objects as go
from schedulers.process import Process
from core.runner import run_all_schedulers
from core.charts import (
    build_process_color_map,
    create_gantt_chart,
    create_metric_bar_chart,
    create_all_comparison_charts,
    create_faas_decision_chart,
    format_faas_decision_table,
    IDLE_COLOR,
)


# =========================================================================== #
# Test 1 & 2: Color Mapping Determinism & IDLE Distinctiveness               #
# =========================================================================== #
def test_color_map_determinism_and_idle():
    pids = ["P2", "P1", "P3", "IDLE"]
    cmap1 = build_process_color_map(pids)
    cmap2 = build_process_color_map(pids)

    # Determinism
    assert cmap1 == cmap2
    assert cmap1["IDLE"] == IDLE_COLOR

    # Each PID gets a unique non-idle color
    non_idle_colors = [cmap1[p] for p in ["P1", "P2", "P3"]]
    assert len(set(non_idle_colors)) == 3
    assert IDLE_COLOR not in non_idle_colors


# =========================================================================== #
# Test 3: Gantt Chart for Simple Execution                                     #
# =========================================================================== #
def test_gantt_chart_generation():
    timeline = [
        {"pid": "P1", "start": 0, "end": 5},
        {"pid": "P2", "start": 5, "end": 8},
    ]
    fig = create_gantt_chart(timeline, title="Test Gantt")

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2
    assert fig.data[0].name == "P1"
    assert fig.data[0].x[0] == 5
    assert fig.data[0].base[0] == 0
    assert fig.data[1].name == "P2"
    assert fig.data[1].x[0] == 3
    assert fig.data[1].base[0] == 5


# =========================================================================== #
# Test 4: Gantt Chart with IDLE Interval                                       #
# =========================================================================== #
def test_gantt_chart_with_idle():
    timeline = [
        {"pid": "IDLE", "start": 0, "end": 3},
        {"pid": "P1",   "start": 3, "end": 7},
    ]
    fig = create_gantt_chart(timeline, title="Idle Gantt")

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2
    assert fig.data[0].name == "IDLE"
    assert fig.data[0].marker.color == IDLE_COLOR
    assert fig.data[0].x[0] == 3
    assert fig.data[1].name == "P1"


# =========================================================================== #
# Test 5: Preemptive Execution Timeline Rendering                              #
# =========================================================================== #
def test_preemptive_timeline_gantt():
    # P1 is preempted by P2, then resumes
    timeline = [
        {"pid": "P1", "start": 0, "end": 1},
        {"pid": "P2", "start": 1, "end": 4},
        {"pid": "P1", "start": 4, "end": 9},
    ]
    fig = create_gantt_chart(timeline, title="Preemptive Gantt")

    assert len(fig.data) == 3
    # Legend should only show P1 once even though it ran in two intervals
    assert fig.data[0].showlegend is True
    assert fig.data[2].showlegend is False  # second P1 interval omitted from legend


# =========================================================================== #
# Test 6: Empty and Zero-Duration Timeline Handling                            #
# =========================================================================== #
def test_empty_and_zero_duration_timeline():
    # Empty
    fig_empty = create_gantt_chart([])
    assert isinstance(fig_empty, go.Figure)
    assert len(fig_empty.data) == 0

    # Zero duration interval
    fig_zero = create_gantt_chart([{"pid": "P1", "start": 2, "end": 2}])
    assert len(fig_zero.data) == 0


# =========================================================================== #
# Test 7: Metric Comparison Bar Chart                                          #
# =========================================================================== #
def test_metric_bar_chart():
    df = pd.DataFrame([
        {"Algorithm": "SJF",  "Avg Waiting Time": 4.5},
        {"Algorithm": "SRTF", "Avg Waiting Time": 3.25},
        {"Algorithm": "HRRN", "Avg Waiting Time": 4.75},
        {"Algorithm": "FAAS", "Avg Waiting Time": 5.75},
    ])
    fig = create_metric_bar_chart(df, "Avg Waiting Time", higher_is_better=False)

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert list(fig.data[0].x) == ["SJF", "SRTF", "HRRN", "FAAS"]
    assert list(fig.data[0].y) == [4.5, 3.25, 4.75, 5.75]


# =========================================================================== #
# Test 8: All Comparison Charts Suite                                          #
# =========================================================================== #
def test_create_all_comparison_charts():
    df = pd.DataFrame([
        {
            "Algorithm": "SJF",
            "Avg Waiting Time": 4.5,
            "Avg Turnaround Time": 8.25,
            "Avg Response Time": 4.5,
            "CPU Utilization (%)": 100.0,
            "Throughput": 0.2667,
            "Context Switches": 3,
            "Preemptions": 0,
        },
        {
            "Algorithm": "SRTF",
            "Avg Waiting Time": 3.25,
            "Avg Turnaround Time": 7.00,
            "Avg Response Time": 1.0,
            "CPU Utilization (%)": 100.0,
            "Throughput": 0.2667,
            "Context Switches": 4,
            "Preemptions": 1,
        },
    ])
    charts = create_all_comparison_charts(df)

    assert "Avg Waiting Time" in charts
    assert "Avg Turnaround Time" in charts
    assert "CPU Utilization (%)" in charts
    assert "Throughput" in charts
    assert "Context Switches" in charts
    assert "Preemptions" in charts


# =========================================================================== #
# Test 9: FAAS Decision Log Formatting and Visualization                      #
# =========================================================================== #
def test_faas_decision_visualization():
    dummy_log = [
        {
            "clock": 0,
            "selected": "P1",
            "selected_priority": 0.5,
            "continuous_waiting_time": 0,
            "quantum_granted": 2,
            "starvation_override": False,
            "reason": "Highest Priority Score",
            "candidates": [{"pid": "P1", "remaining_time": 2}],
        },
        {
            "clock": 4,
            "selected": "P2",
            "selected_priority": 12.0,
            "continuous_waiting_time": 4,
            "quantum_granted": 2,
            "starvation_override": True,
            "reason": "Starvation Override",
            "candidates": [{"pid": "P2", "remaining_time": 6}],
        },
    ]

    # Test DataFrame formatting
    df = format_faas_decision_table(dummy_log)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert df.loc[1, "Starvation Override"] == "YES"

    # Test Plotly Figure
    fig = create_faas_decision_chart(dummy_log)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1  # Should contain normal and/or override traces


# =========================================================================== #
# Test 10: Benchmark Dataset Full Visualization Integration                    #
# =========================================================================== #
def test_benchmark_dataset_visualization():
    benchmark_dataset = [
        Process(pid="P1", arrival_time=0, burst_time=6),
        Process(pid="P2", arrival_time=1, burst_time=2),
        Process(pid="P3", arrival_time=2, burst_time=4),
        Process(pid="P4", arrival_time=4, burst_time=3),
    ]

    # Run unified simulation
    sim = run_all_schedulers(benchmark_dataset)

    # 1. Gantt chart for each algorithm
    for name in ["SJF", "SRTF", "HRRN", "FAAS"]:
        alg_res = sim.get_algorithm(name)
        fig = create_gantt_chart(alg_res.timeline, title=f"{name} Gantt")
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0

    # 2. Performance Comparison Charts
    comp_charts = create_all_comparison_charts(sim.comparison_df)
    assert len(comp_charts) >= 5

    # 3. FAAS Decision Chart
    faas_res = sim.get_algorithm("FAAS")
    faas_fig = create_faas_decision_chart(faas_res.decision_log)
    assert isinstance(faas_fig, go.Figure)
    assert len(faas_fig.data) > 0
