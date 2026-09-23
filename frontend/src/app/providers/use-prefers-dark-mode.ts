import { useSyncExternalStore } from 'react';

const DARK_MODE_QUERY = '(prefers-color-scheme: dark)';

const subscribe = (onChange: () => void): (() => void) => {
  const mediaQuery = window.matchMedia(DARK_MODE_QUERY);
  mediaQuery.addEventListener('change', onChange);
  return () => mediaQuery.removeEventListener('change', onChange);
};

const getSnapshot = (): boolean => window.matchMedia(DARK_MODE_QUERY).matches;

const getServerSnapshot = (): boolean => false;

export const usePrefersDarkMode = (): boolean => useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
