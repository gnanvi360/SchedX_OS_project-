export interface Process {
  pid: string;
  arrival_time: number;
  burst_time: number;
  start_time?: number;
  completion_time?: number;
  turnaround_time?: number;
  waiting_time?: number;
  response_time?: number;
}

export interface PerformanceMetrics {
  algorithm_name: string;
  process_count: number;
  total_simulation_time: number;
  total_busy_time: number;
  total_idle_time: number;
  cpu_utilization: number;
  throughput: number;
  avg_waiting_time: number;
  avg_turnaround_time: number;
  avg_response_time: number;
  max_waiting_time: number;
  max_turnaround_time: number;
  max_response_time: number;
  context_switches: number;
  preemptions: number;
}

export interface TimelineInterval {
  pid: string;
  start: number;
  end: number;
}

export interface AlgorithmResult {
  timeline: TimelineInterval[];
  processes: Process[];
  metrics: PerformanceMetrics;
  decision_log?: any[];
}

export interface SimulationResponse {
  algorithms: Record<string, AlgorithmResult>;
  comparison: Record<string, any>[];
}

export interface FAASCandidate {
  pid: string;
  remaining_time: number;
  continuous_waiting_time: number;
  remaining_priority: number;
  waiting_priority: number;
  final_score: number;
  is_starving: boolean;
  is_selected: boolean;
}

export interface FAASDecisionStep {
  step_index: number;
  clock: number;
  selected_pid: string;
  selected_priority: number;
  quantum_granted: number;
  starvation_override: boolean;
  reason: string;
  starvation_threshold: number;
  configured_quantum: number;
  alpha: number;
  candidates: FAASCandidate[];
  srtf_preferred_pid?: string;
  explanation: string;
}

export interface WorkloadSummary {
  total_processes: number;
  total_burst_time: number;
  avg_burst_time: number;
  avg_arrival_time: number;
  min_burst_time: number;
  max_burst_time: number;
  min_arrival_time: number;
  max_arrival_time: number;
}
