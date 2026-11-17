#!/usr/bin/env bash
# Weekly job: run the pipeline in Docker, publish the report to nginx.
# If any check fails, the old site stays live.
set -euo pipefail

cd "$(dirname "$0")/.."
OUT=$(mktemp -d)
MIN_JOBS=10
WEB_DIR=/var/www/html
POSITIONS=$(python3 -c "from config import POSITIONS; print(*POSITIONS)")

git pull --ff-only
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
rm -rf "$OUT"
echo "Deployed 🚀"