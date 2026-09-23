import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen } from '@testing-library/react';
import { App } from 'antd';
import { describe, expect, it } from 'vitest';

import { UNSUPPORTED_FILE_MESSAGE } from '@/shared/lib/constants';

import { UploadCard } from './UploadCard';

const renderUploadCard = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <App>
        <UploadCard />
      </App>
    </QueryClientProvider>,
  );

const dropFiles = (files: File[]) => {
  const dropZone = screen.getByText('Click or drag files here to upload');
  fireEvent.drop(dropZone, { dataTransfer: { files, items: [], types: ['Files'] } });
};

describe('UploadCard', () => {
  it('tells the user when a dropped file type is not supported', async () => {
    renderUploadCard();

    dropFiles([new File(['%PDF-1.7'], 'contract.pdf', { type: 'application/pdf' })]);

    expect(await screen.findByText(UNSUPPORTED_FILE_MESSAGE)).toBeTruthy();
  });
});
