"""
Bulletproof single-source scraper with comprehensive error handling.
Saves incrementally. Tests each fetch.
"""
import os, sys, json, time, re, traceback
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

OUT_DIR = "/home/z/my-project/urdu_topic/data"
LOG_DIR = "/home/z/my-project/urdu_topic/logs"
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ur,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def safe_get(url, timeout=8):
    """Always returns text or None, never raises."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r.text
    except Exception as e:
        sys.stderr.write(f"  fetch err {url}: {type(e).__name__}\n")
    return None


def collect_express(max_pages=5):
    cats = ["latest-news", "pakistan", "world", "sports", "entertainment", "science", "business", "lifestyle"]
    urls = set()
    for cat in cats:
        for page in range(1, max_pages + 1):
            url = f"https://www.express.pk/{cat}?page={page}"
            html = safe_get(url)
            if not html:
                continue
            try:
                soup = BeautifulSoup(html, "lxml")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if "/story/" in href and re.search(r"/\d{5,}", href):
                        if href.startswith("/"):
                            href = "https://www.express.pk" + href
                        urls.add(href)
            except Exception as e:
                sys.stderr.write(f"  parse err {url}: {e}\n")
                continue
            time.sleep(0.1)
        sys.stderr.write(f"  express/{cat}: {len(urls)} cumulative URLs\n")
    return urls


def parse_express(url):
    html = safe_get(url)
    if not html:
        return None
    try:
        soup = BeautifulSoup(html, "lxml")
        title = ""
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)
        body_parts = []
        # Try content divs first
        content = soup.find("div", class_=re.compile(r"story-content|detail-content|content-area|entry-content"))
        if content:
            for p in content.find_all("p"):
                t = p.get_text(strip=True)
                if t and len(t) > 20:
                    body_parts.append(t)
        # Fallback: all long paragraphs
        if not body_parts:
            for p in soup.find_all("p"):
                t = p.get_text(strip=True)
                if t and len(t) > 40:
                    body_parts.append(t)
        body = " ".join(body_parts[:30])
        if len(body) < 200:
            return None
        path = urlparse(url).path
        parts = [p for p in path.split("/") if p]
        section = parts[0] if parts else "news"
        if section == "story":
            section = "news"
        return {"url": url, "title": title, "section": section, "body": body, "source": "express"}
    except Exception:
        return None


def collect_jang(max_pages=5):
    cats = ["latest-news", "pakistan", "world", "sports", "entertainment", "science", "business", "lifestyle"]
    urls = set()
    for cat in cats:
        for page in range(1, max_pages + 1):
            url = f"https://jang.com.pk/category/{cat}/page/{page}"
            html = safe_get(url)
            if not html:
                continue
            try:
                soup = BeautifulSoup(html, "lxml")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if re.search(r"https://jang\.com\.pk/news/\d+", href):
                        urls.add(href)
            except Exception:
                continue
            time.sleep(0.1)
        sys.stderr.write(f"  jang/{cat}: {len(urls)} cumulative URLs\n")
    return urls


def parse_jang(url):
    html = safe_get(url)
    if not html:
        return None
    try:
        soup = BeautifulSoup(html, "lxml")
        title = ""
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)
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
        path = urlparse(url).path
        parts = [p for p in path.split("/") if p]
        section = parts[1] if len(parts) > 1 else "news"
        return {"url": url, "title": title, "section": section, "body": body, "source": "jang"}
    except Exception:
        return None


def collect_geo(max_pages=5):
    cats = ["latest", "pakistan", "world", "sports", "entertainment", "science", "business", "lifestyle"]
    urls = set()
    for cat in cats:
        for page in range(1, max_pages + 1):
            url = f"https://urdu.geo.tv/category/{cat}/page/{page}"
            html = safe_get(url)
            if not html:
                continue
            try:
                soup = BeautifulSoup(html, "lxml")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if re.search(r"https://urdu\.geo\.tv/(latest|news)/\d+", href):
                        urls.add(href)
            except Exception:
                continue
            time.sleep(0.1)
        sys.stderr.write(f"  geo/{cat}: {len(urls)} cumulative URLs\n")
    return urls


def parse_geo(url):
    html = safe_get(url)
    if not html:
        return None
    try:
        soup = BeautifulSoup(html, "lxml")
        title = ""
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)
        body_parts = []
        content = soup.find("div", class_=re.compile(r"story-area|content-area|entry-content|post-content"))
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
        path = urlparse(url).path
        parts = [p for p in path.split("/") if p]
        section = parts[1] if len(parts) > 1 else "news"
        return {"url": url, "title": title, "section": section, "body": body, "source": "geo"}
    except Exception:
        return None


def collect_samaa(max_pages=4):
    cats = ["news", "pakistan", "world", "sports", "entertainment", "business", "tech"]
    urls = set()
    for cat in cats:
        for page in range(1, max_pages + 1):
            url = f"https://www.samaa.tv/urdu/{cat}?page={page}"
            html = safe_get(url)
            if not html:
                continue
            try:
                soup = BeautifulSoup(html, "lxml")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if re.search(r"\d{6,}", href) and "samaa.tv" in href and "/urdu/" in href:
                        urls.add(href)
            except Exception:
                continue
            time.sleep(0.1)
        sys.stderr.write(f"  samaa/{cat}: {len(urls)} cumulative URLs\n")
    return urls


def parse_samaa(url):
    html = safe_get(url)
    if not html:
        return None
    try:
        soup = BeautifulSoup(html, "lxml")
        title = ""
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)
        body_parts = []
        content = soup.find("div", class_=re.compile(r"story-content|content-area|article-body|post-content"))
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
        path = urlparse(url).path
        parts = [p for p in path.split("/") if p]
        section = parts[1] if len(parts) > 1 else "news"
        return {"url": url, "title": title, "section": section, "body": body, "source": "samaa"}
    except Exception:
        return None


SOURCES = {
    "express": (collect_express, parse_express),
    "jang": (collect_jang, parse_jang),
    "geo": (collect_geo, parse_geo),
    "samaa": (collect_samaa, parse_samaa),
}


def main():
    if len(sys.argv) < 2:
        print("Usage: python 04_scrape_safe.py <source_name>")
        print(f"Sources: {list(SOURCES.keys())}")
        sys.exit(1)

    name = sys.argv[1].lower()
    if name not in SOURCES:
        print(f"Unknown source: {name}")
        sys.exit(1)

    collector, parser = SOURCES[name]
    print(f"=== {name.upper()} ===", flush=True)
    print(f"Collecting URLs...", flush=True)
    t0 = time.time()
    try:
        urls = collector()
    except Exception as e:
        print(f"FATAL during URL collection: {e}", flush=True)
        traceback.print_exc()
        sys.exit(2)

    print(f"URLs collected: {len(urls)} in {time.time()-t0:.1f}s", flush=True)
    if not urls:
        print("No URLs found, exiting", flush=True)
        sys.exit(0)

    url_list = list(urls)[:1500]
    print(f"Parsing {len(url_list)} articles...", flush=True)

    articles = []
    failed = 0
    t1 = time.time()
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(parser, u): u for u in url_list}
        for i, fut in enumerate(as_completed(futures)):
            try:
                art = fut.result(timeout=15)
                if art:
                    articles.append(art)
                else:
                    failed += 1
            except Exception:
                failed += 1
            if (i + 1) % 50 == 0:
                print(f"  [{i+1}/{len(url_list)}] ok={len(articles)} fail={failed} elapsed={time.time()-t1:.1f}s", flush=True)
                # Save incrementally
                out_path = os.path.join(OUT_DIR, f"{name}_articles.json")
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"\nDone: parsed={len(articles)} failed={failed} in {time.time()-t1:.1f}s", flush=True)
    out_path = os.path.join(OUT_DIR, f"{name}_articles.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f"Saved: {out_path}", flush=True)

    # Quick stats
    from collections import Counter
    by_sec = Counter(a["section"] for a in articles)
    print(f"\nTop sections:", flush=True)
    for s, c in by_sec.most_common(10):
        print(f"  {c:5d}  {s}", flush=True)
    total_words = sum(len(a["body"].split()) for a in articles)
    print(f"\nTotal words: {total_words:,}", flush=True)


if __name__ == "__main__":
    main()
