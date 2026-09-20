# 🤗 HuggingFace Spaces Deployment — Run Scraper 24/7 for Free

This guide walks you through deploying the Urdu News Scraper to HuggingFace Spaces,
where it can run **24/7 for free** with persistent storage.

## Why HuggingFace Spaces?

- ✅ **Free forever** — no credit card required
- ✅ **16 GB RAM, 50 GB persistent disk** — enough for ~5M articles (~10 GB)
- ✅ **Always-on** — runs 24/7 (with a heartbeat to prevent sleep)
- ✅ **Persistent storage** — data survives restarts at `/data/`
- ✅ **Outbound HTTP allowed** — can scrape any news site
- ✅ **Web dashboard** — view live progress from your phone
- ✅ **No laptop needed** — works during loadshedding

## Setup Time: ~30 minutes

## Step 1: Create a HuggingFace Account (2 min)

1. Go to https://huggingface.co/join
2. Sign up with your email or GitHub account
3. Verify your email

## Step 2: Create a New Space (5 min)

1. Go to https://huggingface.co/new-space
2. **Owner**: your username
3. **Space name**: `urdu-news-scraper`
4. **License**: MIT
5. **SDK**: **Docker** (important — not Gradio/Streamlit)
6. **Hardware**: **CPU basic (free, 16 GB RAM, 50 GB disk)**
7. **Visibility**: Private (recommended — your scraped data stays private)
8. Click **Create Space**

## Step 3: Upload the Files (10 min)

You have two options:

### Option A: Use the HF Web UI (easy)

1. Open your new Space: `https://huggingface.co/spaces/<your-username>/urdu-news-scraper`
2. Click **Files** → **Add file** → **Upload files**
3. Drag and drop these files from your local `urdu_topic/hf_space/` folder:
   - `app.py`
   - `Dockerfile`
   - `requirements.txt`
   - `README.md` (the HF Space one, not the main repo README)
4. **Important**: also upload the `gui_app` folder contents — create a subfolder called `gui_app/` and upload `urdu_scraper_gui.py` into it

### Option B: Use git (recommended)

```bash
# Clone your HF Space (use your HF token from https://huggingface.co/settings/tokens)
git clone https://huggingface.co/spaces/<your-username>/urdu-news-scraper
cd urdu-news-scraper

# Copy files from this repo
cp -r /path/to/urdu_data/urdu_topic/hf_space/* .
mkdir -p gui_app
cp /path/to/urdu_data/urdu_topic/gui_app/urdu_scraper_gui.py gui_app/

# Commit and push
git add .
git commit -m "Initial deployment"
git push
```

## Step 4: Wait for Build (5 min)

1. Go to your Space URL
2. Watch the **Logs** tab — it will show the Docker image building
3. Build takes ~3-5 minutes (installing Python deps)
4. When done, you'll see:
   ```
   Running on local URL: http://0.0.0.0:7860
   ```

## Step 5: Verify It's Running

1. Open your Space URL in browser: `https://<your-username>-urdu-news-scraper.hf.space`
2. You should see a web dashboard with:
   - **Start** / **Stop** buttons
   - **Status** panel showing all 8 sources
   - **Live Log** showing scraper activity
3. The scraper **auto-starts on boot** (env var `AUTOSTART=1` in Dockerfile)
4. Within 5 minutes you should see logs like:
   ```
   [10:00:05] AUTOSTART=1 detected — starting scraper automatically
   [10:00:10] ============================================================
   [10:00:10] Starting scraper at 2026-09-20T10:00:10
   [10:00:10] Project dir: /data/urdu_scrape
   [10:00:10] Sources: ['nawaiwaqt', 'express', 'aryurdu', ...]
   [10:00:10] Delay: 3.0s, parallel: True
   ```

## Step 6: Check Progress Daily (1 min/day)

Just visit your Space URL anytime — from your phone, library, anywhere:
- See total articles scraped
- See per-source breakdown
- See live log (last 100 lines)
- Click **Stop** if needed (saves state, can resume with Start)

## Step 7: Download Data When Done (~26 days)

After ~26 days of 24/7 scraping, you'll have 5M+ articles.

### Option A: Download via HF web UI

1. Go to your Space → **Files** tab
2. Navigate to `/data/urdu_scrape/data/`
3. Download each `*_articles.json` file

### Option B: Use git LFS

```bash
# Install git-lfs
git lfs install

# Clone your space (includes /data/ if you've set up persistent storage)
git clone https://huggingface.co/spaces/<your-username>/urdu-news-scraper
cd urdu-news-scraper/data/urdu_scrape/data/
ls -lh *.json
```

### Option C: Sync to HF Dataset (recommended)

Add a daily job in `app.py` to push data to a HuggingFace dataset repo:

```python
# In app.py — runs daily
from huggingface_hub import HfApi
api = HfApi(token=os.environ.get("HF_TOKEN"))
api.upload_file(
    path_or_fileobj="/data/urdu_scrape/data/all_articles.json",
    path_in_repo="all_articles.json",
    repo_id="your-username/urdu-news-dataset",
    repo_type="dataset",
)
```

This way your dataset is publicly visible and citable.

## Configuration (Optional)

You can override defaults by setting environment variables in the HF Space settings:

1. Go to your Space → **Settings**
2. Scroll to **Variables and secrets**
3. Add any of these:

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTOSTART` | `1` | Auto-start scraper on boot (set to `0` to disable) |
| `DELAY` | `3` | Seconds between requests per source |
| `MAX_MINUTES` | `0` | Max minutes per source (0 = unlimited) |
| `MAX_ARTICLES` | `0` | Max articles per source (0 = unlimited) |
| `MAX_SITEMAPS` | `500` | Max sitemap files to walk per source |
| `SINCE_DATE` | (empty) | Only scrape articles after this date (YYYY-MM-DD) |
| `PARALLEL_MODE` | `1` | 1 = parallel (8x faster), 0 = sequential |
| `SOURCES` | `all` | Comma-separated list of sources (e.g., `express,aryurdu`) |

## Cost: $0

HuggingFace Spaces free tier includes:
- **CPU basic hardware**: 16 GB RAM, 50 GB disk — free, forever
- **Unlimited build minutes**
- **No outbound bandwidth limits**

## Limitations & Mitigations

### 1. Space sleeps after 48h of no HTTP traffic
**Mitigation**: The app includes a heartbeat that logs every 30 minutes, which counts as activity. Plus, your daily visits to check progress also keep it awake.

If the Space does sleep, just visit the URL — it auto-restarts and the scraper resumes (it's resumable by design).

### 2. 50 GB disk limit
**Mitigation**: 5M articles = ~10 GB, well under the limit. If you want more, sync older data to a HuggingFace dataset repo (free, unlimited).

### 3. No GPU on free tier
**Mitigation**: We don't need GPU — this is just HTTP scraping.

### 4. Single instance
**Mitigation**: One Space = one scraper instance. For more throughput, deploy multiple Spaces (each handles different sources).

## Troubleshooting

### "Build failed"
- Check the **Logs** tab in your Space
- Most common issue: forgot to upload `gui_app/urdu_scraper_gui.py`
- Fix: re-upload the file, push to git

### "App won't start"
- Check logs for Python errors
- Common issue: missing env var
- Fix: set required env vars in Settings → Variables

### "Scraper not making progress"
- Check logs for 403 errors (site blocking)
- Try reducing DELAY to 5s
- Try disabling the blocked source

### "Space slept, data lost?"
- **No!** Persistent storage at `/data/` survives restarts
- Visit the URL — Space rebuilds and resumes from saved state

## Alternative: Oracle Cloud Always Free (more powerful)

If you want even more resources (24 GB RAM, 200 GB disk, 4 ARM cores):

1. Sign up at https://www.oracle.com/cloud/free/ (requires credit card for verification, won't be charged)
2. Create an **Always Free** ARM VM (Ampere A1)
3. SSH into the VM
4. Clone the repo, run the headless scraper:
   ```bash
   git clone https://github.com/Farhan-ux/urdu_data.git
   cd urdu_data/urdu_topic/hf_space
   pip install -r requirements.txt
   python app.py
   ```
5. Use `screen` or `tmux` to keep it running after SSH disconnect

This gives you a real Linux VM with no time limits — best for very long scrapes.

## Summary

**For 95% of users: HuggingFace Spaces is the answer.**
- Free, no credit card, 24/7, persistent, web dashboard
- Set up in 30 minutes
- Check progress from your phone in 1 minute/day
- After 26 days: download 5M+ articles
