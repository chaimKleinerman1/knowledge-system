import type { AssetResponse } from '../assets/types';

export type MatchedBy = 'keyword' | 'semantic';

export interface SearchHit extends AssetResponse {
  matched_by: MatchedBy[];
  score: number;
}

export interface SearchParams {
  query: string;
  limit?: number;
}

export interface SearchResponse {
  query: string;
  items: SearchHit[];
}
