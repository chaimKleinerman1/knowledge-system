import { atom } from 'jotai';

/** The active search text. Empty means "show every file". */
export const searchQueryAtom = atom('');
