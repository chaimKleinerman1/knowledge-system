import { describe, expect, it } from 'vitest';

import { isAcceptedFile } from './upload-limits';

const makeFile = (name: string, type: string): File => new File(['content'], name, { type });

describe('isAcceptedFile', () => {
  it.each([
    ['notes.txt', 'text/plain'],
    ['README.MD', ''],
    ['photo.jpg', 'image/jpeg'],
    ['photo.png', 'image/png'],
    ['photo.webp', 'image/webp'],
    ['animation.gif', 'image/gif'],
  ])('accepts %s', (name, type) => {
    expect(isAcceptedFile(makeFile(name, type))).toBe(true);
  });

  it.each([
    ['contract.pdf', 'application/pdf'],
    ['photo.heic', 'image/heic'],
    ['logo.svg', 'image/svg+xml'],
    ['folder', ''],
  ])('rejects %s', (name, type) => {
    expect(isAcceptedFile(makeFile(name, type))).toBe(false);
  });
});
