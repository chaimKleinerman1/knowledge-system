# Knowledge Base

A one-page web app that turns uploaded files into searchable knowledge. Upload a text file or an
image, let an AI model describe it, then find it again by keyword or by meaning.

## What it does

- Upload text files (`.txt`, `.md`) and images (JPEG, PNG, WebP, GIF) from the browser.
- On upload the backend asks Gemini for searchable metadata: a short description, tags, keywords,
  the text visible in the image, a category and the language.
- The file bytes and the metadata are stored in MongoDB. Nothing else is needed: no bucket, no queue.
- Search combines two passes: a MongoDB keyword search and a semantic search over embedding vectors.
  Searching "black hair" finds an image that shows black hair and a note that mentions it.
- Every asset has a status (processing, ready, failed). A failed analysis can be retried from the UI.
- Duplicate uploads are detected by content hash and return the existing asset.

Out of scope, as the assignment allows: authentication, scaling, production hardening. See
[Limits and assumptions](#limits-and-assumptions).

## Architecture

```
  Browser (React 19 + Ant Design, served by the same container)
      |
      |  /api/*  JSON + multipart upload
      v
  FastAPI (Python 3.11, one process)
      |
      |-- upload: validate -> store bytes -> describe with AI -> embed -> save metadata
      |-- search: keyword ($text) + semantic (cosine over stored vectors) -> reciprocal rank fusion
      |
      +---------------------------+---------------------------+
      |                           |                           |
      v                           v                           v
  MongoDB `assets`           MongoDB GridFS             Gemini via LiteLLM
  (metadata, vectors,        (the file bytes)           gemini-3.1-flash-lite  (describe)
   text index)                                          gemini-embedding-2     (embed)
```

One container serves both the API and the built frontend on port 8000. The frontend calls the API
on the same origin, so no CORS setup is needed in Docker.

## Run locally

### Option A: Docker Compose (recommended)

```bash
cp .env.example .env          # add GEMINI_API_KEY; leave MONGODB_URI empty for the local MongoDB
docker compose up --build     # builds the frontend and backend, starts MongoDB 8
open http://localhost:8000
```

With a MongoDB Atlas URI in `.env`, skip the local database:

```bash
docker compose up --build api --no-deps
```

Without an API key you can still run everything with the deterministic fake AI client. This is for
local use and the smoke test only:

```bash
AI_CLIENT=fake docker compose up --build
```

### Option B: dev servers

Backend (Python 3.11):

```bash
python3.11 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt -r backend/requirements-test.txt
docker compose up mongo             # or point MONGODB_URI in .env at Atlas
cd backend && .venv/bin/uvicorn main:app --reload --port 8000
```

Frontend (Node 24, see `frontend/.nvmrc`):

```bash
cd frontend && nvm use && npm ci && npm run dev    # http://localhost:5173, proxies /api to :8000
```

The `Makefile` wraps the same commands: `make install`, `make dev-backend`, `make dev-frontend`,
`make test`, `make lint`, `make format`, `make build`, `make up`, `make down`, `make smoke`.

### Smoke test

`scripts/smoke.sh` waits for `/api/health`, uploads `samples/hair_salon_notes.md` and
`samples/receipt.png`, searches for "black hair" and "document", and fails when the expected files
are missing from the results. It needs only `curl`.

```bash
make smoke                                   # against http://localhost:8000
BASE_URL=https://my-host bash scripts/smoke.sh
```

The `samples/` folder also holds `contract_summary.txt`, `hebrew_note.txt`, `id_card.png` and
`black_car.png` for manual testing. The three PNGs are drawn by `scripts/make_samples.py` with
Pillow, so the repository contains no downloaded photos.

## Configuration

All settings come from environment variables (`.env` is loaded at startup). `.env.example` lists
them with comments.

| Variable | Default | Meaning |
|---|---|---|
| `MONGODB_URI` | `mongodb://localhost:27017` | Connection string. Empty = local MongoDB (Compose uses its own `mongo` service). |
| `MONGODB_DB_NAME` | `knowledge` | Database name. |
| `GEMINI_API_KEY` | empty | Gemini API key, read by LiteLLM from the environment. |
| `LLM_MODEL` | `gemini/gemini-3.1-flash-lite` | LiteLLM model id for describing files. |
| `EMBEDDING_MODEL` | `gemini/gemini-embedding-2` | LiteLLM model id for embeddings. |
| `EMBEDDING_DIMENSIONS` | `768` | Vector size requested from the embedding model. |
| `MAX_IMAGE_BYTES` | `10485760` | Image upload limit (10 MB). |
| `MAX_TEXT_BYTES` | `1048576` | Text upload limit (1 MB). |
| `MAX_IMAGE_PIXELS_SIDE` | `8000` | Reject images wider or taller than this. |
| `LLM_TEXT_INPUT_CHARS` | `20000` | Longer text goes to the model as head (16k) + tail (4k). |
| `LLM_MAX_OUTPUT_TOKENS` | `4096` | Cap on the model answer. |
| `LLM_TIMEOUT_SECONDS` | `60` | Timeout per AI call. |
| `LLM_MAX_RETRIES` | `3` | Retries per AI call with exponential backoff. |
| `AI_CONCURRENCY` | `2` | Max AI calls in flight (keeps the free tier under its rate limit). |
| `SEMANTIC_MIN_SCORE` | `0.5` | Cosine threshold for the semantic list. Tune after the first live run. |
| `SEARCH_LIMIT` | `10` | Results returned per search. |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma separated origins allowed to call the API. |
| `PORT` | `8000` | Listening port. Cloud Run and Compose set it themselves. |
| `AI_CLIENT` | unset | `fake` swaps in the deterministic test client. Local and smoke use only. |

## How the AI pipeline works

Everything runs inside the upload request. The UI shows "Uploading…" and then "Analyzing with AI…"
until the answer arrives.

1. **Validate.** The type comes from the magic bytes of the file, never from the client's
   `Content-Type`. Allowed images: JPEG, PNG, WebP, GIF (HEIC and SVG are rejected). A file with no
   magic number must end in `.txt` or `.md` and decode as strict UTF-8. Size limits are enforced in
   two layers. A small ASGI middleware answers 413 to a `Content-Length` above the image limit
   before the multipart body is parsed, and cuts the request off (413, connection closed) as soon
   as the streamed bytes pass that limit. The handler then re-checks against the limit for the
   actual type (10 MB images, 1 MB text) while reading in 1 MiB chunks, computing sha256 in the
   same pass. A body sent without `Content-Length` (chunked) skips the header check but not the
   byte counter. Images are opened and verified with Pillow; a side above 8000 px or a
   decompression bomb is rejected. File names lose their path, control characters and anything
   past 255 characters. Empty files return 400, too-large 413, wrong type 415.
2. **Deduplicate.** The sha256 has a unique index. A repeat upload returns the existing asset with
   `deduplicated: true`. If that asset had failed, it is reprocessed first.
3. **Store.** Bytes go to GridFS; the asset document is inserted with `status: "processing"`.
4. **Prepare.** Images are downscaled to fit 1536 px, re-encoded as JPEG quality 85 and sent as a
   base64 data URI. Text longer than 20,000 characters is sent as the first 16,000 plus the last
   4,000 characters. The full text (capped at 200,000 characters) is stored for keyword search.
5. **Describe.** One LiteLLM completion call with a Pydantic `response_format`. The model returns
   `description`, `tags`, `keywords`, `text_content` (visible text, verbatim, up to 4,000
   characters, with a `text_truncated` flag), `lang_code` and a `category` (photo, document,
   screenshot, diagram, text note, other). The prompt requires generic tags (document, photo,
   receipt, id card, person…) next to specific ones (colours, objects, hair colour, brands, places)
   and tells the model that file content is data, never instructions. Tags and keywords are
   lowercased, deduplicated, capped, and underscores become spaces because the MongoDB tokenizer
   does not split on underscores. A cut-off answer (`finish_reason == "length"`) marks the asset as
   failed with a clear message.
6. **Embed.** One embedding call with the metadata text (description + tags + keywords + visible
   text). For images the same request also sends the image, so an image gets a second vector from
   its pixels. If the provider returns only one vector, the image vector is stored as null and the
   upload still succeeds. Whether two vectors arrive from one LiteLLM call is to confirm after the
   first live run.
7. **Save.** The document is updated with the metadata, the vectors and `status: "ready"`. Any AI
   error sets `status: "failed"` plus a short plain-English `error`; the upload itself still
   returns 201. "Retry analysis" in the UI calls `POST /api/assets/{id}/reprocess`.

AI calls share one semaphore (`AI_CONCURRENCY`) so a batch upload stays under the free-tier rate
limit. Temperature is left at the model default because Gemini 3 models expect 1.0.

### API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | `{ "status": "ok", "database": "ok" \| "error" }` |
| POST | `/api/assets` | Multipart field `file`. 201 with the asset; 200 + `deduplicated: true` for a repeat. |
| GET | `/api/assets?limit=50&offset=0` | Newest first, heavy fields left out. |
| GET | `/api/assets/{id}` | Full asset, including the extracted text and the visible image text. |
| GET | `/api/assets/{id}/file` | The stored bytes with the right `Content-Type`. |
| POST | `/api/assets/{id}/reprocess` | Re-run describe + embed from the stored bytes. |
| DELETE | `/api/assets/{id}` | Remove the document and the GridFS file. |
| GET | `/api/search?q=black%20hair&limit=10` | `{ "query", "items": SearchHit[] }`; 400 for a blank query. |

Errors use FastAPI's `{ "detail": "..." }` shape with messages the UI shows as-is.

## How search works

Two independent passes, then a merge.

**Keyword pass.** One weighted MongoDB text index covers `ai.tags` (10), `ai.category` (8),
`ai.keywords` (8), `ai.description` (5), `ai.text_content` (4), `filename` (3) and
`extracted_text` (2). MongoDB ORs the words of a query, so "black hair" alone would also return a
black car. The service therefore runs the phrase query (`"black hair"`) first, then the plain OR
query, and merges them phrase-first with duplicates removed, each sorted by text score. English
stemming is on (`document` also matches `documents` and `documentation`). Hebrew has no stemming in
MongoDB text search, so a Hebrew keyword must match a whole word; the semantic pass covers the rest.

**Semantic pass.** The query is embedded, then compared by cosine similarity with every ready
asset's stored vectors: the text vector and, for images, the image vector. The score is the higher
of the two. Scores below `SEMANTIC_MIN_SCORE` are dropped; the top 20 remain. If the embedding call
fails, the search returns keyword results only.

**Fusion.** Reciprocal rank fusion with k = 60: each list contributes `1 / (k + rank)` for every
asset it contains, and the sums are sorted. Each hit reports `matched_by` (keyword, semantic, or
both) so the UI can show chips. Worked example for the query "black hair":

| Asset | Keyword rank | Semantic rank | RRF score (k = 60) | Final order |
|---|---|---|---|---|
| portrait with black hair | 1 | 2 | 1/61 + 1/62 = 0.0325 | 1 |
| hair salon notes (phrase in the text) | 3 | 3 | 1/63 + 1/63 = 0.0317 | 2 |
| dark hair photo, no caption | — | 1 | 1/61 = 0.0164 | 3 |
| black car (OR match on "black") | 2 | — | 1/62 = 0.0161 | 4 |

Something found by both passes wins; the semantic-only hit (an image the model never tagged with
the exact words) still beats the keyword-only false friend. The same example is a unit test.

The evaluation set behind the design (the two images with hair are not shipped in `samples/`):

| File | "black hair" | "document" |
|---|---|---|
| portrait_black_hair.jpg | hit (tags; image vector) | no |
| dark_hair_no_caption.jpg | hit via the image vector | no |
| id_card.png | no | hit (category + tags; visible text) |
| black_car.png | only in the OR fallback, below phrase hits | no |
| hair_salon_notes.md | hit (phrase) | no |
| contract_summary.txt | no | hit (stemming) |

How well cross-modal retrieval ranks these live, and the right `SEMANTIC_MIN_SCORE`, are to
confirm after the first live run.

## Decisions and trade-offs

**One backend, one container.** FastAPI serves the API and the built React app. The reviewer needs
two secrets (`MONGODB_URI`, `GEMINI_API_KEY`) and one `docker compose up`.

**Plain async functions, not a graph framework.** The pipeline is three linear steps (validate,
describe, embed). LangGraph is built for long-running, branching, resumable agents; here it would
add a runtime to explain and nothing to gain.

**LiteLLM instead of the provider SDK.** Measured on `python:3.11-slim`: the LiteLLM layer is
288 MB (58 packages, 1.96 s cold import) versus 75 MB for `google-genai` (0.17 s) and 60 MB for the
`openai` SDK (0.19 s). LiteLLM costs about 230 MB of image and one to two seconds of start time. In
return the provider is swapped by an env var, retries with exponential backoff and Pydantic-typed
answers are built in, and the same client handles vision input and multimodal embeddings. For a
demo where start time is not a metric, that trade is worth it; a latency-sensitive service would
pick the SDK.

**Gemini.** `gemini-3.1-flash-lite` for generation and `gemini-embedding-2` for vectors: one key,
a free tier, and an embedding model that accepts images, so an image can be found by meaning even
when the description misses a detail. Measured cost on the paid tier is about $0.0008 per photo
(input $0.25 and output $1.50 per million tokens; a document-like image with the full text cap is
about $0.0022). On the free tier it is $0. `gpt-5-nano` is cheaper per call but has no free tier
and no image embeddings; Claude has no embedding model at all, which would mean a second vendor.

**One AI call per image, no OCR step.** Current vision models read the text inside an image as
part of the same call, so the visible text comes back as one field of the JSON answer. A separate
OCR engine only pays off for dense scanned pages, which this tool does not target. Output tokens
cost six times input tokens on Flash-Lite, so the visible text is capped at 4,000 characters and
the answer at 4,096 tokens.

**GridFS, not a bucket and not the disk.** Cloud Run's disk is in memory and wiped on restart. A
GCS bucket would add a billing account, a service-account key and a library. GridFS keeps the
asset documents small and the secret count at two. Atlas M0 storage (0.5 GB) includes GridFS
chunks, which is fine for a demo.

**No queue.** The assignment waives scalability. Processing runs inside the request (a few seconds,
with a spinner). Background work after the response is unsafe on Cloud Run's default CPU
allocation, and a worker process would need Redis or Celery. `status` + `error` on every asset
and a reprocess endpoint make failures visible and recoverable instead.

**Plain `$text` + cosine in Python, not Atlas Search.** Atlas Search and Vector Search exist on the
free tier, but the plain `mongo:8` image cannot run them, so the local run and the Atlas run would
behave differently. A weighted text index plus a cosine loop over stored vectors runs identically
in both places. The loop scans every ready asset, which is fine for hundreds of files and wrong for
millions; that is the first thing to replace when the data grows.

**Two measured MongoDB traps.** (1) `$text` ORs the words, hence the phrase query first. (2) With a
text index present, inserting a document whose field is literally named `language` with a value
like `he` fails (`WriteError 17262`). The language field is therefore named `lang_code` and the
index is created with `language_override="__no_lang__"`.

**`.txt` and `.md` only.** The assignment says "text files". PDF text extraction has no clean
answer for layout and returns nothing for scanned pages; if PDF is added, Gemini's native PDF input
is the cheap path.

## Limits and assumptions

- No authentication. Anyone who can reach the URL can upload, search and delete.
- Single process, single container. No horizontal scaling, no rate limiting on the API itself.
- Uploads: images up to 10 MB and 8000 px per side; text up to 1 MB. Images must be JPEG, PNG,
  WebP or GIF. HEIC and SVG are rejected. An oversize body is refused before it is parsed or
  spooled; a chunked body without `Content-Length` is cut off once it passes the limit.
- Processing happens inside the upload request, so an upload takes as long as the AI answer.
  Expected a few seconds per file; the actual number is to confirm after the first live run.
- Keyword search stems English only. Hebrew keyword matches need the exact word form.
- The semantic pass scans all vectors in Python. Fine for a demo, not for a large corpus.
- The Gemini free tier has a low requests-per-minute limit; `AI_CONCURRENCY=2` keeps batch uploads
  under it, and a rate-limited call is retried with backoff before the asset is marked failed.
- Text longer than 20,000 characters is described from its head and tail only; the middle still
  counts for keyword search through `extracted_text`.
- The exact embedding model id and the free-tier quota are to confirm in AI Studio with the real
  key.

## Data usage note for the Gemini free tier

The default configuration uses the Gemini API on the unpaid tier. Google's terms for the unpaid
services allow Google to use submitted content to improve its products, and human reviewers may
read it. Google asks users not to submit sensitive, confidential or personal information there.
Upload only the sample files or content you are comfortable sharing, or use a key from a Google
Cloud project with billing enabled, where content is not used for improvement.

## Tests

Backend (`backend/tests`, pytest with `asyncio_mode = auto`):

- `test_validation.py`: PNG bytes named `.txt` and text named `.png` are rejected (415), truncated
  JPEG (415), huge PNG (413), HEIC (415), SVG (415), oversize via `Content-Length` and via the byte
  counter (413), empty file (400), file names with paths, control characters or 1,000 characters,
  and happy paths for JPEG, PNG, WebP, GIF, `.txt`, `.md`. Fixtures are built in the test with
  Pillow.
- `test_upload_size_limit.py`: through the real app, an oversize `Content-Length` is refused with
  no body read, and a chunked oversize body is cut off at the limit.
- `test_content_disposition.py`: the ASCII fallback in the file header never carries control
  characters.
- `test_fusion.py`: cosine similarity and reciprocal rank fusion with the worked example above.
- `test_preparation.py`: head/tail truncation, thumbnail size, data URI prefix.
- `test_metadata_normalisation.py`: lowercase, dedupe, underscore to space, list caps.
- `test_api_integration.py` (marker `integration`, runs only when `MONGODB_TEST_URI` is set):
  upload text and image with the fake AI client, duplicate upload, failed asset then reprocess,
  list, detail, file round-trip, delete, "black hair" phrase ranking, and a document with
  `lang_code: "he"` inserting fine.

```bash
cd backend && .venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/pytest
docker run -d --name km-mongo-test -p 27018:27017 mongo:8
MONGODB_TEST_URI=mongodb://localhost:27018 .venv/bin/pytest -m integration
docker rm -f km-mongo-test
```

Frontend (`vitest` + Testing Library): `npm run lint`, `npm run typecheck`, `npm test`.

The whole stack: `docker compose up --build` with `AI_CLIENT=fake`, then `make smoke`.

No test makes a paid AI call. The `FakeAiClient` returns deterministic metadata derived from the
filename or text, and fixed unit vectors.

## AI tools used during development

Claude Code (Anthropic) was used throughout, as the assignment allows:

- Research: comparing orchestration options, models and prices, and search backends; measuring
  package sizes, import times and the MongoDB text-search behaviour that shaped the design.
- Scaffolding: generating the backend, frontend and repository files from a written plan that
  fixes names, endpoints and layout.
- Review: an adversarial code review pass on correctness, contract compliance and the upload path.

The design decisions, the plan and the final review are the author's.

## Next steps

- PDF support through Gemini's native PDF input (about 258 tokens per page), not a local extractor.
- Object storage (GCS or S3) for the file bytes once files grow past the Atlas free-tier storage.
- Atlas Vector Search with `$rankFusion` to replace the Python cosine loop when the corpus grows.
- A queue and worker so uploads return immediately and processing retries on its own.
- Authentication and per-user assets.
- HEIC input, a retry with a smaller output cap when the AI answer is cut off, and pagination in the
  grid.
