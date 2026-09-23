import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { EmptyState } from './EmptyState';

describe('EmptyState', () => {
  it('shows the title and the hint', () => {
    render(
      <EmptyState
        title="No results for “black hair”."
        hint="Try other words."
      />,
    );

    expect(screen.getByText('No results for “black hair”.')).toBeTruthy();
    expect(screen.getByText('Try other words.')).toBeTruthy();
  });

  it('shows the title alone when there is no hint', () => {
    render(<EmptyState title="Upload your first file to start" />);

    expect(screen.getByText('Upload your first file to start')).toBeTruthy();
    expect(screen.queryByText('Try other words.')).toBeNull();
  });
});
