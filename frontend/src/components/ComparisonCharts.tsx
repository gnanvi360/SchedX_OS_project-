import React from 'react';
import { ALGORITHM_COLORS } from '../utils/colors';

interface ComparisonChartsProps {
  comparisonData: Record<string, any>[];
}

interface SingleMetricBarProps {
  title: string;
  metricKey: string;
  data: Record<string, any>[];
  unit?: string;
  lowerIsBetter?: boolean;
}

const SingleMetricBar: React.FC<SingleMetricBarProps> = ({
  title,
  metricKey,
  data,
  unit = '',
  lowerIsBetter = true,
}) => {
  if (!data || data.length === 0) return null;

  const values = data.map((d) => Number(d[metricKey]) || 0);
  const maxVal = Math.max(...values, 1);

  // Find best value
  let bestVal = lowerIsBetter ? Math.min(...values) : Math.max(...values);

  return (
    <div className="card-panel p-4 border border-borderDark rounded-lg bg-panel">
      <div className="flex justify-between items-center mb-3">
        <h4 className="text-sm font-semibold text-ivory tracking-wide">{title}</h4>
        <span className="text-[11px] text-ivory-dark font-mono">
          {lowerIsBetter ? '↓ Lower is better' : '↑ Higher is better'}
        </span>
      </div>

      <div className="space-y-3">
        {data.map((item) => {
          const val = Number(item[metricKey]) || 0;
          const widthPct = Math.max((val / maxVal) * 100, 3);
          const algName = item['Algorithm'] || item['algorithm_name'];
          const isBest = val === bestVal;
          const barColor = ALGORITHM_COLORS[algName] || '#600D1A';

          return (
            <div key={algName} className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="flex items-center space-x-1.5 font-medium">
                  <span
                    className="w-2.5 h-2.5 rounded-sm inline-block"
                    style={{ backgroundColor: barColor }}
                  />
                  <span className="text-ivory font-mono">{algName}</span>
                  {isBest && (
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-burgundy/40 text-rose-300 font-sans border border-burgundy">
                      ★ Best
                    </span>
                  )}
                </span>
                <span className="font-mono text-ivory font-semibold">
                  {typeof val === 'number' ? (Number.isInteger(val) ? val : val.toFixed(2)) : val} {unit}
                </span>
              </div>

              {/* Bar track */}
              <div className="h-4 w-full bg-[#111111] rounded overflow-hidden p-0.5 border border-borderDark/70">
                <div
                  style={{
                    width: `${widthPct}%`,
                    backgroundColor: barColor,
                  }}
                  className={`h-full rounded-sm transition-all duration-300 ${
                    isBest ? 'brightness-125 shadow-sm' : 'opacity-85'
                  }`}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export const ComparisonCharts: React.FC<ComparisonChartsProps> = ({ comparisonData }) => {
  if (!comparisonData || comparisonData.length === 0) {
    return (
      <div className="card-panel p-6 text-center text-ivory-dark border border-borderDark">
        No comparative simulation results available. Run the simulation to compare algorithms.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <SingleMetricBar
          title="Average Waiting Time"
          metricKey="Avg Waiting Time"
          data={comparisonData}
          unit="units"
          lowerIsBetter={true}
        />
        <SingleMetricBar
          title="Average Turnaround Time"
          metricKey="Avg Turnaround Time"
          data={comparisonData}
          unit="units"
          lowerIsBetter={true}
        />
        <SingleMetricBar
          title="Average Response Time"
          metricKey="Avg Response Time"
          data={comparisonData}
          unit="units"
          lowerIsBetter={true}
        />
        <SingleMetricBar
          title="CPU Utilization"
          metricKey="CPU Utilization (%)"
          data={comparisonData}
          unit="%"
          lowerIsBetter={false}
        />
        <SingleMetricBar
          title="Throughput"
          metricKey="Throughput"
          data={comparisonData}
          unit="proc/unit"
          lowerIsBetter={false}
        />
        <SingleMetricBar
          title="Context Switches"
          metricKey="Context Switches"
          data={comparisonData}
          unit="switches"
          lowerIsBetter={true}
        />
      </div>

      {/* Analytical Workload Summary Card */}
      <div className="card-panel-burgundy p-5 border border-borderBurgundy rounded-lg">
        <h4 className="text-sm font-bold uppercase tracking-wider text-ivory mb-2 flex items-center space-x-2">
          <span>⚖️ Workload Performance & Trade-Off Analysis</span>
        </h4>
        <p className="text-xs text-ivory-dark leading-relaxed">
          <strong>Operating Systems Insight:</strong> No single scheduling policy dominates across all workload distributions.
          While <strong>SRTF</strong> minimizes average turnaround time and waiting time by greedily prioritizing shorter jobs,
          it imposes higher context-switching overhead and exposes long-burst jobs to severe starvation.
          <strong>HRRN</strong> prevents starvation non-preemptively, but cannot adapt mid-execution.
          <strong>FAAS</strong> successfully unifies the rapid dispatch of short jobs with dynamic aging and hard starvation prevention guarantees.
        </p>
      </div>
    </div>
  );
};
