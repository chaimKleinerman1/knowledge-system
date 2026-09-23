import { httpClient } from '../http-client';
import type { AssetListParams, AssetListResponse, AssetResponse } from './types';

export interface UploadOptions {
  /** Called with the share of bytes sent so far, from 0 to 1. */
  onUploadProgress?: (fractionSent: number) => void;
}

const assetPath = (id: string): string => `/assets/${encodeURIComponent(id)}`;

const list = async (params: AssetListParams = {}): Promise<AssetListResponse> => {
  const response = await httpClient.get<AssetListResponse>('/assets', { params });
  return response.data;
};

const getById = async (id: string): Promise<AssetResponse> => {
  const response = await httpClient.get<AssetResponse>(assetPath(id));
  return response.data;
};

const upload = async (file: File, options: UploadOptions = {}): Promise<AssetResponse> => {
  const formData = new FormData();
  formData.append('file', file, file.name);

  const response = await httpClient.post<AssetResponse>('/assets', formData, {
    onUploadProgress: event => {
      if (!options.onUploadProgress) {
        return;
      }
      const totalBytes = event.total ?? file.size;
      options.onUploadProgress(totalBytes > 0 ? Math.min(event.loaded / totalBytes, 1) : 1);
    },
  });
  return response.data;
};

const reprocess = async (id: string): Promise<AssetResponse> => {
  const response = await httpClient.post<AssetResponse>(`${assetPath(id)}/reprocess`);
  return response.data;
};

const deleteById = async (id: string): Promise<void> => {
  await httpClient.delete(assetPath(id));
};

export const assetsApi = {
  list,
  getById,
  upload,
  reprocess,
  deleteById,
};
