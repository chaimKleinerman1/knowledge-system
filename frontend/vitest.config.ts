import path from 'node:path';

import { defineConfig } from 'vitest/config';

// Standalone on purpose: the app's vite.config.ts carries dev-server concerns (the API proxy)
// that a test run has no use for.
export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.{ts,tsx}'],
    setupFiles: ['./vitest.setup.ts'],
  },
});
