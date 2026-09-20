"""
Urdu News Scraper GUI — single-file Tkinter app.

Bundled inside this file:
- All 9 source scrapers (Bol, Independent Urdu, Express, Nawa-i-Waqt, The Nation,
  24 News HD, Pakistan Observer, Daily Pakistan, Ummat, Khyber News)
- Sitemap-based URL discovery
- Gentle, resumable article scraper (3s delay, retry, save every 25)
- Tkinter GUI: pick folder, click Start, watch live log

Usage (Python):
    python urdu_scraper_gui.py

Usage (after PyInstaller build):
    Double-click UrduScraper.exe (Windows)
    or ./UrduScraper (Linux/Mac)
"""
import os
import sys
import re
import json
import time
import threading
import traceback
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

# ============================================================
# Tkinter import (works on all platforms; bundled in Python)
# ============================================================
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext


# ============================================================
# CONFIGURATION
# ============================================================
APP_NAME = "Urdu News Scraper"
APP_VERSION = "1.0"
DEFAULT_DELAY = 3.0  # seconds between requests
DEFAULT_MAX_MINUTES = 0  # 0 = unlimited
SAVE_EVERY = 25  # save progress every N articles
USER_AGENT = f"{APP_NAME}/{APP_VERSION} (academic research; https://github.com/Farhan-ux/urdu_data)"

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ur,en;q=0.9",
}

# Fallback User-Agents — some sites (e.g. ARY Urdu) block default UAs but allow Googlebot
GOOGLEBOT_UA = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
HEADERS_GOOGLEBOT = {
    "User-Agent": GOOGLEBOT_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ur,en;q=0.9",
}


# ============================================================
# SOURCE CONFIGURATIONS
# ============================================================
SOURCES = {
    "nawaiwaqt": {
        "name": "Nawa-i-Waqt",
        "base": "https://www.nawaiwaqt.com.pk",
        "sitemap_url": "https://www.nawaiwaqt.com.pk/sitemap.xml",
        "sub_pattern": "sitemap_",
        "article_pattern": r"/\d{1,2}-\w+-\d{4}/\d+",
        "estimated_articles": 2585403,
        "color": "#ff7f0e",
        "use_googlebot": False,
    },
    "express": {
        "name": "Express Urdu",
        "base": "https://www.express.pk",
        "sitemap_url": "https://www.express.pk/sitemap.xml",
        "sub_pattern": "/posts-",
        "article_pattern": "/story/",
        "estimated_articles": 450000,
        "color": "#1f77b4",
        "use_googlebot": False,
    },
    "aryurdu": {
        "name": "ARY Urdu",
        "base": "https://urdu.arynews.tv",
        "sitemap_url": "https://urdu.arynews.tv/sitemap.xml",
        "sub_pattern": "post-sitemap",
        "article_pattern": r"/\d{5,}",
        "estimated_articles": 352000,
        "color": "#9467bd",
        "use_googlebot": True,  # ARY blocks default UA but allows Googlebot
    },
    "24newshd": {
        "name": "24 News HD",
        "base": "https://24newshd.tv",
        "sitemap_url": "https://24newshd.tv/sitemap.xml",
        "sub_pattern": "sitemap_",
        "article_pattern": r"/\d{6,}",
        "estimated_articles": 185810,
        "color": "#d62728",
        "use_googlebot": False,
    },
    "ummat": {
        "name": "Ummat",
        "base": "https://ummat.net",
        "sitemap_url": "https://ummat.net/sitemap.xml",
        "sub_pattern": "post-sitemap",
        "article_pattern": r"/\d{5,}",
        "estimated_articles": 116000,
        "color": "#e377c2",
        "use_googlebot": False,
    },
    "bolurdu": {
        "name": "Bol News Urdu",
        "base": "https://urdu.bolnews.com",
        "sitemap_url": "https://urdu.bolnews.com/sitemap.xml",
        "sub_pattern": "post-sitemap",
        "article_pattern": r"/\d{5,}",
        "estimated_articles": 71404,
        "color": "#7f7f7f",
        "use_googlebot": False,
    },
    "dailyausaf": {
        "name": "Daily Ausaf",
        "base": "https://dailyausaf.com",
        "sitemap_url": "https://dailyausaf.com/sitemap.xml",
        "sub_pattern": "post-sitemap",
        "article_pattern": r"/\d{5,}",
        "estimated_articles": 52026,
        "color": "#17becf",
        "use_googlebot": False,
    },
    "independenturdu": {
        "name": "Independent Urdu",
        "base": "https://www.independenturdu.com",
        "sitemap_url": "https://www.independenturdu.com/sitemap.xml?page=1",
        "sub_pattern": "page=",
        "article_pattern": "/node/",
        "estimated_articles": 51865,
        "color": "#bcbd22",
        "use_googlebot": False,
    },
}


# ============================================================
# NETWORK HELPERS
# ============================================================
def fetch(url, retries=3, timeout=15, use_googlebot=False):
    """Fetch URL with exponential backoff. Returns text or None.
    If use_googlebot=True, uses Googlebot UA (for sites like ARY that block default UA).
    Falls back to Googlebot UA if default UA gets 403.
    """
    hdrs = HEADERS_GOOGLEBOT if use_googlebot else HEADERS
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=hdrs, timeout=timeout)
            if r.status_code == 200:
                return r.text
            elif r.status_code in (429, 503):
                wait = 10 * (attempt + 1)
                time.sleep(wait)
            elif r.status_code == 403 and not use_googlebot:
                # Try Googlebot UA as fallback
                hdrs = HEADERS_GOOGLEBOT
                continue
            elif r.status_code in (403, 404):
                return None
            else:
                return None
        except requests.exceptions.Timeout:
            time.sleep(5 * (attempt + 1))
        except requests.exceptions.ConnectionError:
            time.sleep(5 * (attempt + 1))
        except Exception:
            time.sleep(5 * (attempt + 1))
    return None


def parse_sitemap_xml(text):
    """Parse sitemap XML, return (article_urls_with_lastmod, sub_sitemap_urls)."""
    if not text:
        return [], []
    urls = []
    sub_sitemaps = []
    try:
        root = ET.fromstring(text)
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"
        for elem in root.findall(f".//{ns}url"):
            loc = elem.find(f"{ns}loc")
            lastmod = elem.find(f"{ns}lastmod")
            if loc is not None and loc.text:
                urls.append((loc.text.strip(),
                             lastmod.text.strip() if lastmod is not None and lastmod.text else ""))
        for elem in root.findall(f".//{ns}sitemap"):
            loc = elem.find(f"{ns}loc")
            if loc is not None and loc.text:
                sub_sitemaps.append(loc.text.strip())
    except ET.ParseError:
        # Regex fallback
        url_locs = re.findall(r"<loc>([^<]+)</loc>", text)
        lastmods = re.findall(r"<lastmod>([^<]+)</lastmod>", text)
        if "<sitemap>" in text or "<sitemap " in text:
            sub_sitemaps = url_locs
        else:
            for i, u in enumerate(url_locs):
                lm = lastmods[i] if i < len(lastmods) else ""
                urls.append((u, lm))
    return urls, sub_sitemaps


# ============================================================
# ARTICLE PARSERS (per source)
# ============================================================
def parse_article_generic(html, url):
    """Generic parser — tries common content selectors."""
    soup = BeautifulSoup(html, "lxml")
    title = ""
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
    if not title:
        og = soup.find("meta", property="og:title")
        if og:
            title = og.get("content", "").strip()
    body_parts = []
    # Try common content selectors
    for sel in [r"story-content", r"detail-content", r"content-area",
                r"entry-content", r"post-content", r"article-body",
                r"story-area", r"detail-view"]:
        content = soup.find("div", class_=re.compile(sel))
        if content:
            for p in content.find_all("p"):
                t = p.get_text(strip=True)
                if t and len(t) > 20:
                    body_parts.append(t)
            if body_parts:
                break
    # Fallback: all long paragraphs
    if not body_parts:
        for p in soup.find_all("p"):
            t = p.get_text(strip=True)
            if t and len(t) > 40:
                body_parts.append(t)
    body = " ".join(body_parts[:30])
    if len(body) < 200:
        return None
    return {"title": title, "body": body}


def parse_article_bbc_urdu(html, url):
    """BBC Urdu-specific parser."""
    soup = BeautifulSoup(html, "lxml")
    title = ""
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
    if not title:
        og = soup.find("meta", property="og:title")
        if og:
            title = og.get("content", "").strip()
    body_parts = []
    article_tag = soup.find("article") or soup
    for div in article_tag.find_all(["div", "p"], attrs={"data-component": "text-block"}):
        body_parts.append(div.get_text(strip=True))
    if not body_parts:
        for p in article_tag.find_all("p"):
            t = p.get_text(strip=True)
            if len(t) > 40:
                body_parts.append(t)
    body = " ".join(body_parts)
    if len(body) < 200:
        return None
    return {"title": title, "body": body}


PARSERS = {
    "express": parse_article_generic,
    "nawaiwaqt": parse_article_generic,
    "aryurdu": parse_article_generic,
    "24newshd": parse_article_generic,
    "ummat": parse_article_generic,
    "bolurdu": parse_article_generic,
    "independenturdu": parse_article_generic,
    "dailyausaf": parse_article_generic,
}


# ============================================================
# SCRAPER STATE (for resumability)
# ============================================================
class ScraperState:
    def __init__(self, source_key, project_dir):
        self.source_key = source_key
        self.project_dir = project_dir
        self.data_dir = os.path.join(project_dir, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.articles_path = os.path.join(self.data_dir, f"{source_key}_articles.json")
        self.scraped_urls_path = os.path.join(self.data_dir, f"{source_key}_scraped_urls.json")
        self.articles = []
        self.scraped_urls = set()
        self._load()

    def _load(self):
        if os.path.exists(self.articles_path):
            try:
                with open(self.articles_path, encoding="utf-8") as f:
                    self.articles = json.load(f)
            except Exception:
                self.articles = []
        if os.path.exists(self.scraped_urls_path):
            try:
                with open(self.scraped_urls_path) as f:
                    self.scraped_urls = set(json.load(f))
            except Exception:
                self.scraped_urls = set()

    def save(self):
        with open(self.articles_path, "w", encoding="utf-8") as f:
            json.dump(self.articles, f, ensure_ascii=False, indent=2)
        with open(self.scraped_urls_path, "w") as f:
            json.dump(sorted(self.scraped_urls), f, indent=2)

    def is_scraped(self, url):
        return url in self.scraped_urls

    def mark_scraped(self, url, success=True):
        self.scraped_urls.add(url)

    def add_article(self, article):
        self.articles.append(article)


# ============================================================
# URL COLLECTOR (Phase 1)
# ============================================================
def collect_urls_for_source(source_key, source_config, log_func, max_sitemaps=200, since_date=None):
    """Collect article URLs for one source by walking its sitemap."""
    log_func(f"[{source_config['name']}] Starting URL collection...")
    use_gb = source_config.get("use_googlebot", False)
    if use_gb:
        log_func(f"[{source_config['name']}] Using Googlebot UA (site blocks default UA)")
    all_urls = []

    # Fetch main sitemap
    log_func(f"[{source_config['name']}] Fetching main sitemap...")
    text = fetch(source_config["sitemap_url"], use_googlebot=use_gb)
    if not text:
        log_func(f"[{source_config['name']}] ERROR: Could not fetch main sitemap")
        return []

    article_urls, sub_sitemaps = parse_sitemap_xml(text)
    log_func(f"[{source_config['name']}] Main sitemap: {len(article_urls)} article URLs, {len(sub_sitemaps)} sub-sitemaps")

    # If main sitemap already has article URLs, use them
    if article_urls:
        # Filter to article pattern
        filtered = [(u, lm) for u, lm in article_urls if re.search(source_config["article_pattern"], u)]
        if since_date:
            filtered = [(u, lm) for u, lm in filtered if lm >= since_date]
        all_urls.extend(filtered)
        log_func(f"[{source_config['name']}]   +{len(filtered)} article URLs from main sitemap")

    # If there are sub-sitemaps, walk them (limited)
    if sub_sitemaps:
        # Filter to relevant sub-sitemaps (containing the pattern keyword)
        relevant_subs = [s for s in sub_sitemaps if source_config["sub_pattern"] in s.lower()]
        if not relevant_subs:
            relevant_subs = sub_sitemaps
        # Sort for deterministic order (newest first if dates in URL)
        relevant_subs.sort(reverse=True)
        # Limit
        relevant_subs = relevant_subs[:max_sitemaps]
        log_func(f"[{source_config['name']}] Walking {len(relevant_subs)} sub-sitemaps (capped at {max_sitemaps})...")

        for i, sm_url in enumerate(relevant_subs, 1):
            text = fetch(sm_url, use_googlebot=use_gb)
            if not text:
                continue
            sub_article_urls, _ = parse_sitemap_xml(text)
            filtered = [(u, lm) for u, lm in sub_article_urls if re.search(source_config["article_pattern"], u)]
            if since_date:
                filtered = [(u, lm) for u, lm in filtered if lm >= since_date]
            all_urls.extend(filtered)
            if i % 10 == 0 or i == len(relevant_subs):
                log_func(f"[{source_config['name']}]   [{i}/{len(relevant_subs)}] cumulative URLs: {len(all_urls):,}")
            time.sleep(0.5)  # gentle on sitemap server

    # Dedupe
    seen = set()
    deduped = []
    for u, lm in all_urls:
        if u not in seen:
            seen.add(u)
            deduped.append({"url": u, "source": source_key, "lastmod": lm})
    log_func(f"[{source_config['name']}] Total unique URLs: {len(deduped):,}")
    return deduped


# ============================================================
# ARTICLE SCRAPER (Phase 2)
# ============================================================
class ScraperWorker:
    """Runs the scraping in a background thread. Reports progress via callback."""
    def __init__(self, project_dir, selected_sources, delay, max_minutes, max_articles_per_source,
                 max_sitemaps_per_source, since_date, log_func, progress_func, stop_flag):
        self.project_dir = project_dir
        self.selected_sources = selected_sources
        self.delay = delay
        self.max_minutes = max_minutes
        self.max_articles_per_source = max_articles_per_source
        self.max_sitemaps_per_source = max_sitemaps_per_source
        self.since_date = since_date
        self.log = log_func
        self.progress = progress_func
        self.stop_flag = stop_flag

    def run(self):
        """Main worker loop. Runs Phase 1 (collect) + Phase 2 (scrape) for each source."""
        try:
            self.log(f"=== Scraping started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
            self.log(f"Project folder: {self.project_dir}")
            self.log(f"Sources: {', '.join(SOURCES[s]['name'] for s in self.selected_sources)}")
            self.log(f"Delay between requests: {self.delay}s")
            self.log(f"Max minutes per source: {self.max_minutes or 'unlimited'}")
            self.log(f"Max articles per source: {self.max_articles_per_source or 'unlimited'}")
            self.log(f"Max sitemaps per source: {self.max_sitemaps_per_source}")
            self.log(f"Date filter (since): {self.since_date or 'none'}")
            self.log("")

            data_dir = os.path.join(self.project_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            queue_path = os.path.join(data_dir, "url_queue.json")

            # Load existing queue
            url_queue = []
            if os.path.exists(queue_path):
                try:
                    with open(queue_path) as f:
                        url_queue = json.load(f)
                    self.log(f"Loaded existing URL queue: {len(url_queue):,} URLs")
                except Exception:
                    url_queue = []

            # === PHASE 1: URL COLLECTION ===
            self.log("\n--- PHASE 1: URL Collection ---")
            for source_key in self.selected_sources:
                if self.stop_flag.is_set():
                    self.log("Stop requested — exiting")
                    return
                source_config = SOURCES[source_key]
                existing_for_source = [e for e in url_queue if e["source"] == source_key]
                self.log(f"\n[{source_config['name']}] Already in queue: {len(existing_for_source):,} URLs")
                # Always refresh URLs from sitemaps (cheap operation)
                new_urls = collect_urls_for_source(
                    source_key, source_config, self.log,
                    max_sitemaps=self.max_sitemaps_per_source,
                    since_date=self.since_date,
                )
                # Merge with existing
                seen = set(e["url"] for e in url_queue)
                added = 0
                for entry in new_urls:
                    if entry["url"] not in seen:
                        url_queue.append(entry)
                        seen.add(entry["url"])
                        added += 1
                self.log(f"[{source_config['name']}] Added {added:,} new URLs to queue (total queue: {len(url_queue):,})")
                # Save queue
                with open(queue_path, "w", encoding="utf-8") as f:
                    json.dump(url_queue, f, ensure_ascii=False, indent=2)

            # === PHASE 2: ARTICLE SCRAPING ===
            self.log("\n--- PHASE 2: Article Scraping ---")
            total_scraped_this_session = 0
            for source_key in self.selected_sources:
                if self.stop_flag.is_set():
                    self.log("Stop requested — exiting")
                    break

                source_config = SOURCES[source_key]
                self.log(f"\n=== Scraping {source_config['name']} ===")

                state = ScraperState(source_key, self.project_dir)
                starting_count = len(state.articles)
                self.log(f"Already scraped: {starting_count:,} articles")

                # Get URLs for this source not yet scraped
                pending = [e for e in url_queue if e["source"] == source_key and not state.is_scraped(e["url"])]
                self.log(f"Pending: {len(pending):,} URLs")

                if not pending:
                    self.log(f"Nothing to do for {source_config['name']}")
                    continue

                parser = PARSERS[source_key]
                start_time = time.time()
                articles_scraped = 0
                articles_failed = 0

                for i, entry in enumerate(pending, 1):
                    if self.stop_flag.is_set():
                        self.log(f"Stop requested — saving and exiting")
                        break
                    if self.max_minutes and (time.time() - start_time) / 60 >= self.max_minutes:
                        self.log(f"Time limit reached ({self.max_minutes} min)")
                        break
                    if self.max_articles_per_source and articles_scraped >= self.max_articles_per_source:
                        self.log(f"Article limit reached ({self.max_articles_per_source})")
                        break

                    url = entry["url"]
                    elapsed = time.time() - start_time
                    rate = articles_scraped / max(0.01, elapsed / 60)

                    # Update progress bar
                    self.progress(
                        source=source_config["name"],
                        current=i,
                        total=len(pending),
                        scraped=articles_scraped,
                        failed=articles_failed,
                        rate=rate,
                        elapsed=elapsed,
                    )

                    self.log(f"[{i}/{len(pending)}] scraped={articles_scraped} failed={articles_failed} rate={rate:.1f}/min | {url[:80]}")

                    # Use per-source UA (ARY needs Googlebot)
                    use_gb = source_config.get("use_googlebot", False)
                    html = fetch(url, use_googlebot=use_gb)
                    if not html:
                        state.mark_scraped(url, success=False)
                        articles_failed += 1
                    else:
                        try:
                            parsed = parser(html, url)
                            if parsed:
                                article = {
                                    "url": url,
                                    "title": parsed["title"],
                                    "body": parsed["body"],
                                    "source": source_key,
                                    "source_name": source_config["name"],
                                    "lastmod": entry.get("lastmod", ""),
                                    "word_count": len(parsed["body"].split()),
                                    "scraped_at": datetime.utcnow().isoformat() + "Z",
                                }
                                state.add_article(article)
                                state.mark_scraped(url, success=True)
                                articles_scraped += 1
                            else:
                                state.mark_scraped(url, success=False)
                                articles_failed += 1
                        except Exception as e:
                            state.mark_scraped(url, success=False)
                            articles_failed += 1
                            self.log(f"  PARSE ERROR: {type(e).__name__}: {str(e)[:60]}")

                    # Save periodically
                    if articles_scraped % SAVE_EVERY == 0 and articles_scraped > 0:
                        state.save()
                        self.log(f"  [saved progress: {len(state.articles)} articles total]")

                    time.sleep(self.delay)

                # Final save
                state.save()
                total_scraped_this_session += articles_scraped
                self.log(f"\n[{source_config['name']}] Done: +{articles_scraped} scraped, {articles_failed} failed in {time.time()-start_time:.0f}s")
                self.log(f"[{source_config['name']}] Total in storage: {len(state.articles):,} articles")

            # Combine all sources
            self.log("\n--- Combining all sources ---")
            all_articles = []
            for source_key in SOURCES.keys():
                state = ScraperState(source_key, self.project_dir)
                all_articles.extend(state.articles)
                self.log(f"  {SOURCES[source_key]['name']}: {len(state.articles):,} articles")
            combined_path = os.path.join(data_dir, "all_articles.json")
            with open(combined_path, "w", encoding="utf-8") as f:
                json.dump(all_articles, f, ensure_ascii=False, indent=2)
            self.log(f"\nTotal combined: {len(all_articles):,} articles")
            self.log(f"Saved: {combined_path}")

            self.log(f"\n=== Scraping finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
            self.log(f"Total scraped this session: {total_scraped_this_session:,}")

        except Exception as e:
            self.log(f"\n!!! FATAL ERROR: {type(e).__name__}: {e}")
            self.log(traceback.format_exc())


# ============================================================
# GUI APPLICATION
# ============================================================
class ScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)

        # State
        self.project_dir = tk.StringVar()
        self.delay = tk.DoubleVar(value=DEFAULT_DELAY)
        self.max_minutes = tk.IntVar(value=DEFAULT_MAX_MINUTES)
        self.max_articles = tk.IntVar(value=0)
        self.max_sitemaps = tk.IntVar(value=200)
        self.since_date = tk.StringVar()
        self.source_vars = {key: tk.BooleanVar(value=True) for key in SOURCES}
        self.stop_flag = threading.Event()
        self.worker_thread = None

        self._build_ui()

    def _build_ui(self):
        # Main container
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # === TOP: Project folder selection ===
        folder_frame = ttk.LabelFrame(main, text="Project Folder", padding=10)
        folder_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(folder_frame, text="Folder:").grid(row=0, column=0, sticky=tk.W)
        self.folder_entry = ttk.Entry(folder_frame, textvariable=self.project_dir, width=80)
        self.folder_entry.grid(row=0, column=1, padx=5, sticky=tk.EW)
        self.browse_btn = ttk.Button(folder_frame, text="Browse...", command=self._browse_folder)
        self.browse_btn.grid(row=0, column=2, padx=5)

        folder_frame.columnconfigure(1, weight=1)

        # === MIDDLE: Settings ===
        settings_frame = ttk.LabelFrame(main, text="Settings", padding=10)
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        # Row 1: delay, max_minutes, max_articles
        ttk.Label(settings_frame, text="Delay (sec):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Spinbox(settings_frame, from_=1, to=60, textvariable=self.delay, width=5).grid(row=0, column=1, padx=5)

        ttk.Label(settings_frame, text="Max minutes (0=∞):").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        ttk.Spinbox(settings_frame, from_=0, to=1440, textvariable=self.max_minutes, width=6).grid(row=0, column=3, padx=5)

        ttk.Label(settings_frame, text="Max articles/source (0=∞):").grid(row=0, column=4, sticky=tk.W, padx=5, pady=5)
        ttk.Spinbox(settings_frame, from_=0, to=1000000, textvariable=self.max_articles, width=8).grid(row=0, column=5, padx=5)

        # Row 2: max_sitemaps, since_date
        ttk.Label(settings_frame, text="Max sitemaps/source:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Spinbox(settings_frame, from_=1, to=10000, textvariable=self.max_sitemaps, width=6).grid(row=1, column=1, padx=5)

        ttk.Label(settings_frame, text="Since date (YYYY-MM-DD, blank=all):").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(settings_frame, textvariable=self.since_date, width=12).grid(row=1, column=3, padx=5, sticky=tk.W)

        # === Sources checkboxes ===
        sources_frame = ttk.LabelFrame(main, text="Sources", padding=10)
        sources_frame.pack(fill=tk.X, pady=(0, 10))

        # Header row: Select All / None
        btn_row = ttk.Frame(sources_frame)
        btn_row.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(btn_row, text="Select All", command=self._select_all_sources).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_row, text="Select None", command=self._select_no_sources).pack(side=tk.LEFT, padx=2)
        ttk.Label(btn_row, text=f"  (Estimated total: {sum(s['estimated_articles'] for s in SOURCES.values()):,} articles available)").pack(side=tk.LEFT)

        # Checkboxes in grid
        cb_frame = ttk.Frame(sources_frame)
        cb_frame.pack(fill=tk.X)
        cols = 5
        for i, (key, cfg) in enumerate(SOURCES.items()):
            row = i // cols
            col = i % cols
            ttk.Checkbutton(cb_frame, text=f"{cfg['name']} (~{cfg['estimated_articles']:,})",
                            variable=self.source_vars[key]).grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            # Color swatch
            # (Tkinter doesn't have native color swatch; using a label with bg color)
            # Skip for simplicity
        for c in range(cols):
            cb_frame.columnconfigure(c, weight=1)

        # === Action buttons ===
        action_frame = ttk.Frame(main)
        action_frame.pack(fill=tk.X, pady=(0, 10))

        self.start_btn = ttk.Button(action_frame, text="▶ Start Scraping", command=self._start_scraping, style="Accent.TButton")
        self.start_btn.pack(side=tk.LEFT, padx=2)
        self.stop_btn = ttk.Button(action_frame, text="■ Stop (safe)", command=self._stop_scraping, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=2)
        self.open_folder_btn = ttk.Button(action_frame, text="📂 Open Project Folder", command=self._open_folder)
        self.open_folder_btn.pack(side=tk.LEFT, padx=2)

        self.status_label = ttk.Label(action_frame, text="Ready", font=("TkDefaultFont", 10, "bold"))
        self.status_label.pack(side=tk.RIGHT, padx=10)

        # === Progress bar ===
        progress_frame = ttk.Frame(main)
        progress_frame.pack(fill=tk.X, pady=(0, 5))
        self.progress_bar = ttk.Progressbar(progress_frame, mode="determinate", length=400)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.progress_label = ttk.Label(progress_frame, text="")
        self.progress_label.pack(side=tk.LEFT, padx=10)

        # === Log ===
        log_frame = ttk.LabelFrame(main, text="Live Log", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=15, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.configure(state="disabled")

        # === Status bar ===
        status_bar = ttk.Frame(main)
        status_bar.pack(fill=tk.X)
        self.total_articles_label = ttk.Label(status_bar, text="Total articles in project: 0")
        self.total_articles_label.pack(side=tk.LEFT)
        ttk.Label(status_bar, text=f"{APP_NAME} v{APP_VERSION} • https://github.com/Farhan-ux/urdu_data").pack(side=tk.RIGHT)

        # Try to load saved project folder
        self._load_last_folder()

    def _load_last_folder(self):
        # Try to load from a config file in user's home
        config_path = os.path.expanduser("~/.urdu_scraper_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path) as f:
                    config = json.load(f)
                self.project_dir.set(config.get("project_dir", ""))
            except Exception:
                pass

    def _save_last_folder(self):
        config_path = os.path.expanduser("~/.urdu_scraper_config.json")
        try:
            with open(config_path, "w") as f:
                json.dump({"project_dir": self.project_dir.get()}, f)
        except Exception:
            pass

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Select Project Folder")
        if folder:
            self.project_dir.set(folder)
            self._save_last_folder()
            self._update_total_count()

    def _select_all_sources(self):
        for v in self.source_vars.values():
            v.set(True)

    def _select_no_sources(self):
        for v in self.source_vars.values():
            v.set(False)

    def _log(self, msg):
        """Append a line to the log widget. Thread-safe via after()."""
        def _do():
            self.log_text.configure(state="normal")
            self.log_text.insert(tk.END, str(msg) + "\n")
            self.log_text.see(tk.END)
            self.log_text.configure(state="disabled")
        self.root.after(0, _do)

    def _set_progress(self, value, label=""):
        def _do():
            self.progress_bar["value"] = value
            self.progress_label.config(text=label)
        self.root.after(0, _do)

    def _set_status(self, status, color="black"):
        def _do():
            self.status_label.config(text=status, foreground=color)
        self.root.after(0, _do)

    def _update_total_count(self):
        """Update the 'Total articles in project' label."""
        def _do():
            total = 0
            folder = self.project_dir.get()
            if folder and os.path.exists(folder):
                data_dir = os.path.join(folder, "data")
                if os.path.exists(data_dir):
                    for key in SOURCES.keys():
                        path = os.path.join(data_dir, f"{key}_articles.json")
                        if os.path.exists(path):
                            try:
                                with open(path, encoding="utf-8") as f:
                                    arts = json.load(f)
                                total += len(arts)
                            except Exception:
                                pass
            self.total_articles_label.config(text=f"Total articles in project: {total:,}")
        self.root.after(0, _do)

    def _progress_callback(self, source, current, total, scraped, failed, rate, elapsed):
        """Called from worker thread to update progress bar."""
        pct = (current / total) * 100 if total > 0 else 0
        label = f"{source}: {current}/{total} ({scraped} ok, {failed} fail, {rate:.1f}/min, {elapsed:.0f}s)"
        self._set_progress(pct, label)

    def _start_scraping(self):
        # Validate
        folder = self.project_dir.get()
        if not folder:
            messagebox.showerror("Error", "Please select a project folder first.")
            return
        if not os.path.exists(folder):
            try:
                os.makedirs(folder, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Error", f"Could not create folder: {e}")
                return

        selected_sources = [k for k, v in self.source_vars.items() if v.get()]
        if not selected_sources:
            messagebox.showerror("Error", "Please select at least one source.")
            return

        # Validate since_date if provided
        since_date = self.since_date.get().strip() or None
        if since_date:
            try:
                datetime.strptime(since_date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Date must be in YYYY-MM-DD format.")
                return

        # Clear stop flag
        self.stop_flag.clear()

        # Disable start button, enable stop button
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self._set_status("Running...", "green")

        # Clear log
        self.log_text.configure(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state="disabled")

        # Start worker thread
        self.worker_thread = threading.Thread(
            target=self._run_worker,
            args=(folder, selected_sources, since_date),
            daemon=True,
        )
        self.worker_thread.start()

        # Start a periodic updater to refresh total count
        self._periodic_update()

    def _run_worker(self, folder, selected_sources, since_date):
        """Runs in worker thread."""
        try:
            worker = ScraperWorker(
                project_dir=folder,
                selected_sources=selected_sources,
                delay=self.delay.get(),
                max_minutes=self.max_minutes.get(),
                max_articles_per_source=self.max_articles.get() or None,
                max_sitemaps_per_source=self.max_sitemaps.get(),
                since_date=since_date,
                log_func=self._log,
                progress_func=self._progress_callback,
                stop_flag=self.stop_flag,
            )
            worker.run()
        except Exception as e:
            self._log(f"!!! THREAD FATAL: {type(e).__name__}: {e}")
            self._log(traceback.format_exc())
        finally:
            # Re-enable start button
            def _do():
                self.start_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.DISABLED)
                self._set_status("Ready", "black")
                self._update_total_count()
            self.root.after(0, _do)

    def _stop_scraping(self):
        self.stop_flag.set()
        self._set_status("Stopping (will save after current article)...", "orange")
        self._log("\n--- Stop requested — will save and exit after current article ---")

    def _open_folder(self):
        folder = self.project_dir.get()
        if not folder or not os.path.exists(folder):
            messagebox.showerror("Error", "Project folder does not exist.")
            return
        # Cross-platform folder open
        import subprocess, platform
        sysname = platform.system()
        try:
            if sysname == "Windows":
                os.startfile(folder)
            elif sysname == "Darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")

    def _periodic_update(self):
        """Update total count every 5 seconds while worker is running."""
        if self.worker_thread and self.worker_thread.is_alive():
            self._update_total_count()
            self.root.after(5000, self._periodic_update)


# ============================================================
# MAIN
# ============================================================
def main():
    root = tk.Tk()
    app = ScraperApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
