import type { AssetResponse } from '@/shared/api/assets';

/** Longer than any normal analysis; a "processing" asset older than this was interrupted. */
export const STUCK_PROCESSING_MS = 2 * 60 * 1000;

/** True when an upload never finished its analysis, for example because the server restarted. */
export const isStuckProcessing = (asset: AssetResponse, now: number = Date.now()): boolean =>
  asset.status === 'processing' && now - new Date(asset.updated_at).getTime() > STUCK_PROCESSING_MS;
