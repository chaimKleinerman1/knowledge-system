import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook } from '@testing-library/react';
import type { ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { type AssetResponse, assetsApi, assetsQueryKeys } from '@/shared/api/assets';

import { useReprocessAsset } from './use-reprocess-asset';

const failedTextAsset: AssetResponse = {
  id: 'asset-1',
  filename: 'hair_salon_notes.md',
  kind: 'text',
  mime_type: 'text/markdown',
  size_bytes: 2048,
  status: 'failed',
  error: 'The AI could not analyze this file.',
  created_at: '2026-09-23T08:00:00Z',
  updated_at: '2026-09-23T08:00:05Z',
  file_url: '/api/assets/asset-1/file',
  ai: null,
  extracted_text: 'Client notes: long black hair.',
  deduplicated: false,
};

describe('useReprocessAsset', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('leaves the detail cache to the refetch instead of the stripped reprocess response', async () => {
    const queryClient = new QueryClient();
    const detailKey = assetsQueryKeys.detail(failedTextAsset.id);
    queryClient.setQueryData(detailKey, failedTextAsset);
    vi.spyOn(assetsApi, 'reprocess').mockResolvedValue({
      ...failedTextAsset,
      status: 'ready',
      error: null,
      extracted_text: null,
    });
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
    const { result } = renderHook(() => useReprocessAsset(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync(failedTextAsset.id);
    });

    expect(queryClient.getQueryData<AssetResponse>(detailKey)?.extracted_text).toBe('Client notes: long black hair.');
    expect(queryClient.getQueryState(detailKey)?.isInvalidated).toBe(true);
  });
});
