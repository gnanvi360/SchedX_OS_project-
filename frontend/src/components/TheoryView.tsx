import React, { useState } from 'react';

export const TheoryView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'SJF' | 'SRTF' | 'HRRN' | 'FAAS' | 'VIVA'>('FAAS');

  const vivaQuestions = [
    {
      q: 'Why is SJF provably optimal for minimizing average waiting time?',
      a: 'When all processes arrive simultaneously, sorting bursts in non-decreasing order assigns the largest multiplier (n-1) to the shortest job, minimizing the overall sum of waiting times: W_total = Σ (n - i) * b_i.',
    },
    {
      q: 'What is the fundamental difference between SRTF and FAAS?',
      a: 'SRTF greedily prioritizes the shortest remaining burst time at every single tick without considering waiting duration, leading to indefinite starvation for long jobs. FAAS incorporates dynamic waiting-time aging (α × ContinuousWait) and enforces a hard starvation prevention threshold (T_starve), plus a bounded quantum Q=2 to avoid 1-tick context switch thrashing.',
    },
    {
      q: 'Why does FAAS track Continuous Waiting Time separately from Cumulative Waiting Time?',
      a: 'Continuous waiting time measures unserviced latency since the most recent CPU execution slice and resets to 0 upon dispatch to prevent processes from "gaming" the starvation threshold. Cumulative waiting time continuously accumulates total queue latency across the process life cycle for accurate system-wide metrics.',
    },
    {
      q: 'How does HRRN prevent starvation without preemption?',
      a: 'HRRN calculates the Response Ratio = (W + B) / B = 1 + (W / B). Even for very long jobs with large B, as waiting time W increases monotonically, the numerator grows until its response ratio surpasses newly arrived short jobs, naturally guaranteeing CPU service.',
    },
    {
      q: 'What is dispatch latency versus scheduling decision overhead?',
      a: 'The scheduler executes the algorithmic decision logic to pick the next candidate PID. The dispatcher is the kernel component that performs the physical context switch: saving CPU registers, switching to user mode, and jumping to the program counter location.',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div>
        <h2 className="text-xl font-bold text-ivory tracking-wide">Scheduling Theory &amp; Viva Preparation</h2>
        <p className="text-xs text-ivory-dark mt-1">
          Comprehensive reference guide on uniprocessor scheduling mechanics, mathematical formulations, and viva defense concepts.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-borderDark space-x-1">
        {(['FAAS', 'SJF', 'SRTF', 'HRRN', 'VIVA'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-xs font-mono font-semibold transition-all border-b-2 ${
              activeTab === tab
                ? 'border-burgundy text-white bg-[#0D0507]'
                : 'border-transparent text-ivory-dark hover:text-white'
            }`}
          >
            {tab === 'VIVA' ? '🎓 Viva Voce Q&A' : tab}
          </button>
        ))}
      </div>

      {/* Tab Contents */}
      {activeTab === 'FAAS' && (
        <div className="card-panel-burgundy p-6 border border-borderBurgundy rounded-lg space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-ivory">Fairness-Aware Adaptive Scheduling (FAAS)</h3>
            <span className="text-[10px] px-2.5 py-1 bg-burgundy rounded text-white font-mono font-semibold">
              Proposed Policy
            </span>
          </div>

          <p className="text-xs text-ivory leading-relaxed">
            FAAS is engineered to bridge the gap between the optimal turnaround efficiency of SRTF,
            the starvation immunity of HRRN, and the bounded preemption stability of Round Robin.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs pt-2">
            <div className="p-3.5 bg-[#050505] rounded border border-borderDark space-y-1.5">
              <div className="font-bold text-cyan-400 font-mono">1. Composite Priority Formula</div>
              <div className="font-mono text-[11px] bg-[#111111] p-2 rounded border border-borderDark text-ivory">
                Priority = (1 / RemainingTime) + (α × ContinuousWait)
              </div>
              <p className="text-ivory-dark text-[11px]">
                Reciprocal remaining time favors quick completion, while dynamic linear aging escalates waiting jobs.
              </p>
            </div>

            <div className="p-3.5 bg-[#050505] rounded border border-borderDark space-y-1.5">
              <div className="font-bold text-rose-300 font-mono">2. Hard Starvation Prevention</div>
              <div className="font-mono text-[11px] bg-[#111111] p-2 rounded border border-borderDark text-ivory">
                Trigger: ContinuousWaitingTime ≥ T_starve
              </div>
              <p className="text-ivory-dark text-[11px]">
                Bypasses standard priority competition and immediately dispatches the longest-starving job.
              </p>
            </div>

            <div className="p-3.5 bg-[#050505] rounded border border-borderDark space-y-1.5">
              <div className="font-bold text-emerald-400 font-mono">3. Continuous vs Cumulative Waiting</div>
              <p className="text-ivory-dark text-[11px] leading-relaxed">
                Continuous wait resets to 0 upon receiving CPU service to prevent processes from gaming the threshold, while cumulative wait tracks full queue lifetime.
              </p>
            </div>

            <div className="p-3.5 bg-[#050505] rounded border border-borderDark space-y-1.5">
              <div className="font-bold text-amber-400 font-mono">4. Bounded Service Quantum (Q=2)</div>
              <p className="text-ivory-dark text-[11px] leading-relaxed">
                Enforces a minimum guaranteed slice of min(Q, Remaining), preventing 1-tick preemption thrashing and cache degradation.
              </p>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'SJF' && (
        <div className="card-panel p-6 border border-borderDark rounded-lg space-y-4">
          <h3 className="text-base font-bold text-ivory">Shortest Job First (SJF) — Non-Preemptive</h3>
          <p className="text-xs text-ivory-dark leading-relaxed">
            Whenever the CPU becomes idle, the process with the smallest initial burst time among arrived processes is selected.
            Once dispatched, it executes to completion without interruption.
          </p>
          <div className="text-xs space-y-2 font-mono text-ivory">
            <div>• Selection Rule: argmin(BurstTime, ArrivalTime, PID)</div>
            <div>• Preemption: None (Non-Preemptive)</div>
            <div>• Starvation Vulnerability: High — continuous stream of short jobs starves long jobs.</div>
          </div>
        </div>
      )}

      {activeTab === 'SRTF' && (
        <div className="card-panel p-6 border border-borderDark rounded-lg space-y-4">
          <h3 className="text-base font-bold text-ivory">Shortest Remaining Time First (SRTF) — Preemptive</h3>
          <p className="text-xs text-ivory-dark leading-relaxed">
            The preemptive variant of SJF. Whenever a process arrives or finishes, the scheduler checks if any ready candidate has a strictly smaller remaining burst than the running process. If so, preemption occurs immediately.
          </p>
          <div className="text-xs space-y-2 font-mono text-ivory">
            <div>• Selection Rule: argmin(RemainingTime, ArrivalTime, PID)</div>
            <div>• Preemption: Continuous (at any arrival boundary)</div>
            <div>• Theoretical Optimality: Provably minimal average turnaround and waiting time.</div>
            <div>• Drawbacks: High context switches, cache invalidation, and severe starvation for long jobs.</div>
          </div>
        </div>
      )}

      {activeTab === 'HRRN' && (
        <div className="card-panel p-6 border border-borderDark rounded-lg space-y-4">
          <h3 className="text-base font-bold text-ivory">Highest Response Ratio Next (HRRN) — Non-Preemptive Aging</h3>
          <p className="text-xs text-ivory-dark leading-relaxed">
            Designed to mitigate SJF starvation without preemption. Considers both burst length and elapsed waiting time in the ready queue.
          </p>
          <div className="text-xs space-y-2 font-mono text-ivory">
            <div>• Response Ratio Formula: RR = (W + B) / B = 1 + (W / B)</div>
            <div>• Selection Rule: argmax(RR, -ArrivalTime, -PID)</div>
            <div>• Starvation Immunity: Guaranteed — older jobs accumulate high ratios.</div>
            <div>• Limitation: Non-preemptive nature means long jobs block urgent interactive tasks once started.</div>
          </div>
        </div>
      )}

      {activeTab === 'VIVA' && (
        <div className="space-y-4">
          <div className="card-panel p-4 border border-borderDark rounded-lg bg-panel">
            <h4 className="text-sm font-bold text-ivory mb-1">Operating Systems Laboratory Viva Voce Questions</h4>
            <p className="text-xs text-ivory-dark">
              Click on any question to inspect the concise academic answer.
            </p>
          </div>

          {vivaQuestions.map((item, idx) => (
            <div key={idx} className="card-panel p-4 border border-borderDark rounded-lg bg-[#0A0A0A] space-y-2">
              <div className="text-xs font-bold text-ivory flex items-start space-x-2">
                <span className="text-burgundy-soft font-mono">Q{idx + 1}.</span>
                <span>{item.q}</span>
              </div>
              <p className="text-xs text-ivory-dark pl-6 leading-relaxed bg-[#050505] p-3 rounded border border-borderDark/60">
                {item.a}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
