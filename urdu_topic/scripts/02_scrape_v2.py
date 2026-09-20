"""
Robust multi-source Urdu news scraper — sequential per source.
Each source has its own link pattern + content parser.
Targets: Express, Jang, Geo, Dunya, Samaa, Nawa-i-Waqt
"""
import os, json, time, re, sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

OUT_DIR = "/home/z/my-project/urdu_topic/data"
os.makedirs(OUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ur,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def fetch(url, retries=2, timeout=12):
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            if r.status_code == 200:
                return r.text
            elif r.status_code == 429:
                time.sleep(3 + attempt * 2)
            else:
                return None
        except Exception:
            time.sleep(1 + attempt)
    return None


# ============================================================
# EXPRESS
# ============================================================
def express_collect_urls(pages_per_cat=10):
    cats = [
        "https://www.express.pk/latest-news",
        "https://www.express.pk/pakistan",
        "https://www.express.pk/world",
        "https://www.express.pk/sports",
        "https://www.express.pk/entertainment",
        "https://www.express.pk/science",
        "https://www.express.pk/business",
        "https://www.express.pk/lifestyle",
    ]
    urls = set()
    for cat in cats:
        for page in range(1, pages_per_cat + 1):
            url = f"{cat}?page={page}"
            html = fetch(url)
            if not html:
                continue
            soup = BeautifulSoup(html, "lxml")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/story/" in href and re.search(r"/\d{5,}", href):
                    if href.startswith("/"):
                        href = "https://www.express.pk" + href
                    urls.add(href)
            time.sleep(0.4)
    return urls


def express_parse(url):
    html = fetch(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "lxml")
    title = ""
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
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
    path = urlparse(url).path
    parts = [p for p in path.split("/") if p]
    section = parts[0] if parts else "news"
    date = ""
    time_tag = soup.find("time")
    if time_tag:
        date = time_tag.get("datetime", "") or time_tag.get_text(strip=True)
    return {"url": url, "title": title, "section": section, "date": date, "body": body, "source": "express"}


# ============================================================
# JANG
# ============================================================
def jang_collect_urls(pages_per_cat=8):
    cats = [
        "https://jang.com.pk/category/latest-news",
        "https://jang.com.pk/category/pakistan",
        "https://jang.com.pk/category/world",
        "https://jang.com.pk/category/sports",
        "https://jang.com.pk/category/entertainment",
        "https://jang.com.pk/category/science",
        "https://jang.com.pk/category/business",
        "https://jang.com.pk/category/lifestyle",
    ]
    urls = set()
    for cat in cats:
        for page in range(1, pages_per_cat + 1):
            url = f"{cat}/page/{page}"
            html = fetch(url)
            if not html:
                continue
            soup = BeautifulSoup(html, "lxml")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if re.search(r"https://jang\.com\.pk/news/\d+", href):
                    urls.add(href)
            time.sleep(0.4)
    return urls


def jang_parse(url):
    html = fetch(url)
    if not html:
        return None
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
    date = ""
    time_tag = soup.find("time")
    if time_tag:
        date = time_tag.get("datetime", "") or time_tag.get_text(strip=True)
    return {"url": url, "title": title, "section": section, "date": date, "body": body, "source": "jang"}


# ============================================================
# GEO
# ============================================================
def geo_collect_urls(pages_per_cat=8):
    cats = [
        "https://urdu.geo.tv/category/pakistan",
        "https://urdu.geo.tv/category/world",
        "https://urdu.geo.tv/category/sports",
        "https://urdu.geo.tv/category/entertainment",
        "https://urdu.geo.tv/category/science",
        "https://urdu.geo.tv/category/business",
        "https://urdu.geo.tv/category/lifestyle",
        "https://urdu.geo.tv/category/latest",
    ]
    urls = set()
    for cat in cats:
        for page in range(1, pages_per_cat + 1):
            url = f"{cat}/page/{page}"
            html = fetch(url)
            if not html:
                continue
            soup = BeautifulSoup(html, "lxml")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if re.search(r"https://urdu\.geo\.tv/latest/\d+", href) or re.search(r"https://urdu\.geo\.tv/news/\d+", href):
                    urls.add(href)
            time.sleep(0.4)
    return urls


def geo_parse(url):
    html = fetch(url)
    if not html:
        return None
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
    date = ""
    time_tag = soup.find("time")
    if time_tag:
        date = time_tag.get("datetime", "") or time_tag.get_text(strip=True)
    return {"url": url, "title": title, "section": section, "date": date, "body": body, "source": "geo"}


# ============================================================
# SAMAA
# ============================================================
def samaa_collect_urls(pages_per_cat=6):
    cats = [
        "https://www.samaa.tv/urdu/news",
        "https://www.samaa.tv/urdu/pakistan",
        "https://www.samaa.tv/urdu/world",
        "https://www.samaa.tv/urdu/sports",
        "https://www.samaa.tv/urdu/entertainment",
        "https://www.samaa.tv/urdu/business",
        "https://www.samaa.tv/urdu/tech",
    ]
    urls = set()
    for cat in cats:
        for page in range(1, pages_per_cat + 1):
            url = f"{cat}?page={page}"
            html = fetch(url)
            if not html:
                continue
            soup = BeautifulSoup(html, "lxml")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if re.search(r"\d{6,}", href) and "samaa.tv" in href:
                    urls.add(href)
            time.sleep(0.4)
    return urls


def samaa_parse(url):
    html = fetch(url)
    if not html:
        return None
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
    date = ""
    time_tag = soup.find("time")
    if time_tag:
        date = time_tag.get("datetime", "") or time_tag.get_text(strip=True)
    return {"url": url, "title": title, "section": section, "date": date, "body": body, "source": "samaa"}


# ============================================================
# NAWA-I-WAQT
# ============================================================
def nawaiwaqt_collect_urls(pages_per_cat=6):
    cats = [
        "https://www.nawaiwaqt.com.pk/latest-news",
        "https://www.nawaiwaqt.com.pk/pakistan",
        "https://www.nawaiwaqt.com.pk/world",
        "https://www.nawaiwaqt.com.pk/sports",
        "https://www.nawaiwaqt.com.pk/entertainment",
        "https://www.nawaiwaqt.com.pk/science",
        "https://www.nawaiwaqt.com.pk/business",
    ]
    urls = set()
    for cat in cats:
        for page in range(1, pages_per_cat + 1):
            url = f"{cat}/page/{page}"
            html = fetch(url)
            if not html:
                continue
            soup = BeautifulSoup(html, "lxml")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if re.search(r"\d{6,}", href) and "nawaiwaqt" in href:
                    urls.add(href)
            time.sleep(0.4)
    return urls


def nawaiwaqt_parse(url):
    html = fetch(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "lxml")
    title = ""
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
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
    date = ""
    time_tag = soup.find("time")
    if time_tag:
        date = time_tag.get("datetime", "") or time_tag.get_text(strip=True)
    return {"url": url, "title": title, "section": section, "date": date, "body": body, "source": "nawaiwaqt"}


SOURCES = [
    ("express", express_collect_urls, express_parse),
    ("jang", jang_collect_urls, jang_parse),
    ("geo", geo_collect_urls, geo_parse),
    ("samaa", samaa_collect_urls, samaa_parse),
    ("nawaiwaqt", nawaiwaqt_collect_urls, nawaiwaqt_parse),
]


def scrape_source(name, collector, parser, max_articles=1500):
    print(f"\n=== {name.upper()} ===")
    print(f"  Collecting URLs...")
    urls = collector()
    print(f"  URLs: {len(urls)}")
    if not urls:
        return []

    url_list = list(urls)[:max_articles]
    print(f"  Parsing {len(url_list)} articles (parallel)...")
    articles = []
    failed = 0
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(parser, u): u for u in url_list}
        for i, fut in enumerate(as_completed(futures)):
            try:
                art = fut.result()
                if art:
                    articles.append(art)
                else:
                    failed += 1
            except Exception:
                failed += 1
            if (i + 1) % 100 == 0:
                print(f"    [{i+1}/{len(url_list)}] ok={len(articles)} fail={failed}")
                # Save partial periodically
                out_path = os.path.join(OUT_DIR, f"{name}_articles.json")
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f"  Final: parsed={len(articles)} failed={failed}")
    out_path = os.path.join(OUT_DIR, f"{name}_articles.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {out_path}")
    return articles


def main():
    # Allow running a single source via command-line arg
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    all_articles = []

    # Load BBC Urdu (already scraped)
    bbc_path = os.path.join(OUT_DIR, "bbc_urdu_articles.json")
    if os.path.exists(bbc_path) and target == "all":
        with open(bbc_path) as f:
            all_articles = json.load(f)
        print(f"Loaded BBC Urdu: {len(all_articles)} articles")

    for name, collector, parser in SOURCES:
        if target != "all" and target != name:
            continue
        try:
            articles = scrape_source(name, collector, parser)
            all_articles.extend(articles)
        except Exception as e:
            print(f"  ERROR on {name}: {e}")
            continue

    if target == "all":
        # Save combined
        out_path = os.path.join(OUT_DIR, "all_articles.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(all_articles, f, ensure_ascii=False, indent=2)
        print(f"\n=== COMBINED ===")
        print(f"Total: {len(all_articles)} articles")
        print(f"Saved: {out_path}")
        from collections import Counter
        by_source = Counter(a["source"] for a in all_articles)
        for s, c in by_source.most_common():
            print(f"  {c:5d}  {s}")


if __name__ == "__main__":
    main()
