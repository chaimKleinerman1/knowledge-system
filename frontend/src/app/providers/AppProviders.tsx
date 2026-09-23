import { QueryClientProvider } from '@tanstack/react-query';
import { App as AntdApp, ConfigProvider, theme } from 'antd';
import { Provider as JotaiProvider } from 'jotai';
import type { ReactNode } from 'react';

import { queryClient } from './query-client';
import { usePrefersDarkMode } from './use-prefers-dark-mode';

const ACCENT_COLOR = '#2f6fed';

interface AppProvidersProps {
  children: ReactNode;
}

export const AppProviders = ({ children }: AppProvidersProps) => {
  const prefersDarkMode = usePrefersDarkMode();

  return (
    <QueryClientProvider client={queryClient}>
      <JotaiProvider>
        <ConfigProvider
          theme={{
            algorithm: prefersDarkMode ? theme.darkAlgorithm : theme.defaultAlgorithm,
            token: { colorPrimary: ACCENT_COLOR, borderRadius: 8 },
          }}
        >
          <AntdApp>{children}</AntdApp>
        </ConfigProvider>
      </JotaiProvider>
    </QueryClientProvider>
  );
};
