import { useMutation } from '@tanstack/react-query';

import { assetsApi } from '@/shared/api/assets';

import { useInvalidateAssets } from './use-invalidate-assets';

/**
 * The reprocess response has the list shape (no text content), so it must not replace the detail
 * cache; the awaited refetch brings the full record back in one step.
 */
export const useReprocessAsset = () => {
  const invalidateAssets = useInvalidateAssets();

  return useMutation({
    mutationFn: (assetId: string) => assetsApi.reprocess(assetId),
    onSuccess: () => invalidateAssets(),
  });
};
