import { MAX_IMAGE_BYTES, MAX_TEXT_BYTES } from '@/shared/lib/constants';

/** Mirrors the server limits so an oversize file is rejected before any bytes are sent. */
export const isFileTooBig = (file: File): boolean => {
  const limit = file.type.startsWith('image/') ? MAX_IMAGE_BYTES : MAX_TEXT_BYTES;
  return file.size > limit;
};
