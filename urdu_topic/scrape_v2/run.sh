#!/usr/bin/env bash
# Easy runner for the scrape v2 pipeline.
#
# Usage:
#   ./run.sh                          # default: 60 min, all sources
#   ./run.sh 240                      # 4 hours
#   ./run.sh 240 express              # 4 hours, only Express
#   ./run.sh 240 express 5            # 4 hours, only Express, 5s delay
#   ./run.sh collect                  # just collect URLs (no scraping)
#
# After running, commit + push to GitHub:
#   git add urdu_topic/data/
#   git commit -m "Scraped N articles"
#   git push origin main

set -e
cd "$(dirname "$0")/.."  # cd to urdu_topic/

PYTHON="${PYTHON:-python3}"
MAX_MINUTES="${1:-60}"
SOURCE="${2:-all}"
DELAY="${3:-3}"

if [ "$1" = "collect" ]; then
    echo "=== Phase 1: Collecting URLs from sitemaps ==="
    $PYTHON scrape_v2/01_collect_urls.py --since 2021-01-01
    echo ""
    echo "=== Done. Now run: ./scrape_v2/run.sh ==="
    exit 0
fi

# Phase 1: collect URLs if not done yet
if [ ! -f "data/url_queue.json" ]; then
    echo "=== Phase 1: Collecting URLs from sitemaps (one-time) ==="
    $PYTHON scrape_v2/01_collect_urls.py --since 2021-01-01
    echo ""
fi

# Phase 2: scrape articles
echo "=== Phase 2: Scraping articles ==="
echo "  Max minutes: $MAX_MINUTES"
echo "  Source: $SOURCE"
echo "  Delay: ${DELAY}s"
echo ""
$PYTHON scrape_v2/02_scrape_articles.py --max-minutes "$MAX_MINUTES" --source "$SOURCE" --delay "$DELAY"

echo ""
echo "=== Done. To push to GitHub: ==="
echo "  git add urdu_topic/data/"
echo "  git commit -m \"Scraped more articles\""
echo "  git push origin main"
