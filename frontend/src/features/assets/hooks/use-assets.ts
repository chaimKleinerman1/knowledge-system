import { useQuery } from '@tanstack/react-query';

import { type AssetListResponse, assetsApi, assetsQueryKeys } from '@/shared/api/assets';
import { ASSET_LIST_LIMIT, PROCESSING_POLL_MS } from '@/shared/lib/constants';

import { isStuckProcessing } from '../asset-status';

const LIST_PARAMS = { limit: ASSET_LIST_LIMIT, offset: 0 };

// A stuck asset will not change on its own, so it must not keep the list polling forever.
const hasProcessingAsset = (data: AssetListResponse | undefined): boolean =>
  data?.items.some(asset => asset.status === 'processing' && !isStuckProcessing(asset)) ?? false;

export const useAssets = () =>
  useQuery({
    queryKey: assetsQueryKeys.list(LIST_PARAMS),
    queryFn: () => assetsApi.list(LIST_PARAMS),
    // A file uploaded from another tab shows as "processing" here until its analysis finishes.
    refetchInterval: query => (hasProcessingAsset(query.state.data) ? PROCESSING_POLL_MS : false),
  });
