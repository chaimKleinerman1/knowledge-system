import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

// Testing Library only unmounts between tests on its own when `afterEach` is a global; vitest keeps it
// as an import, so the unmount is registered here.
afterEach(cleanup);

/**
 * Browser globals that Ant Design reads at render time and jsdom does not provide.
 * matchMedia drives responsive breakpoints; ResizeObserver backs overlays and lists.
 */
if (typeof window !== 'undefined') {
  if (!window.matchMedia) {
    window.matchMedia = ((query: string): MediaQueryList => {
      const minimum = query.match(/min-width:\s*(\d+(?:\.\d+)?)/);
      const maximum = query.match(/max-width:\s*(\d+(?:\.\d+)?)/);
      const viewportWidth = 1920;
      const matches =
        (!minimum || viewportWidth >= Number(minimum[1])) && (!maximum || viewportWidth <= Number(maximum[1]));
      return {
        matches,
        media: query,
        onchange: null,
        addEventListener: () => undefined,
        removeEventListener: () => undefined,
        addListener: () => undefined,
        removeListener: () => undefined,
        dispatchEvent: () => false,
      } as unknown as MediaQueryList;
    }) as typeof window.matchMedia;
  }

  if (!('ResizeObserver' in globalThis)) {
    class ResizeObserverStub {
      observe(): void {}
      unobserve(): void {}
      disconnect(): void {}
    }
    Object.defineProperty(globalThis, 'ResizeObserver', { value: ResizeObserverStub, configurable: true });
  }
}
