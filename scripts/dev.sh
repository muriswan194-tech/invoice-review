set -euo pipefail
cd "$(dirname "$0")/.."

(
  cd backend
  uv run --locked --no-sync uvicorn app.main:app --reload
) &
(
  cd frontend
  pnpm dev
) &

trap 'kill 0' EXIT INT TERM
wait
