export type AssetKind = 'image' | 'text';

export type AssetStatus = 'processing' | 'ready' | 'failed';

export interface AiMetadataResponse {
  description: string;
  tags: string[];
  keywords: string[];
  category: string;
  lang_code: string | null;
  /** Text found in an image. Sent by the detail endpoint only. */
  text_content: string | null;
  text_truncated: boolean;
  model: string;
  prompt_version: string;
  processed_at: string;
}

export interface AssetResponse {
  id: string;
  filename: string;
  kind: AssetKind;
  mime_type: string;
  size_bytes: number;
  status: AssetStatus;
  error: string | null;
  created_at: string;
  updated_at: string;
  file_url: string;
  /** Null until the AI analysis is ready. */
  ai: AiMetadataResponse | null;
  /** Content of a text file. Sent by the detail endpoint only. */
  extracted_text: string | null;
  /** True when an upload matched a file that already existed. */
  deduplicated: boolean;
}

export interface AssetListParams {
  limit?: number;
  offset?: number;
}

export interface AssetListResponse {
  items: AssetResponse[];
  total: number;
}
