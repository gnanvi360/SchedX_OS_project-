import React, { useState } from 'react';
import { FAASDecisionStep } from '../types';

interface FaasInspectorProps {
  steps: FAASDecisionStep[];
  onRerunRequested?: () => void;
}

export const FaasInspector: React.FC<FaasInspectorProps> = ({ steps, onRerunRequested }) => {
  const [currentStepIdx, setCurrentStepIdx] = useState<number>(0);

  if (!steps || steps.length === 0) {
    return (
      <div className="card-panel p-8 text-center border border-borderDark rounded-lg space-y-4">
        <div className="text-3xl">🔬</div>
        <h3 className="text-lg font-bold text-ivory">No FAAS Decision History Available</h3>
        <p className="text-xs text-ivory-dark max-w-md mx-auto">
          Please run a simulation that includes the FAAS algorithm in the &quot;Algorithm Scheduling&quot; tab to inspect decision logs step-by-step.
        </p>
        {onRerunRequested && (
          <button
            onClick={onRerunRequested}
            className="px-4 py-2 bg-burgundy hover:bg-burgundy-soft text-white text-xs font-semibold rounded border border-borderBurgundy transition-colors"
          >
            Go to Algorithm Scheduling
          </button>
        )}
      </div>
    );
  }

  const safeIdx = Math.min(Math.max(currentStepIdx, 0), steps.length - 1);
  const step = steps[safeIdx];
  const totalSteps = steps.length;
  const selectedCandidate = step.candidates.find((c) => c.is_selected);

  // Maximum score for scaling the stacked bars
  const maxScore = Math.max(...step.candidates.map((c) => c.final_score), 1);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div>
        <h2 className="text-xl font-bold text-ivory tracking-wide">
          Fairness-Aware Adaptive Scheduling (FAAS) — Decision Inspector
        </h2>
        <p className="text-xs text-ivory-dark mt-1">
          Interactive step-by-step observation of scheduling decisions, priority score decomposition, aging dynamics, and starvation prevention overrides.
        </p>
      </div>

      {/* Step Navigation Bar */}
      <div className="card-panel p-4 border border-borderDark rounded-lg bg-panel flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setCurrentStepIdx(0)}
            disabled={safeIdx === 0}
            className="px-3 py-1.5 bg-[#141414] hover:bg-burgundy border border-borderDark disabled:opacity-40 disabled:hover:bg-[#141414] text-xs font-medium rounded text-ivory transition-colors"
          >
            ⏮ First
          </button>
          <button
            onClick={() => setCurrentStepIdx((prev) => Math.max(0, prev - 1))}
            disabled={safeIdx === 0}
            className="px-3 py-1.5 bg-[#141414] hover:bg-burgundy border border-borderDark disabled:opacity-40 disabled:hover:bg-[#141414] text-xs font-medium rounded text-ivory transition-colors"
          >
            ◀ Prev
          </button>
        </div>

        {/* Step Selector Dropdown */}
        <div className="flex-1 max-w-md">
          <select
            value={safeIdx}
            onChange={(e) => setCurrentStepIdx(Number(e.target.value))}
            className="w-full bg-[#0A0A0A] border border-borderBurgundy/60 text-ivory text-xs rounded px-3 py-1.5 font-mono focus:outline-none focus:border-burgundy-soft"
          >
            {steps.map((s, idx) => (
              <option key={s.step_index} value={idx}>
                Step {s.step_index}/{totalSteps} (Clock t = {s.clock}, Dispatched: {s.selected_pid})
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setCurrentStepIdx((prev) => Math.min(totalSteps - 1, prev + 1))}
            disabled={safeIdx === totalSteps - 1}
            className="px-3 py-1.5 bg-[#141414] hover:bg-burgundy border border-borderDark disabled:opacity-40 disabled:hover:bg-[#141414] text-xs font-medium rounded text-ivory transition-colors"
          >
            Next ▶
          </button>
          <button
            onClick={() => setCurrentStepIdx(totalSteps - 1)}
            disabled={safeIdx === totalSteps - 1}
            className="px-3 py-1.5 bg-[#141414] hover:bg-burgundy border border-borderDark disabled:opacity-40 disabled:hover:bg-[#141414] text-xs font-medium rounded text-ivory transition-colors"
          >
            Last ⏭
          </button>
        </div>
      </div>

      {/* Decision Status Banner */}
      {step.starvation_override ? (
        <div className="bg-[#1A0508] border-2 border-red-600 rounded-lg p-5 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-red-400 font-bold text-sm tracking-wider uppercase flex items-center space-x-2">
              <span className="animate-pulse text-lg">🚨</span>
              <span>STARVATION PREVENTION OVERRIDE ACTIVATED</span>
            </span>
            <span className="px-3 py-1 bg-burgundy rounded text-white text-xs font-mono font-semibold">
              Time t = {step.clock}
            </span>
          </div>
          <p className="text-xs text-ivory mt-2 leading-relaxed">
            Process <strong className="text-white font-mono">{step.selected_pid}</strong> reached continuous waiting time of{' '}
            <strong className="text-red-300">
              {selectedCandidate ? selectedCandidate.continuous_waiting_time : step.starvation_threshold}
            </strong>{' '}
            units, exceeding the configured starvation threshold (
            <strong className="text-red-400">T_starve = {step.starvation_threshold}</strong>).
            Standard priority scoring was bypassed to prevent indefinite postponement and guarantee CPU allocation.
          </p>
        </div>
      ) : (
        <div className="bg-[#0A0A0A] border border-borderBurgundy rounded-lg p-5">
          <div className="flex items-center justify-between">
            <span className="text-cyan-400 font-bold text-xs tracking-wider uppercase flex items-center space-x-2">
              <span>⚖️ NORMAL FAIRNESS-AWARE PRIORITY DISPATCH</span>
            </span>
            <span className="px-3 py-1 bg-[#141414] border border-borderDark rounded text-ivory text-xs font-mono">
              Time t = {step.clock}
            </span>
          </div>
          <p className="text-xs text-ivory mt-2 leading-relaxed">
            Process <strong className="text-white font-mono">{step.selected_pid}</strong> won scheduling dispatch with the
            highest composite priority score of{' '}
            <strong className="text-cyan-300 font-mono">{step.selected_priority.toFixed(4)}</strong>.
          </p>
        </div>
      )}

      {/* Dynamic Educational Step Explanation Callout */}
      <div className="card-panel border-l-4 border-l-burgundy-soft p-4 rounded-r-lg bg-[#080808]">
        <div className="text-[11px] uppercase tracking-wider text-ivory-dark font-semibold mb-1">
          Step Analysis &amp; Decision Breakdown
        </div>
        <div
          className="text-xs text-ivory leading-relaxed"
          dangerouslySetInnerHTML={{ __html: step.explanation }}
        />
      </div>

      {/* Metric Cards Row for this Decision Point */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="card-panel p-3.5 text-center border border-borderDark rounded bg-[#0A0A0A]">
          <div className="text-[11px] uppercase tracking-wider text-ivory-dark">Simulation Clock</div>
          <div className="text-xl font-bold font-mono text-ivory mt-1">t = {step.clock}</div>
        </div>
        <div className="card-panel p-3.5 text-center border border-borderDark rounded bg-[#0A0A0A]">
          <div className="text-[11px] uppercase tracking-wider text-ivory-dark">Selected Process</div>
          <div className="text-xl font-bold font-mono text-cyan-400 mt-1">{step.selected_pid}</div>
        </div>
        <div className="card-panel p-3.5 text-center border border-borderDark rounded bg-[#0A0A0A]">
          <div className="text-[11px] uppercase tracking-wider text-ivory-dark">Priority Score</div>
          <div className="text-xl font-bold font-mono text-ivory mt-1">{step.selected_priority.toFixed(4)}</div>
        </div>
        <div className="card-panel p-3.5 text-center border border-borderDark rounded bg-[#0A0A0A]">
          <div className="text-[11px] uppercase tracking-wider text-ivory-dark">Guaranteed Quantum</div>
          <div className="text-xl font-bold font-mono text-rose-300 mt-1">{step.quantum_granted} units</div>
        </div>
      </div>

      {/* Stacked Priority Component Breakdown Chart */}
      <div className="card-panel p-5 border border-borderDark rounded-lg bg-panel">
        <div className="flex justify-between items-center mb-4 pb-2 border-b border-borderDark">
          <div>
            <h4 className="text-sm font-semibold text-ivory">Priority Component Decomposition</h4>
            <p className="text-[11px] text-ivory-dark">
              Formula: Priority = (1 / RemainingTime) + (α × ContinuousWaitingTime)
            </p>
          </div>
          <div className="flex items-center space-x-4 text-xs font-mono">
            <span className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-[#4361EE]" />
              <span className="text-ivory-dark">1 / Remaining</span>
            </span>
            <span className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-[#853B47]" />
              <span className="text-ivory-dark">{step.alpha} × Wait</span>
            </span>
          </div>
        </div>

        {/* Stacked Bar Visualizer */}
        <div className="space-y-3.5 pt-1 pb-3">
          {step.candidates.map((cand) => {
            const remWidthPct = (cand.remaining_priority / maxScore) * 100;
            const waitWidthPct = (cand.waiting_priority / maxScore) * 100;
            const isWinner = cand.is_selected;

            return (
              <div key={cand.pid} className="space-y-1">
                <div className="flex justify-between items-center text-xs">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono font-bold text-ivory">{cand.pid}</span>
                    {isWinner && (
                      <span className="px-1.5 py-0.2 rounded bg-burgundy text-white font-sans text-[10px] font-semibold border border-rose-400">
                        {step.starvation_override ? '★ STARVATION OVERRIDE' : '★ SELECTED'}
                      </span>
                    )}
                    {cand.is_starving && !isWinner && (
                      <span className="px-1.5 py-0.2 rounded bg-red-950 text-red-300 font-sans text-[10px] border border-red-800">
                        Starving
                      </span>
                    )}
                  </div>
                  <span className="font-mono text-ivory font-semibold text-xs">
                    Score: {cand.final_score.toFixed(4)}{' '}
                    <span className="text-ivory-dark text-[10px] font-normal">
                      (Rem: {cand.remaining_priority.toFixed(3)} + Wait: {cand.waiting_priority.toFixed(3)})
                    </span>
                  </span>
                </div>

                {/* Stacked bar container */}
                <div className="h-5 w-full bg-[#111111] rounded overflow-hidden flex p-0.5 border border-borderDark">
                  {/* Remaining component */}
                  <div
                    style={{ width: `${remWidthPct}%` }}
                    className="h-full bg-[#4361EE] rounded-l-sm transition-all duration-300 relative group"
                    title={`Remaining Priority: ${cand.remaining_priority}`}
                  />
                  {/* Waiting component */}
                  <div
                    style={{ width: `${waitWidthPct}%` }}
                    className="h-full bg-[#853B47] rounded-r-sm transition-all duration-300 relative group"
                    title={`Aging Priority: ${cand.waiting_priority}`}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Candidate Comparison Table */}
      <div className="card-panel p-5 border border-borderDark rounded-lg bg-panel">
        <h4 className="text-sm font-semibold text-ivory mb-1">Ready Queue Candidate Processes</h4>
        <p className="text-[11px] text-ivory-dark mb-3">
          Numerical inspection of all candidate processes competing at time t = {step.clock}.
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border-collapse">
            <thead>
              <tr className="border-b border-borderDark bg-[#0A0A0A] text-ivory-dark font-mono text-[11px]">
                <th className="py-2.5 px-3">Selected</th>
                <th className="py-2.5 px-3">PID</th>
                <th className="py-2.5 px-3">Remaining Time</th>
                <th className="py-2.5 px-3">Continuous Wait</th>
                <th className="py-2.5 px-3">1 / Remaining</th>
                <th className="py-2.5 px-3">{step.alpha} × Wait</th>
                <th className="py-2.5 px-3">Composite Score</th>
                <th className="py-2.5 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-borderDark/60 font-mono">
              {step.candidates.map((cand) => (
                <tr
                  key={cand.pid}
                  className={`hover:bg-[#141414] transition-colors ${
                    cand.is_selected ? 'bg-burgundy/15 font-semibold text-white' : 'text-ivory'
                  }`}
                >
                  <td className="py-2 px-3">
                    {cand.is_selected ? <span className="text-rose-400 font-bold">✓ YES</span> : '—'}
                  </td>
                  <td className="py-2 px-3 font-bold">{cand.pid}</td>
                  <td className="py-2 px-3">{cand.remaining_time}</td>
                  <td className="py-2 px-3">{cand.continuous_waiting_time}</td>
                  <td className="py-2 px-3 text-[#7089FF]">{cand.remaining_priority.toFixed(4)}</td>
                  <td className="py-2 px-3 text-rose-300">{cand.waiting_priority.toFixed(4)}</td>
                  <td className="py-2 px-3 font-bold">{cand.final_score.toFixed(4)}</td>
                  <td className="py-2 px-3">
                    {cand.is_starving ? (
                      <span className="text-red-400 font-bold">Starving (Override)</span>
                    ) : (
                      <span className="text-ivory-dark">Normal</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
