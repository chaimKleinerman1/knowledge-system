import { describe, expect, it } from 'vitest';

import type { AssetResponse } from '@/shared/api/assets';

import { isStuckProcessing, STUCK_PROCESSING_MS } from './asset-status';

const asset = (status: AssetResponse['status'], updatedAt: string): AssetResponse =>
  ({ status, updated_at: updatedAt }) as AssetResponse;

describe('isStuckProcessing', () => {
  const now = Date.parse('2026-09-23T12:00:00Z');

  it('is true only for a processing asset older than the stuck limit', () => {
    const old = new Date(now - STUCK_PROCESSING_MS - 1000).toISOString();
    const recent = new Date(now - 10_000).toISOString();
    expect(isStuckProcessing(asset('processing', old), now)).toBe(true);
    expect(isStuckProcessing(asset('processing', recent), now)).toBe(false);
  });

  it('is false for finished assets however old they are', () => {
    const old = new Date(now - 10 * STUCK_PROCESSING_MS).toISOString();
    expect(isStuckProcessing(asset('ready', old), now)).toBe(false);
    expect(isStuckProcessing(asset('failed', old), now)).toBe(false);
  });
});
