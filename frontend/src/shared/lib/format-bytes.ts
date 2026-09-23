const UNITS = ['B', 'KB', 'MB', 'GB'] as const;

export const formatBytes = (bytes: number): string => {
  if (!Number.isFinite(bytes) || bytes < 0) {
    return '0 B';
  }
  let value = bytes;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < UNITS.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  const fractionDigits = unitIndex > 0 && value < 10 ? 1 : 0;
  return `${value.toFixed(fractionDigits)} ${UNITS[unitIndex]}`;
};
