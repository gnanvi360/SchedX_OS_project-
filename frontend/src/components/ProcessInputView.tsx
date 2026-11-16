import React, { useState } from 'react';
import { Process, WorkloadSummary } from '../types';
import { generateProcessesApi } from '../api';

interface ProcessInputViewProps {
  processes: Process[];
  onProcessesChange: (processes: Process[]) => void;
  presets: Record<string, Process[]>;
  distributions: string[];
  onNavigateToRun?: () => void;
}

export const ProcessInputView: React.FC<ProcessInputViewProps> = ({
  processes,
  onProcessesChange,
  presets,
  distributions,
  onNavigateToRun,
}) => {
  // Manual add form state
  const [newPid, setNewPid] = useState<string>(`P${processes.length + 1}`);
  const [newAt, setNewAt] = useState<number>(0);
  const [newBt, setNewBt] = useState<number>(4);
  const [inputError, setInputError] = useState<string | null>(null);

  // Generator form state
  const [genCount, setGenCount] = useState<number>(5);
  const [genMinAt, setGenMinAt] = useState<number>(0);
  const [genMaxAt, setGenMaxAt] = useState<number>(10);
  const [genMinBt, setGenMinBt] = useState<number>(1);
  const [genMaxBt, setGenMaxBt] = useState<number>(10);
  const [genDist, setGenDist] = useState<string>('Uniform Distribution');
  const [genSeed, setGenSeed] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [workloadSummary, setWorkloadSummary] = useState<WorkloadSummary | null>(null);

  // Manual Add Handler
  const handleAddProcess = (e: React.FormEvent) => {
    e.preventDefault();
    setInputError(null);

    const cleanPid = newPid.trim();
    if (!cleanPid) {
      setInputError('Process ID cannot be empty.');
      return;
    }
    if (processes.some((p) => p.pid === cleanPid)) {
      setInputError(`Process ID "${cleanPid}" already exists. PIDs must be unique.`);
      return;
    }
    if (newAt < 0) {
      setInputError('Arrival time must be ≥ 0.');
      return;
    }
    if (newBt <= 0) {
      setInputError('Burst time must be ≥ 1.');
      return;
    }

    const updated = [
      ...processes,
      { pid: cleanPid, arrival_time: newAt, burst_time: newBt },
    ];
    // Sort by arrival time for neat ordering
    updated.sort((a, b) => a.arrival_time - b.arrival_time);
    onProcessesChange(updated);

    // Auto-increment default next PID
    setNewPid(`P${updated.length + 1}`);
  };

  // Delete Process Handler
  const handleDeleteProcess = (pid: string) => {
    const updated = processes.filter((p) => p.pid !== pid);
    onProcessesChange(updated);
  };

  // Inline Cell Update
  const handleUpdateProcess = (index: number, field: 'arrival_time' | 'burst_time', val: number) => {
    const updated = [...processes];
    updated[index] = { ...updated[index], [field]: val };
    onProcessesChange(updated);
  };

  // Load Preset
  const handleLoadPreset = (presetName: string) => {
    if (presets[presetName]) {
      onProcessesChange(presets[presetName]);
      setWorkloadSummary(null);
    }
  };

  // Generator Call
  const handleGenerate = async () => {
    setIsGenerating(true);
    setInputError(null);
    try {
      const seedNum = genSeed.trim() !== '' ? Number(genSeed) : undefined;
      const res = await generateProcessesApi({
        num_processes: genCount,
        min_arrival: genMinAt,
        max_arrival: genMaxAt,
        min_burst: genMinBt,
        max_burst: genMaxBt,
        distribution: genDist,
        seed: seedNum,
      });
      onProcessesChange(res.processes);
      setWorkloadSummary(res.summary);
    } catch (err: any) {
      setInputError(err.message || 'Failed to generate random workload');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-ivory tracking-wide">Workload &amp; Process Input</h2>
          <p className="text-xs text-ivory-dark mt-1">
            Configure CPU scheduling tasks manually, load academic benchmark datasets, or generate synthetic workloads.
          </p>
        </div>
        {onNavigateToRun && (
          <button
            onClick={onNavigateToRun}
            disabled={processes.length === 0}
            className="px-4 py-2 bg-burgundy hover:bg-burgundy-soft disabled:opacity-40 text-white font-medium text-xs rounded border border-borderBurgundy transition-colors shadow-md"
          >
            Proceed to Algorithm Scheduling ▶
          </button>
        )}
      </div>

      {inputError && (
        <div className="p-3 bg-red-950/60 border border-red-700 text-red-200 text-xs rounded">
          ⚠️ {inputError}
        </div>
      )}

      {/* Preset Workload Buttons Row */}
      <div className="card-panel p-4 border border-borderDark rounded-lg bg-panel">
        <div className="text-xs font-semibold text-ivory-dark uppercase tracking-wider mb-2.5">
          Load Academic Benchmark Datasets:
        </div>
        <div className="flex flex-wrap gap-2">
          {Object.keys(presets).map((name) => (
            <button
              key={name}
              onClick={() => handleLoadPreset(name)}
              className="px-3 py-1.5 bg-[#141414] hover:bg-burgundy border border-borderDark hover:border-borderBurgundy text-ivory text-xs rounded transition-colors font-medium"
            >
              📋 {name}
            </button>
          ))}
          <button
            onClick={() => onProcessesChange([])}
            className="px-3 py-1.5 bg-[#18080A] hover:bg-red-900/60 border border-red-900/50 text-red-300 text-xs rounded transition-colors"
          >
            🗑 Clear All
          </button>
        </div>
      </div>

      {/* Main Grid: Process Table (Left) + Generator (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Process Table & Manual Input Form */}
        <div className="lg:col-span-7 space-y-4">
          <div className="card-panel p-5 border border-borderDark rounded-lg bg-panel">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-sm font-semibold text-ivory">Active Process Queue ({processes.length})</h3>
              <span className="text-xs text-ivory-dark font-mono">
                Total Workload: {processes.reduce((acc, p) => acc + p.burst_time, 0)} CPU ticks
              </span>
            </div>

            {/* Editable Table */}
            <div className="overflow-x-auto border border-borderDark rounded">
              <table className="w-full text-xs text-left border-collapse">
                <thead>
                  <tr className="bg-[#0A0A0A] border-b border-borderDark text-ivory-dark font-mono text-[11px]">
                    <th className="py-2.5 px-3">PID</th>
                    <th className="py-2.5 px-3">Arrival Time (AT)</th>
                    <th className="py-2.5 px-3">Burst Time (BT)</th>
                    <th className="py-2.5 px-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-borderDark/60 font-mono">
                  {processes.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="py-6 text-center text-ivory-dark text-xs italic">
                        No processes loaded. Add one below or load a preset.
                      </td>
                    </tr>
                  ) : (
                    processes.map((p, idx) => (
                      <tr key={p.pid} className="hover:bg-[#141414] transition-colors">
                        <td className="py-2 px-3 font-bold text-white">{p.pid}</td>
                        <td className="py-2 px-3">
                          <input
                            type="number"
                            min="0"
                            value={p.arrival_time}
                            onChange={(e) =>
                              handleUpdateProcess(idx, 'arrival_time', Math.max(0, Number(e.target.value)))
                            }
                            className="w-20 px-2 py-1 bg-[#050505] border border-borderDark rounded text-ivory text-xs font-mono focus:outline-none focus:border-burgundy"
                          />
                        </td>
                        <td className="py-2 px-3">
                          <input
                            type="number"
                            min="1"
                            value={p.burst_time}
                            onChange={(e) =>
                              handleUpdateProcess(idx, 'burst_time', Math.max(1, Number(e.target.value)))
                            }
                            className="w-20 px-2 py-1 bg-[#050505] border border-borderDark rounded text-ivory text-xs font-mono focus:outline-none focus:border-burgundy"
                          />
                        </td>
                        <td className="py-2 px-3 text-right">
                          <button
                            onClick={() => handleDeleteProcess(p.pid)}
                            className="px-2 py-1 bg-[#1A0A0C] hover:bg-red-900/60 border border-red-950 text-red-300 text-[11px] rounded transition-colors"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Quick Add Form */}
            <form onSubmit={handleAddProcess} className="mt-4 pt-3 border-t border-borderDark flex flex-wrap items-end gap-3">
              <div className="w-24">
                <label className="block text-[10px] text-ivory-dark uppercase font-semibold mb-1">PID</label>
                <input
                  type="text"
                  value={newPid}
                  onChange={(e) => setNewPid(e.target.value)}
                  className="w-full px-2.5 py-1.5 bg-[#050505] border border-borderDark rounded text-ivory text-xs font-mono focus:outline-none focus:border-burgundy"
                  placeholder="P1"
                />
              </div>
              <div className="w-28">
                <label className="block text-[10px] text-ivory-dark uppercase font-semibold mb-1">Arrival Time</label>
                <input
                  type="number"
                  min="0"
                  value={newAt}
                  onChange={(e) => setNewAt(Math.max(0, Number(e.target.value)))}
                  className="w-full px-2.5 py-1.5 bg-[#050505] border border-borderDark rounded text-ivory text-xs font-mono focus:outline-none focus:border-burgundy"
                />
              </div>
              <div className="w-28">
                <label className="block text-[10px] text-ivory-dark uppercase font-semibold mb-1">Burst Time</label>
                <input
                  type="number"
                  min="1"
                  value={newBt}
                  onChange={(e) => setNewBt(Math.max(1, Number(e.target.value)))}
                  className="w-full px-2.5 py-1.5 bg-[#050505] border border-borderDark rounded text-ivory text-xs font-mono focus:outline-none focus:border-burgundy"
                />
              </div>
              <button
                type="submit"
                className="px-4 py-1.5 bg-[#141414] hover:bg-burgundy border border-borderDark hover:border-borderBurgundy text-white text-xs font-semibold rounded transition-colors"
              >
                + Add Process
              </button>
            </form>
          </div>
        </div>

        {/* Right Column: Random Workload Generator */}
        <div className="lg:col-span-5 space-y-4">
          <div className="card-panel-burgundy p-5 border border-borderBurgundy rounded-lg">
            <h3 className="text-sm font-semibold text-ivory mb-1 flex items-center space-x-2">
              <span>🎲 Random Process Generator</span>
            </h3>
            <p className="text-[11px] text-ivory-dark mb-4">
              Synthesize realistic process arrival and burst distributions for stress-testing.
            </p>

            <div className="space-y-3.5 text-xs">
              <div>
                <label className="block text-ivory-dark mb-1">Number of Processes ({genCount})</label>
                <input
                  type="range"
                  min="1"
                  max="50"
                  value={genCount}
                  onChange={(e) => setGenCount(Number(e.target.value))}
                  className="w-full accent-burgundy"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-ivory-dark mb-1">Min Arrival</label>
                  <input
                    type="number"
                    min="0"
                    value={genMinAt}
                    onChange={(e) => setGenMinAt(Number(e.target.value))}
                    className="w-full px-2 py-1 bg-[#050505] border border-borderDark rounded text-ivory font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="block text-ivory-dark mb-1">Max Arrival</label>
                  <input
                    type="number"
                    min="0"
                    value={genMaxAt}
                    onChange={(e) => setGenMaxAt(Number(e.target.value))}
                    className="w-full px-2 py-1 bg-[#050505] border border-borderDark rounded text-ivory font-mono text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-ivory-dark mb-1">Min Burst</label>
                  <input
                    type="number"
                    min="1"
                    value={genMinBt}
                    onChange={(e) => setGenMinBt(Number(e.target.value))}
                    className="w-full px-2 py-1 bg-[#050505] border border-borderDark rounded text-ivory font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="block text-ivory-dark mb-1">Max Burst</label>
                  <input
                    type="number"
                    min="1"
                    value={genMaxBt}
                    onChange={(e) => setGenMaxBt(Number(e.target.value))}
                    className="w-full px-2 py-1 bg-[#050505] border border-borderDark rounded text-ivory font-mono text-xs"
                  />
                </div>
              </div>

              <div>
                <label className="block text-ivory-dark mb-1">Distribution Preset</label>
                <select
                  value={genDist}
                  onChange={(e) => setGenDist(e.target.value)}
                  className="w-full px-2.5 py-1.5 bg-[#050505] border border-borderDark rounded text-ivory text-xs"
                >
                  {distributions.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-ivory-dark mb-1">Random Seed (Optional Reproducibility)</label>
                <input
                  type="text"
                  value={genSeed}
                  onChange={(e) => setGenSeed(e.target.value)}
                  placeholder="e.g. 42"
                  className="w-full px-2.5 py-1 bg-[#050505] border border-borderDark rounded text-ivory text-xs font-mono"
                />
              </div>

              <button
                onClick={handleGenerate}
                disabled={isGenerating}
                className="w-full py-2 bg-burgundy hover:bg-burgundy-soft disabled:opacity-50 text-white font-semibold rounded text-xs transition-colors shadow"
              >
                {isGenerating ? 'Generating Workload...' : '⚡ Generate Workload'}
              </button>
            </div>

            {/* Generated Summary Statistics */}
            {workloadSummary && (
              <div className="mt-4 pt-3 border-t border-borderBurgundy/60 text-[11px] font-mono text-ivory-dark space-y-1">
                <div className="text-ivory font-bold mb-1">Workload Profile:</div>
                <div>Total Burst: {workloadSummary.total_burst_time} units</div>
                <div>Avg Burst: {workloadSummary.avg_burst_time} units</div>
                <div>Avg Arrival: {workloadSummary.avg_arrival_time} units</div>
                <div>Burst Range: [{workloadSummary.min_burst_time}, {workloadSummary.max_burst_time}]</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
