#!/usr/bin/env bash
# Smoke test against a running server: upload two samples, run two searches,
# exit non-zero when the expected files are missing from the results.
#
#   BASE_URL=http://localhost:8000 bash scripts/smoke.sh
#
# Needs only curl and a running server with a real API key.

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
WAIT_SECONDS="${WAIT_SECONDS:-90}"
REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SAMPLES_DIRECTORY="${REPOSITORY_ROOT}/samples"

log() {
  printf '[smoke] %s\n' "$*"
}

fail() {
  printf '[smoke] FAIL: %s\n' "$*" >&2
  exit 1
}

wait_for_health() {
  log "Waiting for ${BASE_URL}/api/health (up to ${WAIT_SECONDS}s)"
  local elapsed=0
  local body=""
  while (( elapsed < WAIT_SECONDS )); do
    body="$(curl --silent --max-time 5 "${BASE_URL}/api/health" || true)"
    if grep -Eq '"status": ?"ok"' <<<"${body}" && grep -Eq '"database": ?"ok"' <<<"${body}"; then
      log "Server is healthy"
      return 0
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
  fail "Server did not become healthy in ${WAIT_SECONDS}s (last response: ${body:-none})"
}

upload_sample() {
  local file_path="$1"
  local file_name
  file_name="$(basename "${file_path}")"
  local response_file
  response_file="$(mktemp)"
  local status_code
  status_code="$(curl --silent --output "${response_file}" --write-out '%{http_code}' \
    --form "file=@${file_path}" "${BASE_URL}/api/assets")"
  local body
  body="$(cat "${response_file}")"
  rm -f "${response_file}"

  # 201 = new asset, 200 = the same bytes were uploaded before (deduplicated).
  case "${status_code}" in
    200|201) ;;
    *) fail "Upload of ${file_name} returned HTTP ${status_code}: ${body}" ;;
  esac

  if grep -Eq '"status": ?"ready"' <<<"${body}"; then
    log "Uploaded ${file_name} (HTTP ${status_code}, ready)"
  else
    log "WARNING: ${file_name} is not ready, searches may miss it (HTTP ${status_code}): ${body}"
  fi
}

expect_search_hit() {
  local query="$1"
  local expected_file_name="$2"
  local body
  body="$(curl --silent --fail --get --data-urlencode "q=${query}" "${BASE_URL}/api/search")" \
    || fail "Search for \"${query}\" failed"

  if grep -Eq "\"filename\": ?\"${expected_file_name}\"" <<<"${body}"; then
    log "Search \"${query}\" found ${expected_file_name}"
  else
    fail "Search \"${query}\" did not return ${expected_file_name}. Response: ${body}"
  fi
}

main() {
  wait_for_health
  upload_sample "${SAMPLES_DIRECTORY}/hair_salon_notes.md"
  upload_sample "${SAMPLES_DIRECTORY}/receipt.png"
  expect_search_hit "black hair" "hair_salon_notes.md"
  expect_search_hit "document" "receipt.png"
  log "PASS"
}

main "$@"
