"""
faas_explainer.py
-----------------
Decision explanation and inspection engine for Fairness-Aware Adaptive Scheduling (FAAS).

Provides a read-only educational observation layer over the actual FAAS algorithm execution.
Extracts decision history, decomposes mathematical priority components, detects divergence
from pure SRTF, and generates rich Plotly component charts and student-friendly explanations.

Does NOT modify or duplicate the scheduling algorithm.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import pandas as pd
import plotly.graph_objects as go


@dataclass
class CandidateDetail:
    """Detailed breakdown of a single candidate process at a decision step."""
    pid: str
    remaining_time: int
    continuous_waiting_time: int
    remaining_priority: float
    waiting_priority: float
    final_score: float
    is_starving: bool
    is_selected: bool


@dataclass
class FAASDecisionStep:
    """Structured record of a single scheduling decision point in FAAS."""
    step_index: int
    clock: int
    selected_pid: str
    selected_priority: float
    quantum_granted: int
    starvation_override: bool
    reason: str
    starvation_threshold: int
    configured_quantum: int
    alpha: float
    candidates: List[CandidateDetail] = field(default_factory=list)
    srtf_preferred_pid: Optional[str] = None
    explanation: str = ""

    @property
    def selected_candidate(self) -> Optional[CandidateDetail]:
        """Returns the detail object for the selected process."""
        for c in self.candidates:
            if c.is_selected:
                return c
        return None


def parse_faas_decision_history(
    decision_log: List[Dict[str, Any]],
    alpha: float = 4.0,
    starvation_threshold: int = 8,
    quantum: int = 2,
) -> List[FAASDecisionStep]:
    """
    Parses the raw decision_log produced by run_faas into structured,
    explained FAASDecisionStep objects.

    Parameters:
        decision_log (list[dict]): Raw decision records from schedulers/faas.py.
        alpha (float): Configured aging factor.
        starvation_threshold (int): Configured starvation threshold.
        quantum (int): Configured service quantum.

    Returns:
        list[FAASDecisionStep]: Sequence of explained decision steps.
    """
    if not decision_log:
        return []

    steps = []
    for idx, d in enumerate(decision_log, start=1):
        clock = d.get("clock", 0)
        selected_pid = d.get("selected", "")
        selected_priority = d.get("selected_priority", 0.0)
        quantum_granted = d.get("quantum_granted", quantum)
        starvation_override = d.get("starvation_override", False)
        reason = d.get("reason", "Highest Priority Score")

        raw_candidates = d.get("candidates", [])
        candidate_details = []

        # Find which process SRTF would prefer (strictly smallest remaining time)
        srtf_preferred = None
        if raw_candidates:
            srtf_candidate = min(
                raw_candidates,
                key=lambda c: (c.get("remaining_time", 9999), c.get("pid", ""))
            )
            srtf_preferred = srtf_candidate.get("pid")

        for c in raw_candidates:
            pid = c.get("pid", "")
            rem = c.get("remaining_time", 1)
            wait = c.get("continuous_waiting_time", 0)
            is_starving = c.get("is_starving", False)
            is_selected = (pid == selected_pid)

            rem_priority = round(1.0 / rem, 4) if rem > 0 else 0.0
            wait_priority = round(alpha * wait, 4)
            score = round(rem_priority + wait_priority, 4)

            candidate_details.append(
                CandidateDetail(
                    pid=pid,
                    remaining_time=rem,
                    continuous_waiting_time=wait,
                    remaining_priority=rem_priority,
                    waiting_priority=wait_priority,
                    final_score=score,
                    is_starving=is_starving,
                    is_selected=is_selected,
                )
            )

        # Dynamic student-friendly explanation generation
        explanation_lines = []
        if starvation_override:
            sel_detail = next((c for c in candidate_details if c.is_selected), None)
            wait_val = sel_detail.continuous_waiting_time if sel_detail else starvation_threshold
            explanation_lines.append(
                f"At simulation time t = {clock}, process <b>{selected_pid}</b> was dispatched via a "
                f"<span style='color: #d62728; font-weight: bold;'>Starvation Prevention Override</span>. "
                f"Its continuous waiting time reached {wait_val} units (exceeding the starvation threshold of {starvation_threshold} units). "
                f"Normal priority score competition was bypassed to guarantee CPU service to the longest-starving job."
            )
        else:
            sel_detail = next((c for c in candidate_details if c.is_selected), None)
            rem_p = sel_detail.remaining_priority if sel_detail else 0.0
            wait_p = sel_detail.waiting_priority if sel_detail else 0.0
            explanation_lines.append(
                f"At simulation time t = {clock}, process <b>{selected_pid}</b> was dispatched with the "
                f"highest calculated priority score of <b>{selected_priority:.4f}</b>. "
                f"The remaining-time component contributed {rem_p:.4f} (1/{sel_detail.remaining_time if sel_detail else 'Rem'}), "
                f"while continuous waiting aging contributed {wait_p:.4f} ({alpha} × {sel_detail.continuous_waiting_time if sel_detail else 0})."
            )

            # Contrast with pure SRTF if decisions diverge
            if srtf_preferred and srtf_preferred != selected_pid:
                srtf_det = next((c for c in candidate_details if c.pid == srtf_preferred), None)
                srtf_rem = srtf_det.remaining_time if srtf_det else 'N/A'
                explanation_lines.append(
                    f"<br><b>Divergence from SRTF:</b> Pure SRTF would have selected <b>{srtf_preferred}</b> "
                    f"due to its shorter remaining time ({srtf_rem} units). However, FAAS favored {selected_pid} "
                    f"because its continuous waiting time raised its fairness priority score above {srtf_preferred}."
                )

        explanation_lines.append(
            f"<br><b>Guaranteed Quantum:</b> Granted {quantum_granted} CPU time units "
            f"(bounded dispatch interval ≤ {quantum} units)."
        )

        steps.append(
            FAASDecisionStep(
                step_index=idx,
                clock=clock,
                selected_pid=selected_pid,
                selected_priority=selected_priority,
                quantum_granted=quantum_granted,
                starvation_override=starvation_override,
                reason=reason,
                starvation_threshold=starvation_threshold,
                configured_quantum=quantum,
                alpha=alpha,
                candidates=candidate_details,
                srtf_preferred_pid=srtf_preferred,
                explanation=" ".join(explanation_lines),
            )
        )

    return steps


def create_candidate_comparison_df(step: FAASDecisionStep) -> pd.DataFrame:
    """
    Transforms candidate details for a specific decision step into a pandas DataFrame.
    """
    if not step or not step.candidates:
        return pd.DataFrame()

    rows = []
    for c in step.candidates:
        rows.append({
            "Selected": "✓ YES" if c.is_selected else "",
            "PID": c.pid,
            "Remaining Time": c.remaining_time,
            "Continuous Wait": c.continuous_waiting_time,
            "Remaining Priority (1/Rem)": c.remaining_priority,
            f"Waiting Priority ({step.alpha}×Wait)": c.waiting_priority,
            "Total Priority Score": c.final_score,
            "Starving?": "YES (Override)" if c.is_starving else "No",
        })

    return pd.DataFrame(rows)


def create_priority_component_chart(step: FAASDecisionStep) -> go.Figure:
    """
    Generates an interactive Plotly stacked bar chart showing the breakdown of
    Remaining-Time Priority vs Waiting-Time Priority for all candidates at this step.
    """
    fig = go.Figure()

    if not step or not step.candidates:
        fig.add_annotation(
            text="No candidate processes available at this step.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=15, color="gray"),
        )
        fig.update_layout(title="FAAS Priority Decomposition")
        return fig

    pids = [c.pid for c in step.candidates]
    rem_prios = [c.remaining_priority for c in step.candidates]
    wait_prios = [c.waiting_priority for c in step.candidates]
    selected_mask = [c.is_selected for c in step.candidates]

    # Bar 1: Remaining-time priority (SRTF component)
    fig.add_trace(go.Bar(
        name="Remaining-Time Priority (1 / Rem)",
        x=pids,
        y=rem_prios,
        marker=dict(color="#4361EE", line=dict(color="#111111", width=1)),
        hoverinfo="text",
        hovertext=[
            f"<b>{c.pid}</b><br>Remaining Time: {c.remaining_time}<br>Remaining Priority: {c.remaining_priority:.4f}"
            for c in step.candidates
        ],
    ))

    # Bar 2: Waiting-time priority (Aging component)
    fig.add_trace(go.Bar(
        name=f"Waiting-Time Priority ({step.alpha} × Wait)",
        x=pids,
        y=wait_prios,
        marker=dict(color="#853B47", line=dict(color="#111111", width=1)),
        hoverinfo="text",
        hovertext=[
            f"<b>{c.pid}</b><br>Continuous Wait: {c.continuous_waiting_time}<br>Aging Score: {c.waiting_priority:.4f}"
            for c in step.candidates
        ],
    ))

    # Add annotation arrow pointing to the selected process
    for i, c in enumerate(step.candidates):
        if c.is_selected:
            total_score = c.remaining_priority + c.waiting_priority
            annotation_text = "★ SELECTED (Starvation Override)" if step.starvation_override else "★ SELECTED"
            fig.add_annotation(
                x=c.pid,
                y=total_score,
                text=annotation_text,
                showarrow=True,
                arrowhead=2,
                arrowcolor="#FFFFFF",
                arrowsize=1.2,
                arrowwidth=2,
                ax=0,
                ay=-35,
                font=dict(color="#FFFFFF", size=12, family="Arial Black"),
                bgcolor="#600D1A" if step.starvation_override else "#1E1E1E",
                bordercolor="#853B47",
                borderwidth=1,
            )

    fig.update_layout(
        barmode="stack",
        title=dict(
            text=f"<b>Candidate Priority Score Decomposition at Time t = {step.clock}</b>",
            x=0.5,
            font=dict(size=16),
        ),
        xaxis=dict(title="<b>Process ID</b>"),
        yaxis=dict(title="<b>Priority Score</b>", showgrid=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        height=380,
        margin=dict(l=40, r=40, t=80, b=50),
    )

    return fig
