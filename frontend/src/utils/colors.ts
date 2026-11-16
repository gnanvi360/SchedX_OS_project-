export const ALGORITHM_COLORS: Record<string, string> = {
  SJF: '#4CC9F0',
  SRTF: '#F72585',
  HRRN: '#7209B7',
  FAAS: '#853B47',
};

const PROCESS_PALETTE = [
  '#4361EE', // Royal Blue
  '#3A0CA3', // Deep Indigo
  '#7209B7', // Purple
  '#F72585', // Rose Magenta
  '#4CC9F0', // Vivid Cyan
  '#06D6A0', // Emerald Green
  '#FFD166', // Amber Gold
  '#EF476F', // Coral Red
  '#118AB2', // Ocean Teal
  '#8338EC', // Bright Violet
  '#FB5607', // Neon Orange
  '#FF006E', // Hot Pink
];

export function buildProcessColorMap(pids: string[]): Record<string, string> {
  const map: Record<string, string> = {
    IDLE: '#333333',
  };
  pids.forEach((pid, index) => {
    map[pid] = PROCESS_PALETTE[index % PROCESS_PALETTE.length];
  });
  return map;
}
