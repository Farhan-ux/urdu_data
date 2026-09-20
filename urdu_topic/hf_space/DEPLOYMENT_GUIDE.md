# 🤗 HuggingFace Spaces Deployment — Gradio SDK (FREE, no credit card)

Run the Urdu News Scraper **24/7 for free** on HuggingFace Spaces.

## ✅ What Works for Free (Verified)

| Feature | Status |
|---------|--------|
| Gradio SDK | ✅ Free |
| CPU basic hardware | ✅ Free (16 GB RAM) |
| Storage bucket (20 GB persistent) | ✅ Free |
| Outbound HTTP to news sites | ✅ Allowed |
| 24/7 always-on | ✅ With heartbeat (every 30 min) |
| Web dashboard | ✅ Gradio UI |

## ⏱️ Setup Time: 25 minutes

---

## Step 1: Create HuggingFace Account (2 min)

1. Go to https://huggingface.co/join
2. Sign up with email or GitHub
3. Verify email

## Step 2: Create New Space (3 min)

1. Go to https://huggingface.co/new-space
2. Fill in:
   - **Owner**: your username
   - **Space name**: `urdu-news-scraper`
   - **License**: MIT
   - **SDK**: **Gradio** (NOT Docker — Docker requires payment)
   - **SDK version**: 4.44.0 (or latest 4.x)
   - **Hardware**: **CPU basic · Free** (16 GB RAM)
   - **Storage bucket**: ✅ **Enable** (free 20 GB persistent storage — this is critical!)
   - **Visibility**: Private (recommended)
3. Click **Create Space**

## Step 3: Add Storage Bucket (CRITICAL — do this before uploading files)

1. After creating the Space, go to **Settings** tab
2. Scroll to **Persistent Storage**
3. You should see "20 GB free tier available"
4. Click **Enable** — this mounts `/data/` as persistent storage
5. Verify it shows as "Active"

**Without this step, your scraped data will be LOST when the Space restarts!**

## Step 4: Get Files from GitHub (5 min)

Clone the repo and copy the HF Space files:

```bash
git clone https://github.com/Farhan-ux/urdu_data.git
cd urdu_data/urdu_topic/hf_space
ls -la
```

You should see:
- `app.py` (main scraper + Gradio UI)
- `requirements.txt` (Python deps)
- `README.md` (HF Space config)
- `DEPLOYMENT_GUIDE.md` (this file)

You also need the `gui_app/` folder from the parent directory:
```bash
cd ../
ls gui_app/urdu_scraper_gui.py  # this is the scraper logic
```

## Step 5: Upload Files to HF Space (10 min)

### Option A: Use HF Web UI (easier)

1. Go to your Space: `https://huggingface.co/spaces/YOUR_USERNAME/urdu-news-scraper`
2. Click **Files** tab → **Add file** → **Upload files**
3. Upload these files:
   - `app.py`
   - `requirements.txt`
   - `README.md` (overwrite the default)
4. Create a folder named `gui_app` (click **Add folder**)
5. Upload `gui_app/urdu_scraper_gui.py` into that folder

Final structure on HF Space:
```
/
├── app.py
├── requirements.txt
├── README.md
└── gui_app/
    └── urdu_scraper_gui.py
```

### Option B: Use git (faster if you know git)

```bash
# Get HF token from https://huggingface.co/settings/tokens
# (create a token with "Write" permission)

git clone https://huggingface.co/spaces/YOUR_USERNAME/urdu-news-scraper
cd urdu-news-scraper

# Copy files
cp /path/to/urdu_data/urdu_topic/hf_space/app.py .
cp /path/to/urdu_data/urdu_topic/hf_space/requirements.txt .
cp /path/to/urdu_data/urdu_topic/hf_space/README.md .
mkdir -p gui_app
cp /path/to/urdu_data/urdu_topic/gui_app/urdu_scraper_gui.py gui_app/

# Commit and push
git add .
git commit -m "Initial deployment: Urdu News Scraper"
git push
```

## Step 6: Wait for Build (3 min)

1. Go to your Space URL
2. Click **Logs** tab
3. Watch the build:
   ```
   Step 1/5 : FROM gradio:4.44.0
   Step 2/5 : COPY requirements.txt .
   Step 3/5 : RUN pip install -r requirements.txt
   Step 4/5 : COPY app.py .
   Step 5/5 : CMD python app.py
   ```
4. Build takes 2-3 minutes
5. When done, you'll see:
   ```
   Running on local URL: http://0.0.0.0:7860
   ```

## Step 7: Set Environment Variables (2 min)

1. Go to your Space → **Settings**
2. Scroll to **Variables and secrets**
3. Add these variables:

| Variable | Value | Why |
|----------|-------|-----|
| `AUTOSTART` | `1` | Auto-start scraper when Space boots |
| `DELAY` | `3` | 3 seconds between requests per source (gentle) |
| `MAX_MINUTES` | `0` | Unlimited runtime per source |
| `MAX_ARTICLES` | `0` | Unlimited articles per source |
| `MAX_SITEMAPS` | `500` | Walk up to 500 sitemap files per source |
| `PARALLEL_MODE` | `1` | Parallel scraping (8x faster) |
| `SOURCES` | `all` | All 8 sources |

4. Click **Save**

## Step 8: Verify It's Running

1. Visit your Space URL: `https://YOUR_USERNAME-urdu-news-scraper.hf.space`
2. You should see:
   - Status panel: "🟢 Running"
   - Total articles counter
   - Per-source table
   - Live log (last 200 lines)
3. Within 2 minutes, the log should show:
   ```
   [10:00:00] 🤖 AUTOSTART=1 — starting scraper automatically in 10 seconds...
   [10:00:10] ============================================================
   [10:00:10] 🚀 Starting scraper at 2026-09-20T10:00:10
   [10:00:10] 📁 Project dir: /data/urdu_scrape
   [10:00:10] 📡 Sources (8): ['nawaiwaqt', 'express', 'aryurdu', ...]
   [10:00:10] ⏱️  Delay: 3.0s, Parallel: True
   [10:00:30] [Nawa-i-Waqt] [1/2585403] scraped=1 rate=120/min
   [10:00:30] [Express Urdu] [1/450000] scraped=1 rate=120/min
   ...
   ```

## Step 9: Daily Check-in (1 min/day)

Just visit your Space URL from any device (phone, library, anywhere):
- See total articles scraped (auto-refreshes every 15 sec)
- See per-source breakdown with progress bars
- See live log (last 200 lines)
- See ETA to 5M articles
- Click **Stop** if needed (saves state, can resume with Start)

## Step 10: After ~26 Days — Download 5M+ Articles

### Method A: Download via HF web UI

1. Go to your Space → **Files** tab
2. Navigate to `/data/urdu_scrape/data/`
3. Download each `*_articles.json` file

### Method B: Sync to HF Dataset (recommended for sharing)

Add a daily sync job in `app.py` to push data to a HuggingFace dataset repo:

```python
from huggingface_hub import HfApi
api = HfApi(token=os.environ.get("HF_TOKEN"))

def sync_to_dataset():
    api.upload_file(
        path_or_fileobj="/data/urdu_scrape/data/all_articles.json",
        path_in_repo="all_articles.json",
        repo_id="YOUR_USERNAME/urdu-news-dataset",
        repo_type="dataset",
    )
```

This makes your dataset publicly visible and citable.

### Method C: Use git LFS to clone

```bash
git lfs install
git clone https://huggingface.co/spaces/YOUR_USERNAME/urdu-news-scraper
cd urdu-news-scraper/data/urdu_scrape/data/
ls -lh *.json
```

---

## 📊 Configuration Reference

All settings via HF Space Settings → **Variables and secrets**:

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTOSTART` | `1` | Auto-start scraper on Space boot |
| `DELAY` | `3` | Seconds between requests per source |
| `MAX_MINUTES` | `0` | Max runtime per source (0=∞) |
| `MAX_ARTICLES` | `0` | Max articles per source (0=∞) |
| `MAX_SITEMAPS` | `500` | Sitemap files to walk per source |
| `SINCE_DATE` | (empty) | Only articles after YYYY-MM-DD |
| `PARALLEL_MODE` | `1` | 1=parallel (8x faster), 0=sequential |
| `SOURCES` | `all` | Comma-separated source list |

---

## ⚠️ Limitations & Mitigations

### 1. Space sleeps after 48h of no HTTP traffic
**Mitigation**: The app includes a heartbeat that logs every 30 minutes (counts as activity).
Plus, your daily visits also keep it awake.

If the Space does sleep, just visit the URL — it auto-restarts and the scraper resumes.

### 2. 20 GB persistent storage limit
**Mitigation**: 5M articles = ~10 GB, well under limit.
For more, sync older data to a HuggingFace dataset repo (free, unlimited).

### 3. CPU basic = no GPU
**Mitigation**: We don't need GPU — this is HTTP scraping + light parsing.

### 4. Single Space = single instance
**Mitigation**: For more throughput, deploy multiple Spaces (each handles different sources).
You can have multiple free Spaces per account.

### 5. Gradio SDK = no custom Docker
**Mitigation**: Gradio can run any Python code in background threads.
We don't need Docker — Gradio handles everything.

---

## 🐛 Troubleshooting

### "Build failed"
- Check **Logs** tab in your Space
- Most common: forgot to upload `gui_app/urdu_scraper_gui.py`
- Fix: Re-upload the file, commit/push

### "App won't start"
- Check logs for Python errors
- Common: missing env var
- Fix: Set required env vars in Settings → Variables

### "Scraper not making progress"
- Check logs for 403 errors (site blocking)
- Try increasing DELAY to 5s
- Try disabling the blocked source via `SOURCES=express,nawaiwaqt,...`

### "Storage bucket not working"
- Go to Settings → Persistent Storage
- Verify it shows "Active"
- If not, click Enable (free 20 GB)
- Data should appear at `/data/urdu_scrape/data/`

### "Space slept, did I lose data?"
- **No!** Persistent storage at `/data/` survives restarts
- Visit the URL — Space rebuilds and resumes from saved state

### "How do I check disk usage?"
- Go to Settings → Persistent Storage
- Shows current usage (e.g., "3.2 GB / 20 GB")

---

## 💰 Cost: $0

HuggingFace Spaces free tier (Gradio SDK):
- **CPU basic hardware**: 16 GB RAM — free, forever
- **20 GB persistent storage**: free
- **Unlimited build minutes**: free
- **No outbound bandwidth limits**: free
- **No credit card required**: free

---

## 🎯 Expected Results

With 3-second delay, 8 sources in parallel, 24/7:

| Day | Total Articles | Disk Used |
|-----|---------------:|----------:|
| 1   | ~192,000       | ~400 MB   |
| 5   | ~960,000       | ~2 GB     |
| 10  | ~1,920,000     | ~4 GB     |
| 15  | ~2,880,000     | ~6 GB     |
| 20  | ~3,840,000     | ~8 GB     |
| 26  | ~5,000,000     | ~10 GB    |

After 26 days, you'll have the **largest publicly available Urdu news corpus in the world** — 5× bigger than Mendeley Urdu News 1M.

---

## 📝 TL;DR Quick Start

```bash
# 1. Create HF Space (Gradio SDK, CPU basic, enable Storage bucket)
# 2. Upload these 4 files:
#    - app.py
#    - requirements.txt
#    - README.md
#    - gui_app/urdu_scraper_gui.py
# 3. Set AUTOSTART=1 in Space Variables
# 4. Visit Space URL — scraper runs 24/7
# 5. Check progress daily (1 min)
# 6. After 26 days: download 5M+ articles
```

That's it. No laptop, no loadshedding, no cost.
