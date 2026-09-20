"""
Multi-source Urdu news scraper.
Targets: Express, Jang, Geo, Dunya, Samaa, Nawa-i-Waqt
For each source: walk category pages, collect article URLs, parse title+body+section.
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

# Source configs: name -> {base, categories, article_url_pattern}
SOURCES = {
    "express": {
        "base": "https://www.express.pk",
        "categories": [
            "https://www.express.pk/latest-news",
            "https://www.express.pk/pakistan",
            "https://www.express.pk/world",
            "https://www.express.pk/sports",
            "https://www.express.pk/entertainment",
            "https://www.express.pk/science",
            "https://www.express.pk/business",
            "https://www.express.pk/lifestyle",
            "https://www.express.pk/crime",
            "https://www.express.pk/corona-virus",
        ],
        "pattern": r"/[^/]+/\d+/",
        "page_param": "?page={}",
    },
    "jang": {
        "base": "https://jang.com.pk",
        "categories": [
            "https://jang.com.pk/category/latest-news",
            "https://jang.com.pk/category/pakistan",
            "https://jang.com.pk/category/world",
            "https://jang.com.pk/category/sports",
            "https://jang.com.pk/category/entertainment",
            "https://jang.com.pk/category/science",
            "https://jang.com.pk/category/business",
            "https://jang.com.pk/category/lifestyle",
            "https://jang.com.pk/category/magazines",
        ],
        "pattern": r"/\d+/",
        "page_param": "page/{}",
    },
    "geo": {
        "base": "https://urdu.geo.tv",
        "categories": [
            "https://urdu.geo.tv/category/pakistan",
            "https://urdu.geo.tv/category/world",
            "https://urdu.geo.tv/category/sports",
            "https://urdu.geo.tv/category/entertainment",
            "https://urdu.geo.tv/category/science",
            "https://urdu.geo.tv/category/business",
            "https://urdu.geo.tv/category/lifestyle",
        ],
        "pattern": r"/\d+/",
        "page_param": "page/{}",
    },
    "dunya": {
        "base": "https://urdu.dunyanews.tv",
        "categories": [
            "https://urdu.dunyanews.tv/index.php/main/0/0",
            "https://urdu.dunyanews.tv/index.php/main/2/0",  # Pakistan
            "https://urdu.dunyanews.tv/index.php/main/4/0",  # World
            "https://urdu.dunyanews.tv/index.php/main/10/0", # Sports
            "https://urdu.dunyanews.tv/index.php/main/13/0", # Entertainment
            "https://urdu.dunyanews.tv/index.php/main/9/0",  # Business
            "https://urdu.dunyanews.tv/index.php/main/12/0", # Science
        ],
        "pattern": r"/\d+_",
        "page_param": "/{}",
    },
    "samaa": {
        "base": "https://www.samaa.tv",
        "categories": [
            "https://www.samaa.tv/urdu/news",
            "https://www.samaa.tv/urdu/pakistan",
            "https://www.samaa.tv/urdu/world",
            "https://www.samaa.tv/urdu/sports",
            "https://www.samaa.tv/urdu/entertainment",
            "https://www.samaa.tv/urdu/business",
            "https://www.samaa.tv/urdu/tech",
            "https://www.samaa.tv/urdu/health",
        ],
        "pattern": r"/\d+/",
        "page_param": "?page={}",
    },
    "nawaiwaqt": {
        "base": "https://www.nawaiwaqt.com.pk",
        "categories": [
            "https://www.nawaiwaqt.com.pk/latest-news",
            "https://www.nawaiwaqt.com.pk/pakistan",
            "https://www.nawaiwaqt.com.pk/world",
            "https://www.nawaiwaqt.com.pk/sports",
            "https://www.nawaiwaqt.com.pk/entertainment",
            "https://www.nawaiwaqt.com.pk/science",
            "https://www.nawaiwaqt.com.pk/business",
            "https://www.nawaiwaqt.com.pk/lifestyle",
        ],
        "pattern": r"/\d+-",
        "page_param": "page/{}",
    },
}


def fetch(url, retries=2, timeout=15):
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


def collect_urls_from_source(source_name, config, pages_per_category=8):
    """Walk category pages to collect article URLs."""
    urls = set()
    for cat_url in config["categories"]:
        for page in range(1, pages_per_category + 1):
            # Build page URL
            if config["page_param"].startswith("?"):
                page_url = f"{cat_url}{config['page_param'].format(page)}"
            elif config["page_param"].startswith("page/"):
                page_url = f"{cat_url}/{config['page_param'].format(page)}"
            else:
                page_url = f"{cat_url}{config['page_param'].format(page)}"

            html = fetch(page_url)
            if not html:
                continue
            soup = BeautifulSoup(html, "lxml")
            new_count = 0
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if re.search(config["pattern"], href):
                    if href.startswith("/"):
                        full = urljoin(config["base"], href)
                    elif href.startswith("http"):
                        full = href
                    else:
                        full = urljoin(config["base"] + "/", href)
                    # Filter to same domain
                    if config["base"] in full or source_name in full:
                        urls.add(full)
                        new_count += 1
            if page == 1:
                print(f"  [{source_name}] {cat_url.split('/')[-1]}: page 1 -> {new_count} URLs")
            time.sleep(0.5)
    return urls


def parse_article_express(url):
    """Parse Express Urdu article."""
    html = fetch(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "lxml")
    # Title
    title = ""
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
    # Body
    body_parts = []
    # Express uses .story-content or .detail-content
    content = soup.find("div", class_=re.compile(r"story-content|detail-content|content-area"))
    if content:
        for p in content.find_all("p"):
            t = p.get_text(strip=True)
            if t and len(t) > 20:
                body_parts.append(t)
    if not body_parts:
        # Fallback: all paragraphs in main
        for p in soup.find_all("p"):
            t = p.get_text(strip=True)
            if t and len(t) > 40 and "javascript" not in t.lower():
                body_parts.append(t)
    body = " ".join(body_parts[:30])  # cap at 30 paragraphs
    if len(body) < 200:
        return None
    # Section from URL
    path = urlparse(url).path
    section = path.split("/")[1] if len(path.split("/")) > 1 else "news"
    # Date
    date = ""
    time_tag = soup.find("time")
    if time_tag:
        date = time_tag.get("datetime", "") or time_tag.get_text(strip=True)
    return {"url": url, "title": title, "section": section, "date": date, "body": body, "source": "express"}


def parse_article_jang(url):
    """Parse Jang article."""
    html = fetch(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "lxml")
    title = ""
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
    body_parts = []
    content = soup.find("div", class_=re.compile(r"detail-view|story-content|content-area"))
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


def parse_article_geo(url):
    """Parse Geo Urdu article."""
    html = fetch(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "lxml")
    title = ""
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
    body_parts = []
    content = soup.find("div", class_=re.compile(r"story-area|content-area|entry-content"))
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


def parse_article_dunya(url):
    """Parse Dunya News Urdu article."""
    html = fetch(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "lxml")
    title = ""
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
    body_parts = []
    content = soup.find("div", class_=re.compile(r"news-detail|story-content|content-area"))
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
    section = "news"
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 2:
        section = parts[0]
    date = ""
    time_tag = soup.find("time")
    if time_tag:
        date = time_tag.get("datetime", "") or time_tag.get_text(strip=True)
    return {"url": url, "title": title, "section": section, "date": date, "body": body, "source": "dunya"}


def parse_article_samaa(url):
    """Parse Samaa Urdu article."""
    html = fetch(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "lxml")
    title = ""
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
    body_parts = []
    content = soup.find("div", class_=re.compile(r"story-content|content-area|article-body"))
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


def parse_article_nawaiwaqt(url):
    """Parse Nawa-i-Waqt article."""
    html = fetch(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "lxml")
    title = ""
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
    body_parts = []
    content = soup.find("div", class_=re.compile(r"story-content|content-area|detail-content"))
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


PARSERS = {
    "express": parse_article_express,
    "jang": parse_article_jang,
    "geo": parse_article_geo,
    "dunya": parse_article_dunya,
    "samaa": parse_article_samaa,
    "nawaiwaqt": parse_article_nawaiwaqt,
}


def main():
    all_articles = []
    # Load existing BBC articles
    bbc_path = os.path.join(OUT_DIR, "bbc_urdu_articles.json")
    if os.path.exists(bbc_path):
        with open(bbc_path) as f:
            bbc_articles = json.load(f)
        all_articles.extend(bbc_articles)
        print(f"Loaded {len(bbc_articles)} existing BBC Urdu articles")

    for source_name, config in SOURCES.items():
        print(f"\n=== Source: {source_name} ===")
        # Step 1: collect URLs
        urls = collect_urls_from_source(source_name, config, pages_per_category=8)
        print(f"  Total URLs collected: {len(urls)}")
        if not urls:
            continue

        # Save URL list
        url_path = os.path.join(OUT_DIR, f"{source_name}_urls.json")
        with open(url_path, "w") as f:
            json.dump(sorted(urls), f, indent=2)

        # Step 2: parse articles in parallel
        parser = PARSERS[source_name]
        articles = []
        failed = 0
        url_list = list(urls)[:1500]  # cap at 1500 per source to keep total manageable
        print(f"  Parsing up to {len(url_list)} articles...")
        with ThreadPoolExecutor(max_workers=8) as ex:
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

        print(f"  Parsed: {len(articles)}  Failed: {failed}")

        # Save source articles
        out_path = os.path.join(OUT_DIR, f"{source_name}_articles.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        all_articles.extend(articles)
        print(f"  Saved: {out_path}")

    # Combine all
    print(f"\n=== Final combine ===")
    out_path = os.path.join(OUT_DIR, "all_articles.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)
    print(f"Total articles: {len(all_articles)}")
    print(f"Saved: {out_path}")

    # Stats
    from collections import Counter
    by_source = Counter(a["source"] for a in all_articles)
    print("\nBy source:")
    for s, c in by_source.most_common():
        print(f"  {c:5d}  {s}")

    by_section = Counter(a["section"] for a in all_articles)
    print(f"\nTop 15 sections:")
    for s, c in by_section.most_common(15):
        print(f"  {c:5d}  {s}")

    total_words = sum(len(a["body"].split()) for a in all_articles)
    print(f"\nTotal words: {total_words:,}")
    print(f"Avg words/article: {total_words // max(1, len(all_articles))}")


if __name__ == "__main__":
    main()
