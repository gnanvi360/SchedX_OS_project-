import React, { useState } from 'react';
import { TimelineInterval } from '../types';

interface GanttChartProps {
  timeline: TimelineInterval[];
  title?: string;
  algorithmName?: string;
  colorMap: Record<string, string>;
  accentColor?: string;
}

export const GanttChart: React.FC<GanttChartProps> = ({
  timeline,
  title,
  algorithmName,
  colorMap,
  accentColor = '#853B47',
}) => {
  const [hoveredInterval, setHoveredInterval] = useState<TimelineInterval | null>(null);

  if (!timeline || timeline.length === 0) {
    return (
      <div className="card-panel p-6 text-center text-ivory-dark border border-borderDark">
        No execution timeline available. Run the simulation to view Gantt charts.
      </div>
    );
  }

  const totalTime = Math.max(...timeline.map((i) => i.end), 1);
  const minTime = Math.min(...timeline.map((i) => i.start), 0);
  const timeSpan = totalTime - minTime;

  // Generate tick marks (max ~15-20 ticks for legibility)
  const step = timeSpan > 40 ? 5 : timeSpan > 20 ? 2 : 1;
  const ticks = [];
  for (let t = 0; t <= totalTime; t += step) {
    ticks.push(t);
  }
  if (!ticks.includes(totalTime)) {
    ticks.push(totalTime);
  }

  return (
    <div className="card-panel p-5 border border-borderDark rounded-lg bg-panel">
      {/* Title & Algorithm Header */}
      <div className="flex items-center justify-between mb-4 pb-2 border-b border-borderDark">
        <div className="flex items-center space-x-3">
          <span
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: accentColor }}
          />
          <h3 className="text-base font-semibold text-ivory tracking-wide">
            {title || `${algorithmName} Execution Timeline`}
          </h3>
        </div>
        <span className="text-xs px-2.5 py-1 rounded bg-[#111111] border border-borderDark text-ivory-dark font-mono">
          Total Makespan: {totalTime} units
        </span>
      </div>

      {/* Hover Info Tooltip Bar */}
      <div className="h-8 mb-3 flex items-center justify-between text-xs px-3 bg-[#050505] rounded border border-borderDark font-mono">
        {hoveredInterval ? (
          <>
            <span className="text-ivory">
              Entity: <strong style={{ color: colorMap[hoveredInterval.pid] || '#FFFFFF' }}>{hoveredInterval.pid}</strong>
            </span>
            <span className="text-ivory-dark">
              Span: <span className="text-ivory">{hoveredInterval.start}</span> → <span className="text-ivory">{hoveredInterval.end}</span>
            </span>
            <span className="text-ivory-dark">
              Duration: <span className="text-ivory font-semibold">{hoveredInterval.end - hoveredInterval.start}</span> units
            </span>
            <span className="text-ivory-dark">
              Type: {hoveredInterval.pid === 'IDLE' ? '⚡ CPU Idle' : '⚙️ Process Service'}
            </span>
          </>
        ) : (
          <span className="text-ivory-dark text-[11px] italic">
            Hover over any execution block to inspect start, completion, and duration details.
          </span>
        )}
      </div>

      {/* Gantt Bar Visualization Container */}
      <div className="relative pt-1 pb-6 overflow-x-auto">
        <div className="min-w-[650px]">
          {/* Main Execution Track */}
          <div className="h-14 w-full flex bg-[#030303] rounded border border-borderDark overflow-hidden relative shadow-inner">
            {timeline.map((interval, idx) => {
              const widthPct = ((interval.end - interval.start) / timeSpan) * 100;
              const isIdle = interval.pid === 'IDLE';
              const blockColor = isIdle ? '#2A2A2A' : colorMap[interval.pid] || '#600D1A';

              return (
                <div
                  key={`${interval.pid}-${interval.start}-${idx}`}
                  style={{
                    width: `${widthPct}%`,
                    backgroundColor: blockColor,
                  }}
                  onMouseEnter={() => setHoveredInterval(interval)}
                  onMouseLeave={() => setHoveredInterval(null)}
                  className={`h-full relative group transition-all duration-150 cursor-pointer flex items-center justify-center border-r border-[#000000]/60 ${
                    isIdle
                      ? 'bg-diagonal-stripes opacity-75'
                      : 'hover:brightness-125'
                  }`}
                >
                  {/* Label inside bar if wide enough */}
                  <span
                    className={`font-mono text-xs font-bold truncate px-1 drop-shadow-md select-none ${
                      isIdle ? 'text-gray-400 text-[10px]' : 'text-white'
                    }`}
                  >
                    {interval.pid}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Time Axis & Ticks */}
          <div className="relative w-full h-7 mt-1.5 border-t border-[#333333]">
            {ticks.map((t) => {
              const leftPct = (t / timeSpan) * 100;
              return (
                <div
                  key={t}
                  style={{ left: `${leftPct}%` }}
                  className="absolute transform -translate-x-1/2 flex flex-col items-center"
                >
                  <div className="w-0.5 h-1.5 bg-[#555555]" />
                  <span className="text-[10px] text-ivory-dark font-mono mt-0.5 select-none">
                    {t}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Unique Process Badges Footer */}
      <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-borderDark text-xs">
        <span className="text-ivory-dark text-[11px] uppercase tracking-wider mr-1">Legend:</span>
        {Object.entries(colorMap)
          .filter(([pid]) => timeline.some((item) => item.pid === pid))
          .map(([pid, color]) => (
            <div
              key={pid}
              className="flex items-center space-x-1.5 px-2 py-0.5 rounded bg-[#111111] border border-borderDark"
            >
              <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: color }} />
              <span className="text-ivory font-mono text-[11px] font-medium">{pid}</span>
            </div>
          ))}
      </div>
    </div>
  );
};
