import { describe, expect, it } from 'vitest';

import { MAX_IMAGE_BYTES, MAX_TEXT_BYTES } from '@/shared/lib/constants';

import { isAcceptedFile, isFileTooBig } from './upload-limits';

const makeFile = (name: string, type: string, sizeBytes = 7): File =>
  new File([new Uint8Array(sizeBytes)], name, { type });

describe('upload limits', () => {
  it('accepts text files by extension and images by type', () => {
    expect(isAcceptedFile(makeFile('notes.txt', 'text/plain'))).toBe(true);
    expect(isAcceptedFile(makeFile('README.MD', ''))).toBe(true);
    expect(isAcceptedFile(makeFile('photo.jpg', 'image/jpeg'))).toBe(true);
    expect(isAcceptedFile(makeFile('contract.pdf', 'application/pdf'))).toBe(false);
    expect(isAcceptedFile(makeFile('photo.heic', 'image/heic'))).toBe(false);
  });

  it('applies the image limit to images and the text limit to everything else', () => {
    expect(isFileTooBig(makeFile('photo.png', 'image/png', MAX_IMAGE_BYTES))).toBe(false);
    expect(isFileTooBig(makeFile('photo.png', 'image/png', MAX_IMAGE_BYTES + 1))).toBe(true);
    expect(isFileTooBig(makeFile('notes.txt', 'text/plain', MAX_TEXT_BYTES))).toBe(false);
    expect(isFileTooBig(makeFile('notes.txt', 'text/plain', MAX_TEXT_BYTES + 1))).toBe(true);
  });
});
