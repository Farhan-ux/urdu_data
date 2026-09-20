# Scrape v2 — Gentle, Resumable, Sitemap-Based Scraper

A complete rewrite of the scraper that:
- **Discovers URLs via sitemaps** (1 request per sitemap, very gentle on servers)
- **Crawls articles sequentially** with configurable delay (default 3 seconds)
- **Saves progress every 25 articles** — safe to kill and restart anytime
- **Resumes from where it stopped** — keeps track of scraped URLs in `<source>_scraped_urls.json`
- **Handles network errors** with exponential backoff retry
- **Time-limited mode** — stop after N minutes (default 60)
- **Article limit mode** — stop after N articles per source
- **Graceful shutdown** — Ctrl+C stops after current article and saves state

## Coverage

Based on sitemap discovery:

| Source | Article URLs Available | Date Range |
|--------|------------------------|------------|
| Express | ~450,000 (90+ sitemaps × 5000 URLs each) | 2013 → 2026 |
| Nawa-i-Waqt | ~50,000+ (6,259 sub-sitemaps, sampling) | varies |
| BBC Urdu | ~100 (small sitemap) | 2014 → 2026 |
| Jang | ~500 (category pages, fake pagination) | recent only |
| **Total** | **~500,000+ available** | |

## Quick Start

```bash
# Step 1: Install deps
pip install -r requirements.txt

# Step 2: Collect URLs from sitemaps (one-time, ~5 min)
python scrape_v2/01_collect_urls.py

# Step 3: Scrape articles (run for as long as you want)
# Default: 60 minutes, 3s delay between requests, all sources
python scrape_v2/02_scrape_articles.py

# Step 4: To resume, just run again — it picks up where it stopped
python scrape_v2/02_scrape_articles.py
```

## Usage Examples

### Collect URLs

```bash
# All sources, all sitemaps (comprehensive)
python scrape_v2/01_collect_urls.py

# Only Express, only 5 sitemaps (testing)
python scrape_v2/01_collect_urls.py --source express --max-sitemaps 5

# Only articles from 2021 onwards (post-Mendeley dataset)
python scrape_v2/01_collect_urls.py --since 2021-01-01

# Only Nawa-i-Waqt
python scrape_v2/01_collect_urls.py --source nawaiwaqt
```

### Scrape Articles

```bash
# Default: 60 min, all sources, 3s delay
python scrape_v2/02_scrape_articles.py

# Run for 4 hours
python scrape_v2/02_scrape_articles.py --max-minutes 240

# Scrape 5000 articles per source
python scrape_v2/02_scrape_articles.py --max-articles 5000

# Only Express, 5s delay (extra gentle)
python scrape_v2/02_scrape_articles.py --source express --delay 5

# Stop after 30 min OR 2000 articles (whichever first)
python scrape_v2/02_scrape_articles.py --max-minutes 30 --max-articles 2000

# Resume anytime — just run again
python scrape_v2/02_scrape_articles.py
```

## Throughput Estimates

With default 3-second delay:

| Setting | Articles/hour | Articles/day |
|---------|---------------|--------------|
| 3s delay, 1 source | ~1,000 | ~24,000 |
| 3s delay, all 4 sources (sequential) | ~4,000 | ~96,000 |
| 5s delay (extra gentle), 1 source | ~600 | ~14,400 |

**Recommended for a weekend run (8 hours, all sources, 3s delay):** ~30,000 articles → 60x bigger than current dataset.

## File Layout

After running, you'll have:

```
urdu_topic/data/
├── url_queue.json                  ← All discovered URLs (from Phase 1)
├── express_articles.json           ← Scraped Express articles (cumulative)
├── express_scraped_urls.json       ← Set of Express URLs already attempted
├── jang_articles.json
├── jang_scraped_urls.json
├── nawaiwaqt_articles.json
├── nawaiwaqt_scraped_urls.json
├── bbc_urdu_articles.json
├── bbc_urdu_scraped_urls.json
└── all_articles.json               ← Combined (auto-regenerated)
```

## Safety Features

1. **Never re-scrapes a URL** — `<source>_scraped_urls.json` tracks everything attempted (success or failure)
2. **Save every 25 articles** — at most you lose 24 articles of work on a crash
3. **Graceful Ctrl+C** — finishes current article, saves state, exits cleanly
4. **Network retry** — 3 attempts with exponential backoff on connection errors
5. **Rate-limit aware** — if server returns 429/503, waits 10-30s and retries
6. **Honest User-Agent** — identifies as academic research with repo URL

## Being Gentle on Servers

- 3-second delay between requests to same host (configurable)
- Sequential per source (no parallel workers hammering one server)
- One sitemap request per sitemap file (Phase 1)
- Identifies ourselves in User-Agent
- Obeys 429/503 rate-limit responses

If you get blocked by a server, increase `--delay` to 5 or 10 seconds.

## Workflow: Run Locally, Push Back Results

After you've scraped a chunk locally:

```bash
# 1. Commit your scraped data
cd urdu_data
git add urdu_topic/data/*_articles.json urdu_topic/data/*_scraped_urls.json urdu_topic/data/url_queue.json
git commit -m "Scraped N articles from <source>"

# 2. Push to GitHub
git push origin main
```

Or you can zip up the data and share it any other way.

## Re-preprocessing After Scraping

Once you have more articles, re-run the preprocessing pipeline:

```bash
# Re-classify sections and re-build vocabulary
python scripts/08_preprocess.py

# Re-train models
python scripts/09_train_models.py
python scripts/10_train_round2.py

# Re-generate figures
python scripts/11_make_figures.py

# Re-package dataset
python scripts/12_package_dataset.py
```

## Troubleshooting

**"Queue file not found"** — Run `01_collect_urls.py` first.

**"0 URLs pending"** — All URLs have been scraped already. Run `01_collect_urls.py` again to fetch more sitemaps, or remove the `<source>_scraped_urls.json` file to reset.

**Server returns 403 Forbidden** — Server is blocking your IP. Wait a few hours, increase `--delay`, or try a different network.

**Many articles fail to parse** — Some URLs may be removed or redirect. The script logs failures and moves on. Check `<source>_articles.json` to see what was successfully scraped.

**Disk space** — Each article is ~2KB on average. 100,000 articles = ~200 MB. Plan accordingly.
