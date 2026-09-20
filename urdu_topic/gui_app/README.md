# Urdu News Scraper GUI

A standalone desktop app that scrapes Urdu news articles from 7 major Pakistani
news outlets. Just pick a folder, click "Start", and walk away.

## 📥 Download

Pre-built binaries will be available in the [releases page](https://github.com/Farhan-ux/urdu_data/releases) once built.

If you want to build it yourself:

```bash
# Install PyInstaller
pip install pyinstaller

# Build (creates dist/UrduScraper or dist/UrduScraper.exe)
cd urdu_topic/gui_app
pyinstaller --clean UrduScraper.spec
```

The executable will be in `dist/` folder. Double-click to run.

## 🎯 Sources Covered

| Source | Articles Available | Date Range | Notes |
|--------|-------------------:|------------|-------|
| Nawa-i-Waqt | 2,585,403 | 2002 → 2026 | Largest source; daily sitemaps |
| Express Urdu | 450,000 | 2013 → 2026 | 92 sub-sitemaps × 5000 URLs |
| **ARY Urdu** | **352,000** | **2013 → 2026** | **Uses Googlebot UA (site blocks default)** |
| 24 News HD | 185,810 | 2020 → 2026 | Daily sitemaps |
| Ummat | 116,000 | 2018 → 2026 | 116 sub-sitemaps × 1000 URLs |
| Bol News Urdu | 71,404 | 2022 → 2026 | 72 sub-sitemaps × 1000 URLs |
| Daily Ausaf | 52,026 | recent | 52 sub-sitemaps × 1000 URLs |
| Independent Urdu | 51,865 | 2018 → 2026 | 2 paged sitemaps |
| **Total** | **3,864,508** | **2002 → 2026** | **3.8x bigger than Mendeley 1M** |

### Sites that couldn't be scraped (JavaScript-rendered or hard-blocked)

- **Geo Urdu** — JS-rendered, no sitemap accessible
- **Samaa Urdu** — JS-rendered, no sitemap accessible
- **Aaj News** — Hard 403 block, no sitemap
- **Dawn Urdu** — Hard 403 block, no sitemap
- **Dunya Urdu** — JS-rendered homepage
- **UrduPoint** — No sitemap, JS-rendered

These would require Selenium (browser automation) — out of scope for this gentle
HTTP-based scraper.

## ✨ Features

- **One-click start** — pick folder, click Start, walk away
- **⚡ Parallel mode (NEW)** — 8x faster! One thread per source, all sources scraped simultaneously. Each source still gets gentle 3s delay between requests to its own host.
- **Live log** — watch every URL being scraped in real time (per-source prefixed)
- **Resumable** — kill anytime, restart picks up where it left off
- **Gentle on servers** — 3-second delay between requests to SAME host (configurable)
- **Network resilient** — retries with exponential backoff on connection errors
- **Time-limited** — set max minutes (default unlimited)
- **Article-limited** — set max articles per source
- **Date filter** — only scrape articles since YYYY-MM-DD
- **Auto-save** — progress saved every 25 articles per source
- **Per-source control** — enable/disable each source individually
- **Live progress bar** — combined progress across all active sources
- **Per-source UA fallback** — ARY Urdu uses Googlebot UA (site blocks default)
- **Open folder button** — quick access to scraped data

## 🖱️ How to Use

1. **Double-click the executable** to launch
2. **Click "Browse..."** and pick a folder where data will be stored
3. **(Optional) Adjust settings**:
   - Delay: seconds between requests (default 3)
   - Max minutes: 0 = unlimited
   - Max articles/source: 0 = unlimited
   - Max sitemaps/source: how many sitemap files to walk (default 200)
   - Since date: only scrape articles after this date
4. **(Optional) Toggle sources** — Select All / Select None buttons
5. **Click "Start Scraping"** ▶
6. **Watch the live log** — every URL is logged as it's scraped
7. **To stop safely**: click "Stop (safe)" — saves after current article
8. **To resume**: just click "Start" again — skips already-scraped URLs

## 📁 Output Structure

After running, your project folder will contain:

```
your-project-folder/
├── data/
│   ├── url_queue.json                  ← All discovered URLs
│   ├── nawaiwaqt_articles.json         ← Scraped articles per source
│   ├── nawaiwaqt_scraped_urls.json     ← Set of URLs already attempted
│   ├── express_articles.json
│   ├── express_scraped_urls.json
│   ├── ... (one pair per source)
│   └── all_articles.json               ← Combined (auto-regenerated)
└── (no other files — app is self-contained)
```

## 🔧 How It Works

### Phase 1: URL Collection (sitemap-based)

For each source, the app:
1. Fetches the source's `sitemap.xml` (1 request)
2. Parses sub-sitemap URLs from the index
3. Walks each sub-sitemap (1 request each, 0.5s delay)
4. Extracts article URLs matching source-specific patterns
5. Saves the complete URL queue to `url_queue.json`

This phase is **very gentle** — just reads XML files. ~200 sitemap fetches per source.

### Phase 2: Article Scraping

For each URL in the queue (per source):
1. Skip if already scraped (resumable)
2. Fetch the article HTML (3s delay before next request)
3. Parse with BeautifulSoup (extract title + body)
4. Save to `<source>_articles.json`
5. Mark URL as scraped in `<source>_scraped_urls.json`
6. Save progress every 25 articles

## 🚀 Throughput

### Sequential mode (old)
With 3-second delay, one source at a time:

| Setting | Articles/hour | Articles/day |
|---------|--------------:|-------------:|
| 3s delay, 1 source | ~1,000 | ~24,000 |
| 3s delay, all 8 sources (sequential) | ~1,000 | ~24,000 |

### ⚡ Parallel mode (new default) — 8x faster!
One thread per source, all 8 sources scraped simultaneously:

| Setting | Articles/hour | Articles/day | Articles/month |
|---------|--------------:|-------------:|---------------:|
| 3s delay, 8 sources in parallel | **~8,000** | **~192,000** | **~5,760,000** |
| 2s delay, 8 sources in parallel | ~12,000 | ~288,000 | ~8,640,000 |
| 5s delay (extra gentle), 8 sources | ~4,800 | ~115,000 | ~3,450,000 |

**🎯 To hit 5M+ articles (your target):**
- 3s delay, parallel mode → **~26 days** of continuous scraping
- 2s delay, parallel mode → **~17 days**
- 3s delay, 24/7 for a month → **~5.7M articles** ✅

This is exactly what parallel mode was designed for. Run it 24/7 for a month and
you'll have a 5M+ article Urdu corpus — **5x bigger than the Mendeley Urdu News 1M dataset**.

## 🛡️ Safety Features

1. **Never re-scrapes a URL** — `<source>_scraped_urls.json` tracks everything
2. **Save every 25 articles** — at most you lose 24 articles of work on a crash
3. **Safe stop button** — finishes current article, saves state, exits cleanly
4. **Network retry** — 3 attempts with exponential backoff
5. **Rate-limit aware** — if server returns 429/503, waits 10-30s and retries
6. **Honest User-Agent** — identifies as academic research with repo URL
7. **Sequential per source** — no parallel workers hammering one server

## 🌐 Being Gentle on Servers

This app is designed to be a polite web citizen:

- **3-second default delay** between requests (configurable 1-60s)
- **Sequential per source** — never parallel requests to same host
- **Honest User-Agent** identifying academic research
- **Obeys 429/503** rate-limit responses
- **Sitemap-based discovery** — minimizes category-page requests

If you get blocked by a server (403 Forbidden), increase the delay to 5-10 seconds.

## 📝 Building from Source

### Prerequisites

- Python 3.10+
- pip

### Install dependencies

```bash
pip install requests beautifulsoup4 lxml pyinstaller
```

### Build executable

```bash
cd urdu_topic/gui_app
pyinstaller --clean UrduScraper.spec
```

Output will be in `dist/UrduScraper` (Linux/Mac) or `dist/UrduScraper.exe` (Windows).

### Run from source (without building)

```bash
pip install requests beautifulsoup4 lxml
python urdu_scraper_gui.py
```

## 🐛 Troubleshooting

**"Could not fetch main sitemap"** — Site may be down or blocking. Try again later,
or temporarily disable that source.

**"403 Forbidden" errors** — Server is blocking your IP. Increase delay to 5-10s.
If still blocked, wait a few hours and try again.

**App crashes on startup** — Make sure you have write access to your home directory
(the app saves config to `~/.urdu_scraper_config.json`).

**"Stop button doesn't work"** — The stop is graceful: it finishes the current article
first, then saves and exits. This can take up to ~15 seconds.

**Disk space warning** — Each article is ~2KB on average. 1M articles = ~2GB.
Make sure your project folder has enough space.

## 📜 License

MIT — see repository LICENSE.

## 🙏 Acknowledgments

This scraper is part of academic research on Urdu NLP at:
https://github.com/Farhan-ux/urdu_data

If you use this tool or the scraped data in your research, please cite:

```bibtex
@misc{urdu_data_2026,
  title={Urdu NLP Research: Survey, Dataset, and Topic Modeling Benchmark},
  author={Farhan Ch},
  year={2026},
  url={https://github.com/Farhan-ux/urdu_data}
}
```
