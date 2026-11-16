import React from 'react';
import { Process, SimulationResponse } from '../types';
import { ALGORITHM_COLORS } from '../utils/colors';

interface DashboardOverviewProps {
  processes: Process[];
  simulationResults: SimulationResponse | null;
  onNavigateToTab: (tab: string) => void;
}

export const DashboardOverview: React.FC<DashboardOverviewProps> = ({
  processes,
  simulationResults,
  onNavigateToTab,
}) => {
  const totalBurst = processes.reduce((acc, p) => acc + p.burst_time, 0);

  return (
    <div className="space-y-6">
      {/* Hero Banner */}
      <div className="card-panel-burgundy p-6 sm:p-8 border border-borderBurgundy rounded-xl relative overflow-hidden">
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="inline-block px-3 py-1 bg-burgundy/40 border border-burgundy rounded-full text-[11px] font-semibold text-rose-300 uppercase tracking-wider">
            Operating Systems Core Laboratory Platform
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight leading-tight">
            Advanced CPU Scheduling Simulator &amp; Benchmarking Engine
          </h1>
          <p className="text-xs sm:text-sm text-ivory-dark leading-relaxed">
            Comparative analysis of classical uniprocessor scheduling algorithms against our proposed{' '}
            <strong className="text-white">Fairness-Aware Adaptive Scheduling (FAAS)</strong> policy.
            Inspect execution timelines, turnaround benchmarks, dynamic waiting-time aging, and hard starvation prevention overrides.
          </p>

          <div className="pt-2 flex flex-wrap gap-3">
            <button
              onClick={() => onNavigateToTab('Process Input')}
              className="px-5 py-2.5 bg-burgundy hover:bg-burgundy-soft text-white text-xs font-bold rounded-lg border border-rose-500/40 shadow-lg transition-all"
            >
              Configure Workload &amp; Processes →
            </button>
            <button
              onClick={() => onNavigateToTab('Algorithm Scheduling')}
              className="px-5 py-2.5 bg-[#141414] hover:bg-[#1E1E1E] text-ivory text-xs font-semibold rounded-lg border border-borderDark transition-all"
            >
              Run Simulation Engine ▶
            </button>
          </div>
        </div>
      </div>

      {/* Live System Status Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card-panel p-4 border border-borderDark rounded-lg bg-panel">
          <div className="text-[11px] uppercase tracking-wider text-ivory-dark font-mono">Loaded Processes</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">{processes.length}</div>
          <div className="text-[11px] text-ivory-dark mt-0.5">Ready for simulation</div>
        </div>

        <div className="card-panel p-4 border border-borderDark rounded-lg bg-panel">
          <div className="text-[11px] uppercase tracking-wider text-ivory-dark font-mono">Total Workload</div>
          <div className="text-2xl font-bold font-mono text-cyan-400 mt-1">{totalBurst}</div>
          <div className="text-[11px] text-ivory-dark mt-0.5">Cumulative burst units</div>
        </div>

        <div className="card-panel p-4 border border-borderDark rounded-lg bg-panel">
          <div className="text-[11px] uppercase tracking-wider text-ivory-dark font-mono">Scheduler Policies</div>
          <div className="text-2xl font-bold font-mono text-rose-300 mt-1">4</div>
          <div className="text-[11px] text-ivory-dark mt-0.5">SJF, SRTF, HRRN, FAAS</div>
        </div>

        <div className="card-panel p-4 border border-borderDark rounded-lg bg-panel">
          <div className="text-[11px] uppercase tracking-wider text-ivory-dark font-mono">Starvation Guard</div>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">ACTIVE</div>
          <div className="text-[11px] text-ivory-dark mt-0.5">FAAS Hard Override Enabled</div>
        </div>
      </div>

      {/* Algorithm Feature Matrix Cards */}
      <div>
        <h3 className="text-sm font-bold uppercase tracking-wider text-ivory-dark mb-3">
          Implemented Scheduling Policies
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            {
              name: 'SJF',
              title: 'Shortest Job First',
              type: 'Non-Preemptive',
              advantage: 'Minimizes average wait time for simultaneous arrivals.',
              risk: 'High starvation risk for long-burst jobs.',
              color: ALGORITHM_COLORS.SJF,
            },
            {
              name: 'SRTF',
              title: 'Shortest Remaining Time',
              type: 'Preemptive',
              advantage: 'Theoretically optimal turnaround time.',
              risk: 'Severe starvation risk; high context switch overhead.',
              color: ALGORITHM_COLORS.SRTF,
            },
            {
              name: 'HRRN',
              title: 'Highest Response Ratio',
              type: 'Non-Preemptive with Aging',
              advantage: 'Eliminates starvation through waiting time aging.',
              risk: 'Non-preemptive blocking of urgent interactive jobs.',
              color: ALGORITHM_COLORS.HRRN,
            },
            {
              name: 'FAAS',
              title: 'Fairness-Aware Adaptive',
              type: 'Bounded Preemptive ($Q=2$)',
              advantage: 'Starvation-immune, bounded preemption, dynamic aging.',
              risk: 'Minor turnaround tradeoff for absolute fairness.',
              color: ALGORITHM_COLORS.FAAS,
            },
          ].map((alg) => (
            <div
              key={alg.name}
              className="card-panel p-4 border border-borderDark rounded-lg bg-panel flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono font-bold text-sm text-white" style={{ color: alg.color }}>
                    {alg.name}
                  </span>
                  <span className="text-[9px] px-1.5 py-0.5 bg-[#141414] border border-borderDark rounded font-mono text-ivory-dark">
                    {alg.type}
                  </span>
                </div>
                <h4 className="text-xs font-semibold text-ivory">{alg.title}</h4>
                <div className="mt-2.5 text-[11px] space-y-1 text-ivory-dark">
                  <div>
                    <span className="text-emerald-400 font-semibold">✓</span> {alg.advantage}
                  </div>
                  <div>
                    <span className="text-rose-400 font-semibold">⚠</span> {alg.risk}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Summary if simulation has already run */}
      {simulationResults && (
        <div className="card-panel p-5 border border-borderDark rounded-lg bg-panel">
          <div className="flex justify-between items-center mb-3 pb-2 border-b border-borderDark">
            <h4 className="text-sm font-semibold text-ivory">Simulation Cache Overview</h4>
            <span className="text-xs font-mono text-emerald-400">● Results Ready</span>
          </div>
          <p className="text-xs text-ivory-dark">
            Execution outputs for all 4 algorithms are currently in memory. You can inspect Gantt charts, process-level logs, comparative graphs, and the FAAS step inspector.
          </p>
          <div className="flex flex-wrap gap-2 pt-3">
            <button
              onClick={() => onNavigateToTab('Gantt Charts')}
              className="px-3 py-1.5 bg-[#141414] hover:bg-burgundy text-white text-xs rounded border border-borderDark font-medium transition-colors"
            >
              Inspect Gantt Charts
            </button>
            <button
              onClick={() => onNavigateToTab('Performance Metrics')}
              className="px-3 py-1.5 bg-[#141414] hover:bg-burgundy text-white text-xs rounded border border-borderDark font-medium transition-colors"
            >
              View Metrics
            </button>
            <button
              onClick={() => onNavigateToTab('FAAS Inspector')}
              className="px-3 py-1.5 bg-burgundy hover:bg-burgundy-soft text-white text-xs rounded border border-borderBurgundy font-medium transition-colors"
            >
              Open FAAS Inspector
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
