import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { AssetResponse } from '@/shared/api/assets';

import { AssetCard } from './AssetCard';

const readyTextAsset: AssetResponse = {
  id: 'asset-1',
  filename: 'hair_salon_notes.md',
  kind: 'text',
  mime_type: 'text/markdown',
  size_bytes: 2048,
  status: 'ready',
  error: null,
  created_at: '2026-09-23T08:00:00Z',
  updated_at: '2026-09-23T08:00:05Z',
  file_url: '/api/assets/asset-1/file',
  ai: {
    description: 'Notes from a hair salon about clients with black hair and their appointments.',
    tags: ['note', 'salon', 'hair', 'black hair', 'appointments', 'clients', 'schedule'],
    keywords: ['salon', 'haircut'],
    category: 'text_note',
    lang_code: 'en',
    text_content: null,
    text_truncated: false,
    model: 'fake',
    prompt_version: 'v1',
    processed_at: '2026-09-23T08:00:05Z',
  },
  extracted_text: null,
  deduplicated: false,
};

describe('AssetCard', () => {
  it('shows the filename, category, description and at most five tags', () => {
    render(
      <AssetCard
        asset={readyTextAsset}
        onOpen={vi.fn()}
      />,
    );

    expect(screen.getByText('hair_salon_notes.md')).toBeTruthy();
    expect(screen.getByText('Text note')).toBeTruthy();
    expect(screen.getByText(/Notes from a hair salon/)).toBeTruthy();
    expect(screen.getByText('appointments')).toBeTruthy();
    expect(screen.queryByText('clients')).toBeNull();
    expect(screen.getByText('+2')).toBeTruthy();
    expect(screen.queryByText('Failed')).toBeNull();
  });

  it('shows a failed badge when the analysis failed', () => {
    render(
      <AssetCard
        asset={{ ...readyTextAsset, status: 'failed', ai: null, error: 'The AI answer was cut off.' }}
        onOpen={vi.fn()}
      />,
    );

    expect(screen.getByText('Failed')).toBeTruthy();
  });
});
