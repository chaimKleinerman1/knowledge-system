import { act, fireEvent, render, screen } from '@testing-library/react';
import { createStore, Provider } from 'jotai';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { SEARCH_DEBOUNCE_MS, SEARCH_PLACEHOLDER } from '@/shared/lib/constants';

import { searchQueryAtom } from './atoms';
import { SearchBar } from './SearchBar';

const renderSearchBar = (initialQuery = '') => {
  const store = createStore();
  store.set(searchQueryAtom, initialQuery);
  const view = render(
    <Provider store={store}>
      <SearchBar />
    </Provider>,
  );
  return { store, view, input: screen.getByPlaceholderText(SEARCH_PLACEHOLDER) };
};

const advanceTimers = (milliseconds: number) => {
  act(() => {
    vi.advanceTimersByTime(milliseconds);
  });
};

describe('SearchBar', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('commits the query only after the typing pause', () => {
    const { store, input } = renderSearchBar();

    fireEvent.change(input, { target: { value: 'black hair' } });
    expect(store.get(searchQueryAtom)).toBe('');

    advanceTimers(SEARCH_DEBOUNCE_MS - 1);
    expect(store.get(searchQueryAtom)).toBe('');

    advanceTimers(1);
    expect(store.get(searchQueryAtom)).toBe('black hair');
  });

  it('clearing the box resets the query', () => {
    const { store, view } = renderSearchBar('receipt');
    const clearButton = view.container.querySelector('.ant-input-clear-icon');
    expect(clearButton).not.toBeNull();

    fireEvent.click(clearButton as Element);
    advanceTimers(SEARCH_DEBOUNCE_MS);

    expect(store.get(searchQueryAtom)).toBe('');
  });
});
