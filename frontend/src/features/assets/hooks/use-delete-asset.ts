import { useMutation, useQueryClient } from '@tanstack/react-query';

import { assetsApi, assetsQueryKeys } from '@/shared/api/assets';

import { useInvalidateAssets } from './use-invalidate-assets';

export const useDeleteAsset = () => {
  const queryClient = useQueryClient();
  const invalidateAssets = useInvalidateAssets();

  return useMutation({
    mutationFn: (assetId: string) => assetsApi.deleteById(assetId),
    onSuccess: async (_result, assetId) => {
      queryClient.removeQueries({ queryKey: assetsQueryKeys.detail(assetId) });
      await invalidateAssets();
    },
  });
};
