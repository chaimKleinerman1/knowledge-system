# Knowledge Base

Live demo: https://knowledge-system-638408023620.me-west1.run.app (Cloud Run, wakes up in a few
seconds after idle time). Code: https://github.com/chaimKleinerman1/knowledge-system

A one-page web app that turns uploaded files into searchable knowledge. You upload a text file
(`.txt`, `.md`) or an image (JPEG, PNG, WebP, GIF); the backend asks Gemini for a description,
tags, keywords, the text visible in the image, a category and the language, stores the file and
the metadata in MongoDB, and lets you find it again by keyword or by meaning: "black hair" finds
a note that mentions it and a photo that shows it. A failed analysis can be retried, a repeat
upload returns the existing asset, and any asset can be deleted. Authentication, scaling and
production hardening are out of scope, as the assignment allows.

## Architecture

```
Browser (React + Ant Design)
    |  /api/*  JSON + multipart upload
    v
FastAPI (Python 3.11), one container that also serves the React build (same origin, no CORS)
    |-> MongoDB, Atlas or local: assets collection (metadata, vectors, text index) + GridFS (files)
    +-> Gemini via LiteLLM: gemini-3.1-flash-lite (describe), gemini-embedding-2 (embed)
```

## Run locally

The app needs two secrets in `.env`: a MongoDB connection string (an Atlas free-tier cluster works)
and a Gemini API key. With Docker Compose (builds the frontend and the backend into one container):

```bash
cp .env.example .env          # fill in MONGODB_URI and GEMINI_API_KEY
docker compose up --build     # or: make up
open http://localhost:8000
```

With dev servers (Python 3.11 and Node 24, see `frontend/.nvmrc`):

```bash
make install                  # backend venv + requirements, frontend npm ci
make dev-backend              # uvicorn with reload on http://localhost:8000, reads .env
make dev-frontend             # Vite on http://localhost:5173, proxies /api to :8000
```

## Configuration

Settings come from environment variables; `.env` is loaded at startup.

| Variable | Default | Meaning |
|---|---|---|
| `MONGODB_URI` | required | MongoDB connection string (Atlas `mongodb+srv://...`). |
| `MONGODB_DB_NAME` | `knowledge` | Database name. |
| `GEMINI_API_KEY` | empty | Gemini API key, read by LiteLLM from the environment. |
| `LLM_MODEL` | `gemini/gemini-3.1-flash-lite` | LiteLLM model id for describing files. |
| `EMBEDDING_MODEL` | `gemini/gemini-embedding-2` | LiteLLM model id for embeddings. |
| `MAX_IMAGE_BYTES` | `10485760` | Image upload limit (10 MB). |
| `MAX_TEXT_BYTES` | `1048576` | Text upload limit (1 MB). |
| `SEMANTIC_MIN_SCORE` | `0.5` | Cosine threshold for the semantic pass. |

See `.env.example` for the rest (timeouts, retries, output caps, CORS, port).

## How it works

Upload runs inside one request; the UI shows "Uploading…", then "Analyzing with AI…":

1. **Validate.** The type comes from the file's magic bytes, never from the client's
   `Content-Type`, and must be on the allow-list (JPEG, PNG, WebP, GIF; a file with no magic
   number must end in `.txt` or `.md` and decode as UTF-8). Once the body has arrived its size is
   checked: 10 MB for images, 1 MB for text. Empty file 400, too large 413, wrong type 415.
2. **Deduplicate.** The sha256 of the bytes has a unique index. A repeat upload returns the
   existing asset with `deduplicated: true`; if that asset had failed, it is reprocessed first.
3. **Store.** The bytes go to GridFS and the asset document is inserted with `status: "processing"`.
4. **Describe and embed.** One LiteLLM completion call with a Pydantic response format returns
   the description, tags, keywords, visible text, category and `lang_code`. Images are downscaled
   first; long text is sent as head plus tail. One embedding call then turns the metadata text
   into a vector; for images the same call also embeds the pixels, so an image gets a second vector.
5. **Save.** The document gets the metadata, the vectors and `status: "ready"`. An AI error sets
   `status: "failed"` with a short message; the upload still returns 201, and "Retry analysis"
   in the UI calls `POST /api/assets/{id}/reprocess`.

Search runs two passes and merges them. The keyword pass uses one weighted MongoDB text index
over tags, category, keywords, description, visible text, filename and extracted text. MongoDB
ORs the words of a query, so "black hair" alone would also return a black car; the service runs
the phrase query first and the plain query second, phrase hits on top. The semantic pass embeds
the query and compares it by cosine similarity with every ready asset's stored vectors (the text
vector and, for images, the image vector; the higher score counts), dropping anything under 0.5.
The two ranked lists are merged with reciprocal rank fusion, so something found by both passes
wins. Each hit says whether it matched by keyword, by meaning, or both, shown as chips in the UI.

## Decisions

- One backend, one container: FastAPI serves the API and the React build, not two services.
- LiteLLM, because I know it and it swaps providers by env var; the cost is a bigger image.
- Gemini: a free tier, and its embedding model accepts images, so a photo can be found by meaning
  even when the description missed a detail.
- No separate OCR step: the vision model reads the text inside the image in the same call.
- Files in GridFS, not a bucket, so the reviewer needs two secrets and one `docker compose up`.
- No queue, because scale is out of scope for the assignment: processing runs inside the upload
  request (5–15 s). What a queue would give at this size is kept in a lighter form: the asset is
  saved first, an AI error sets `status: "failed"` with a message, and a reprocess endpoint retries.
  A queue and worker are the first thing to add for real traffic.
- MongoDB text index + cosine in Python, not Atlas Search: no search indexes to manage, it works
  on the Atlas free tier, and it is easy to explain. Atlas Vector Search is the upgrade path when
  the corpus grows.
- `.txt` and `.md` only; PDF is a next step (Gemini reads PDF natively).

## Limits and assumptions

- No authentication: anyone who reaches the URL can upload, search and delete.
- Single process, one file per upload, no rate limiting on the API itself.
- Uploads: images up to 10 MB and 8000 px per side, text up to 1 MB. HEIC and SVG are rejected.
- Processing happens inside the upload request; on the Gemini free tier an upload takes 5–15 s.
- Search is English-first: MongoDB stems English only, so a Hebrew keyword must match the whole
  word. The semantic pass still finds Hebrew queries by meaning.
- The semantic pass scans every vector in Python. Fine for hundreds of files, not for millions.
- The Gemini free tier has a low requests-per-minute limit; calls retry with backoff before an
  asset is marked failed.
- A field named `language` would break the MongoDB text index (MongoDB reads it as the document's
  text language and rejects values like `he`), so the field is called `lang_code`.

## Data note for the Gemini free tier

On the unpaid tier Google may use submitted content to improve its products, and human reviewers
may read it. Upload only the samples or content you are comfortable sharing, or use a paid key.

## Tests

```bash
make lint                                                    # ruff, eslint, tsc
make test                                                    # pytest + vitest
docker run -d --name km-mongo-test -p 27018:27017 mongo:8    # the integration tests need a MongoDB
MONGODB_TEST_URI=mongodb://localhost:27018 make test         # runs them too
docker rm -f km-mongo-test
```

Unit tests cover file validation, cosine and reciprocal rank fusion, input preparation, metadata
normalisation and the React components; integration tests run the API end to end with a fake AI
client that lives in the tests folder (upload, dedupe, fail and retry, file download headers,
search ranking, delete). `make smoke` uploads two samples to a running server (`BASE_URL`,
default `http://localhost:8000`) and checks two searches; it needs only curl.
No test makes a paid AI call. Checked by hand in the browser with the real models: image and text
upload, the size and type errors, search, the detail drawer, delete, a failed analysis and then
"Retry analysis", a duplicate upload, phone width, light and dark mode.

## AI tools used during development

Claude Code (Anthropic) was used throughout, as the assignment allows: for research (model,
library and search-backend options, MongoDB text-search behaviour), for scaffolding the code from
a written plan, and for a code review pass. The design decisions, the plan and the final review
are the author's.

## Next steps

- PDF support through Gemini's native PDF input.
- Object storage (GCS or S3) for the file bytes once they outgrow the Atlas free tier.
- Atlas Vector Search with `$rankFusion` instead of the Python cosine loop when the corpus grows.
- A queue and worker so uploads return at once and processing retries on its own.
- Authentication and per-user assets.
