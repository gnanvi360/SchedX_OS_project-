# CPU Scheduling Simulator & Benchmarking Platform
### Featuring Fairness-Aware Adaptive Scheduling (FAAS)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![React 18+](https://img.shields.io/badge/frontend-React%20%7C%20TypeScript%20%7C%20Tailwind-blue.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-teal.svg)](https://fastapi.tiangolo.com/)
[![Tests Passing](https://img.shields.io/badge/tests-99%20passed-brightgreen.svg)](https://pytest.org/)

---

## 1. Project Overview & Objectives

In modern multi-programmed operating systems, the short-term CPU scheduler plays a pivotal role in allocating scarce processor time among competing ready tasks. Classical uniprocessor scheduling policies—such as **Shortest Job First (SJF)**, **Shortest Remaining Time First (SRTF)**, and **Highest Response Ratio Next (HRRN)**—each optimize specific criteria while exhibiting severe real-world drawbacks.

This project delivers:
1. An **Operating Systems simulation and benchmarking application** comparing classical algorithms against our novel proposed scheduling policy: **Fairness-Aware Adaptive Scheduling (FAAS)**.
2. A **Common Performance Metrics Engine** evaluating turnaround times, waiting times, response times, throughput, CPU utilization, context switches, and preemptions across identical workloads.
3. A **Production Full-Stack Web Application**:
   - **Frontend:** React 18 with TypeScript, Tailwind CSS, Lucide icons, responsive interactive Gantt chart visualizers, dynamic metric breakdown bars, and step-by-step decision inspectors.
   - **Backend:** Python FastAPI REST server wrapping the core scheduling engine with zero algorithm modifications.
   - **Prototype:** Streamlit interactive dashboard (`app.py`).
4. An automated test suite comprising **99 unit, integration, and mathematical regression tests** with 100% test passage.

---

## 2. Problem Statement & Motivation

### The Algorithmic Dilemma:
- **Shortest Job First (SJF):** Provably minimizes average waiting time when all jobs arrive simultaneously, but its non-preemptive nature causes the **convoy effect** and indefinite postponement (**starvation**) for long jobs if short jobs arrive continuously.
- **Shortest Remaining Time First (SRTF):** Achieves theoretical optimal average turnaround time through preemption. However, it suffers from severe starvation of CPU-bound processes and introduces high context-switch frequency and CPU cache thrashing.
- **Highest Response Ratio Next (HRRN):** Eliminates starvation by dynamically increasing priority via waiting-time aging ($RR = 1 + W/B$). However, its non-preemptive design means that once a long job gains the CPU, high-priority interactive tasks are blocked.

### The Solution: Fairness-Aware Adaptive Scheduling (FAAS)
FAAS bridges the gap between the optimal turnaround efficiency of SRTF, the starvation-immunity of HRRN, and the bounded preemption stability of Round Robin by combining:
- **Reciprocal Remaining-Time Priority:** Efficiently dispatches short jobs first.
- **Dynamic Waiting-Time Aging:** Continuously scales priority for unserviced waiting jobs.
- **Hard Starvation Prevention Overrides:** Automatically grants emergency execution when a process waits continuously beyond a strict threshold ($T_{\text{starve}}$).
- **Guaranteed Bounded Service Quantum ($Q=2$):** Eliminates 1-unit context switch thrashing by guaranteeing bounded CPU execution slices.

---

## 3. Technology Stack & Architecture

### Full-Stack Architecture
- **Frontend:** React 18, TypeScript, Tailwind CSS, Vite bundler
- **Backend API:** Python FastAPI, Uvicorn ASGI server, Pydantic validation
- **Core Algorithms & Domain:** Pure Python 3.11 (`schedulers/`, `core/`)
- **Automated Testing:** Pytest 8.3 (99 tests)

### Directory Structure
```
├── backend/                    # FastAPI REST API Layer
│   └── main.py                 # REST endpoints wrapping scheduling engine
│
├── frontend/                   # React TypeScript Web Application
│   ├── src/
│   │   ├── components/         # GanttChart, FaasInspector, Metrics, Comparison
│   │   ├── api.ts              # Type-safe API client
│   │   ├── types.ts            # TypeScript interfaces
│   │   ├── utils/colors.ts     # Process and algorithm palette
│   │   ├── App.tsx             # Root component with horizontal navigation
│   │   └── main.tsx            # Application entry point
│   ├── dist/                   # Production-compiled static assets
│   ├── tailwind.config.js      # Dark burgundy, black & ivory styling
│   └── vite.config.ts          # Vite configuration with API proxy
│
├── schedulers/                 # Algorithm Domain Layer
│   ├── process.py              # Process data model & state transition logic
│   ├── sjf.py                  # Non-preemptive Shortest Job First
│   ├── srtf.py                 # Preemptive Shortest Remaining Time First
│   ├── hrrn.py                 # Non-preemptive Highest Response Ratio Next
│   └── faas.py                 # Proposed Fairness-Aware Adaptive Scheduling
│
├── core/                       # Orchestration & Evaluation Engine
│   ├── runner.py               # Unified execution runner & immutability manager
│   ├── metrics.py              # Standardized 10-metric calculation engine
│   ├── charts.py               # Plotly Gantt & comparative visualizer
│   ├── generator.py            # Parametric & preset random workload generator
│   └── faas_explainer.py       # Read-only FAAS decision history & decomposition
│
├── tests/                      # Automated Regression Test Suite (99 tests)
│   ├── test_backend_api.py     # FastAPI endpoints integration tests
│   ├── test_faas.py            # FAAS algorithm and override tests
│   ├── test_faas_explainer.py  # Decision inspector tests
│   └── ...                     # SJF, SRTF, HRRN, Metrics, Runner, Charts tests
│
├── docs/                       # Academic Reference Documentation
│   ├── ALGORITHM_EXPLANATION.md # Detailed algorithmic theory & step-by-step traces
│   ├── VIVA_PREP.md            # Comprehensive viva voce exam preparation guide
│   └── TEST_CASES.md           # Test suite architecture & case descriptions
│
├── run_website.py              # One-click execution script for the web application
├── app.py                      # Interactive Streamlit Prototype
├── requirements.txt            # Python dependencies
└── README.md                   # Primary system documentation
```

---

## 4. Implemented Scheduling Algorithms

| Algorithm | Preemption Mode | Mathematical Selection Criterion | Starvation Risk | Context Switching |
|---|---|---|---|---|
| **SJF** | Non-Preemptive | $\arg\min (BT_i, AT_i, \text{PID}_i)$ | High for long tasks | Minimal ($N-1$) |
| **SRTF** | Preemptive | $\arg\min (\text{Remaining}_i(t), AT_i, \text{PID}_i)$ | Severe for long tasks | High (continuous) |
| **HRRN** | Non-Preemptive | $\arg\max \left( 1 + \frac{W_i}{BT_i}, -AT_i, -\text{PID}_i \right)$ | None (dynamic aging) | Minimal ($N-1$) |
| **FAAS** | Bounded Preemptive | $\arg\max \left( \frac{1}{\text{Rem}_i} + \alpha W_{\text{cont}, i} \right)$ or Starvation Override | Zero (hard override at $T_{\text{starve}}$) | Bounded by $Q=2$ |

---

## 5. Performance Metrics & Mathematical Formulations

The metrics engine calculates 10 standardized performance indicators for every simulation:

1. **Turnaround Time ($TAT_i$):**
   $$TAT_i = CT_i - AT_i$$
2. **Waiting Time ($WT_i$):**
   $$WT_i = TAT_i - BT_i$$
3. **Response Time ($RT_i$):**
   $$RT_i = ST_i - AT_i$$
4. **Average Turnaround Time:**
   $$\text{Avg } TAT = \frac{1}{N} \sum_{i=1}^{N} TAT_i$$
5. **Average Waiting Time:**
   $$\text{Avg } WT = \frac{1}{N} \sum_{i=1}^{N} WT_i$$
6. **Average Response Time:**
   $$\text{Avg } RT = \frac{1}{N} \sum_{i=1}^{N} RT_i$$
7. **CPU Utilization (%):**
   $$\text{CPU Utilization} = \left( \frac{\text{Total Busy Time}}{\text{Total Busy Time} + \text{Total Idle Time}} \right) \times 100\%$$
8. **Throughput:**
   $$\text{Throughput} = \frac{N}{\max(CT_i)}$$
9. **Context Switches:** Transitions from one process to a different process ($p_{\text{curr}} \ne p_{\text{next}}$).
10. **Preemptions:** Executing processes interrupted before burst completion.

---

## 6. The FAAS Algorithm & Fairness Mechanisms

### 1. Composite Priority Scoring
$$\text{Priority}(p_i) = \frac{1}{\text{RemainingTime}_i} + \left( \alpha \times \text{ContinuousWaitingTime}_i \right)$$
- $\frac{1}{\text{RemainingTime}_i}$: Reciprocal remaining time prioritizes short tasks.
- $\alpha \times \text{ContinuousWaitingTime}_i$: Dynamic aging escalates waiting processes linearly ($\alpha = 4.0$ by default).

### 2. Hard Starvation Prevention Override
$$\text{Starvation Trigger: } \text{ContinuousWaitingTime}_i \ge T_{\text{starve}}$$
When continuous wait hits or exceeds $T_{\text{starve}}$ (default: $8$ units), normal priority competition is bypassed. The longest-starving process is dispatched immediately.

### 3. Continuous vs Cumulative Waiting Time
- **Continuous Wait ($W_{\text{cont}}$):** Tracks consecutive waiting time since the most recent CPU execution. Resets to $0$ immediately upon CPU dispatch, preventing process gaming.
- **Cumulative Wait ($W_{\text{cumul}}$):** Monotonically accumulates total wait time across the lifespan to preserve accurate performance metrics.

### 4. Guaranteed Bounded Service Quantum ($Q$)
Dispatched processes execute for $\min(Q, \text{RemainingTime})$ before another scheduling decision occurs ($Q=2$ by default), eliminating 1-unit preemption thrashing.

---

## 7. Installation & Quick Start

### Prerequisites
- Python 3.10+ (tested on Python 3.11)
- Node.js 18+ (tested on Node v22)
- PowerShell (Windows) or Terminal (macOS/Linux)

### Step 1: Install Python Dependencies
```powershell
pip install -r requirements.txt
```

### Step 2: Run the Complete Test Suite
```powershell
python -m pytest -p no:anyio -v
```
All **99 automated tests** will execute and pass.

### Step 3: Run the Website (One-Click)
```powershell
python run_website.py
```
This automatically starts the FastAPI backend (which hosts the compiled React frontend) and opens your browser at:
`http://127.0.0.1:8000`

### Alternative: Frontend Development Mode
To develop on the frontend with hot-module reloading:
```powershell
# Terminal 1: Start FastAPI backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2: Start Vite React dev server
cd frontend
npm run dev
```
Open `http://localhost:3000`.

---

## 8. Website Navigation & Features

1. **Dashboard:** High-level system overview, loaded workload summary, and feature matrix cards.
2. **Process Input:**
   - Spreadsheet editor: add, delete, and inline-edit process arrival/burst times.
   - Preset selector: Benchmark Dataset (P1-P4), Simultaneous Arrivals, Starvation Trace, Idle Trace.
   - Random generator: Uniform, Short-Job Heavy, Long-Job Heavy, and Mixed Workload distributions with reproducible seeds.
3. **Algorithm Scheduling:** Enable/disable algorithms, tune FAAS parameters ($Q$, $\alpha$, $T_{\text{starve}}$), and execute simulations.
4. **Gantt Charts:** Interactive timeline with hover tooltips, tick markers, CPU idle periods, and stacked or tabbed views.
5. **Performance Metrics:** Per-process completion tables, CSV export, and aggregate cards.
6. **FAAS Inspector:** Step-by-step decision inspector with First/Prev/Next/Last navigation, starvation override alert banners, priority decomposition stacked bar charts, and candidate comparison tables.
7. **Comparison:** Side-by-side comparative metric bar charts with best-performer highlights and trade-off analysis.
8. **Viva & Theory:** Theoretical algorithm summaries and top viva voce exam questions with answers.
