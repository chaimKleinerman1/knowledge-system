import { useCallback, useEffect, useRef, useState } from 'react';

import { type AssetResponse, assetsApi } from '@/shared/api/assets';
import { getErrorMessage } from '@/shared/api/http-client';

import { useInvalidateAssets } from './use-invalidate-assets';

export type UploadPhase = 'queued' | 'uploading' | 'analyzing' | 'done' | 'failed';

export interface UploadJob {
  id: string;
  filename: string;
  phase: UploadPhase;
  /** The saved file, once the phase is "done". */
  asset?: AssetResponse;
  /** The server's explanation, once the phase is "failed". */
  errorMessage?: string;
}

type Timer = ReturnType<typeof setTimeout>;

const DONE_JOB_VISIBLE_MS = 8_000;

/**
 * Uploads files one request at a time, in the order they were added. The server analyses each file
 * inside the upload request, so a job moves to "analyzing" once its bytes have all been sent.
 */
export const useUploadQueue = () => {
  const [jobs, setJobs] = useState<UploadJob[]>([]);
  const chainRef = useRef<Promise<void>>(Promise.resolve());
  const timersRef = useRef<Set<Timer>>(new Set());
  const nextJobNumberRef = useRef(1);
  const invalidateAssets = useInvalidateAssets();

  const updateJob = useCallback((jobId: string, changes: Partial<UploadJob>) => {
    setJobs(current => current.map(job => (job.id === jobId ? { ...job, ...changes } : job)));
  }, []);

  const dismissJob = useCallback((jobId: string) => {
    setJobs(current => current.filter(job => job.id !== jobId));
  }, []);

  const dismissJobLater = useCallback(
    (jobId: string) => {
      const timers = timersRef.current;
      const timer = setTimeout(() => {
        timers.delete(timer);
        dismissJob(jobId);
      }, DONE_JOB_VISIBLE_MS);
      timers.add(timer);
    },
    [dismissJob],
  );

  const runJob = useCallback(
    async (jobId: string, file: File) => {
      updateJob(jobId, { phase: 'uploading' });
      try {
        const asset = await assetsApi.upload(file, {
          onUploadProgress: fractionSent => {
            if (fractionSent >= 1) {
              updateJob(jobId, { phase: 'analyzing' });
            }
          },
        });
        updateJob(jobId, { phase: 'done', asset });
        dismissJobLater(jobId);
        void invalidateAssets();
      } catch (error) {
        updateJob(jobId, { phase: 'failed', errorMessage: getErrorMessage(error) });
      }
    },
    [updateJob, dismissJobLater, invalidateAssets],
  );

  const enqueue = useCallback(
    (file: File) => {
      const jobId = `upload-${nextJobNumberRef.current}`;
      nextJobNumberRef.current += 1;
      setJobs(current => [...current, { id: jobId, filename: file.name, phase: 'queued' }]);
      chainRef.current = chainRef.current.then(() => runJob(jobId, file));
    },
    [runJob],
  );

  useEffect(() => {
    const timers = timersRef.current;
    return () => {
      timers.forEach(timer => clearTimeout(timer));
      timers.clear();
    };
  }, []);

  return { jobs, enqueue, dismissJob };
};
