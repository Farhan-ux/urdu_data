# Scrapy settings for urdu_news_scraper project
# Optimized for 5M+ article scraping with auto-throttle

import os
from scrapy.utils.log import configure_logging

BOT_NAME = "urdu_news_scraper"
SPIDER_MODULES = ["urdu_news_scraper.spiders"]
NEWSPIDER_MODULE = "urdu_news_scraper.spiders"

# ============================================================
# CONCURRENCY — aggressive but polite
# ============================================================
CONCURRENT_REQUESTS = 64              # Total concurrent requests across all spiders
CONCURRENT_REQUESTS_PER_DOMAIN = 16   # Per domain (each news site)
DOWNLOAD_DELAY = 0.1                  # 100ms between requests (vs 500ms before)
DOWNLOAD_TIMEOUT = 15

# ============================================================
# RETRY & ROBUSTNESS
# ============================================================
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [429, 500, 502, 503, 504, 408, 111]
DOWNLOAD_MAXSIZE = 5 * 1024 * 1024    # 5 MB max per article
DOWNLOAD_WARNSIZE = 1 * 1024 * 1024

# ============================================================
# AUTO THROTTLE — auto-adjusts speed based on server response
# ============================================================
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0.1
AUTOTHROTTLE_MAX_DELAY = 5.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 12.0  # Target 12 concurrent per domain
AUTOTHROTTLE_DEBUG = False

# ============================================================
# CACHING & DEDUP
# ============================================================
HTTPCACHE_ENABLED = False  # Disable for production (saves disk)
DUPEFILTER_CLASS = "scrapy.dupefilters.RFPDupeFilter"

# ============================================================
# USER AGENTS — rotate to avoid blocking
# ============================================================
USER_AGENT = "Mozilla/5.0 (compatible; UrduNLP-Research/2.0; +https://github.com/Farhan-ux/urdu_data; academic research)"

# Rotate user agents per request
DOWNLOADER_MIDDLEWARES = {
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
    "urdu_news_scraper.middlewares.RotateUserAgentMiddleware": 400,
    "urdu_news_scraper.middlewares.RetryMiddleware": 550,
}

# ============================================================
# ITEM PIPELINES — save articles + dedup
# ============================================================
ITEM_PIPELINES = {
    "urdu_news_scraper.pipelines.DuplicatesPipeline": 100,
    "urdu_news_scraper.pipelines.JsonWriterPipeline": 200,
    "urdu_news_scraper.pipelines.CsvWriterPipeline": 300,
    "urdu_news_scraper.pipelines.StatsPipeline": 400,
}

# ============================================================
# OUTPUT
# ============================================================
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/data/urdu_scrape")
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
LOG_DATEFORMAT = "%H:%M:%S"

# Robots.txt — we override since we're scraping news sites (not following robots)
ROBOTSTXT_OBEY = False

# Telnet console (disabled for security)
TELNETCONSOLE_ENABLED = False

# Cookies (not needed for news sites)
COOKIES_ENABLED = False

# Referer (helps avoid blocking)
REFERER_ENABLED = True
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ur,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
}
