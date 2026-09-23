import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

const HAS_TIMEZONE = /(Z|[+-]\d{2}:?\d{2})$/i;

/** The server stores UTC; a timestamp without an offset would otherwise be read as local time. */
const parseServerDate = (value: string): dayjs.Dayjs => dayjs(HAS_TIMEZONE.test(value) ? value : `${value}Z`);

export const formatDateTime = (value: string): string => parseServerDate(value).format('MMM D, YYYY HH:mm');

export const formatRelativeTime = (value: string): string => parseServerDate(value).fromNow();
