"""
charts.py
---------
Interactive visualization engine for SchedX using Plotly.

Generates:
  1. Gantt charts for CPU execution timelines (with distinct IDLE intervals and consistent process colors).
  2. Multi-algorithm comparative bar charts for all performance metrics.
  3. FAAS scheduling decision visualizations showing priority scores, aging, and starvation overrides.

All functions accept structured runner outputs or DataFrames and return Plotly figures
ready to be embedded into Streamlit using st.plotly_chart().
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


# =========================================================================== #
# Consistent Palette Definitions                                              #
# =========================================================================== #
PROCESS_PALETTE = [
    "#4361EE",  # Royal Blue
    "#3A0CA3",  # Indigo
    "#7209B7",  # Purple
    "#F72585",  # Pink
    "#4CC9F0",  # Sky Blue
    "#4895EF",  # Dodger Blue
    "#560BAD",  # Deep Purple
    "#B5179E",  # Magenta
    "#06D6A0",  # Teal Green
    "#FFD166",  # Amber Yellow
    "#EF476F",  # Coral Red
    "#118AB2",  # Ocean Blue
]

IDLE_COLOR = "#9E9E9E"  # Neutral Grey for CPU Idle intervals

ALGORITHM_COLORS = {
    "SJF": "#1f77b4",   # Blue
    "SRTF": "#ff7f0e",  # Orange
    "HRRN": "#2ca02c",  # Green
    "FAAS": "#d62728",  # Red / Crimson
}


def build_process_color_map(pids: List[str]) -> Dict[str, str]:
    """
    Creates a deterministic color map assigning each PID a distinct color.
    Ensures 'IDLE' is always mapped to the standard idle color.

    Parameters:
        pids (list[str]): List of process identifiers.

    Returns:
        dict: Mapping from pid string to hex color code.
    """
    unique_pids = sorted(list(set(pid for pid in pids if pid != "IDLE")))
    color_map = {}
    for i, pid in enumerate(unique_pids):
        color_map[pid] = PROCESS_PALETTE[i % len(PROCESS_PALETTE)]
    color_map["IDLE"] = IDLE_COLOR
    return color_map


# =========================================================================== #
# 1. Gantt Chart Generator                                                    #
# =========================================================================== #
def create_gantt_chart(
    timeline: List[Dict[str, Any]],
    title: str = "CPU Execution Timeline (Gantt Chart)",
    color_map: Optional[Dict[str, str]] = None,
) -> go.Figure:
    """
    Generates a horizontal Gantt chart representing CPU execution intervals over time.

    Parameters:
        timeline (list[dict]): List of interval dictionaries:
                               [{"pid": "P1", "start": 0, "end": 4}, ...]
        title (str): Chart title.
        color_map (dict, optional): Mapping from PID to color. Generated if not supplied.

    Returns:
        go.Figure: Interactive Plotly figure.
    """
    fig = go.Figure()

    # Handle empty or invalid timeline
    if not timeline:
        fig.add_annotation(
            text="No timeline data available.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(title=title, xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig

    # Determine colors
    all_pids = [entry["pid"] for entry in timeline]
    if color_map is None:
        color_map = build_process_color_map(all_pids)

    # Track unique PIDs already added to the legend so we don't duplicate legend items
    legend_tracker = set()
    total_time = max(entry["end"] for entry in timeline)

    for entry in timeline:
        pid = entry["pid"]
        start = entry["start"]
        end = entry["end"]
        duration = end - start

        if duration <= 0:
            continue

        bar_color = color_map.get(pid, "#888888")
        show_in_legend = (pid not in legend_tracker)
        legend_tracker.add(pid)

        # Process label displayed on the bar if duration allows
        display_text = f"{pid}" if duration >= 1 else ""

        # Rich HTML hover text
        if pid == "IDLE":
            hover = (
                f"<b>CPU State:</b> IDLE<br>"
                f"<b>Start Time:</b> {start}<br>"
                f"<b>End Time:</b> {end}<br>"
                f"<b>Idle Duration:</b> {duration} time units"
            )
            opacity = 0.6
        else:
            hover = (
                f"<b>Process:</b> {pid}<br>"
                f"<b>Start Time:</b> {start}<br>"
                f"<b>End Time:</b> {end}<br>"
                f"<b>Duration:</b> {duration} time units"
            )
            opacity = 0.95

        fig.add_trace(go.Bar(
            name=pid,
            x=[duration],
            base=[start],
            y=["CPU Schedule"],
            orientation="h",
            marker=dict(
                color=bar_color,
                opacity=opacity,
                line=dict(color="#1E1E1E", width=1.5),
            ),
            text=display_text,
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(color="white", size=13, family="Arial Black"),
            hoverinfo="text",
            hovertext=hover,
            showlegend=show_in_legend,
        ))

    # Layout styling
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", x=0.5, font=dict(size=18)),
        barmode="overlay",
        xaxis=dict(
            title="<b>Time Units (Clock Ticks)</b>",
            tickmode="linear",
            tick0=0,
            dtick=1 if total_time <= 30 else 2,
            range=[0, total_time + 0.5],
            showgrid=True,
            gridcolor="#E0E0E0",
            zeroline=True,
        ),
        yaxis=dict(
            title="",
            showticklabels=False,
            showgrid=False,
        ),
        legend=dict(
            title="<b>Processes</b>",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
        ),
        height=260,
        margin=dict(l=40, r=40, t=80, b=50),
        plot_bgcolor="#FAFAFA",
    )

    return fig


# =========================================================================== #
# 2. Performance Comparison Charts                                            #
# =========================================================================== #
def create_metric_bar_chart(
    comparison_df: pd.DataFrame,
    metric_column: str,
    title: Optional[str] = None,
    y_axis_title: Optional[str] = None,
    higher_is_better: bool = False,
) -> go.Figure:
    """
    Generates a single comparative bar chart for a specific metric across algorithms.

    Parameters:
        comparison_df (pd.DataFrame): DataFrame with 'Algorithm' and metric columns.
        metric_column (str): Name of the metric column in comparison_df.
        title (str, optional): Chart title.
        y_axis_title (str, optional): Y-axis label.
        higher_is_better (bool): If True, notes that higher is better. Default False (e.g. latency).

    Returns:
        go.Figure: Interactive bar chart.
    """
    fig = go.Figure()

    if comparison_df.empty or metric_column not in comparison_df.columns:
        fig.add_annotation(
            text="Metric data unavailable.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(title=title or metric_column)
        return fig

    chart_title = title or f"Comparison: {metric_column}"
    y_title = y_axis_title or metric_column

    algorithms = comparison_df["Algorithm"].tolist()
    values = comparison_df[metric_column].tolist()
    colors = [ALGORITHM_COLORS.get(alg, "#555555") for alg in algorithms]

    fig.add_trace(go.Bar(
        x=algorithms,
        y=values,
        marker=dict(
            color=colors,
            line=dict(color="#222222", width=1.5),
        ),
        text=[f"{v:.2f}" if isinstance(v, float) else f"{v}" for v in values],
        textposition="outside",
        hoverinfo="text",
        hovertext=[
            f"<b>Algorithm:</b> {alg}<br><b>{metric_column}:</b> {val}"
            for alg, val in zip(algorithms, values)
        ],
    ))

    # Add subtitle hint
    subtitle = "Higher is better ↑" if higher_is_better else "Lower is better ↓"

    fig.update_layout(
        title=dict(
            text=f"<b>{chart_title}</b><br><span style='font-size:12px; color:gray;'>({subtitle})</span>",
            x=0.5,
            font=dict(size=16),
        ),
        xaxis=dict(title="<b>Algorithm</b>"),
        yaxis=dict(title=f"<b>{y_title}</b>", showgrid=True, gridcolor="#EBEBEB"),
        height=380,
        margin=dict(l=40, r=40, t=70, b=50),
        plot_bgcolor="#FFFFFF",
    )

    return fig


def create_all_comparison_charts(comparison_df: pd.DataFrame) -> Dict[str, go.Figure]:
    """
    Generates a full suite of comparative charts for all metrics.

    Returns:
        dict: Mapping metric name to Plotly Figure.
    """
    charts = {}

    metric_configs = [
        ("Avg Waiting Time", "Average Waiting Time (Time Units)", False),
        ("Avg Turnaround Time", "Average Turnaround Time (Time Units)", False),
        ("Avg Response Time", "Average Response Time (Time Units)", False),
        ("CPU Utilization (%)", "CPU Utilization (%)", True),
        ("Throughput", "Throughput (Processes / Time Unit)", True),
        ("Context Switches", "Context Switches Count", False),
        ("Preemptions", "Preemptions Count", False),
    ]

    for col, y_title, higher_better in metric_configs:
        if col in comparison_df.columns:
            charts[col] = create_metric_bar_chart(
                comparison_df=comparison_df,
                metric_column=col,
                title=f"Comparative {col}",
                y_axis_title=y_title,
                higher_is_better=higher_better,
            )

    return charts


# =========================================================================== #
# 3. FAAS Decision Log Visualization                                          #
# =========================================================================== #
def format_faas_decision_table(decision_log: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Transforms raw FAAS decision log entries into a clean tabular DataFrame
    suitable for display in Streamlit.
    """
    if not decision_log:
        return pd.DataFrame()

    rows = []
    for step_idx, d in enumerate(decision_log, start=1):
        selected_pid = d.get("selected")
        # Find candidate details for selected process if available
        cand_match = [c for c in d.get("candidates", []) if c.get("pid") == selected_pid]
        rem_time = cand_match[0].get("remaining_time", "N/A") if cand_match else "N/A"

        rows.append({
            "Step": step_idx,
            "Clock Time": d.get("clock"),
            "Selected Process": selected_pid,
            "Reason": d.get("reason"),
            "Priority Score": d.get("selected_priority"),
            "Continuous Wait": d.get("continuous_waiting_time"),
            "Remaining Time": rem_time,
            "Quantum Granted": d.get("quantum_granted"),
            "Starvation Override": "YES" if d.get("starvation_override") else "No",
        })

    return pd.DataFrame(rows)


def create_faas_decision_chart(decision_log: List[Dict[str, Any]]) -> go.Figure:
    """
    Visualizes FAAS priority scores and decisions across simulation time.

    Shows:
      - Selected process at each decision timestamp
      - Priority score of the selected process
      - Starvation override markers (highlighted with distinct symbols)
    """
    fig = go.Figure()

    if not decision_log:
        fig.add_annotation(
            text="No FAAS decision logs available.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(title="FAAS Decision History")
        return fig

    clocks = [d["clock"] for d in decision_log]
    scores = [d["selected_priority"] for d in decision_log]
    pids = [d["selected"] for d in decision_log]
    overrides = [d["starvation_override"] for d in decision_log]
    reasons = [d["reason"] for d in decision_log]
    quantums = [d["quantum_granted"] for d in decision_log]
    waits = [d["continuous_waiting_time"] for d in decision_log]

    # Trace 1: Normal Decisions
    normal_indices = [i for i, ov in enumerate(overrides) if not ov]
    if normal_indices:
        fig.add_trace(go.Scatter(
            x=[clocks[i] for i in normal_indices],
            y=[scores[i] for i in normal_indices],
            mode="lines+markers",
            name="Normal Priority Dispatch",
            marker=dict(size=10, color="#1f77b4", symbol="circle"),
            line=dict(color="#1f77b4", width=2),
            text=[pids[i] for i in normal_indices],
            hoverinfo="text",
            hovertext=[
                f"<b>Time:</b> {clocks[i]}<br>"
                f"<b>Selected:</b> {pids[i]}<br>"
                f"<b>Priority Score:</b> {scores[i]:.4f}<br>"
                f"<b>Wait Time:</b> {waits[i]}<br>"
                f"<b>Quantum Granted:</b> {quantums[i]}<br>"
                f"<b>Reason:</b> {reasons[i]}"
                for i in normal_indices
            ],
        ))

    # Trace 2: Starvation Override Events
    starv_indices = [i for i, ov in enumerate(overrides) if ov]
    if starv_indices:
        fig.add_trace(go.Scatter(
            x=[clocks[i] for i in starv_indices],
            y=[scores[i] for i in starv_indices],
            mode="markers",
            name="Starvation Override Event",
            marker=dict(size=14, color="#d62728", symbol="star", line=dict(color="black", width=1.5)),
            text=[pids[i] for i in starv_indices],
            hoverinfo="text",
            hovertext=[
                f"<b>Time:</b> {clocks[i]} [STARVATION OVERRIDE]<br>"
                f"<b>Selected:</b> {pids[i]}<br>"
                f"<b>Continuous Wait:</b> {waits[i]} (Exceeded Threshold)<br>"
                f"<b>Quantum Granted:</b> {quantums[i]}"
                for i in starv_indices
            ],
        ))

    fig.update_layout(
        title=dict(text="<b>FAAS Dynamic Priority Score & Scheduling Decisions</b>", x=0.5, font=dict(size=16)),
        xaxis=dict(title="<b>Simulation Time</b>", tickmode="linear", dtick=2),
        yaxis=dict(title="<b>Priority Score: (1/Rem) + (α × Wait)</b>", showgrid=True),
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
        height=380,
        margin=dict(l=40, r=40, t=80, b=50),
        plot_bgcolor="#FFFFFF",
    )

    return fig
