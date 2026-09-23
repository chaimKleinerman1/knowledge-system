import { useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';

import { assetsQueryKeys } from '@/shared/api/assets';
import { searchQueryKeys } from '@/shared/api/search';

/** Any change to a file can change the list and every search result, so both are refreshed together. */
export const useInvalidateAssets = () => {
  const queryClient = useQueryClient();

  return useCallback(
    () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: assetsQueryKeys.all }),
        queryClient.invalidateQueries({ queryKey: searchQueryKeys.all }),
      ]),
    [queryClient],
  );
};
