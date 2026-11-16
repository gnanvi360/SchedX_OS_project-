import React, { useState, useEffect } from 'react';
import { Process, SimulationResponse, FAASDecisionStep } from './types';
import {
  checkBackendHealth,
  getPresets,
  getDistributions,
  runSimulationApi,
  fetchFaasInspectorApi,
} from './api';
import { buildProcessColorMap, ALGORITHM_COLORS } from './utils/colors';

import { DashboardOverview } from './components/DashboardOverview';
import { ProcessInputView } from './components/ProcessInputView';
import { AlgorithmSchedulingView } from './components/AlgorithmSchedulingView';
import { GanttChart } from './components/GanttChart';
import { MetricsView } from './components/MetricsView';
import { FaasInspector } from './components/FaasInspector';
import { ComparisonCharts } from './components/ComparisonCharts';
import { TheoryView } from './components/TheoryView';

// Top Horizontal Navigation Tabs
const TABS = [
  'Dashboard',
  'Process Input',
  'Algorithm Scheduling',
  'Gantt Charts',
  'Performance Metrics',
  'FAAS Inspector',
  'Comparison',
  'Viva & Theory',
];

export const App: React.FC = () => {
  // Navigation State
  const [currentTab, setCurrentTab] = useState<string>('Dashboard');

  // Backend Health State
  const [backendOnline, setBackendOnline] = useState<boolean>(false);

  // Process Dataset State (Default to academic benchmark dataset)
  const [processes, setProcesses] = useState<Process[]>([
    { pid: 'P1', arrival_time: 0, burst_time: 6 },
    { pid: 'P2', arrival_time: 1, burst_time: 2 },
    { pid: 'P3', arrival_time: 2, burst_time: 4 },
    { pid: 'P4', arrival_time: 4, burst_time: 3 },
  ]);

  // Presets and Distributions
  const [presets, setPresets] = useState<Record<string, Process[]>>({});
  const [distributions, setDistributions] = useState<string[]>([
    'Uniform Distribution',
    'Short-Job Heavy',
    'Long-Job Heavy',
    'Mixed Workload',
  ]);

  // Scheduling Configuration State
  const [selectedAlgorithms, setSelectedAlgorithms] = useState<Record<string, boolean>>({
    SJF: true,
    SRTF: true,
    HRRN: true,
    FAAS: true,
  });
  const [faasQuantum, setFaasQuantum] = useState<number>(2);
  const [faasAlpha, setFaasAlpha] = useState<number>(4.0);
  const [faasStarvationThreshold, setFaasStarvationThreshold] = useState<number>(8);

  // Simulation Results & State
  const [simulationResults, setSimulationResults] = useState<SimulationResponse | null>(null);
  const [faasSteps, setFaasSteps] = useState<FAASDecisionStep[]>([]);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [appError, setAppError] = useState<string | null>(null);

  // Gantt Chart View Mode (Stacked vs Individual Tabs)
  const [ganttViewMode, setGanttViewMode] = useState<'stacked' | 'tabs'>('stacked');
  const [activeGanttAlg, setActiveGanttAlg] = useState<string>('FAAS');

  // Load initial backend health and presets
  useEffect(() => {
    let mounted = true;

    const initBackend = async () => {
      const isHealthy = await checkBackendHealth();
      if (!mounted) return;
      setBackendOnline(isHealthy);

      if (isHealthy) {
        try {
          const [loadedPresets, loadedDists] = await Promise.all([
            getPresets(),
            getDistributions(),
          ]);
          if (mounted) {
            setPresets(loadedPresets);
            setDistributions(loadedDists);
          }
        } catch (e) {
          console.warn('Backend presets fetch error:', e);
        }
      }
    };

    initBackend();

    // Heartbeat ping every 10 seconds
    const interval = setInterval(async () => {
      const healthy = await checkBackendHealth();
      if (mounted) setBackendOnline(healthy);
    }, 10000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  // Algorithm Toggle
  const handleToggleAlgorithm = (algName: string) => {
    setSelectedAlgorithms((prev) => ({
      ...prev,
      [algName]: !prev[algName],
    }));
  };

  // Run Simulation Handler
  const handleRunSimulation = async () => {
    if (processes.length === 0) {
      setAppError('Please provide at least one process.');
      return;
    }

    setIsRunning(true);
    setAppError(null);

    try {
      // 1. Run simulation across all schedulers
      const simData = await runSimulationApi(
        processes,
        faasQuantum,
        faasAlpha,
        faasStarvationThreshold
      );
      setSimulationResults(simData);

      // 2. Fetch detailed FAAS decision inspector steps
      try {
        const steps = await fetchFaasInspectorApi(
          processes,
          faasQuantum,
          faasAlpha,
          faasStarvationThreshold
        );
        setFaasSteps(steps);
      } catch (err) {
        console.warn('FAAS steps load failed:', err);
      }

      // Automatically navigate to Gantt charts to inspect execution
      setCurrentTab('Gantt Charts');
    } catch (err: any) {
      setAppError(err.message || 'Simulation run failed');
    } finally {
      setIsRunning(false);
    }
  };

  // Build process color map
  const allPids = processes.map((p) => p.pid);
  const colorMap = buildProcessColorMap(allPids);

  return (
    <div className="min-h-screen bg-black text-ivory flex flex-col font-sans">
      {/* Top Header & Horizontal Navigation Bar */}
      <header className="border-b border-borderDark bg-[#060606] sticky top-0 z-50 shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
            {/* Title / Department Branding */}
            <div>
              <span className="text-[10px] text-burgundy-soft font-mono font-semibold uppercase tracking-widest block">
                Operating Systems Core Laboratory
              </span>
              <h1 className="text-lg sm:text-xl font-bold text-white tracking-tight">
                CPU Scheduling Simulator
              </h1>
            </div>

            {/* Backend Connection Status Badge */}
            <div className="flex items-center space-x-3 self-end md:self-auto">
              <div
                className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono border ${
                  backendOnline
                    ? 'bg-emerald-950/60 border-emerald-700/60 text-emerald-300'
                    : 'bg-red-950/60 border-red-700/60 text-red-300'
                }`}
              >
                <span
                  className={`w-2 h-2 rounded-full ${
                    backendOnline ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'
                  }`}
                />
                <span>{backendOnline ? 'API Connected' : 'Connecting to API...'}</span>
              </div>
            </div>
          </div>

          {/* Horizontal Navigation Tabs */}
          <nav className="mt-3 pt-2 border-t border-borderDark flex overflow-x-auto space-x-1 py-1 no-scrollbar">
            {TABS.map((tab) => {
              const isActive = currentTab === tab;
              return (
                <button
                  key={tab}
                  onClick={() => setCurrentTab(tab)}
                  className={`px-3.5 py-1.5 rounded text-xs font-medium whitespace-nowrap transition-all duration-150 ${
                    isActive
                      ? 'bg-burgundy text-white shadow-sm font-semibold border border-rose-500/30'
                      : 'text-ivory-dark hover:text-white hover:bg-[#141414]'
                  }`}
                >
                  {tab}
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Main View Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6">
        {/* Global Error Banner */}
        {appError && (
          <div className="mb-6 p-4 bg-red-950/80 border border-red-700 rounded-lg text-red-200 text-xs flex justify-between items-center">
            <span>⚠️ {appError}</span>
            <button
              onClick={() => setAppError(null)}
              className="text-red-400 hover:text-white font-bold ml-4"
            >
              ✕
            </button>
          </div>
        )}

        {/* Tab 1: Dashboard Overview */}
        {currentTab === 'Dashboard' && (
          <DashboardOverview
            processes={processes}
            simulationResults={simulationResults}
            onNavigateToTab={setCurrentTab}
          />
        )}

        {/* Tab 2: Process Input */}
        {currentTab === 'Process Input' && (
          <ProcessInputView
            processes={processes}
            onProcessesChange={setProcesses}
            presets={presets}
            distributions={distributions}
            onNavigateToRun={() => setCurrentTab('Algorithm Scheduling')}
          />
        )}

        {/* Tab 3: Algorithm Scheduling */}
        {currentTab === 'Algorithm Scheduling' && (
          <AlgorithmSchedulingView
            processes={processes}
            selectedAlgorithms={selectedAlgorithms}
            onToggleAlgorithm={handleToggleAlgorithm}
            faasQuantum={faasQuantum}
            onFaasQuantumChange={setFaasQuantum}
            faasAlpha={faasAlpha}
            onFaasAlphaChange={setFaasAlpha}
            faasStarvationThreshold={faasStarvationThreshold}
            onFaasThresholdChange={setFaasStarvationThreshold}
            isRunning={isRunning}
            onRunSimulation={handleRunSimulation}
            simulationResults={simulationResults}
            onNavigateToTab={setCurrentTab}
          />
        )}

        {/* Tab 4: Gantt Charts */}
        {currentTab === 'Gantt Charts' && (
          <div className="space-y-6">
            <div className="flex flex-wrap justify-between items-center gap-3">
              <div>
                <h2 className="text-xl font-bold text-ivory tracking-wide">
                  Execution Timelines (Gantt Charts)
                </h2>
                <p className="text-xs text-ivory-dark mt-1">
                  Visual representation of uniprocessor CPU allocation over elapsed simulation time.
                </p>
              </div>

              {simulationResults && Object.keys(simulationResults.algorithms).length > 0 && (
                <div className="flex items-center space-x-2 bg-[#0A0A0A] p-1 border border-borderDark rounded-lg text-xs">
                  <button
                    onClick={() => setGanttViewMode('stacked')}
                    className={`px-3 py-1 rounded transition-colors ${
                      ganttViewMode === 'stacked'
                        ? 'bg-burgundy text-white font-semibold'
                        : 'text-ivory-dark hover:text-white'
                    }`}
                  >
                    Compare All
                  </button>
                  <button
                    onClick={() => setGanttViewMode('tabs')}
                    className={`px-3 py-1 rounded transition-colors ${
                      ganttViewMode === 'tabs'
                        ? 'bg-burgundy text-white font-semibold'
                        : 'text-ivory-dark hover:text-white'
                    }`}
                  >
                    Individual Tabs
                  </button>
                </div>
              )}
            </div>

            {!simulationResults || Object.keys(simulationResults.algorithms).length === 0 ? (
              <div className="card-panel p-8 text-center border border-borderDark rounded-lg space-y-3">
                <div className="text-3xl">📊</div>
                <h3 className="text-base font-bold text-ivory">No Gantt Charts Generated Yet</h3>
                <p className="text-xs text-ivory-dark max-w-md mx-auto">
                  Run the simulation in &quot;Algorithm Scheduling&quot; to generate execution timelines.
                </p>
                <button
                  onClick={() => setCurrentTab('Algorithm Scheduling')}
                  className="px-4 py-2 bg-burgundy hover:bg-burgundy-soft text-white text-xs font-semibold rounded border border-borderBurgundy transition-colors"
                >
                  Go to Algorithm Scheduling
                </button>
              </div>
            ) : ganttViewMode === 'stacked' ? (
              <div className="space-y-5">
                {Object.entries(simulationResults.algorithms)
                  .filter(([name]) => selectedAlgorithms[name] ?? true)
                  .map(([name, algRes]) => (
                    <GanttChart
                      key={name}
                      timeline={algRes.timeline}
                      title={`${name} Execution Timeline`}
                      algorithmName={name}
                      colorMap={colorMap}
                      accentColor={ALGORITHM_COLORS[name]}
                    />
                  ))}
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex space-x-1 border-b border-borderDark pb-1">
                  {Object.keys(simulationResults.algorithms).map((name) => (
                    <button
                      key={name}
                      onClick={() => setActiveGanttAlg(name)}
                      className={`px-4 py-1.5 rounded text-xs font-mono font-medium transition-all ${
                        activeGanttAlg === name
                          ? 'bg-burgundy text-white shadow'
                          : 'text-ivory-dark hover:text-white'
                      }`}
                    >
                      {name}
                    </button>
                  ))}
                </div>

                {simulationResults.algorithms[activeGanttAlg] && (
                  <GanttChart
                    timeline={simulationResults.algorithms[activeGanttAlg].timeline}
                    title={`${activeGanttAlg} Execution Timeline`}
                    algorithmName={activeGanttAlg}
                    colorMap={colorMap}
                    accentColor={ALGORITHM_COLORS[activeGanttAlg]}
                  />
                )}
              </div>
            )}
          </div>
        )}

        {/* Tab 5: Performance Metrics */}
        {currentTab === 'Performance Metrics' && (
          <MetricsView
            simulationResults={simulationResults}
            onNavigateToTab={setCurrentTab}
          />
        )}

        {/* Tab 6: FAAS Inspector */}
        {currentTab === 'FAAS Inspector' && (
          <FaasInspector
            steps={faasSteps}
            onRerunRequested={() => setCurrentTab('Algorithm Scheduling')}
          />
        )}

        {/* Tab 7: Comparison */}
        {currentTab === 'Comparison' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-bold text-ivory tracking-wide">
                Cross-Algorithm Comparative Performance
              </h2>
              <p className="text-xs text-ivory-dark mt-1">
                Side-by-side performance benchmarks evaluated over identical process arrival sequences.
              </p>
            </div>

            {simulationResults && simulationResults.comparison.length > 0 ? (
              <ComparisonCharts comparisonData={simulationResults.comparison} />
            ) : (
              <div className="card-panel p-8 text-center border border-borderDark rounded-lg space-y-3">
                <div className="text-3xl">⚖️</div>
                <h3 className="text-base font-bold text-ivory">No Comparative Data Available</h3>
                <p className="text-xs text-ivory-dark max-w-md mx-auto">
                  Run the simulation across multiple algorithms to view side-by-side comparative charts.
                </p>
                <button
                  onClick={() => setCurrentTab('Algorithm Scheduling')}
                  className="px-4 py-2 bg-burgundy hover:bg-burgundy-soft text-white text-xs font-semibold rounded border border-borderBurgundy transition-colors"
                >
                  Go to Algorithm Scheduling
                </button>
              </div>
            )}
          </div>
        )}

        {/* Tab 8: Viva & Theory */}
        {currentTab === 'Viva & Theory' && <TheoryView />}
      </main>

      {/* Footer */}
      <footer className="border-t border-borderDark bg-[#050505] py-4 text-center text-xs text-ivory-dark font-mono">
        Operating Systems Laboratory • Uniprocessor CPU Scheduling Simulator • Academic Project
      </footer>
    </div>
  );
};

export default App;
