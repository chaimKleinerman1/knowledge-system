import { skipToken, useQuery } from '@tanstack/react-query';

import { assetsApi, assetsQueryKeys } from '@/shared/api/assets';

export const useAsset = (assetId: string | null) =>
  useQuery({
    queryKey: assetsQueryKeys.detail(assetId ?? ''),
    queryFn: assetId ? () => assetsApi.getById(assetId) : skipToken,
  });
