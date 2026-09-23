# Stage 1: build the frontend into static files.
FROM node:24-alpine AS frontend-build

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: the backend serves the API and the built frontend on one port.
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
COPY --from=frontend-build /frontend/dist ./static

EXPOSE 8000

# Cloud Run injects PORT; everything else falls back to 8000.
CMD ["sh", "-c", "uvicorn main:create_app --factory --host 0.0.0.0 --port ${PORT:-8000}"]
