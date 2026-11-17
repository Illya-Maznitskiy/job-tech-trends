#!/usr/bin/env bash
# Weekly job: run the pipeline in Docker, publish the report to nginx.
# If any check fails, the old site stays live.
set -euo pipefail

# Everything is in a function so bash reads the whole body first,
# even if "git pull" changes this file while it runs.
main() {
  cd "$(dirname "$0")/.."
  OUT=$(mktemp -d)
  trap 'rm -rf "$OUT"' EXIT
  MIN_JOBS=10
  WEB_DIR=/var/www/html

  git pull --ff-only
  # Read after the pull, so new positions are picked up at once
  POSITIONS=$(python3 -c "from config import POSITIONS; print(*POSITIONS)")

  docker build -t job-tech-trends .
  docker rm -f job_tech_trends_cont 2>/dev/null || true
  docker run --name job_tech_trends_cont --env-file .env job-tech-trends
  docker cp job_tech_trends_cont:/app/analytics/data/. "$OUT/analytics"
  docker cp job_tech_trends_cont:/app/scraping/data/. "$OUT/scraping"
  docker rm job_tech_trends_cont

  # Guards
  [ -f "$OUT/analytics/index.html" ] || { echo "No report"; exit 1; }
  today=$(date +%F)
  [ "$(date -r "$OUT/analytics/index.html" +%F)" = "$today" ] \
    || { echo "Report is not from today"; exit 1; }
  for p in $POSITIONS; do
    jobs=$(( $(wc -l < "$OUT/scraping/$p/jobs.csv") - 1 ))
    [ "$jobs" -gt "$MIN_JOBS" ] || { echo "$p: only $jobs jobs"; exit 1; }
  done

  cp -r "$OUT/analytics/." "$WEB_DIR/"
  echo "Deployed 🚀"
}

main "$@"; exit
