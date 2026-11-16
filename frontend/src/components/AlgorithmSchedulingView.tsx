import React from 'react';
import { Process, SimulationResponse } from '../types';
import { ALGORITHM_COLORS } from '../utils/colors';

interface AlgorithmSchedulingViewProps {
  processes: Process[];
  selectedAlgorithms: Record<string, boolean>;
  onToggleAlgorithm: (name: string) => void;
  faasQuantum: number;
  onFaasQuantumChange: (q: number) => void;
  faasAlpha: number;
  onFaasAlphaChange: (a: number) => void;
  faasStarvationThreshold: number;
  onFaasThresholdChange: (t: number) => void;
  isRunning: boolean;
  onRunSimulation: () => void;
  simulationResults: SimulationResponse | null;
  onNavigateToTab: (tabName: string) => void;
}

export const AlgorithmSchedulingView: React.FC<AlgorithmSchedulingViewProps> = ({
  processes,
  selectedAlgorithms,
  onToggleAlgorithm,
  faasQuantum,
  onFaasQuantumChange,
  faasAlpha,
  onFaasAlphaChange,
  faasStarvationThreshold,
  onFaasThresholdChange,
  isRunning,
  onRunSimulation,
  simulationResults,
  onNavigateToTab,
}) => {
  const algorithmsList = [
    {
      name: 'SJF',
      label: 'Shortest Job First',
      badge: 'Non-Preemptive',
      desc: 'Dispatches the process with the smallest initial CPU burst time. Minimizes average wait times when jobs arrive together, but susceptible to long-job starvation.',
    },
    {
      name: 'SRTF',
      label: 'Shortest Remaining Time First',
      badge: 'Preemptive',
      desc: 'Preempts running tasks whenever an arriving task has a strictly smaller remaining burst. Yields theoretically optimal turnaround time at the cost of high context switches.',
    },
    {
      name: 'HRRN',
      label: 'Highest Response Ratio Next',
      badge: 'Non-Preemptive with Aging',
      desc: 'Dynamically computes Response Ratio = 1 + (W/B). Waiting time accumulation naturally promotes older jobs, preventing starvation without preemption.',
    },
    {
      name: 'FAAS',
      label: 'Fairness-Aware Adaptive Scheduling',
      badge: 'Proposed Custom Algorithm',
      desc: 'Combines reciprocal remaining-time priority, continuous-waiting dynamic aging, hard starvation prevention threshold overrides, and bounded quantum stability.',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div>
        <h2 className="text-xl font-bold text-ivory tracking-wide">Algorithm Selection &amp; Simulation Engine</h2>
        <p className="text-xs text-ivory-dark mt-1">
          Select target scheduling policies, calibrate FAAS hyperparameters, and dispatch the simulation on your configured workload.
        </p>
      </div>

      {/* Algorithms Selection Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {algorithmsList.map((alg) => {
          const isSelected = selectedAlgorithms[alg.name] ?? true;
          const color = ALGORITHM_COLORS[alg.name] || '#600D1A';

          return (
            <div
              key={alg.name}
              onClick={() => onToggleAlgorithm(alg.name)}
              className={`p-4 rounded-lg border cursor-pointer transition-all ${
                isSelected
                  ? 'bg-panel border-borderBurgundy shadow-md'
                  : 'bg-[#080808] border-borderDark opacity-60 hover:opacity-85'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2.5">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => onToggleAlgorithm(alg.name)}
                    className="accent-burgundy w-4 h-4 rounded cursor-pointer"
                  />
                  <div>
                    <span className="font-mono font-bold text-sm text-ivory mr-2">{alg.name}</span>
                    <span className="text-xs text-ivory-dark font-medium">{alg.label}</span>
                  </div>
                </div>
                <span
                  className="text-[10px] px-2 py-0.5 rounded font-mono font-medium"
                  style={{
                    backgroundColor: `${color}20`,
                    color: color,
                    border: `1px solid ${color}40`,
                  }}
                >
                  {alg.badge}
                </span>
              </div>
              <p className="text-xs text-ivory-dark mt-2.5 leading-relaxed pl-6.5">{alg.desc}</p>
            </div>
          );
        })}
      </div>

      {/* FAAS Hyperparameter Controls */}
      <div className="card-panel-burgundy p-5 border border-borderBurgundy rounded-lg">
        <div className="flex items-center justify-between mb-3 pb-2 border-b border-borderBurgundy/60">
          <div>
            <h3 className="text-sm font-bold text-ivory uppercase tracking-wider">
              FAAS Hyperparameter Calibration
            </h3>
            <p className="text-[11px] text-ivory-dark">
              Fine-tune the mathematical parameters governing priority escalation and preemption boundaries.
            </p>
          </div>
          <span className="text-[10px] px-2 py-1 bg-burgundy rounded text-white font-mono">
            Active in FAAS
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
          {/* Quantum Q */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="text-ivory font-medium">Guaranteed Quantum (Q)</span>
              <span className="font-mono text-rose-300 font-bold">{faasQuantum} units</span>
            </div>
            <input
              type="range"
              min="1"
              max="10"
              value={faasQuantum}
              onChange={(e) => onFaasQuantumChange(Number(e.target.value))}
              className="w-full accent-burgundy"
            />
            <p className="text-[10px] text-ivory-dark">
              Bounded CPU execution slice. Default Q=2 eliminates context-switch thrashing.
            </p>
          </div>

          {/* Aging Factor Alpha */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="text-ivory font-medium">Aging Weight (α)</span>
              <span className="font-mono text-rose-300 font-bold">{faasAlpha.toFixed(1)}</span>
            </div>
            <input
              type="range"
              min="0"
              max="10"
              step="0.5"
              value={faasAlpha}
              onChange={(e) => onFaasAlphaChange(Number(e.target.value))}
              className="w-full accent-burgundy"
            />
            <p className="text-[10px] text-ivory-dark">
              Scaling multiplier on unserviced continuous wait time: (α × ContinuousWait).
            </p>
          </div>

          {/* Starvation Threshold */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="text-ivory font-medium">Starvation Threshold (T_starve)</span>
              <span className="font-mono text-rose-300 font-bold">{faasStarvationThreshold} units</span>
            </div>
            <input
              type="range"
              min="2"
              max="30"
              value={faasStarvationThreshold}
              onChange={(e) => onFaasThresholdChange(Number(e.target.value))}
              className="w-full accent-burgundy"
            />
            <p className="text-[10px] text-ivory-dark">
              Hard threshold triggering emergency execution override if wait exceeds this limit.
            </p>
          </div>
        </div>
      </div>

      {/* Big Action Run Button */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 card-panel border border-borderDark rounded-lg">
        <div className="text-xs text-ivory-dark">
          {processes.length === 0 ? (
            <span className="text-red-400">⚠️ No processes available. Add processes in Process Input first.</span>
          ) : (
            <span>
              Ready to execute across <strong className="text-white font-mono">{processes.length}</strong> processes with{' '}
              <strong className="text-white font-mono">{Object.values(selectedAlgorithms).filter(Boolean).length}</strong>{' '}
              algorithms.
            </span>
          )}
        </div>

        <button
          onClick={onRunSimulation}
          disabled={isRunning || processes.length === 0}
          className="w-full sm:w-auto px-8 py-3 bg-gradient-to-r from-burgundy-dark via-burgundy to-burgundy-soft hover:brightness-125 disabled:opacity-40 text-white font-bold text-sm rounded shadow-lg transition-all flex items-center justify-center space-x-2 border border-rose-500/40"
        >
          {isRunning ? (
            <>
              <span className="animate-spin text-lg">⚙️</span>
              <span>Executing Schedulers...</span>
            </>
          ) : (
            <>
              <span>▶ RUN SIMULATION</span>
            </>
          )}
        </button>
      </div>

      {/* Quick Navigation Cards if Simulation Results Exist */}
      {simulationResults && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
          <button
            onClick={() => onNavigateToTab('Gantt Charts')}
            className="p-4 bg-panel hover:bg-[#141414] border border-borderDark rounded-lg text-left transition-colors group"
          >
            <div className="text-xs text-ivory-dark group-hover:text-white">View Timelines</div>
            <div className="text-sm font-bold text-ivory mt-0.5">📊 Inspect Gantt Charts →</div>
          </button>
          <button
            onClick={() => onNavigateToTab('Performance Metrics')}
            className="p-4 bg-panel hover:bg-[#141414] border border-borderDark rounded-lg text-left transition-colors group"
          >
            <div className="text-xs text-ivory-dark group-hover:text-white">Review Numbers</div>
            <div className="text-sm font-bold text-ivory mt-0.5">📈 Performance Metrics →</div>
          </button>
          <button
            onClick={() => onNavigateToTab('FAAS Inspector')}
            className="p-4 bg-panel hover:bg-[#141414] border border-borderBurgundy rounded-lg text-left transition-colors group"
          >
            <div className="text-xs text-rose-300 group-hover:text-white">Decision Transparency</div>
            <div className="text-sm font-bold text-ivory mt-0.5">🔬 FAAS Step Inspector →</div>
          </button>
        </div>
      )}
    </div>
  );
};
