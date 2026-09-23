import { httpClient } from '../http-client';
import type { SearchParams, SearchResponse } from './types';

const search = async ({ query, limit }: SearchParams): Promise<SearchResponse> => {
  const response = await httpClient.get<SearchResponse>('/search', { params: { q: query, limit } });
  return response.data;
};

export const searchApi = {
  search,
};
