"""
app.py
------
Main interactive Streamlit application for the CPU Scheduling Simulator.

Features:
  - Black, burgundy, ivory, and white aesthetic.
  - Horizontal top navigation (Dashboard, Process Input, Algorithm Scheduling,
    Gantt Charts, Performance Metrics, Comparison, About).
  - Manual and sample process dataset management.
  - Interactive execution of SJF, SRTF, HRRN, and FAAS.
  - Interactive Plotly Gantt charts with consistent process colors.
  - Comprehensive metrics tables and side-by-side comparative charts.
  - FAAS decision log inspection and educational algorithm explanations.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import List, Dict, Any

from schedulers.process import Process
from core.runner import run_all_schedulers, SimulationResults, validate_processes
from core.charts import (
    create_gantt_chart,
    create_metric_bar_chart,
    create_all_comparison_charts,
    create_faas_decision_chart,
    format_faas_decision_table,
    build_process_color_map,
    ALGORITHM_COLORS,
)
from core.generator import (
    generate_processes,
    calculate_workload_summary,
    DISTRIBUTION_PRESETS,
)
from core.faas_explainer import (
    parse_faas_decision_history,
    create_candidate_comparison_df,
    create_priority_component_chart,
)
from schedulers.sjf import run_sjf
from schedulers.srtf import run_srtf
from schedulers.hrrn import run_hrrn
from schedulers.faas import run_faas
from core.metrics import calculate_metrics, metrics_to_dataframe


# =========================================================================== #
# Streamlit Page Configuration                                                #
# =========================================================================== #
st.set_page_config(
    page_title="CPU Scheduling Simulator",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================================== #
# Custom CSS Styling: Black, Burgundy, Ivory, and White Theme                  #
# =========================================================================== #
DARK_THEME_CSS = """
<style>
    /* Global Page Styling */
    .stApp {
        background-color: #000000 !important;
        color: #F5F0E8 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
        font-family: 'Playfair Display', Georgia, serif !important;
        font-weight: 600;
        letter-spacing: -0.02em;
    }

    /* Top Horizontal Navigation Container */
    .nav-container {
        display: flex;
        justify-content: center;
        gap: 10px;
        padding: 12px 0 20px 0;
        border-bottom: 1px solid #222222;
        margin-bottom: 25px;
    }

    /* Custom Cards and Containers */
    .custom-card {
        background-color: #0A0A0A;
        border: 1px solid #1E1E1E;
        border-radius: 6px;
        padding: 20px;
        margin-bottom: 20px;
    }

    .custom-card-accent {
        background-color: #0A0A0A;
        border: 1px solid #600D1A;
        border-radius: 6px;
        padding: 20px;
        margin-bottom: 20px;
    }

    /* Metric Display Box */
    .metric-box {
        background-color: #0D0D0D;
        border: 1px solid #261014;
        border-radius: 6px;
        padding: 14px 18px;
        text-align: center;
        margin-bottom: 12px;
    }
    .metric-value {
        font-size: 26px;
        font-weight: 700;
        color: #FFFFFF;
        font-family: 'Inter', sans-serif;
        margin-top: 4px;
    }
    .metric-label {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #A7A7A7;
    }

    /* Streamlit Buttons Styling */
    .stButton>button {
        background-color: #111111;
        color: #F5F0E8;
        border: 1px solid #333333;
        border-radius: 4px;
        padding: 8px 18px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #600D1A !important;
        border-color: #853B47 !important;
        color: #FFFFFF !important;
    }

    /* Run Simulation Button Override */
    div[data-testid="stButton"] button:has-text("RUN SIMULATION") {
        background-color: #600D1A !important;
        border-color: #853B47 !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    /* Dataframe and Tables */
    .stDataFrame {
        border: 1px solid #1E1E1E !important;
        border-radius: 4px;
    }

    /* Separator */
    .burgundy-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #600D1A, #853B47, transparent);
        margin: 25px 0;
    }
</style>
"""
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)


# =========================================================================== #
# Helper: Apply Dark Theme to Plotly Figures                                  #
# =========================================================================== #
def apply_dark_theme(fig: go.Figure) -> go.Figure:
    """Configures a Plotly figure to seamlessly match our black/ivory theme."""
    fig.update_layout(
        paper_bgcolor="#000000",
        plot_bgcolor="#050505",
        font=dict(color="#F5F0E8", family="Inter, sans-serif"),
        xaxis=dict(
            gridcolor="#1A1A1A",
            zerolinecolor="#333333",
            tickfont=dict(color="#A7A7A7"),
            title_font=dict(color="#FFFFFF"),
        ),
        yaxis=dict(
            gridcolor="#1A1A1A",
            zerolinecolor="#333333",
            tickfont=dict(color="#A7A7A7"),
            title_font=dict(color="#FFFFFF"),
        ),
        legend=dict(
            font=dict(color="#F5F0E8"),
            bgcolor="rgba(0,0,0,0.6)",
            bordercolor="#222222",
        ),
    )
    return fig


# =========================================================================== #
# Session State Initialization                                                #
# =========================================================================== #
SAMPLE_DATASETS = {
    "Benchmark Dataset (P1-P4)": [
        {"pid": "P1", "arrival_time": 0, "burst_time": 6},
        {"pid": "P2", "arrival_time": 1, "burst_time": 2},
        {"pid": "P3", "arrival_time": 2, "burst_time": 4},
        {"pid": "P4", "arrival_time": 4, "burst_time": 3},
    ],
    "Simultaneous Arrivals (t=0)": [
        {"pid": "P1", "arrival_time": 0, "burst_time": 8},
        {"pid": "P2", "arrival_time": 0, "burst_time": 4},
        {"pid": "P3", "arrival_time": 0, "burst_time": 2},
        {"pid": "P4", "arrival_time": 0, "burst_time": 6},
    ],
    "Starvation Risk Trace": [
        {"pid": "P1", "arrival_time": 0, "burst_time": 16},
        {"pid": "P2", "arrival_time": 1, "burst_time": 2},
        {"pid": "P3", "arrival_time": 3, "burst_time": 2},
        {"pid": "P4", "arrival_time": 5, "burst_time": 2},
        {"pid": "P5", "arrival_time": 7, "burst_time": 2},
    ],
    "Idle CPU Intervals Trace": [
        {"pid": "P1", "arrival_time": 3, "burst_time": 4},
        {"pid": "P2", "arrival_time": 9, "burst_time": 3},
        {"pid": "P3", "arrival_time": 15, "burst_time": 2},
    ],
}

if "current_tab" not in st.session_state:
    st.session_state["current_tab"] = "Dashboard"

if "process_list" not in st.session_state:
    st.session_state["process_list"] = SAMPLE_DATASETS["Benchmark Dataset (P1-P4)"].copy()

if "simulation_results" not in st.session_state:
    st.session_state["simulation_results"] = None

if "faas_quantum" not in st.session_state:
    st.session_state["faas_quantum"] = 2

if "faas_alpha" not in st.session_state:
    st.session_state["faas_alpha"] = 4.0

if "faas_starvation_threshold" not in st.session_state:
    st.session_state["faas_starvation_threshold"] = 8

if "faas_decision_idx" not in st.session_state:
    st.session_state["faas_decision_idx"] = 0


# =========================================================================== #
# Top Horizontal Navigation Bar                                               #
# =========================================================================== #
TABS = [
    "Dashboard",
    "Process Input",
    "Algorithm Scheduling",
    "Gantt Charts",
    "Performance Metrics",
    "FAAS Inspector",
    "Comparison",
    "About",
]

st.markdown("<div style='text-align: center; margin-top: 10px; margin-bottom: 6px;'><span style='color: #853B47; font-size: 13px; text-transform: uppercase; letter-spacing: 0.15em;'>Operating Systems Core Laboratory</span><h1 style='margin: 0; font-size: 38px;'>CPU Scheduling Simulator</h1></div>", unsafe_allow_html=True)

nav_cols = st.columns(len(TABS))
for i, tab in enumerate(TABS):
    is_active = (st.session_state["current_tab"] == tab)
    label = f"◆ {tab}" if is_active else tab
    if nav_cols[i].button(label, key=f"nav_btn_{tab}", use_container_width=True):
        st.session_state["current_tab"] = tab
        st.rerun()

st.markdown("<div class='burgundy-divider'></div>", unsafe_allow_html=True)

current_tab = st.session_state["current_tab"]


# =========================================================================== #
# SECTION 1: DASHBOARD / HOME                                                 #
# =========================================================================== #
if current_tab == "Dashboard":
    st.markdown("<h2 style='text-align: center; margin-bottom: 6px;'>Uniprocessor Scheduling Analysis Engine</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #A7A7A7; max-width: 820px; margin: 0 auto 30px auto; font-size: 15px;'>An interactive educational environment for evaluating uniprocessor CPU scheduling policies. Compare classical algorithms against Fairness-Aware Adaptive Scheduling (FAAS) using unified execution traces.</p>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("""
        <div class='custom-card-accent'>
            <h3 style='margin-top: 0; font-size: 20px; color: #FFFFFF;'>Why CPU Scheduling Matters</h3>
            <p style='color: #F5F0E8; font-size: 14px; line-height: 1.6;'>
                In multiprogrammed uniprocessor operating systems, multiple processes reside concurrently in memory competing for CPU execution.
                The <b>CPU Scheduler</b> determines which ready process is allocated the CPU when the currently running process terminates, blocks, or yields.
            </p>
            <p style='color: #A7A7A7; font-size: 13px; line-height: 1.6;'>
                Optimal scheduling balances conflicting goals: minimizing average turnaround time, preventing process starvation, controlling context-switch overhead, and ensuring bounded interactive response times.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class='custom-card'>
            <h3 style='margin-top: 0; font-size: 20px; color: #FFFFFF;'>Simulator Capabilities</h3>
            <ul style='color: #F5F0E8; font-size: 14px; line-height: 1.8; padding-left: 20px;'>
                <li><b>Deterministic Evaluation:</b> All algorithms operate on isolated, identical process copies.</li>
                <li><b>Preemptive & Non-Preemptive Engines:</b> SJF, SRTF, HRRN, and FAAS.</li>
                <li><b>Interactive Gantt Timelines:</b> Plotly charts displaying exact execution intervals and idle periods.</li>
                <li><b>Decision Transparency:</b> Trace dynamic priority aging and starvation overrides.</li>
                <li><b>Comprehensive Metrics:</b> Turnaround, Waiting, Response, CPU Utilization, and Context Switches.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<h3 style='margin-top: 25px; margin-bottom: 15px;'>Core Algorithm Architecture</h3>", unsafe_allow_html=True)

    alg_cols = st.columns(4)

    with alg_cols[0]:
        st.markdown("""
        <div class='custom-card' style='height: 230px;'>
            <span style='color: #1f77b4; font-size: 12px; font-weight: 700; text-transform: uppercase;'>Algorithm 01</span>
            <h4 style='margin: 6px 0 10px 0;'>SJF</h4>
            <p style='color: #A7A7A7; font-size: 13px; line-height: 1.5;'>
                <b>Non-Preemptive Shortest Job First.</b> Selects the process with the smallest initial burst time among arrived jobs. Executes to completion without interruption.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with alg_cols[1]:
        st.markdown("""
        <div class='custom-card' style='height: 230px;'>
            <span style='color: #ff7f0e; font-size: 12px; font-weight: 700; text-transform: uppercase;'>Algorithm 02</span>
            <h4 style='margin: 6px 0 10px 0;'>SRTF</h4>
            <p style='color: #A7A7A7; font-size: 13px; line-height: 1.5;'>
                <b>Shortest Remaining Time First.</b> Preemptive version of SJF. Re-evaluates on every arrival. Interrupts the running process if a shorter job enters the queue.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with alg_cols[2]:
        st.markdown("""
        <div class='custom-card' style='height: 230px;'>
            <span style='color: #2ca02c; font-size: 12px; font-weight: 700; text-transform: uppercase;'>Algorithm 03</span>
            <h4 style='margin: 6px 0 10px 0;'>HRRN</h4>
            <p style='color: #A7A7A7; font-size: 13px; line-height: 1.5;'>
                <b>Highest Response Ratio Next.</b> Non-preemptive scheduling with aging. Selects highest ratio <i>(W + B) / B</i>, naturally preventing starvation.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with alg_cols[3]:
        st.markdown("""
        <div class='custom-card-accent' style='height: 230px;'>
            <span style='color: #d62728; font-size: 12px; font-weight: 700; text-transform: uppercase;'>Algorithm 04 (Proposed)</span>
            <h4 style='margin: 6px 0 10px 0;'>FAAS</h4>
            <p style='color: #A7A7A7; font-size: 13px; line-height: 1.5;'>
                <b>Fairness-Aware Adaptive Scheduling.</b> Bounded quantum preemption, dynamic aging score <i>(1/Rem + α·Wait)</i>, and hard starvation threshold overrides.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='text-align: center; margin-top: 25px;'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        if st.button("Proceed to Process Input →", use_container_width=True):
            st.session_state["current_tab"] = "Process Input"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================================== #
# SECTION 2: PROCESS INPUT                                                    #
# =========================================================================== #
elif current_tab == "Process Input":
    st.markdown("<h2>Process Dataset Management</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #A7A7A7; font-size: 14px;'>Define the input workload trace. All four scheduling algorithms will be evaluated against this exact process sequence.</p>", unsafe_allow_html=True)

    c_sample, c_actions = st.columns([2, 1])

    with c_sample:
        selected_sample = st.selectbox(
            "Load Sample Workload Scenario:",
            list(SAMPLE_DATASETS.keys()),
            index=0,
        )
        if st.button("Load Selected Scenario"):
            st.session_state["process_list"] = [d.copy() for d in SAMPLE_DATASETS[selected_sample]]
            st.session_state["simulation_results"] = None
            st.success(f"Loaded '{selected_sample}'.")
            st.rerun()

    with c_actions:
        st.write("")
        st.write("")
        if st.button("Reset to Default Benchmark", use_container_width=True):
            st.session_state["process_list"] = [d.copy() for d in SAMPLE_DATASETS["Benchmark Dataset (P1-P4)"]]
            st.session_state["simulation_results"] = None
            st.rerun()

    # --- Random Process Generator Card ---
    st.markdown("<div class='burgundy-divider'></div>", unsafe_allow_html=True)
    with st.expander("🎲 Configure & Generate Random Workload", expanded=True):
        st.markdown("<h4 style='color: #FFFFFF; margin-top: 0;'>Random Process Generator</h4>", unsafe_allow_html=True)
        st.caption("Generate reproducible, mathematically modeled workloads across custom distributions and ranges.")

        rg_col1, rg_col2 = st.columns(2)
        with rg_col1:
            gen_count = st.number_input("Number of Processes (1 to 100):", min_value=1, max_value=100, value=5, step=1)
            gen_preset = st.selectbox("Workload Distribution Preset:", DISTRIBUTION_PRESETS, index=0)

        with rg_col2:
            st.write("<b>Arrival Time Range [Min, Max]:</b>", unsafe_allow_html=True)
            at_col1, at_col2 = st.columns(2)
            with at_col1:
                gen_min_at = st.number_input("Min Arrival:", min_value=0, max_value=200, value=0, step=1, key="gen_min_at")
            with at_col2:
                gen_max_at = st.number_input("Max Arrival:", min_value=0, max_value=200, value=10, step=1, key="gen_max_at")

            st.write("<b>Burst Time Range [Min, Max]:</b>", unsafe_allow_html=True)
            bt_col1, bt_col2 = st.columns(2)
            with bt_col1:
                gen_min_bt = st.number_input("Min Burst:", min_value=1, max_value=200, value=1, step=1, key="gen_min_bt")
            with bt_col2:
                gen_max_bt = st.number_input("Max Burst:", min_value=1, max_value=200, value=10, step=1, key="gen_max_bt")

        rg_seed_col, rg_btn_col1, rg_btn_col2 = st.columns([2, 1, 1])
        with rg_seed_col:
            seed_input_str = st.text_input("Random Seed (Optional for reproducibility):", value="", placeholder="e.g. 42")
        with rg_btn_col1:
            st.write("")
            st.write("")
            generate_clicked = st.button("Generate Processes", use_container_width=True)
        with rg_btn_col2:
            st.write("")
            st.write("")
            regenerate_clicked = st.button("Regenerate ⟳", use_container_width=True)

        if generate_clicked or regenerate_clicked:
            # Parse seed
            parsed_seed = None
            valid_seed = True
            if seed_input_str.strip():
                try:
                    parsed_seed = int(seed_input_str.strip())
                except ValueError:
                    valid_seed = False
                    st.error("Error: Random seed must be a valid integer.")

            if valid_seed:
                try:
                    generated_objs = generate_processes(
                        num_processes=int(gen_count),
                        arrival_range=(int(gen_min_at), int(gen_max_at)),
                        burst_range=(int(gen_min_bt), int(gen_max_bt)),
                        distribution=gen_preset,
                        seed=parsed_seed,
                    )
                    # Update session state with generated processes
                    st.session_state["process_list"] = [
                        {"pid": p.pid, "arrival_time": p.arrival_time, "burst_time": p.burst_time}
                        for p in generated_objs
                    ]
                    st.session_state["simulation_results"] = None
                    st.success(f"Generated {len(generated_objs)} processes using '{gen_preset}' preset (Seed: {parsed_seed if parsed_seed is not None else 'Random'}).")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Generation Error: {str(ex)}")

        # Workload summary statistics for current processes
        current_procs_for_summary = [
            Process(p["pid"], p["arrival_time"], p["burst_time"])
            for p in st.session_state["process_list"]
        ]
        w_summary = calculate_workload_summary(current_procs_for_summary)

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        s1, s2, s3, s4, s5, s6 = st.columns(6)
        with s1:
            st.markdown(f"<div class='metric-box'><div class='metric-label'>Processes</div><div class='metric-value'>{w_summary['total_processes']}</div></div>", unsafe_allow_html=True)
        with s2:
            st.markdown(f"<div class='metric-box'><div class='metric-label'>Total Burst</div><div class='metric-value'>{w_summary['total_burst_time']}</div></div>", unsafe_allow_html=True)
        with s3:
            st.markdown(f"<div class='metric-box'><div class='metric-label'>Avg Burst</div><div class='metric-value'>{w_summary['avg_burst_time']}</div></div>", unsafe_allow_html=True)
        with s4:
            st.markdown(f"<div class='metric-box'><div class='metric-label'>Avg Arrival</div><div class='metric-value'>{w_summary['avg_arrival_time']}</div></div>", unsafe_allow_html=True)
        with s5:
            st.markdown(f"<div class='metric-box'><div class='metric-label'>Min Burst</div><div class='metric-value'>{w_summary['min_burst_time']}</div></div>", unsafe_allow_html=True)
        with s6:
            st.markdown(f"<div class='metric-box'><div class='metric-label'>Max Burst</div><div class='metric-value'>{w_summary['max_burst_time']}</div></div>", unsafe_allow_html=True)

    st.markdown("<div class='burgundy-divider'></div>", unsafe_allow_html=True)

    col_editor, col_add = st.columns([3, 2])

    with col_editor:
        st.markdown("<h4>Current Process Table</h4>", unsafe_allow_html=True)
        st.caption("Double-click any cell to edit Arrival Time or Burst Time. Delete or add rows using table controls.")

        df_current = pd.DataFrame(st.session_state["process_list"])

        edited_df = st.data_editor(
            df_current,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "pid": st.column_config.TextColumn("Process ID", required=True),
                "arrival_time": st.column_config.NumberColumn("Arrival Time", min_value=0, step=1, required=True),
                "burst_time": st.column_config.NumberColumn("Burst Time", min_value=1, step=1, required=True),
            },
            key="process_data_editor",
        )

        # Update session state on edit
        st.session_state["process_list"] = edited_df.to_dict(orient="records")

    with col_add:
        st.markdown("<h4>Add Process Manually</h4>", unsafe_allow_html=True)
        with st.form("add_process_form", clear_on_submit=True):
            next_pid = f"P{len(st.session_state['process_list']) + 1}"
            new_pid = st.text_input("Process ID (PID):", value=next_pid)
            new_at = st.number_input("Arrival Time:", min_value=0, step=1, value=0)
            new_bt = st.number_input("Burst Time:", min_value=1, step=1, value=4)
            submitted = st.form_submit_button("Add Process to Queue")

            if submitted:
                # Validation
                existing_pids = [p["pid"].strip() for p in st.session_state["process_list"]]
                if new_pid.strip() in existing_pids:
                    st.error(f"Error: Process ID '{new_pid}' already exists. PIDs must be unique.")
                elif new_bt <= 0:
                    st.error("Error: Burst Time must be greater than zero.")
                elif new_at < 0:
                    st.error("Error: Arrival Time cannot be negative.")
                else:
                    st.session_state["process_list"].append({
                        "pid": new_pid.strip(),
                        "arrival_time": int(new_at),
                        "burst_time": int(new_bt),
                    })
                    st.session_state["simulation_results"] = None
                    st.success(f"Added {new_pid} (AT={new_at}, BT={new_bt})")
                    st.rerun()

    st.markdown("<div class='burgundy-divider'></div>", unsafe_allow_html=True)

    # Validation feedback
    raw_list = st.session_state["process_list"]
    validation_passed = True
    error_msg = ""

    if not raw_list:
        validation_passed = False
        error_msg = "Process list is currently empty. Please add at least one process."
    else:
        seen = set()
        for p in raw_list:
            if not p.get("pid"):
                validation_passed = False
                error_msg = "A process has an empty PID."
                break
            if p["pid"] in seen:
                validation_passed = False
                error_msg = f"Duplicate PID detected: '{p['pid']}'. Every process must have a unique ID."
                break
            seen.add(p["pid"])
            if p.get("arrival_time", -1) < 0:
                validation_passed = False
                error_msg = f"Process {p['pid']} has negative arrival time."
                break
            if p.get("burst_time", 0) <= 0:
                validation_passed = False
                error_msg = f"Process {p['pid']} has burst time <= 0. Burst time must be positive."
                break

    if validation_passed:
        st.success(f"Dataset Validated: {len(raw_list)} processes ready for scheduling.")
        if st.button("Proceed to Scheduling Execution →", use_container_width=False):
            st.session_state["current_tab"] = "Algorithm Scheduling"
            st.rerun()
    else:
        st.warning(f"⚠️ Validation Warning: {error_msg}")


# =========================================================================== #
# SECTION 3: ALGORITHM SCHEDULING                                             #
# =========================================================================== #
elif current_tab == "Algorithm Scheduling":
    st.markdown("<h2>Algorithm Scheduling Configuration & Execution</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #A7A7A7; font-size: 14px;'>Configure algorithm parameters and execute simulations. Each algorithm will receive an independent copy of the verified process dataset.</p>", unsafe_allow_html=True)

    # Convert session state dictionaries to Process instances
    processes = [
        Process(pid=str(p["pid"]), arrival_time=int(p["arrival_time"]), burst_time=int(p["burst_time"]))
        for p in st.session_state["process_list"]
    ]

    col_algs, col_faas_params = st.columns([1, 1])

    with col_algs:
        st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
        st.markdown("<h4>Select Algorithms to Run</h4>", unsafe_allow_html=True)
        run_sjf_opt = st.checkbox("Shortest Job First (SJF) — Non-preemptive", value=True)
        run_srtf_opt = st.checkbox("Shortest Remaining Time First (SRTF) — Preemptive", value=True)
        run_hrrn_opt = st.checkbox("Highest Response Ratio Next (HRRN) — Non-preemptive", value=True)
        run_faas_opt = st.checkbox("Fairness-Aware Adaptive Scheduling (FAAS) — Proposed Custom", value=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_faas_params:
        st.markdown("<div class='custom-card-accent'>", unsafe_allow_html=True)
        st.markdown("<h4>FAAS Custom Parameters</h4>", unsafe_allow_html=True)
        q_val = st.slider("Time Quantum (Q):", min_value=1, max_value=10, value=st.session_state["faas_quantum"], step=1, help="Maximum CPU time granted per dispatch.")
        alpha_val = st.slider("Aging Factor (α):", min_value=0.0, max_value=10.0, value=float(st.session_state["faas_alpha"]), step=0.5, help="Multiplier for continuous waiting time.")
        starv_val = st.slider("Starvation Threshold:", min_value=1, max_value=30, value=st.session_state["faas_starvation_threshold"], step=1, help="Continuous waiting time that triggers guaranteed service override.")

        st.session_state["faas_quantum"] = q_val
        st.session_state["faas_alpha"] = alpha_val
        st.session_state["faas_starvation_threshold"] = starv_val
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='text-align: center; margin: 30px 0;'>", unsafe_allow_html=True)
    run_btn = st.button("RUN SIMULATION", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if run_btn:
        try:
            validate_processes(processes)

            with st.spinner("Executing simulation engines across independent process spaces..."):
                sim_res = run_all_schedulers(
                    processes,
                    faas_quantum=st.session_state["faas_quantum"],
                    faas_alpha=st.session_state["faas_alpha"],
                    faas_starvation_threshold=st.session_state["faas_starvation_threshold"],
                )

            # Filter algorithms based on user checkboxes
            selected_algs = {}
            if run_sjf_opt and "SJF" in sim_res.algorithms:
                selected_algs["SJF"] = sim_res.algorithms["SJF"]
            if run_srtf_opt and "SRTF" in sim_res.algorithms:
                selected_algs["SRTF"] = sim_res.algorithms["SRTF"]
            if run_hrrn_opt and "HRRN" in sim_res.algorithms:
                selected_algs["HRRN"] = sim_res.algorithms["HRRN"]
            if run_faas_opt and "FAAS" in sim_res.algorithms:
                selected_algs["FAAS"] = sim_res.algorithms["FAAS"]

            filtered_comparison_df = sim_res.comparison_df[
                sim_res.comparison_df["Algorithm"].isin(selected_algs.keys())
            ]

            st.session_state["simulation_results"] = SimulationResults(
                algorithms=selected_algs,
                comparison_df=filtered_comparison_df,
                metrics_summary={k: v.metrics for k, v in selected_algs.items()},
            )

            st.success(f"Simulation completed successfully for {len(selected_algs)} algorithms!")
            st.session_state["current_tab"] = "Gantt Charts"
            st.rerun()

        except Exception as e:
            st.error(f"Simulation Execution Error: {str(e)}")

    if st.session_state["simulation_results"] is not None:
        st.info("Simulation results are currently cached in memory. You can inspect Gantt Charts, Performance Metrics, and Comparisons via the top navigation.")


# =========================================================================== #
# SECTION 4: GANTT CHARTS                                                     #
# =========================================================================== #
elif current_tab == "Gantt Charts":
    st.markdown("<h2>Execution Timelines (Gantt Charts)</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #A7A7A7; font-size: 14px;'>Visual representation of CPU allocation over time. Hover over any block to inspect exact start, completion, and duration details.</p>", unsafe_allow_html=True)

    sim = st.session_state["simulation_results"]

    if sim is None or not sim.algorithms:
        st.warning("No simulation results available. Please configure your workload in 'Process Input' and click 'RUN SIMULATION' in 'Algorithm Scheduling'.")
    else:
        # Build shared process color map for visual consistency across all Gantt charts
        all_pids = [p["pid"] for p in st.session_state["process_list"]]
        color_map = build_process_color_map(all_pids)

        view_mode = st.radio("Display Mode:", ["Stacked (Compare All)", "Tabs (Inspect Individually)"], horizontal=True)

        if view_mode == "Stacked (Compare All)":
            for name, alg_res in sim.algorithms.items():
                st.markdown(f"<h4 style='color: {ALGORITHM_COLORS.get(name, '#FFFFFF')}; margin-top: 15px;'>{name} Timeline</h4>", unsafe_allow_html=True)
                fig = create_gantt_chart(alg_res.timeline, title=f"{name} Execution Timeline", color_map=color_map)
                fig = apply_dark_theme(fig)
                st.plotly_chart(fig, use_container_width=True)
        else:
            gantt_tabs = st.tabs(list(sim.algorithms.keys()))
            for idx, (name, alg_res) in enumerate(sim.algorithms.items()):
                with gantt_tabs[idx]:
                    fig = create_gantt_chart(alg_res.timeline, title=f"{name} Execution Timeline", color_map=color_map)
                    fig = apply_dark_theme(fig)
                    st.plotly_chart(fig, use_container_width=True)

                    # Interval details table
                    with st.expander(f"Inspect Raw Timeline Intervals ({name})"):
                        st.dataframe(pd.DataFrame(alg_res.timeline), use_container_width=True)


# =========================================================================== #
# SECTION 5: PERFORMANCE METRICS                                              #
# =========================================================================== #
elif current_tab == "Performance Metrics":
    st.markdown("<h2>Performance Metrics & Process Details</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #A7A7A7; font-size: 14px;'>Process-level scheduling outputs and calculated aggregate metrics for each algorithm.</p>", unsafe_allow_html=True)

    sim = st.session_state["simulation_results"]

    if sim is None or not sim.algorithms:
        st.warning("No simulation results available. Please run the simulation first.")
    else:
        selected_alg = st.selectbox("Select Algorithm to Inspect:", list(sim.algorithms.keys()))
        alg_res = sim.algorithms[selected_alg]
        m = alg_res.metrics

        # Summary Metric Cards Row
        st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"<div class='metric-box'><div class='metric-label'>Avg Turnaround Time</div><div class='metric-value'>{m.avg_turnaround_time:.2f}</div></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='metric-box'><div class='metric-label'>Avg Waiting Time</div><div class='metric-value'>{m.avg_waiting_time:.2f}</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='metric-box'><div class='metric-label'>Avg Response Time</div><div class='metric-value'>{m.avg_response_time:.2f}</div></div>", unsafe_allow_html=True)
        with c4:
            st.markdown(f"<div class='metric-box'><div class='metric-label'>CPU Utilization</div><div class='metric-value'>{m.cpu_utilization:.1f}%</div></div>", unsafe_allow_html=True)

        c5, c6, c7, c8 = st.columns(4)
        with c5:
            st.markdown(f"<div class='metric-box'><div class='metric-label'>Throughput</div><div class='metric-value'>{m.throughput:.4f}</div></div>", unsafe_allow_html=True)
        with c6:
            st.markdown(f"<div class='metric-box'><div class='metric-label'>Context Switches</div><div class='metric-value'>{m.context_switches}</div></div>", unsafe_allow_html=True)
        with c7:
            st.markdown(f"<div class='metric-box'><div class='metric-label'>Preemptions</div><div class='metric-value'>{m.preemptions}</div></div>", unsafe_allow_html=True)
        with c8:
            st.markdown(f"<div class='metric-box'><div class='metric-label'>Total Simulation Time</div><div class='metric-value'>{m.total_simulation_time}</div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Process Level Table
        st.markdown(f"<h4>Process-Level Output Table ({selected_alg})</h4>", unsafe_allow_html=True)
        st.dataframe(alg_res.process_dataframe, use_container_width=True)

        # Download process table button
        csv_data = alg_res.process_dataframe.to_csv(index=False)
        st.download_button(
            label=f"Download {selected_alg} Metrics as CSV",
            data=csv_data,
            file_name=f"{selected_alg}_scheduling_results.csv",
            mime="text/csv",
        )

        # FAAS Specific Decision Log
        if selected_alg == "FAAS" and alg_res.decision_log:
            st.markdown("<div class='burgundy-divider'></div>", unsafe_allow_html=True)
            st.markdown("<h4>FAAS Decision Transparency Log</h4>", unsafe_allow_html=True)
            st.caption("Inspect the mathematical factors (remaining time, continuous wait, priority score) at every scheduling tick.")

            if st.button("🔬 Open Interactive FAAS Decision Inspector", key="btn_goto_faas_inspector"):
                st.session_state["current_tab"] = "FAAS Inspector"
                st.rerun()

            df_faas_log = format_faas_decision_table(alg_res.decision_log)
            st.dataframe(df_faas_log, use_container_width=True)

            faas_fig = create_faas_decision_chart(alg_res.decision_log)
            faas_fig = apply_dark_theme(faas_fig)
            st.plotly_chart(faas_fig, use_container_width=True)


# =========================================================================== #
# SECTION 6: FAAS DECISION INSPECTOR                                          #
# =========================================================================== #
elif current_tab == "FAAS Inspector":
    st.markdown("<h2>Fairness-Aware Adaptive Scheduling (FAAS) — Decision Inspector</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color: #A7A7A7; font-size: 14px;'>Step-by-step interactive inspection of scheduling decisions, mathematical priority score decomposition, aging dynamics, and starvation prevention overrides.</p>",
        unsafe_allow_html=True,
    )

    sim = st.session_state["simulation_results"]

    if sim is None or "FAAS" not in sim.algorithms:
        st.warning("No FAAS simulation results available. Please navigate to 'Algorithm Scheduling', ensure FAAS is selected, and click 'RUN SIMULATION'.")
        col_btn1, _ = st.columns([1, 3])
        with col_btn1:
            if st.button("Go to Algorithm Scheduling", key="goto_scheduling_from_faas"):
                st.session_state["current_tab"] = "Algorithm Scheduling"
                st.rerun()
    else:
        faas_res = sim.algorithms["FAAS"]
        if not faas_res.decision_log:
            st.info("No decision points were logged for this workload (process list may be empty or instantaneous).")
        else:
            steps = parse_faas_decision_history(
                faas_res.decision_log,
                alpha=st.session_state.get("faas_alpha", 4.0),
                starvation_threshold=st.session_state.get("faas_starvation_threshold", 8),
                quantum=st.session_state.get("faas_quantum", 2),
            )

            total_steps = len(steps)
            curr_idx = st.session_state.get("faas_decision_idx", 0)
            if curr_idx < 0:
                curr_idx = 0
            if curr_idx >= total_steps:
                curr_idx = total_steps - 1
            st.session_state["faas_decision_idx"] = curr_idx

            # Navigation bar for decision steps
            st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
            nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns([1, 1, 4, 1, 1])

            with nav_col1:
                if st.button("⏮ First", disabled=(curr_idx == 0), key="faas_nav_first", use_container_width=True):
                    st.session_state["faas_decision_idx"] = 0
                    st.rerun()

            with nav_col2:
                if st.button("◀ Prev", disabled=(curr_idx == 0), key="faas_nav_prev", use_container_width=True):
                    st.session_state["faas_decision_idx"] = max(0, curr_idx - 1)
                    st.rerun()

            with nav_col3:
                step_options = [
                    f"Step {s.step_index}/{total_steps} (t = {s.clock}, Selected {s.selected_pid})"
                    for s in steps
                ]
                selected_option = st.selectbox(
                    "Navigate Decision Points:",
                    options=range(total_steps),
                    index=curr_idx,
                    format_func=lambda i: step_options[i],
                    key="faas_step_selector",
                    label_visibility="collapsed",
                )
                if selected_option != curr_idx:
                    st.session_state["faas_decision_idx"] = selected_option
                    st.rerun()

            with nav_col4:
                if st.button("Next ▶", disabled=(curr_idx == total_steps - 1), key="faas_nav_next", use_container_width=True):
                    st.session_state["faas_decision_idx"] = min(total_steps - 1, curr_idx + 1)
                    st.rerun()

            with nav_col5:
                if st.button("Last ⏭", disabled=(curr_idx == total_steps - 1), key="faas_nav_last", use_container_width=True):
                    st.session_state["faas_decision_idx"] = total_steps - 1
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

            current_step = steps[st.session_state["faas_decision_idx"]]

            # Highlight Decision Status Banner
            if current_step.starvation_override:
                st.markdown(
                    f"""
                    <div style='background-color: #1A0508; border: 2px solid #D62728; border-radius: 6px; padding: 18px; margin-bottom: 20px;'>
                        <div style='display: flex; align-items: center; justify-content: space-between;'>
                            <span style='color: #FF4D4D; font-size: 16px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em;'>
                                🚨 STARVATION PREVENTION OVERRIDE ACTIVATED
                            </span>
                            <span style='background-color: #600D1A; color: #FFFFFF; font-size: 12px; padding: 4px 10px; border-radius: 4px; font-weight: 600;'>
                                Time t = {current_step.clock}
                            </span>
                        </div>
                        <p style='color: #F5F0E8; font-size: 14px; margin-top: 10px; margin-bottom: 0; line-height: 1.6;'>
                            Process <b style='color: #FFFFFF;'>{current_step.selected_pid}</b> reached continuous waiting time of 
                            <b>{current_step.selected_candidate.continuous_waiting_time if current_step.selected_candidate else current_step.starvation_threshold}</b> time units, 
                            exceeding the starvation threshold (<b style='color: #FF4D4D;'>T_starve = {current_step.starvation_threshold}</b>). 
                            Standard priority scoring was bypassed to prevent indefinite postponement and guarantee CPU allocation.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div style='background-color: #0A0A0A; border: 1px solid #600D1A; border-radius: 6px; padding: 18px; margin-bottom: 20px;'>
                        <div style='display: flex; align-items: center; justify-content: space-between;'>
                            <span style='color: #4CC9F0; font-size: 15px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em;'>
                                ⚖️ NORMAL FAIRNESS-AWARE PRIORITY DISPATCH
                            </span>
                            <span style='background-color: #111111; border: 1px solid #333333; color: #FFFFFF; font-size: 12px; padding: 4px 10px; border-radius: 4px; font-weight: 600;'>
                                Time t = {current_step.clock}
                            </span>
                        </div>
                        <p style='color: #F5F0E8; font-size: 14px; margin-top: 10px; margin-bottom: 0; line-height: 1.6;'>
                            Process <b style='color: #FFFFFF;'>{current_step.selected_pid}</b> won scheduling dispatch with the highest composite priority score of 
                            <b style='color: #4CC9F0;'>{current_step.selected_priority:.4f}</b>.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Educational Step Explanation Callout
            st.markdown(
                f"""
                <div style='background-color: #0D0D0D; border-left: 4px solid #853B47; border-radius: 4px; padding: 14px 18px; margin-bottom: 20px;'>
                    <div style='color: #A7A7A7; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;'>
                        Educational Step Breakdown
                    </div>
                    <div style='color: #F5F0E8; font-size: 14px; line-height: 1.6;'>
                        {current_step.explanation}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Metrics row for this step
            st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
            k1, k2, k3, k4 = st.columns(4)
            with k1:
                st.markdown(f"<div class='metric-box'><div class='metric-label'>Simulation Clock</div><div class='metric-value'>t = {current_step.clock}</div></div>", unsafe_allow_html=True)
            with k2:
                st.markdown(f"<div class='metric-box'><div class='metric-label'>Selected Process</div><div class='metric-value' style='color: #4CC9F0;'>{current_step.selected_pid}</div></div>", unsafe_allow_html=True)
            with k3:
                st.markdown(f"<div class='metric-box'><div class='metric-label'>Priority Score</div><div class='metric-value'>{current_step.selected_priority:.4f}</div></div>", unsafe_allow_html=True)
            with k4:
                st.markdown(f"<div class='metric-box'><div class='metric-label'>Guaranteed Quantum</div><div class='metric-value'>{current_step.quantum_granted} units</div></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Priority Component Breakdown Stacked Chart
            st.markdown("<h4>Mathematical Priority Component Decomposition</h4>", unsafe_allow_html=True)
            st.caption("Visualizing the dual-component formula: Priority = (1 / RemainingTime) + (α × ContinuousWaitingTime).")
            chart = create_priority_component_chart(current_step)
            chart = apply_dark_theme(chart)
            st.plotly_chart(chart, use_container_width=True)

            # Candidate Comparison Table
            st.markdown("<h4>Ready Queue Candidate Comparison</h4>", unsafe_allow_html=True)
            st.caption("Numerical snapshot of all arrived and ready candidate processes at this decision instant.")
            candidate_df = create_candidate_comparison_df(current_step)
            st.dataframe(candidate_df, use_container_width=True)

            # Educational Deep Dive Expanders
            st.markdown("<div class='burgundy-divider'></div>", unsafe_allow_html=True)
            st.markdown("<h4>Scheduling Theory Deep Dives</h4>", unsafe_allow_html=True)

            with st.expander("📚 Why FAAS May Diverge from Pure SRTF"):
                st.markdown(f"""
                - **SRTF Logic:** Pure SRTF greedily chooses whichever process has the smallest remaining burst time.
                - **The Flaw:** If short jobs arrive repeatedly, long-burst processes experience indefinite postponement (starvation).
                - **FAAS Resolution:** As a longer job waits, its continuous waiting time accumulates. Multiplied by aging coefficient $\\alpha = {current_step.alpha}$, its composite priority score steadily increases. Eventually, the aging component $( \\alpha \\times W_{{cont}} )$ outweighs the reciprocal remaining time $( 1 / R )$ of newly arrived short jobs, causing an intentional, fairness-driven divergence from SRTF.
                """)

            with st.expander("🛡️ Hard Starvation Prevention Threshold Mechanics"):
                st.markdown(f"""
                - **Configured Threshold:** $T_{{starve}} = {current_step.starvation_threshold}$ time units.
                - **Trigger:** If any ready process has waited continuously for $\\ge {current_step.starvation_threshold}$ units without receiving CPU service, the scheduler declares it starving.
                - **Action:** Standard priority formula comparisons are bypassed. The starving process with the largest continuous waiting time is immediately dispatched.
                - **Reset Rule:** Once dispatched, its continuous waiting time resets to 0. (Note: Cumulative waiting time continues to be tracked accurately for total metrics).
                """)

            with st.expander("⏱️ Bounded Preemption & Guaranteed Quantum"):
                st.markdown(f"""
                - **Configured Quantum:** $Q = {current_step.configured_quantum}$ time units.
                - **Why not tick-by-tick (1 unit) preemption?** Tick-by-tick preemptive scheduling can cause excessive context switches (thrashing) and high cache invalidation overhead.
                - **FAAS Guarantee:** A dispatched process runs uninterrupted for $\\min(Q, p.\\text{{remaining\\_time}})$ before another scheduling decision occurs, balancing responsiveness with system throughput.
                """)


# =========================================================================== #
# SECTION 7: ALGORITHM COMPARISON                                             #
# =========================================================================== #
elif current_tab == "Comparison":
    st.markdown("<h2>Cross-Algorithm Comparative Performance</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #A7A7A7; font-size: 14px;'>Side-by-side performance benchmarks across all executed scheduling policies on identical inputs.</p>", unsafe_allow_html=True)

    sim = st.session_state["simulation_results"]

    if sim is None or not sim.algorithms:
        st.warning("No simulation results available. Please run the simulation first.")
    else:
        st.markdown("<h4>Unified Metrics Comparison Table</h4>", unsafe_allow_html=True)
        st.dataframe(sim.comparison_df, use_container_width=True)

        st.markdown("<div class='burgundy-divider'></div>", unsafe_allow_html=True)

        st.markdown("<h4>Visual Benchmark Comparisons</h4>", unsafe_allow_html=True)
        charts_map = create_all_comparison_charts(sim.comparison_df)

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if "Avg Turnaround Time" in charts_map:
                st.plotly_chart(apply_dark_theme(charts_map["Avg Turnaround Time"]), use_container_width=True)
            if "Avg Response Time" in charts_map:
                st.plotly_chart(apply_dark_theme(charts_map["Avg Response Time"]), use_container_width=True)
            if "Context Switches" in charts_map:
                st.plotly_chart(apply_dark_theme(charts_map["Context Switches"]), use_container_width=True)

        with col_c2:
            if "Avg Waiting Time" in charts_map:
                st.plotly_chart(apply_dark_theme(charts_map["Avg Waiting Time"]), use_container_width=True)
            if "CPU Utilization (%)" in charts_map:
                st.plotly_chart(apply_dark_theme(charts_map["CPU Utilization (%)"]), use_container_width=True)
            if "Preemptions" in charts_map:
                st.plotly_chart(apply_dark_theme(charts_map["Preemptions"]), use_container_width=True)

        # Analytical Summary & Best Performer Breakdown
        st.markdown("<div class='custom-card-accent'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #FFFFFF; margin-top: 0;'>Workload Analysis & Trade-Offs</h4>", unsafe_allow_html=True)

        best_wt = sim.comparison_df.sort_values(by="Avg Waiting Time").iloc[0]
        best_tat = sim.comparison_df.sort_values(by="Avg Turnaround Time").iloc[0]
        best_rt = sim.comparison_df.sort_values(by="Avg Response Time").iloc[0]

        st.markdown(f"""
        <p style='color: #F5F0E8; font-size: 14px; line-height: 1.6;'>
            • <b>Lowest Average Waiting Time:</b> <span style='color: #4CC9F0;'>{best_wt['Algorithm']}</span> ({best_wt['Avg Waiting Time']:.2f} time units)<br>
            • <b>Lowest Average Turnaround Time:</b> <span style='color: #4CC9F0;'>{best_tat['Algorithm']}</span> ({best_tat['Avg Turnaround Time']:.2f} time units)<br>
            • <b>Fastest Average Initial Response:</b> <span style='color: #4CC9F0;'>{best_rt['Algorithm']}</span> ({best_rt['Avg Response Time']:.2f} time units)
        </p>
        <p style='color: #A7A7A7; font-size: 13px; line-height: 1.5; margin-bottom: 0;'>
            <b>Academic Viva Insight:</b> No scheduling algorithm is universally optimal. SRTF achieves mathematically minimal average waiting times but causes high context switches and risks long-job starvation. HRRN prevents starvation non-preemptively but cannot adapt mid-execution. FAAS balances low turnaround times with strict starvation prevention guarantees.
        </p>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


# =========================================================================== #
# SECTION 8: ABOUT / EDUCATIONAL EXPLANATIONS                                 #
# =========================================================================== #
elif current_tab == "About":
    st.markdown("<h2>Scheduling Theory & Viva Preparation</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #A7A7A7; font-size: 14px;'>Comprehensive reference guide on scheduling policies, mathematical formulations, and trade-offs.</p>", unsafe_allow_html=True)

    tab_sjf, tab_srtf, tab_hrrn, tab_faas = st.tabs(["SJF", "SRTF", "HRRN", "FAAS (Proposed)"])

    with tab_sjf:
        st.markdown("""
        ### Shortest Job First (SJF)
        - **Type:** Non-Preemptive
        - **Selection Rule:** $\\arg\\min_{p \\in \\text{ready}} p.\\text{burst\\_time}$
        - **How it works:** Whenever the CPU becomes idle, the scheduler inspects all arrived processes and picks the one with the smallest burst time. Once dispatched, it runs to completion without interruption.
        - **Advantages:** Simple to implement; minimizes average waiting time when all jobs arrive simultaneously.
        - **Disadvantages:** Severe starvation risk for long jobs if short jobs arrive continuously; burst time must be known in advance.
        """)

    with tab_srtf:
        st.markdown("""
        ### Shortest Remaining Time First (SRTF)
        - **Type:** Preemptive
        - **Selection Rule:** $\\arg\\min_{p \\in \\text{ready}} p.\\text{remaining\\_time}$
        - **How it works:** At every arrival event, the scheduler compares the newly arrived job's burst against the running process's remaining time. If shorter, the running process is immediately preempted.
        - **Advantages:** Mathematically optimal average waiting and turnaround time.
        - **Disadvantages:** High context-switch overhead; severe starvation for long jobs; frequent cache invalidation.
        """)

    with tab_hrrn:
        st.markdown("""
        ### Highest Response Ratio Next (HRRN)
        - **Type:** Non-Preemptive with Dynamic Aging
        - **Selection Rule:** $\\text{Response Ratio} = \\frac{W + B}{B} = 1 + \\frac{W}{B}$
        - **How it works:** When the CPU is free, the scheduler computes the response ratio for all ready processes. Older waiting jobs accumulate higher ratios, naturally overtaking newly arrived short jobs.
        - **Advantages:** Starvation is mathematically eliminated without preemption.
        - **Disadvantages:** Non-preemptive nature means long jobs block urgent interactive tasks once started.
        """)

    with tab_faas:
        st.markdown("""
        ### Fairness-Aware Adaptive Scheduling (FAAS)
        - **Type:** Bounded Preemptive with Dynamic Aging & Hard Starvation Overrides
        - **Normal Priority Formula:**
          $$\\text{Priority}(p) = \\frac{1}{p.\\text{remaining\\_time}} + \\alpha \\times p.\\text{continuous\\_waiting\\_time}$$
        - **Guaranteed Service Quantum:** $Q = 2$ units (dispatch interval is bounded to eliminate context-switch thrashing).
        - **Starvation Protection Override:** If $W_{\\text{cont}} \\ge T_{\\text{starve}}$ (default: 8 units), the process is guaranteed immediate priority regardless of remaining burst length.
        - **Continuous vs Cumulative Waiting Time:** Continuous wait is reset to 0 upon receiving CPU service, preventing starvation gaming while keeping cumulative stats accurate.
        """)
