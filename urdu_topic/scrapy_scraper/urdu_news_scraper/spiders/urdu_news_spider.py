"""
Single spider that crawls all 8 Urdu news sources with category-based pagination.

For each source:
1. Start from category pages (e.g., /pakistan, /world, /sports)
2. Follow pagination (page/2, page/3, ...)
3. Extract article URLs
4. Visit each article URL and extract: title, body, category, publish_date

Category is captured from the URL path — this becomes the ground-truth label.
"""
import os
import re
import scrapy
from urllib.parse import urljoin
from datetime import datetime
from ..items import ArticleItem


# ============================================================
# SOURCE CONFIGURATIONS
# ============================================================
SOURCES = {
    "express": {
        "name": "Express Urdu",
        "base": "https://www.express.pk",
        "categories": [
            ("pakistan", "pakistan"), ("world", "world"), ("sports", "sports"),
            ("entertainment", "entertainment"), ("science", "science"),
            ("business", "business"), ("lifestyle", "lifestyle"),
            ("crime", "crime"), ("latest-news", "news"),
        ],
        "article_pattern": r"/story/(\d+)",
        "paginate_template": "{base}/{cat}?page={page}",
        "max_pages_per_cat": 1000,  # very deep
        "use_googlebot": False,
    },
    "nawaiwaqt": {
        "name": "Nawa-i-Waqt",
        "base": "https://www.nawaiwaqt.com.pk",
        "categories": [
            ("pakistan", "pakistan"), ("world", "world"), ("sports", "sports"),
            ("entertainment", "entertainment"), ("business", "business"),
            ("latest-news", "news"),
        ],
        "article_pattern": r"/(\d{1,2}-\w+-\d{4})/(\d+)",
        "paginate_template": "{base}/{cat}/page/{page}",
        "max_pages_per_cat": 5000,  # 6254 sitemaps = many pages
        "use_googlebot": False,
    },
    "aryurdu": {
        "name": "ARY Urdu",
        "base": "https://urdu.arynews.tv",
        "categories": [
            ("category/pakistan", "pakistan"), ("category/world", "world"),
            ("category/sports", "sports"), ("category/entertainment", "entertainment"),
            ("category/business", "business"), ("category/latest-news", "news"),
        ],
        "article_pattern": r"/(\d{5,})",
        "paginate_template": "{base}/{cat}/page/{page}",
        "max_pages_per_cat": 500,
        "use_googlebot": True,  # ARY blocks default UA
    },
    "24newshd": {
        "name": "24 News HD",
        "base": "https://24newshd.tv",
        "categories": [
            ("category/pakistan", "pakistan"), ("category/world", "world"),
            ("category/sports", "sports"), ("category/entertainment", "entertainment"),
            ("category/business", "business"),
        ],
        "article_pattern": r"/(\d{5,})",
        "paginate_template": "{base}/{cat}/page/{page}",
        "max_pages_per_cat": 500,
        "use_googlebot": False,
    },
    "ummat": {
        "name": "Ummat",
        "base": "https://ummat.net",
        "categories": [
            ("category/pakistan", "pakistan"), ("category/world", "world"),
            ("category/sports", "sports"), ("category/business", "business"),
            ("category/latest", "news"),
        ],
        "article_pattern": r"/(\d{5,})",
        "paginate_template": "{base}/{cat}/page/{page}",
        "max_pages_per_cat": 500,
        "use_googlebot": False,
    },
    "bolurdu": {
        "name": "Bol News Urdu",
        "base": "https://urdu.bolnews.com",
        "categories": [
            ("category/latest-news", "news"), ("category/pakistan", "pakistan"),
            ("category/world", "world"), ("category/sports", "sports"),
            ("category/entertainment", "entertainment"), ("category/business", "business"),
        ],
        "article_pattern": r"/(\d{5,})",
        "paginate_template": "{base}/{cat}/page/{page}",
        "max_pages_per_cat": 500,
        "use_googlebot": False,
    },
    "dailyausaf": {
        "name": "Daily Ausaf",
        "base": "https://dailyausaf.com",
        "categories": [
            ("category/pakistan", "pakistan"), ("category/world", "world"),
            ("category/sports", "sports"), ("category/entertainment", "entertainment"),
            ("category/business", "business"),
        ],
        "article_pattern": r"/(\d{5,})",
        "paginate_template": "{base}/{cat}/page/{page}",
        "max_pages_per_cat": 500,
        "use_googlebot": False,
    },
    "independenturdu": {
        "name": "Independent Urdu",
        "base": "https://www.independenturdu.com",
        "categories": [
            ("pakistan", "pakistan"), ("world", "world"),
            ("sports", "sports"), ("entertainment", "entertainment"),
            ("business", "business"), ("science", "science"),
        ],
        "article_pattern": r"/node/(\d+)",
        "paginate_template": "{base}/{cat}?page={page}",
        "max_pages_per_cat": 1000,
        "use_googlebot": False,
    },
}


class UrduNewsSpider(scrapy.Spider):
    """Crawl all Urdu news sources with category-based pagination."""
    name = "urdu_news"
    source_key = "all"  # Used by pipelines

    def __init__(self, sources=None, max_pages=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow filtering sources via CLI: -a sources=express,nawaiwaqt
        if sources:
            self.sources_to_run = [s.strip() for s in sources.split(",") if s.strip() in SOURCES]
        else:
            self.sources_to_run = list(SOURCES.keys())
        # Allow max_pages override: -a max_pages=100
        self.max_pages_override = int(max_pages) if max_pages else None
        # DEBUG: log to stderr so we can see it
        import sys
        print(f"DEBUG: Spider init — sources_to_run={self.sources_to_run}, max_pages_override={self.max_pages_override}", file=sys.stderr, flush=True)

    async def start(self):
        """Scrapy 2.19+ entry point — must be async generator."""
        import sys
        print(f"DEBUG: start called — sources_to_run={self.sources_to_run}", file=sys.stderr, flush=True)
        for source_key in self.sources_to_run:
            cfg = SOURCES[source_key]
            print(f"DEBUG: yielding requests for {source_key} ({len(cfg['categories'])} categories)", file=sys.stderr, flush=True)
            for cat_path, cat_label in cfg["categories"]:
                url = f"{cfg['base']}/{cat_path}"
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_category,
                    meta={
                        "source_key": source_key,
                        "source_name": cfg["name"],
                        "category": cat_label,
                        "cat_path": cat_path,
                        "page": 1,
                        "use_googlebot": cfg["use_googlebot"],
                    },
                    dont_filter=True,
                    errback=self.on_error,
                )

    def parse_category(self, response):
        """Parse a category page: extract article URLs + follow pagination."""
        meta = response.meta
        source_key = meta["source_key"]
        cfg = SOURCES[source_key]
        category = meta["category"]
        page = meta["page"]

        # Extract article URLs matching this source's pattern
        article_urls = response.css("a::attr(href)").getall()
        article_pattern = cfg["article_pattern"]
        base = cfg["base"]

        seen_in_page = set()
        for href in article_urls:
            # Normalize
            if href.startswith("/"):
                href = urljoin(base, href)
            if not href.startswith(base):
                continue
            if re.search(article_pattern, href) and href not in seen_in_page:
                seen_in_page.add(href)
                yield scrapy.Request(
                    url=href,
                    callback=self.parse_article,
                    meta={
                        "source_key": source_key,
                        "source_name": cfg["name"],
                        "category": category,
                        "use_googlebot": meta.get("use_googlebot", False),
                    },
                    errback=self.on_error,
                )

        # Follow pagination (up to max_pages_per_cat)
        max_pages = self.max_pages_override or cfg["max_pages_per_cat"]
        if page < max_pages:
            next_page = page + 1
            next_url = cfg["paginate_template"].format(base=base, cat=meta["cat_path"], page=next_page)
            yield scrapy.Request(
                url=next_url,
                callback=self.parse_category,
                meta={
                    **meta,
                    "page": next_page,
                },
                dont_filter=True,
                errback=self.on_error,
            )

    def parse_article(self, response):
        """Parse an article page: extract title, body, date."""
        meta = response.meta
        source_key = meta["source_key"]
        source_name = meta["source_name"]
        category = meta["category"]

        # Extract title
        title = ""
        h1 = response.css("h1::text").get()
        if h1:
            title = h1.strip()
        else:
            og_title = response.css('meta[property="og:title"]::attr(content)').get()
            if og_title:
                title = og_title.strip()

        # Extract body — try common content selectors
        body_parts = []
        for selector in [
            'div[class*="story-content"] p::text',
            'div[class*="detail-content"] p::text',
            'div[class*="content-area"] p::text',
            'div[class*="entry-content"] p::text',
            'div[class*="post-content"] p::text',
            'div[class*="article-body"] p::text',
            'div[class*="story-area"] p::text',
            'div[class*="detail-view"] p::text',
            'article p::text',
        ]:
            texts = response.css(selector).getall()
            if texts:
                body_parts = [t.strip() for t in texts if t.strip() and len(t.strip()) > 20]
                if body_parts:
                    break
        # Fallback: all long paragraphs
        if not body_parts:
            texts = response.css("p::text").getall()
            body_parts = [t.strip() for t in texts if t.strip() and len(t.strip()) > 40]

        body = " ".join(body_parts[:30])
        if len(body) < 200:
            return  # skip non-articles

        # Extract publish date
        publish_date = ""
        time_tag = response.css("time::attr(datetime)").get()
        if time_tag:
            publish_date = time_tag
        else:
            date_text = response.css("time::text").get()
            if date_text:
                publish_date = date_text.strip()

        # Build item
        item = ArticleItem()
        item["url"] = response.url
        item["title"] = title
        item["body"] = body
        item["category"] = category
        item["source"] = source_key
        item["source_name"] = source_name
        item["publish_date"] = publish_date
        item["author"] = ""
        item["word_count"] = len(body.split())
        item["scraped_at"] = datetime.utcnow().isoformat() + "Z"
        yield item

    def on_error(self, failure):
        """Log errors but don't crash."""
        self.logger.warning(f"Request failed: {failure.value}")
