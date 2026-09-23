import { useCallback, useEffect, useMemo, useRef } from 'react';

type Timer = ReturnType<typeof setTimeout>;

/**
 * Delays `callback` until `delayMs` passes without a new call. The latest callback is always the
 * one that runs, so callers may pass an inline function.
 */
export const useDebouncedCallback = <Arguments extends unknown[]>(
  callback: (...args: Arguments) => void,
  delayMs: number,
) => {
  const callbackRef = useRef(callback);
  const timerRef = useRef<Timer | undefined>(undefined);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  const cancel = useCallback(() => {
    if (timerRef.current !== undefined) {
      clearTimeout(timerRef.current);
      timerRef.current = undefined;
    }
  }, []);

  const schedule = useCallback(
    (...args: Arguments) => {
      cancel();
      timerRef.current = setTimeout(() => {
        timerRef.current = undefined;
        callbackRef.current(...args);
      }, delayMs);
    },
    [cancel, delayMs],
  );

  useEffect(() => cancel, [cancel]);

  return useMemo(() => ({ schedule, cancel }), [schedule, cancel]);
};
