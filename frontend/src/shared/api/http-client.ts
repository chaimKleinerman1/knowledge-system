import axios, { isAxiosError } from 'axios';

/** Every API call rejects with this shape: a message the UI can show as-is. */
export class ApiError extends Error {
  readonly status: number | undefined;

  constructor(message: string, status?: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

interface ValidationIssue {
  msg?: unknown;
}

interface ErrorBody {
  detail?: unknown;
}

const FALLBACK_MESSAGE = 'The server sent an unexpected answer. Please try again.';
const NETWORK_MESSAGE = 'Cannot reach the server. Check your connection and try again.';

/** FastAPI sends `detail` as a sentence, or as a list of issues for request validation errors. */
const readDetail = (body: unknown): string | undefined => {
  if (typeof body !== 'object' || body === null) {
    return undefined;
  }
  const { detail } = body as ErrorBody;
  if (typeof detail === 'string' && detail.trim().length > 0) {
    return detail;
  }
  if (Array.isArray(detail)) {
    const messages = detail
      .map(issue => (typeof issue === 'object' && issue !== null ? (issue as ValidationIssue).msg : undefined))
      .filter((message): message is string => typeof message === 'string' && message.length > 0);
    if (messages.length > 0) {
      return messages.join(' ');
    }
  }
  return undefined;
};

export const toApiError = (error: unknown): ApiError => {
  if (error instanceof ApiError) {
    return error;
  }
  if (isAxiosError(error)) {
    if (!error.response) {
      return new ApiError(NETWORK_MESSAGE);
    }
    return new ApiError(readDetail(error.response.data) ?? FALLBACK_MESSAGE, error.response.status);
  }
  if (error instanceof Error && error.message.length > 0) {
    return new ApiError(error.message);
  }
  return new ApiError(FALLBACK_MESSAGE);
};

export const getErrorMessage = (error: unknown): string => toApiError(error).message;

export const httpClient = axios.create({ baseURL: '/api' });

httpClient.interceptors.response.use(
  response => response,
  (error: unknown) => Promise.reject(toApiError(error)),
);
