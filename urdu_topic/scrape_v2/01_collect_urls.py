"""
Phase 1: Sitemap-based URL collector.

GENTLE: Reads only sitemap XML files (very low server load). One request per
sitemap file, with 2-second delay between requests to same host.

Output: data/url_queue.json — a list of {url, source, lastmod, sitemap} dicts,
sorted by date (newest first).

Usage:
    python 01_collect_urls.py                    # collect from all sources
    python 01_collect_urls.py --source express   # only one source
    python 01_collect_urls.py --max-sitemaps 10  # limit per source (testing)
    python 01_collect_urls.py --since 2021-01-01 # filter by date
"""
import os, sys, json, time, re, argparse
import requests
from urllib.parse import urlparse
from xml.etree import ElementTree as ET
from datetime import datetime
from collections import defaultdict

DATA_DIR = "/home/z/my-project/urdu_topic/data"
os.makedirs(DATA_DIR, exist_ok=True)

# Gentle User-Agent identifying ourselves
HEADERS = {
    "User-Agent": "UrduNLP-Research/1.0 (academic research; https://github.com/Farhan-ux/urdu_data)",
    "Accept": "application/xml,text/xml,*/*",
    "Accept-Language": "ur,en;q=0.9",
}


def fetch(url, retries=3, timeout=15):
    """Fetch with exponential backoff. Returns text or None."""
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            if r.status_code == 200:
                return r.text
            elif r.status_code in (429, 503):
                # Server asked us to slow down
                wait = 5 * (attempt + 1)
                print(f"    Rate limited (HTTP {r.status_code}); waiting {wait}s", flush=True)
                time.sleep(wait)
            elif r.status_code == 404:
                return None  # No retry on 404
            else:
                print(f"    HTTP {r.status_code} on {url}", flush=True)
                return None
        except requests.exceptions.Timeout:
            print(f"    Timeout (attempt {attempt+1})", flush=True)
            time.sleep(3 * (attempt + 1))
        except requests.exceptions.ConnectionError as e:
            print(f"    Connection error (attempt {attempt+1}): {str(e)[:80]}", flush=True)
            time.sleep(3 * (attempt + 1))
        except Exception as e:
            print(f"    Error (attempt {attempt+1}): {type(e).__name__}", flush=True)
            time.sleep(3 * (attempt + 1))
    return None


def parse_sitemap_xml(text):
    """Parse sitemap XML, return list of (url, lastmod) tuples or sub-sitemap URLs."""
    if not text:
        return [], []
    urls = []
    sub_sitemaps = []
    try:
        # Try parsing as XML
        root = ET.fromstring(text)
        # Strip namespace
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        for elem in root.findall(f".//{ns}url"):
            loc_elem = elem.find(f"{ns}loc")
            lastmod_elem = elem.find(f"{ns}lastmod")
            if loc_elem is not None and loc_elem.text:
                url = loc_elem.text.strip()
                lastmod = lastmod_elem.text.strip() if lastmod_elem is not None and lastmod_elem.text else ""
                urls.append((url, lastmod))

        for elem in root.findall(f".//{ns}sitemap"):
            loc_elem = elem.find(f"{ns}loc")
            if loc_elem is not None and loc_elem.text:
                sub_sitemaps.append(loc_elem.text.strip())
    except ET.ParseError:
        # Fallback: regex (some sitemaps are not well-formed)
        url_locs = re.findall(r"<loc>([^<]+)</loc>", text)
        lastmods = re.findall(r"<lastmod>([^<]+)</lastmod>", text)
        # Distinguish sitemap index vs url set by checking for <sitemap> tags
        if "<sitemap>" in text or "<sitemap " in text:
            sub_sitemaps = url_locs
        else:
            for i, url in enumerate(url_locs):
                lastmod = lastmods[i] if i < len(lastmods) else ""
                urls.append((url, lastmod))
    return urls, sub_sitemaps


# ============================================================
# EXPRESS — 90+ posts-N.xml sitemaps, 5000 URLs each
# ============================================================
def collect_express(max_sitemaps=None, since=None):
    """Collect Express article URLs from sitemap."""
    print("\n=== EXPRESS ===", flush=True)
    all_urls = []
    base = "https://www.express.pk"
    # Start with main sitemap
    print("  Fetching main sitemap...", flush=True)
    text = fetch(f"{base}/sitemap.xml")
    if not text:
        print("  ERROR: Could not fetch main sitemap", flush=True)
        return []

    # Find all posts-N.xml sub-sitemaps
    _, sub_sitemaps = parse_sitemap_xml(text)
    posts_sitemaps = [s for s in sub_sitemaps if "/posts-" in s and ".xml" in s]
    posts_sitemaps.sort()
    print(f"  Found {len(posts_sitemaps)} posts-*.xml sub-sitemaps", flush=True)

    if max_sitemaps:
        posts_sitemaps = posts_sitemaps[:max_sitemaps]
        print(f"  Limited to first {max_sitemaps} (for testing)", flush=True)

    for i, sm_url in enumerate(posts_sitemaps, 1):
        print(f"  [{i}/{len(posts_sitemaps)}] {sm_url.split('/')[-1]}", flush=True, end=" ")
        text = fetch(sm_url)
        if not text:
            print("FAILED", flush=True)
            continue
        urls, _ = parse_sitemap_xml(text)
        # Filter: keep only /story/<id>/ URLs (actual articles)
        article_urls = [(u, lm) for u, lm in urls if "/story/" in u]
        # Apply date filter
        if since:
            article_urls = [(u, lm) for u, lm in article_urls if lm >= since]
        print(f"{len(article_urls)} articles", flush=True)
        all_urls.extend(article_urls)
        time.sleep(2)  # gentle delay between sitemap fetches

    # Dedupe
    seen = set()
    deduped = []
    for u, lm in all_urls:
        if u not in seen:
            seen.add(u)
            deduped.append({"url": u, "source": "express", "lastmod": lm, "sitemap": "posts"})
    print(f"  Total Express URLs (deduped): {len(deduped)}", flush=True)
    return deduped


# ============================================================
# NAWA-I-WAQT — sitemap_news.xml + sitemap_categories.xml + date sitemaps
# ============================================================
def collect_nawaiwaqt(max_sitemaps=None, since=None):
    """Collect Nawa-i-Waqt article URLs from sitemap."""
    print("\n=== NAWA-I-WAQT ===", flush=True)
    all_urls = []
    base = "https://www.nawaiwaqt.com.pk"

    # Main sitemap has 6259 sub-sitemaps — too many to fetch all
    # Strategy: fetch sitemap_news.xml (most recent) + sample sitemap_categories.xml
    print("  Fetching sitemap_news.xml...", flush=True)
    text = fetch(f"{base}/sitemap_news.xml")
    if text:
        urls, _ = parse_sitemap_xml(text)
        article_urls = [(u, lm) for u, lm in urls if re.search(r"/\d{1,2}-\w+-\d{4}/\d+", u)]
        if since:
            article_urls = [(u, lm) for u, lm in article_urls if lm >= since]
        print(f"    {len(article_urls)} articles from sitemap_news.xml", flush=True)
        all_urls.extend(article_urls)
    time.sleep(2)

    # Also try fetching a sample of date-based sitemaps from main index
    print("  Fetching main sitemap index...", flush=True)
    text = fetch(f"{base}/sitemap.xml")
    if text:
        _, sub_sitemaps = parse_sitemap_xml(text)
        # Filter to sitemap_news_* or sitemap_categories
        date_sitemaps = [s for s in sub_sitemaps if "sitemap_news" in s or "sitemap_categories" in s]
        # Sample at most 50 sitemaps (gentle)
        sample_size = min(50, len(date_sitemaps))
        if max_sitemaps:
            sample_size = min(sample_size, max_sitemaps)
        print(f"  Found {len(date_sitemaps)} news/categories sitemaps; sampling {sample_size}", flush=True)
        for i, sm_url in enumerate(date_sitemaps[:sample_size], 1):
            print(f"  [{i}/{sample_size}] {sm_url.split('/')[-1]}", flush=True, end=" ")
            text = fetch(sm_url)
            if not text:
                print("FAILED", flush=True)
                continue
            urls, _ = parse_sitemap_xml(text)
            article_urls = [(u, lm) for u, lm in urls if re.search(r"/\d{1,2}-\w+-\d{4}/\d+", u)]
            if since:
                article_urls = [(u, lm) for u, lm in article_urls if lm >= since]
            print(f"{len(article_urls)} articles", flush=True)
            all_urls.extend(article_urls)
            time.sleep(2)

    # Dedupe
    seen = set()
    deduped = []
    for u, lm in all_urls:
        if u not in seen:
            seen.add(u)
            deduped.append({"url": u, "source": "nawaiwaqt", "lastmod": lm, "sitemap": "news"})
    print(f"  Total Nawa-i-Waqt URLs (deduped): {len(deduped)}", flush=True)
    return deduped


# ============================================================
# BBC URDU — small sitemap, but historical URLs available
# ============================================================
def collect_bbc_urdu(max_sitemaps=None, since=None):
    """Collect BBC Urdu article URLs."""
    print("\n=== BBC URDU ===", flush=True)
    base = "https://www.bbc.com/urdu"
    all_urls = []

    # Try several sitemap URLs
    sitemap_urls = [
        f"{base}/sitemap.xml",
        "https://www.bbc.com/sitemaps/urdu-sitemap.xml",
        "https://www.bbc.com/sitemaps/index-urdu.xml",
    ]
    for sm_url in sitemap_urls:
        print(f"  Trying {sm_url}", flush=True)
        text = fetch(sm_url)
        if not text:
            print("    No data", flush=True)
            continue
        urls, sub_sitemaps = parse_sitemap_xml(text)
        if sub_sitemaps:
            print(f"    Found {len(sub_sitemaps)} sub-sitemaps", flush=True)
            for sub in sub_sitemaps[:10]:  # sample up to 10
                print(f"      Fetching {sub.split('/')[-1]}", flush=True, end=" ")
                sub_text = fetch(sub)
                if sub_text:
                    sub_urls, _ = parse_sitemap_xml(sub_text)
                    article_urls = [(u, lm) for u, lm in sub_urls if "/urdu/" in u and re.search(r"/\d{5,}", u)]
                    if since:
                        article_urls = [(u, lm) for u, lm in article_urls if lm >= since]
                    print(f"{len(article_urls)} articles", flush=True)
                    all_urls.extend(article_urls)
                time.sleep(2)
        else:
            article_urls = [(u, lm) for u, lm in urls if "/urdu/" in u and re.search(r"/\d{5,}", u)]
            if since:
                article_urls = [(u, lm) for u, lm in article_urls if lm >= since]
            print(f"    {len(article_urls)} articles", flush=True)
            all_urls.extend(article_urls)
        time.sleep(2)

    # Dedupe
    seen = set()
    deduped = []
    for u, lm in all_urls:
        if u not in seen:
            seen.add(u)
            deduped.append({"url": u, "source": "bbc_urdu", "lastmod": lm, "sitemap": "main"})
    print(f"  Total BBC Urdu URLs (deduped): {len(deduped)}", flush=True)
    return deduped


# ============================================================
# JANG — sitemap returns HTML; fall back to category-page walk
# ============================================================
def collect_jang(max_sitemaps=None, since=None):
    """Jang's sitemap.xml returns non-XML content. Walk categories instead (gently)."""
    print("\n=== JANG ===", flush=True)
    # Jang pagination is fake (returns same content), so single page per category
    cats = [
        "latest-news", "pakistan", "world", "sports", "entertainment",
        "science", "business", "lifestyle", "magazines",
        "sindh", "punjab", "kpk", "balochistan", "islamabad",
        "kashmir", "gilgit-baltistan",
    ]
    all_urls = []
    for cat in cats:
        url = f"https://jang.com.pk/category/{cat}"
        print(f"  {cat}", flush=True, end=" ")
        text = fetch(url)
        if not text:
            print("FAILED", flush=True)
            continue
        # Find article URLs
        urls = re.findall(r'https://jang\.com\.pk/news/\d+', text)
        unique = set(urls)
        print(f"{len(unique)} URLs", flush=True)
        for u in unique:
            all_urls.append({"url": u, "source": "jang", "lastmod": "", "sitemap": f"category-{cat}"})
        time.sleep(3)  # extra gentle on category pages

    # Dedupe
    seen = set()
    deduped = []
    for entry in all_urls:
        if entry["url"] not in seen:
            seen.add(entry["url"])
            deduped.append(entry)
    print(f"  Total Jang URLs (deduped): {len(deduped)}", flush=True)
    return deduped


COLLECTORS = {
    "express": collect_express,
    "nawaiwaqt": collect_nawaiwaqt,
    "bbc_urdu": collect_bbc_urdu,
    "jang": collect_jang,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=list(COLLECTORS.keys()) + ["all"], default="all")
    parser.add_argument("--max-sitemaps", type=int, default=None, help="Limit sitemaps per source (for testing)")
    parser.add_argument("--since", default=None, help="Only include articles after this date (YYYY-MM-DD)")
    parser.add_argument("--output", default=os.path.join(DATA_DIR, "url_queue.json"))
    args = parser.parse_args()

    print(f"=== URL Collection ===", flush=True)
    print(f"Source: {args.source}", flush=True)
    print(f"Max sitemaps per source: {args.max_sitemaps or 'unlimited'}", flush=True)
    print(f"Date filter (since): {args.since or 'none'}", flush=True)
    print(f"Output: {args.output}", flush=True)
    print(flush=True)

    # Load existing queue if any
    existing = []
    if os.path.exists(args.output):
        with open(args.output) as f:
            existing = json.load(f)
        print(f"Loaded existing queue: {len(existing)} URLs", flush=True)

    sources_to_run = [args.source] if args.source != "all" else list(COLLECTORS.keys())

    all_new = []
    for src in sources_to_run:
        try:
            urls = COLLECTORS[src](max_sitemaps=args.max_sitemaps, since=args.since)
            all_new.extend(urls)
        except Exception as e:
            print(f"  ERROR on {src}: {type(e).__name__}: {e}", flush=True)
            import traceback
            traceback.print_exc()

    # Merge with existing
    seen = set(e["url"] for e in existing)
    new_added = 0
    for entry in all_new:
        if entry["url"] not in seen:
            existing.append(entry)
            seen.add(entry["url"])
            new_added += 1

    # Sort by lastmod (newest first)
    existing.sort(key=lambda e: e.get("lastmod", "") or "", reverse=True)

    # Save
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    # Stats
    from collections import Counter
    by_source = Counter(e["source"] for e in existing)
    print(f"\n=== Summary ===", flush=True)
    print(f"  New URLs added: {new_added}", flush=True)
    print(f"  Total in queue: {len(existing)}", flush=True)
    print(f"  By source:", flush=True)
    for s, c in by_source.most_common():
        print(f"    {c:>8,}  {s}", flush=True)

    # Year distribution
    by_year = Counter()
    for e in existing:
        lm = e.get("lastmod", "")
        if lm and len(lm) >= 4:
            by_year[lm[:4]] += 1
    if by_year:
        print(f"  By year:", flush=True)
        for y, c in sorted(by_year.items(), reverse=True)[:10]:
            print(f"    {c:>8,}  {y}", flush=True)


if __name__ == "__main__":
    main()
