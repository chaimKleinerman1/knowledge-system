import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';

import { assetsApi } from '@/shared/api/assets';

import { useInvalidateAssets } from './use-invalidate-assets';

/**
 * The server analyses the file inside the upload request, so once every byte has been sent the
 * wait is for the AI, not the network. `isAnalyzing` tells the two apart.
 */
export const useUploadAsset = () => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const invalidateAssets = useInvalidateAssets();

  const mutation = useMutation({
    mutationFn: (file: File) =>
      assetsApi.upload(file, { onUploadProgress: fractionSent => setIsAnalyzing(fractionSent >= 1) }),
    onMutate: () => setIsAnalyzing(false),
    onSuccess: () => invalidateAssets(),
  });

  return { ...mutation, isAnalyzing };
};
