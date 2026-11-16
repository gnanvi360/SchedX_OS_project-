import React, { useState } from 'react';
import { SimulationResponse } from '../types';
import { ALGORITHM_COLORS } from '../utils/colors';

interface MetricsViewProps {
  simulationResults: SimulationResponse | null;
  onNavigateToTab: (tab: string) => void;
}

export const MetricsView: React.FC<MetricsViewProps> = ({
  simulationResults,
  onNavigateToTab,
}) => {
  if (!simulationResults || Object.keys(simulationResults.algorithms).length === 0) {
    return (
      <div className="card-panel p-8 text-center border border-borderDark rounded-lg space-y-3">
        <div className="text-3xl">📊</div>
        <h3 className="text-base font-bold text-ivory">No Simulation Metrics Available</h3>
        <p className="text-xs text-ivory-dark max-w-md mx-auto">
          Please run the simulation in &quot;Algorithm Scheduling&quot; to calculate turnaround times, waiting times, and CPU utilization.
        </p>
        <button
          onClick={() => onNavigateToTab('Algorithm Scheduling')}
          className="px-4 py-2 bg-burgundy hover:bg-burgundy-soft text-white text-xs font-semibold rounded border border-borderBurgundy transition-colors"
        >
          Go to Algorithm Scheduling
        </button>
      </div>
    );
  }

  const algorithms = Object.keys(simulationResults.algorithms);
  const [selectedAlg, setSelectedAlg] = useState<string>(algorithms[0] || 'SJF');

  const currentResult = simulationResults.algorithms[selectedAlg];
  if (!currentResult) return null;

  const m = currentResult.metrics;
  const algColor = ALGORITHM_COLORS[selectedAlg] || '#600D1A';

  // CSV Download Export Handler
  const handleDownloadCsv = () => {
    const headers = [
      'PID',
      'Arrival Time',
      'Burst Time',
      'Start Time',
      'Completion Time',
      'Turnaround Time',
      'Waiting Time',
      'Response Time',
    ];
    const rows = currentResult.processes.map((p) => [
      p.pid,
      p.arrival_time,
      p.burst_time,
      p.start_time ?? '',
      p.completion_time ?? '',
      p.turnaround_time ?? '',
      p.waiting_time ?? '',
      p.response_time ?? '',
    ]);

    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `${selectedAlg}_scheduling_metrics.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-wrap justify-between items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-ivory tracking-wide">Performance Metrics &amp; Process Details</h2>
          <p className="text-xs text-ivory-dark mt-1">
            Examine process-level scheduling outputs, response latencies, and system-wide utilization aggregates.
          </p>
        </div>

        {/* Algorithm Tabs */}
        <div className="flex items-center space-x-1.5 p-1 bg-[#0A0A0A] border border-borderDark rounded-lg">
          {algorithms.map((name) => (
            <button
              key={name}
              onClick={() => setSelectedAlg(name)}
              className={`px-3 py-1.5 rounded text-xs font-mono font-medium transition-all ${
                selectedAlg === name
                  ? 'bg-burgundy text-white shadow'
                  : 'text-ivory-dark hover:text-white hover:bg-[#141414]'
              }`}
            >
              {name}
            </button>
          ))}
        </div>
      </div>

      {/* Aggregate Metric Cards Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="card-panel p-4 text-center border border-borderDark rounded bg-[#0A0A0A]">
          <div className="text-[11px] uppercase tracking-wider text-ivory-dark">Avg Turnaround Time</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">
            {m.avg_turnaround_time.toFixed(2)}
          </div>
          <div className="text-[10px] text-ivory-dark mt-0.5">Completion - Arrival</div>
        </div>

        <div className="card-panel p-4 text-center border border-borderDark rounded bg-[#0A0A0A]">
          <div className="text-[11px] uppercase tracking-wider text-ivory-dark">Avg Waiting Time</div>
          <div className="text-2xl font-bold font-mono text-cyan-400 mt-1">
            {m.avg_waiting_time.toFixed(2)}
          </div>
          <div className="text-[10px] text-ivory-dark mt-0.5">Turnaround - Burst</div>
        </div>

        <div className="card-panel p-4 text-center border border-borderDark rounded bg-[#0A0A0A]">
          <div className="text-[11px] uppercase tracking-wider text-ivory-dark">Avg Response Time</div>
          <div className="text-2xl font-bold font-mono text-rose-300 mt-1">
            {m.avg_response_time.toFixed(2)}
          </div>
          <div className="text-[10px] text-ivory-dark mt-0.5">First Dispatch - Arrival</div>
        </div>

        <div className="card-panel p-4 text-center border border-borderDark rounded bg-[#0A0A0A]">
          <div className="text-[11px] uppercase tracking-wider text-ivory-dark">CPU Utilization</div>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
            {m.cpu_utilization.toFixed(1)}%
          </div>
          <div className="text-[10px] text-ivory-dark mt-0.5">Busy / (Busy + Idle)</div>
        </div>

        <div className="card-panel p-4 text-center border border-borderDark rounded bg-[#0A0A0A]">
          <div className="text-[11px] uppercase tracking-wider text-ivory-dark">Throughput</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">
            {m.throughput.toFixed(4)}
          </div>
          <div className="text-[10px] text-ivory-dark mt-0.5">Completed procs / unit</div>
        </div>

        <div className="card-panel p-4 text-center border border-borderDark rounded bg-[#0A0A0A]">
          <div className="text-[11px] uppercase tracking-wider text-ivory-dark">Context Switches</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">
            {m.context_switches}
          </div>
          <div className="text-[10px] text-ivory-dark mt-0.5">Process transitions</div>
        </div>

        <div className="card-panel p-4 text-center border border-borderDark rounded bg-[#0A0A0A]">
          <div className="text-[11px] uppercase tracking-wider text-ivory-dark">Preemptions</div>
          <div className="text-2xl font-bold font-mono text-rose-400 mt-1">
            {m.preemptions}
          </div>
          <div className="text-[10px] text-ivory-dark mt-0.5">Mid-burst yields</div>
        </div>

        <div className="card-panel p-4 text-center border border-borderDark rounded bg-[#0A0A0A]">
          <div className="text-[11px] uppercase tracking-wider text-ivory-dark">Total Makespan</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">
            {m.total_simulation_time}
          </div>
          <div className="text-[10px] text-ivory-dark mt-0.5">Total simulation ticks</div>
        </div>
      </div>

      {/* Process Level Metrics Table */}
      <div className="card-panel p-5 border border-borderDark rounded-lg bg-panel">
        <div className="flex flex-wrap justify-between items-center mb-3">
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: algColor }} />
            <h3 className="text-sm font-semibold text-ivory">
              Process-Level Execution Data ({selectedAlg})
            </h3>
          </div>
          <button
            onClick={handleDownloadCsv}
            className="px-3 py-1 bg-[#141414] hover:bg-burgundy border border-borderDark text-ivory text-xs rounded transition-colors font-mono"
          >
            📥 Export CSV
          </button>
        </div>

        <div className="overflow-x-auto border border-borderDark rounded">
          <table className="w-full text-xs text-left border-collapse">
            <thead>
              <tr className="bg-[#0A0A0A] border-b border-borderDark text-ivory-dark font-mono text-[11px]">
                <th className="py-2.5 px-3">PID</th>
                <th className="py-2.5 px-3">Arrival Time</th>
                <th className="py-2.5 px-3">Burst Time</th>
                <th className="py-2.5 px-3">Start Time</th>
                <th className="py-2.5 px-3">Completion Time</th>
                <th className="py-2.5 px-3">Turnaround Time</th>
                <th className="py-2.5 px-3">Waiting Time</th>
                <th className="py-2.5 px-3">Response Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-borderDark/60 font-mono">
              {currentResult.processes.map((p) => (
                <tr key={p.pid} className="hover:bg-[#141414] transition-colors text-ivory">
                  <td className="py-2 px-3 font-bold text-white">{p.pid}</td>
                  <td className="py-2 px-3">{p.arrival_time}</td>
                  <td className="py-2 px-3">{p.burst_time}</td>
                  <td className="py-2 px-3">{p.start_time ?? '—'}</td>
                  <td className="py-2 px-3 font-semibold text-cyan-300">{p.completion_time ?? '—'}</td>
                  <td className="py-2 px-3">{p.turnaround_time ?? '—'}</td>
                  <td className="py-2 px-3 text-rose-300">{p.waiting_time ?? '—'}</td>
                  <td className="py-2 px-3">{p.response_time ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
