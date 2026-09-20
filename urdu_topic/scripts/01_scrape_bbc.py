"""
BBC Urdu article scraper.
Pulls article URLs from BBC Urdu sitemap, then extracts title + body + section + date.
"""
import os, json, time, re, sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

OUT_DIR = "/home/z/my-project/urdu_topic/data"
os.makedirs(OUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ur,en;q=0.9",
}

# BBC Urdu sections
SECTIONS = [
    "https://www.bbc.com/urdu",
    "https://www.bbc.com/urdu/news",
    "https://www.bbc.com/urdu/sport",
    "https://www.bbc.com/urdu/science",
    "https://www.bbc.com/urdu/world",
    "https://www.bbc.com/urdu/pakistan",
    "https://www.bbc.com/urdu/india",
    "https://www.bbc.com/urdu/business",
    "https://www.bbc.com/urdu/entertainment",
    "https://www.bbc.com/urdu/lives",
    "https://www.bbc.com/urdu/regional",
]

def fetch(url, retries=3, timeout=15):
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            if r.status_code == 200:
                return r.text
            elif r.status_code == 429:
                time.sleep(5 * (attempt + 1))
            else:
                return None
        except Exception:
            time.sleep(2 * (attempt + 1))
    return None


def get_article_links_from_section(section_url, max_links=2000):
    """Get article URLs by walking the section pages."""
    urls = set()
    # BBC Urdu uses paths like /urdu/<section>-<id>
    html = fetch(section_url)
    if not html:
        return urls
    soup = BeautifulSoup(html, "lxml")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/urdu/") and "-" in href and re.search(r"\d{5,}", href):
            full = urljoin("https://www.bbc.com", href)
            urls.add(full)
        elif href.startswith("https://www.bbc.com/urdu/") and re.search(r"\d{5,}", href):
            urls.add(href)
    return urls


def get_links_from_sitemap():
    """Try BBC Urdu sitemap for article URLs."""
    urls = set()
    sitemap_urls = [
        "https://www.bbc.com/urdu/sitemap.xml",
        "https://www.bbc.com/sitemaps/urdu-sitemap.xml",
        "https://www.bbc.com/sitemaps/index-urdu.xml",
    ]
    for sm in sitemap_urls:
        xml = fetch(sm, timeout=20)
        if not xml:
            continue
        # Extract URLs from XML
        for match in re.findall(r"<loc>([^<]+)</loc>", xml):
            if "urdu" in match and re.search(r"\d{5,}", match):
                urls.add(match)
    return urls


def parse_article(url):
    """Extract title, body, section, date from BBC Urdu article."""
    html = fetch(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "lxml")

    # Title
    title = ""
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
    if not title:
        og = soup.find("meta", property="og:title")
        if og:
            title = og.get("content", "").strip()

    # Body — BBC Urdu uses <article> with <div data-component="text-block">
    body_parts = []
    article_tag = soup.find("article") or soup
    # Try multiple selectors
    for div in article_tag.find_all(["div", "p"], attrs={"data-component": "text-block"}):
        body_parts.append(div.get_text(strip=True))
    if not body_parts:
        # Fallback: look for main content paragraphs
        for p in article_tag.find_all("p"):
            t = p.get_text(strip=True)
            if len(t) > 40:  # skip captions
                body_parts.append(t)
    body = " ".join(body_parts)

    if not body or len(body) < 200:
        return None

    # Section — from URL pattern or breadcrumbs
    section = ""
    path = urlparse(url).path
    parts = path.split("/")
    if len(parts) >= 3:
        section = parts[2]  # /urdu/<section>-...

    # Date — look for time element
    date = ""
    time_tag = soup.find("time")
    if time_tag:
        date = time_tag.get("datetime", "") or time_tag.get_text(strip=True)

    return {
        "url": url,
        "title": title,
        "section": section,
        "date": date,
        "body": body,
        "source": "bbc_urdu",
        "word_count": len(body.split()),
    }


def main():
    print("=== BBC Urdu Scraper ===")
    # Step 1: collect URLs
    all_urls = set()

    # Try sitemap first
    print("Fetching sitemap...")
    sm_urls = get_links_from_sitemap()
    print(f"  Sitemap: {len(sm_urls)} URLs")
    all_urls.update(sm_urls)

    # Walk sections
    print("Walking sections...")
    for sec in SECTIONS:
        u = get_article_links_from_section(sec)
        print(f"  {sec}: {len(u)} URLs")
        all_urls.update(u)
        time.sleep(1)

    print(f"\nTotal unique article URLs: {len(all_urls)}")
    if not all_urls:
        print("No URLs found. Saving empty result.")
        return

    # Save URL list
    url_list_path = os.path.join(OUT_DIR, "bbc_urdu_urls.json")
    with open(url_list_path, "w") as f:
        json.dump(sorted(all_urls), f, indent=2)
    print(f"Saved URL list: {url_list_path}")

    # Step 2: parse articles (parallel)
    articles = []
    failed = 0
    print(f"\nParsing {len(all_urls)} articles...")
    url_list = list(all_urls)

    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(parse_article, u): u for u in url_list}
        for i, fut in enumerate(as_completed(futures)):
            url = futures[fut]
            try:
                art = fut.result()
                if art:
                    articles.append(art)
                else:
                    failed += 1
            except Exception as e:
                failed += 1
            if (i + 1) % 50 == 0:
                print(f"  [{i+1}/{len(url_list)}] ok={len(articles)} fail={failed}")

    print(f"\nDone. Parsed: {len(articles)}  Failed: {failed}")

    # Save articles
    out_path = os.path.join(OUT_DIR, "bbc_urdu_articles.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f"Saved: {out_path}")

    # Stats
    from collections import Counter
    sections = Counter(a["section"] for a in articles)
    print("\nSection distribution:")
    for s, c in sections.most_common():
        print(f"  {c:5d}  {s}")

    total_words = sum(a["word_count"] for a in articles)
    print(f"\nTotal articles: {len(articles)}")
    print(f"Total words: {total_words:,}")
    print(f"Avg words/article: {total_words // max(1, len(articles))}")


if __name__ == "__main__":
    main()
