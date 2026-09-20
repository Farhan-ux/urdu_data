# 🎯 Month-Long Scraping Plan — Hit 5M+ Urdu Articles

## Goal
Scrape **5,000,000+ Urdu news articles** from 8 Pakistani news outlets using parallel mode.

## Time Required
- **~26 days** with 3s delay (default, gentle)
- **~17 days** with 2s delay (faster, still polite)
- **~12 days** with 1s delay (aggressive — only if no 403s)

## Step-by-Step

### Step 1: Build the App (one-time, 5 minutes)

**Windows:**
```cmd
git clone https://github.com/Farhan-ux/urdu_data.git
cd urdu_data\urdu_topic\gui_app
build_windows.bat
```
Output: `dist\UrduScraper.exe`

**Mac/Linux:**
```bash
git clone https://github.com/Farhan-ux/urdu_data.git
cd urdu_data/urdu_topic/gui_app
chmod +x build_mac_linux.sh
./build_mac_linux.sh
```
Output: `dist/UrduScraper`

### Step 2: Prepare Project Folder

Create a folder with **at least 10 GB free space** (5M articles × ~2KB each = ~10GB):
- Windows: `D:\urdu_scrape\`
- Mac/Linux: `~/urdu_scrape/`

### Step 3: Launch & Configure

1. Double-click `UrduScraper.exe` (or `./UrduScraper` on Mac/Linux)
2. Click **Browse...** → select your project folder
3. Verify these settings:
   - **Delay (sec)**: `3` (default — gentle on servers)
   - **Max minutes (0=∞)**: `0` (unlimited — let it run 24/7)
   - **Max articles/source (0=∞)**: `0` (unlimited)
   - **Max sitemaps/source**: `500` (increased from default 200 to get more historical articles)
   - **Since date**: leave blank (scrape all dates)
   - **Parallel mode**: ✅ ticked (default — 8x faster)
4. Sources: all 8 should be ticked (Select All)

### Step 4: Click Start

The app will:
1. **Phase 1** (~5 min): Fetch sitemaps from all 8 sources in parallel
2. **Phase 2** (24/7 for ~26 days): Scrape articles in parallel

You'll see live logs like:
```
[Nawa-i-Waqt] [25/2585403] scraped=25 fail=0 rate=125.0/min
[Express Urdu] [25/450000] scraped=25 fail=0 rate=125.0/min
[ARY Urdu] [25/352000] scraped=25 fail=0 rate=125.0/min
...
```

### Step 5: Daily Maintenance (5 min/day)

**Every 24 hours:**
1. Click **■ Stop (safe)** — saves after current article (~15 sec)
2. Wait for "Ready" status
3. Open project folder, check `data/` — should have 8 `*_articles.json` files
4. **Commit & push to GitHub**:
   ```bash
   cd urdu_data
   git add urdu_topic/data/
   git commit -m "Day N: scraped X more articles (total Y)"
   git push origin main
   ```
5. Click **▶ Start Scraping** to resume — it picks up where it stopped

### Step 6: Monitor Progress

**Live in app:**
- Progress bar shows combined % across all sources
- Log shows per-source counts every 25 articles
- Status bar shows total articles in project

**Check disk space:**
```bash
du -sh ~/urdu_scrape/data/
```

**Expected growth:**
| Day | Total articles | Disk used |
|-----|---------------:|----------:|
| 1   | ~192,000       | ~400 MB   |
| 5   | ~960,000       | ~2 GB     |
| 10  | ~1,920,000     | ~4 GB     |
| 15  | ~2,880,000     | ~6 GB     |
| 20  | ~3,840,000     | ~8 GB     |
| 26  | ~5,000,000     | ~10 GB    |

## Troubleshooting

### "403 Forbidden" errors for one source
- That source's server is blocking you
- **Fix**: Untick that source temporarily, continue with others
- **Try later**: Re-enable in 6-12 hours

### App crashes / computer restarts
- **No problem!** Just relaunch and click Start
- The app skips already-scraped URLs (tracked in `*_scraped_urls.json`)
- You lose at most 24 articles of progress (saved every 25)

### Network goes down
- App retries 3 times with exponential backoff
- If still failing, it marks the URL as failed and moves on
- When network returns, it continues normally

### Computer goes to sleep
- **Windows**: Settings → Power & sleep → "Never" for both
- **Mac**: System Settings → Energy → "Prevent automatic sleeping"
- **Linux**: `sudo systemctl mask sleep.target suspend.target`

### Disk space warning
- Each article is ~2KB
- 1M articles = 2GB, 5M articles = 10GB
- If running low: stop, commit/push to git, delete local data, restart

## Expected Final Result

After ~26 days of 24/7 parallel scraping:
- **5,000,000+ Urdu articles** across 8 sources
- **~10 GB** of JSON data
- **Date range**: 2002 → 2026 (24 years of Urdu news)
- **5x bigger** than the Mendeley Urdu News 1M dataset
- **Largest publicly available Urdu news corpus** in the world

## What to Do After Scraping

1. **Push final data to GitHub**:
   ```bash
   cd urdu_data
   git add urdu_topic/data/
   git commit -m "Final dataset: 5M+ Urdu news articles"
   git push origin main
   ```

2. **Re-run topic modeling** on the bigger dataset (I'll help with this):
   - Re-preprocess with the larger corpus
   - Re-train LDA, NMF, K-Means, etc.
   - Should see significantly better clustering performance
   - Update paper draft with new results

3. **Release dataset on HuggingFace** for maximum visibility:
   - Create a HuggingFace dataset repo
   - Upload the JSONL file
   - Add dataset card with stats and usage examples

4. **Submit paper** to a Q1 venue:
   - IEEE Access (fast turnaround, Q1 SCI)
   - Or ACL Findings / EMNLP Findings (CCF-A)
   - The 5M+ dataset + benchmark results = strong contribution

## TL;DR

```
Build app → Pick folder → Enable parallel mode → Start → Wait 26 days → 5M+ articles
```

That's it. The app does everything else automatically.
