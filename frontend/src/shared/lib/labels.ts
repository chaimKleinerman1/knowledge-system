import type { MatchedBy } from '@/shared/api/search';

const CATEGORY_LABELS: Record<string, string> = {
  photo: 'Photo',
  document: 'Document',
  screenshot: 'Screenshot',
  diagram: 'Diagram',
  text_note: 'Text note',
  other: 'Other',
};

export const formatCategory = (category: string): string => {
  const known = CATEGORY_LABELS[category];
  if (known) {
    return known;
  }
  const words = category.replaceAll('_', ' ').trim();
  return words.charAt(0).toUpperCase() + words.slice(1);
};

export const MATCHED_BY_LABELS: Record<MatchedBy, string> = {
  keyword: 'keyword',
  semantic: 'meaning',
};

const languageNames = new Intl.DisplayNames(['en'], { type: 'language' });

export const formatLanguage = (languageCode: string | null): string => {
  if (!languageCode) {
    return 'Unknown';
  }
  try {
    return languageNames.of(languageCode) ?? languageCode;
  } catch {
    return languageCode;
  }
};
