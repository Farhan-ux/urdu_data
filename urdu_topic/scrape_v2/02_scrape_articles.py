"""
Phase 2: Gentle, resumable article scraper.

Features:
- Reads URL queue from 01_collect_urls.py output
- Skips URLs already scraped (resumable)
- 3-second delay between requests to same host
- Saves every 25 articles
- Time-limited mode (stop after N minutes)
- Retry with exponential backoff on network errors
- Logs all activity to file

Usage:
    python 02_scrape_articles.py                              # default: 60 min, all sources
    python 02_scrape_articles.py --max-minutes 120            # 2 hours
    python 02_scrape_articles.py --max-articles 5000          # stop after 5k articles
    python 02_scrape_articles.py --source express             # only express
    python 02_scrape_articles.py --delay 5                    # 5-second delay (more gentle)
    python 02_scrape_articles.py --resume                     # resume from last state (default)

The script can be safely killed (Ctrl+C) at any time. It saves progress every 25
articles and on exit. Just run it again to continue.
"""
import os, sys, json, time, re, argparse, signal, traceback
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

DATA_DIR = "/home/z/my-project/urdu_topic/data"
LOG_DIR = "/home/z/my-project/urdu_topic/logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Gentle User-Agent identifying ourselves and giving contact
HEADERS = {
    "User-Agent": "UrduNLP-Research/1.0 (academic research; https://github.com/Farhan-ux/urdu_data)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ur,en;q=0.9",
}

# Per-source article parsers
def parse_express(html, url):
    soup = BeautifulSoup(html, "lxml")
    title = soup.find("h1").get_text(strip=True) if soup.find("h1") else ""
    body_parts = []
    content = soup.find("div", class_=re.compile(r"story-content|detail-content|content-area|entry-content"))
    if content:
        for p in content.find_all("p"):
            t = p.get_text(strip=True)
            if t and len(t) > 20:
                body_parts.append(t)
    if not body_parts:
        for p in soup.find_all("p"):
            t = p.get_text(strip=True)
            if t and len(t) > 40:
                body_parts.append(t)
    body = " ".join(body_parts[:30])
    if len(body) < 200:
        return None
    return {"title": title, "body": body}


def parse_jang(html, url):
    soup = BeautifulSoup(html, "lxml")
    title = soup.find("h1").get_text(strip=True) if soup.find("h1") else ""
    body_parts = []
    content = soup.find("div", class_=re.compile(r"detail-view|story-content|content-area|entry-content"))
    if content:
        for p in content.find_all("p"):
            t = p.get_text(strip=True)
            if t and len(t) > 20:
                body_parts.append(t)
    if not body_parts:
        for p in soup.find_all("p"):
            t = p.get_text(strip=True)
            if t and len(t) > 40:
                body_parts.append(t)
    body = " ".join(body_parts[:30])
    if len(body) < 200:
        return None
    return {"title": title, "body": body}


def parse_nawaiwaqt(html, url):
    soup = BeautifulSoup(html, "lxml")
    title = soup.find("h1").get_text(strip=True) if soup.find("h1") else ""
    body_parts = []
    content = soup.find("div", class_=re.compile(r"story-content|content-area|detail-content|entry-content"))
    if content:
        for p in content.find_all("p"):
            t = p.get_text(strip=True)
            if t and len(t) > 20:
                body_parts.append(t)
    if not body_parts:
        for p in soup.find_all("p"):
            t = p.get_text(strip=True)
            if t and len(t) > 40:
                body_parts.append(t)
    body = " ".join(body_parts[:30])
    if len(body) < 200:
        return None
    return {"title": title, "body": body}


def parse_bbc_urdu(html, url):
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
    "express": parse_express,
    "jang": parse_jang,
    "nawaiwaqt": parse_nawaiwaqt,
    "bbc_urdu": parse_bbc_urdu,
}


# ============================================================
# State management — for resumability
# ============================================================
class ScraperState:
    """Track scraped URLs and articles for resumability."""
    def __init__(self, source):
        self.source = source
        self.articles_path = os.path.join(DATA_DIR, f"{source}_articles.json")
        self.scraped_urls_path = os.path.join(DATA_DIR, f"{source}_scraped_urls.json")
        self.articles = []
        self.scraped_urls = set()
        self.failed_urls = set()
        self._load()

    def _load(self):
        if os.path.exists(self.articles_path):
            try:
                with open(self.articles_path, encoding="utf-8") as f:
                    self.articles = json.load(f)
                print(f"  Loaded {len(self.articles)} existing {self.source} articles", flush=True)
            except Exception as e:
                print(f"  WARN: could not load existing articles: {e}", flush=True)
                self.articles = []
        if os.path.exists(self.scraped_urls_path):
            try:
                with open(self.scraped_urls_path) as f:
                    self.scraped_urls = set(json.load(f))
                print(f"  Loaded {len(self.scraped_urls)} already-scraped URLs", flush=True)
            except Exception:
                self.scraped_urls = set()

    def save(self):
        # Save articles
        with open(self.articles_path, "w", encoding="utf-8") as f:
            json.dump(self.articles, f, ensure_ascii=False, indent=2)
        # Save scraped URLs
        with open(self.scraped_urls_path, "w") as f:
            json.dump(sorted(self.scraped_urls), f, indent=2)

    def is_scraped(self, url):
        return url in self.scraped_urls

    def mark_scraped(self, url, success=True):
        self.scraped_urls.add(url)
        if not success:
            self.failed_urls.add(url)

    def add_article(self, article):
        self.articles.append(article)


# ============================================================
# Graceful shutdown handler
# ============================================================
class GracefulShutdown:
    """Catch Ctrl+C and signal the scraper to stop after current article."""
    def __init__(self):
        self.shutdown_requested = False
        signal.signal(signal.SIGINT, self._handler)
        signal.signal(signal.SIGTERM, self._handler)

    def _handler(self, signum, frame):
        if self.shutdown_requested:
            print("\n  Second Ctrl+C received — forcing exit", flush=True)
            sys.exit(1)
        print("\n  Ctrl+C received — finishing current article then saving (press Ctrl+C again to force exit)", flush=True)
        self.shutdown_requested = True

    def should_stop(self):
        return self.shutdown_requested


# ============================================================
# Fetch with retry
# ============================================================
def fetch(url, retries=3, timeout=15):
    """Fetch URL with exponential backoff. Returns text or None."""
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            if r.status_code == 200:
                return r.text
            elif r.status_code in (429, 503):
                wait = 10 * (attempt + 1)
                print(f"      Rate limited (HTTP {r.status_code}); waiting {wait}s", flush=True)
                time.sleep(wait)
            elif r.status_code == 404:
                return None  # article removed
            elif r.status_code == 403:
                print(f"      Forbidden (HTTP 403) — server blocking us", flush=True)
                return None
            else:
                print(f"      HTTP {r.status_code}", flush=True)
                return None
        except requests.exceptions.Timeout:
            print(f"      Timeout (attempt {attempt+1})", flush=True)
            time.sleep(5 * (attempt + 1))
        except requests.exceptions.ConnectionError as e:
            print(f"      Connection error (attempt {attempt+1})", flush=True)
            time.sleep(5 * (attempt + 1))
        except Exception as e:
            print(f"      Error (attempt {attempt+1}): {type(e).__name__}", flush=True)
            time.sleep(5 * (attempt + 1))
    return None


# ============================================================
# Main scraper loop
# ============================================================
def scrape_source(source, url_queue, max_minutes, max_articles, delay, shutdown):
    """Scrape articles for one source. Returns count scraped."""
    if source not in PARSERS:
        print(f"  No parser for source '{source}', skipping", flush=True)
        return 0

    parser = PARSERS[source]
    state = ScraperState(source)
    starting_count = len(state.articles)

    # Filter queue to this source's URLs not yet scraped
    pending = [e for e in url_queue if e["source"] == source and not state.is_scraped(e["url"])]
    print(f"  {source}: {len(pending)} URLs pending (out of {sum(1 for e in url_queue if e['source'] == source)} total)", flush=True)

    if not pending:
        print(f"  {source}: nothing to do", flush=True)
        return 0

    start_time = time.time()
    articles_scraped = 0
    articles_failed = 0
    save_every = 25

    for i, entry in enumerate(pending, 1):
        # Check stop conditions
        if shutdown.should_stop():
            print(f"\n  Stopping: shutdown requested", flush=True)
            break
        if max_minutes and (time.time() - start_time) / 60 >= max_minutes:
            print(f"\n  Stopping: time limit ({max_minutes} min) reached", flush=True)
            break
        if max_articles and articles_scraped >= max_articles:
            print(f"\n  Stopping: article limit ({max_articles}) reached", flush=True)
            break

        url = entry["url"]
        lastmod = entry.get("lastmod", "")
        elapsed = time.time() - start_time
        rate = articles_scraped / max(1, elapsed / 60)
        print(f"  [{i}/{len(pending)}] elapsed={elapsed:.0f}s scraped={articles_scraped} failed={articles_failed} rate={rate:.1f}/min", flush=True)
        print(f"    URL: {url[:90]}", flush=True)

        html = fetch(url)
        if not html:
            state.mark_scraped(url, success=False)
            articles_failed += 1
            print(f"    FAILED to fetch", flush=True)
        else:
            try:
                parsed = parser(html, url)
                if parsed:
                    article = {
                        "url": url,
                        "title": parsed["title"],
                        "body": parsed["body"],
                        "source": source,
                        "lastmod": lastmod,
                        "word_count": len(parsed["body"].split()),
                        "scraped_at": datetime.utcnow().isoformat() + "Z",
                    }
                    state.add_article(article)
                    state.mark_scraped(url, success=True)
                    articles_scraped += 1
                    print(f"    OK ({article['word_count']} words)", flush=True)
                else:
                    state.mark_scraped(url, success=False)
                    articles_failed += 1
                    print(f"    FAILED to parse (body too short or empty)", flush=True)
            except Exception as e:
                state.mark_scraped(url, success=False)
                articles_failed += 1
                print(f"    PARSE ERROR: {type(e).__name__}: {str(e)[:80]}", flush=True)

        # Save periodically
        if articles_scraped % save_every == 0 and articles_scraped > 0:
            print(f"    [saving progress...]", flush=True)
            state.save()

        # Gentle delay between requests
        time.sleep(delay)

    # Final save
    state.save()
    print(f"\n  {source} done: +{articles_scraped} scraped, {articles_failed} failed in {time.time()-start_time:.0f}s", flush=True)
    print(f"  Total {source} articles in storage: {len(state.articles)}", flush=True)
    return articles_scraped


def main():
    parser = argparse.ArgumentParser(description="Gentle, resumable Urdu news article scraper")
    parser.add_argument("--source", default="all", choices=["all", "express", "jang", "nawaiwaqt", "bbc_urdu"],
                        help="Source to scrape (default: all)")
    parser.add_argument("--max-minutes", type=int, default=60,
                        help="Max runtime in minutes per source (default: 60)")
    parser.add_argument("--max-articles", type=int, default=None,
                        help="Max articles to scrape per source (default: unlimited)")
    parser.add_argument("--delay", type=float, default=3.0,
                        help="Delay between requests in seconds (default: 3)")
    parser.add_argument("--queue-file", default=os.path.join(DATA_DIR, "url_queue.json"),
                        help="URL queue from 01_collect_urls.py")
    args = parser.parse_args()

    print(f"=== Urdu News Scraper (gentle, resumable) ===", flush=True)
    print(f"Source: {args.source}", flush=True)
    print(f"Max minutes per source: {args.max_minutes}", flush=True)
    print(f"Max articles per source: {args.max_articles or 'unlimited'}", flush=True)
    print(f"Delay between requests: {args.delay}s", flush=True)
    print(f"Queue file: {args.queue_file}", flush=True)

    # Load URL queue
    if not os.path.exists(args.queue_file):
        print(f"\nERROR: Queue file not found. Run 01_collect_urls.py first.", flush=True)
        sys.exit(1)
    with open(args.queue_file) as f:
        url_queue = json.load(f)
    print(f"\nLoaded queue: {len(url_queue)} URLs total", flush=True)
    from collections import Counter
    by_source = Counter(e["source"] for e in url_queue)
    for s, c in by_source.most_common():
        print(f"  {c:>8,}  {s}", flush=True)

    # Set up graceful shutdown
    shutdown = GracefulShutdown()

    # Determine sources to run
    sources_to_run = [args.source] if args.source != "all" else list(PARSERS.keys())

    # Run each source
    total_scraped = 0
    for source in sources_to_run:
        if shutdown.should_stop():
            break
        print(f"\n{'='*60}", flush=True)
        print(f"=== Scraping {source.upper()} ===", flush=True)
        print(f"{'='*60}", flush=True)
        try:
            scraped = scrape_source(source, url_queue, args.max_minutes, args.max_articles, args.delay, shutdown)
            total_scraped += scraped
        except Exception as e:
            print(f"  FATAL on {source}: {type(e).__name__}: {e}", flush=True)
            traceback.print_exc()

    print(f"\n=== Done. Total scraped this session: {total_scraped} ===", flush=True)

    # Combine all sources
    print(f"\nCombining all sources...", flush=True)
    all_articles = []
    for source in PARSERS.keys():
        path = os.path.join(DATA_DIR, f"{source}_articles.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                arts = json.load(f)
            all_articles.extend(arts)
            print(f"  {source}: {len(arts)} articles", flush=True)
    combined_path = os.path.join(DATA_DIR, "all_articles.json")
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)
    print(f"\nTotal combined: {len(all_articles)} articles", flush=True)
    print(f"Saved: {combined_path}", flush=True)


if __name__ == "__main__":
    main()
