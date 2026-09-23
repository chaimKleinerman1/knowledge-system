import { ACCEPTED_UPLOAD_TYPES, MAX_IMAGE_BYTES, MAX_TEXT_BYTES } from '@/shared/lib/constants';

const acceptedTypes = ACCEPTED_UPLOAD_TYPES.split(',');

/** Mirrors the server limits so an oversize file is rejected before any bytes are sent. */
export const isFileTooBig = (file: File): boolean => {
  const limit = file.type.startsWith('image/') ? MAX_IMAGE_BYTES : MAX_TEXT_BYTES;
  return file.size > limit;
};

/** Mirrors the Dragger's `accept` list, which drops non-matching files on drag and drop without any callback. */
export const isAcceptedFile = (file: File): boolean =>
  acceptedTypes.some(type => (type.startsWith('.') ? file.name.toLowerCase().endsWith(type) : file.type === type));
