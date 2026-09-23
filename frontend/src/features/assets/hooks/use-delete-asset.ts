import { useMutation, useQueryClient } from '@tanstack/react-query';

import { assetsApi, assetsQueryKeys } from '@/shared/api/assets';
import { searchQueryKeys } from '@/shared/api/search';

export const useDeleteAsset = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (assetId: string) => assetsApi.deleteById(assetId),
    onSuccess: async (_result, assetId) => {
      queryClient.removeQueries({ queryKey: assetsQueryKeys.detail(assetId) });
      // Only lists and searches are refreshed: the drawer is still open at this point, so invalidating
      // the detail scope would refetch the deleted file and get a 404.
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: assetsQueryKeys.lists() }),
        queryClient.invalidateQueries({ queryKey: searchQueryKeys.all }),
      ]);
    },
  });
};
