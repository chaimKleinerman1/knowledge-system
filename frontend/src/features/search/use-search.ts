import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { useAtomValue } from 'jotai';

import { searchApi, searchQueryKeys } from '@/shared/api/search';

import { searchQueryAtom } from './atoms';

export const useSearch = () => {
  const query = useAtomValue(searchQueryAtom).trim();
  const isActive = query.length > 0;

  const result = useQuery({
    queryKey: searchQueryKeys.list({ query }),
    queryFn: () => searchApi.search({ query }),
    enabled: isActive,
    // Keeps the previous hits on screen while the next query loads, so the grid does not flash.
    placeholderData: keepPreviousData,
  });

  return {
    query,
    isActive,
    hits: result.data?.items ?? [],
    hasResult: result.data !== undefined,
    isLoading: result.isLoading,
    isFetching: result.isFetching,
    error: result.error,
    refetch: result.refetch,
  };
};
