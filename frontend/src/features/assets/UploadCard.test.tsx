import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen } from '@testing-library/react';
import { App } from 'antd';
import { describe, expect, it } from 'vitest';

import { FILE_TOO_BIG_MESSAGE, MAX_TEXT_BYTES, UNSUPPORTED_FILE_MESSAGE } from '@/shared/lib/constants';

import { UploadCard } from './UploadCard';

const renderUploadCard = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <App>
        <UploadCard />
      </App>
    </QueryClientProvider>,
  );

describe('UploadCard', () => {
  it('tells the user when a dropped file type is not supported', async () => {
    renderUploadCard();
    const dropZone = screen.getByText('Click or drag a file here to upload');

    fireEvent.drop(dropZone, {
      dataTransfer: { files: [new File(['%PDF-1.7'], 'contract.pdf', { type: 'application/pdf' })], types: ['Files'] },
    });

    expect(await screen.findByText(UNSUPPORTED_FILE_MESSAGE)).toBeTruthy();
  });

  it('rejects a file above the size limit before sending it', async () => {
    const view = renderUploadCard();
    const fileInput = view.container.querySelector('input[type="file"]') as HTMLInputElement;
    const tooBigFile = new File([new Uint8Array(MAX_TEXT_BYTES + 1)], 'big.txt', { type: 'text/plain' });

    fireEvent.change(fileInput, { target: { files: [tooBigFile] } });

    expect(await screen.findByText(FILE_TOO_BIG_MESSAGE)).toBeTruthy();
  });
});
