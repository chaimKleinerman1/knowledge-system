export const MAX_IMAGE_BYTES = 10 * 1024 * 1024;
export const MAX_TEXT_BYTES = 1024 * 1024;
export const FILE_TOO_BIG_MESSAGE = 'File is too big. Max 10 MB for images, 1 MB for text.';

export const ACCEPTED_UPLOAD_TYPES = '.txt,.md,image/jpeg,image/png,image/webp,image/gif';
export const UNSUPPORTED_FILE_MESSAGE = 'Only .txt, .md, JPEG, PNG, WebP and GIF files are supported.';

export const SEARCH_DEBOUNCE_MS = 400;
export const SEARCH_PLACEHOLDER = 'Search files by content, tags or meaning…';

/** The list endpoint pages; the page shows the newest files and relies on search for the rest. */
export const ASSET_LIST_LIMIT = 50;
export const PROCESSING_POLL_MS = 5_000;

export const DESCRIPTION_PREVIEW_CHARS = 120;
export const CARD_TAG_LIMIT = 5;
