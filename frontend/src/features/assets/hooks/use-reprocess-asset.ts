import { useMutation, useQueryClient } from '@tanstack/react-query';

import { assetsApi, assetsQueryKeys } from '@/shared/api/assets';

import { useInvalidateAssets } from './use-invalidate-assets';

export const useReprocessAsset = () => {
  const queryClient = useQueryClient();
  const invalidateAssets = useInvalidateAssets();

  return useMutation({
    mutationFn: (assetId: string) => assetsApi.reprocess(assetId),
    onSuccess: async asset => {
      queryClient.setQueryData(assetsQueryKeys.detail(asset.id), asset);
      await invalidateAssets();
    },
  });
};
