"""
Final scraper — Jang + Nawa-i-Waqt (Express already done, BBC already done).
Jang pagination is fake, so we use 1 page per category but walk all 8 categories.
Nawa-i-Waqt uses date-based URLs.
"""
import os, sys, json, time, re, traceback
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

OUT_DIR = "/home/z/my-project/urdu_topic/data"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ur,en;q=0.9",
}


def safe_get(url, timeout=8):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r.text
    except Exception:
        return None
    return None


# === JANG — 1 page per category ===
def collect_jang():
    cats = ["latest-news", "pakistan", "world", "sports", "entertainment", "science", "business", "lifestyle", "magazines"]
    urls = set()
    for cat in cats:
        url = f"https://jang.com.pk/category/{cat}"
        html = safe_get(url)
        if not html:
            print(f"  jang/{cat}: FAILED", flush=True)
            continue
        soup = BeautifulSoup(html, "lxml")
        page_urls = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if re.search(r"https://jang\.com\.pk/news/\d+", href):
                page_urls.add(href)
        urls.update(page_urls)
        print(f"  jang/{cat}: +{len(page_urls)} (total {len(urls)})", flush=True)
        time.sleep(0.3)
    return urls


def parse_jang(url):
    html = safe_get(url)
    if not html:
        return None
    try:
        soup = BeautifulSoup(html, "lxml")
        title = soup.find("h1").get_text(strip=True) if soup.find("h1") else ""
        body_parts = []
        # Jang uses div.detail-view-content
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


# === NAWA-I-WAQT — date-based URLs ===
def collect_nawaiwaqt():
    # Try multiple categories with date-based URL pattern
    cats = ["latest-news", "pakistan", "world", "sports", "entertainment", "science", "business", "lifestyle"]
    urls = set()
    for cat in cats:
        # Try without /page/
        url = f"https://www.nawaiwaqt.com.pk/{cat}"
        html = safe_get(url)
        if not html:
            print(f"  nawaiwaqt/{cat}: FAILED", flush=True)
            continue
        soup = BeautifulSoup(html, "lxml")
        page_urls = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            # Nawa-i-Waqt uses /DD-Mon-YYYY/<id> pattern
            if re.search(r"nawaiwaqt\.com\.pk/\d{1,2}-\w+-\d{4}/\d+", href):
                page_urls.add(href)
        urls.update(page_urls)
        print(f"  nawaiwaqt/{cat}: +{len(page_urls)} (total {len(urls)})", flush=True)
        time.sleep(0.3)
    return urls


def parse_nawaiwaqt(url):
    html = safe_get(url)
    if not html:
        return None
    try:
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
        path = urlparse(url).path
        parts = [p for p in path.split("/") if p]
        section = parts[0] if parts else "news"
        return {"url": url, "title": title, "section": section, "body": body, "source": "nawaiwaqt"}
    except Exception:
        return None


SOURCES = [
    ("jang", collect_jang, parse_jang),
    ("nawaiwaqt", collect_nawaiwaqt, parse_nawaiwaqt),
]


def run_source(name, collector, parser, max_articles=1500):
    print(f"\n=== {name.upper()} ===", flush=True)
    print(f"Collecting URLs...", flush=True)
    t0 = time.time()
    urls = collector()
    print(f"URLs: {len(urls)} in {time.time()-t0:.1f}s", flush=True)
    if not urls:
        return []

    url_list = list(urls)[:max_articles]
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
                with open(os.path.join(OUT_DIR, f"{name}_articles.json"), "w", encoding="utf-8") as f:
                    json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"Done {name}: parsed={len(articles)} failed={failed} in {time.time()-t1:.1f}s", flush=True)
    with open(os.path.join(OUT_DIR, f"{name}_articles.json"), "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    return articles


def main():
    print(f"Final scraper starting at {time.strftime('%H:%M:%S')}", flush=True)

    all_articles = []
    # Load existing
    for s in ["bbc", "express"]:
        p = os.path.join(OUT_DIR, f"{s}_articles.json")
        if os.path.exists(p):
            with open(p) as f:
                all_articles.extend(json.load(f))
    print(f"Pre-loaded: {len(all_articles)} articles", flush=True)

    for name, collector, parser in SOURCES:
        try:
            arts = run_source(name, collector, parser)
            all_articles.extend(arts)
        except Exception as e:
            print(f"FATAL on {name}: {e}", flush=True)
            traceback.print_exc()

    # Final combine
    print(f"\n=== FINAL ===", flush=True)
    from collections import Counter
    by_source = Counter(a["source"] for a in all_articles)
    for s, c in by_source.most_common():
        print(f"  {c:5d}  {s}", flush=True)
    print(f"Total: {len(all_articles)} articles", flush=True)
    out = os.path.join(OUT_DIR, "all_articles.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)
    print(f"Saved: {out}", flush=True)

    total_words = sum(len(a["body"].split()) for a in all_articles)
    print(f"Total words: {total_words:,}", flush=True)


if __name__ == "__main__":
    main()
