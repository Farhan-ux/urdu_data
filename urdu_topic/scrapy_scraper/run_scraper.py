#!/usr/bin/env python3
"""
Runner script for the Scrapy-based Urdu news scraper.

Usage:
    python run_scraper.py                           # all sources, full crawl
    python run_scraper.py --sources express,nawaiwaqt  # specific sources
    python run_scraper.py --max-pages 100           # limit pages per category (testing)
    python run_scraper.py --max-articles 10000      # stop after N articles (testing)

This script:
1. Starts the Scrapy spider
2. Monitors progress
3. Logs stats every 30 seconds
4. Saves everything to OUTPUT_DIR (default: /data/urdu_scrape)
"""
import os
import sys
import time
import argparse
import threading
from datetime import datetime

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def main():
    parser = argparse.ArgumentParser(description="Scrapy-based Urdu news scraper")
    parser.add_argument("--sources", default=None,
                        help="Comma-separated source keys (default: all)")
    parser.add_argument("--max-pages", type=int, default=None,
                        help="Max pages per category (default: source-specific)")
    parser.add_argument("--max-articles", type=int, default=None,
                        help="Stop after N articles (approximate)")
    parser.add_argument("--output-dir", default=os.environ.get("OUTPUT_DIR", "/data/urdu_scrape"),
                        help="Output directory (default: /data/urdu_scrape)")
    parser.add_argument("--concurrent", type=int, default=64,
                        help="Total concurrent requests (default: 64)")
    parser.add_argument("--concurrent-per-domain", type=int, default=16,
                        help="Concurrent per domain (default: 16)")
    parser.add_argument("--delay", type=float, default=0.1,
                        help="Delay between requests in seconds (default: 0.1)")
    args = parser.parse_args()

    # Set env vars
    os.environ["OUTPUT_DIR"] = args.output_dir
    os.makedirs(args.output_dir, exist_ok=True)

    # Load settings
    settings = get_project_settings()
    settings.set("CONCURRENT_REQUESTS", args.concurrent)
    settings.set("CONCURRENT_REQUESTS_PER_DOMAIN", args.concurrent_per_domain)
    settings.set("DOWNLOAD_DELAY", args.delay)
    settings.set("OUTPUT_DIR", args.output_dir)

    # Log file
    log_path = os.path.join(args.output_dir, f"scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    settings.set("LOG_FILE", log_path)

    print(f"=" * 60)
    print(f"  Scrapy Urdu News Scraper")
    print(f"=" * 60)
    print(f"  Sources: {args.sources or 'all'}")
    print(f"  Max pages/category: {args.max_pages or 'source-specific'}")
    print(f"  Output dir: {args.output_dir}")
    print(f"  Concurrent: {args.concurrent} total, {args.concurrent_per_domain}/domain")
    print(f"  Delay: {args.delay}s")
    print(f"  Log file: {log_path}")
    print(f"  Started: {datetime.now().isoformat()}")
    print(f"=" * 60)

    # Start scraper
    process = CrawlerProcess(settings, install_root_handler=False)
    process.crawl(
        "urdu_news",
        sources=args.sources,
        max_pages=args.max_pages,
    )
    process.start()  # blocks until done

    print(f"\nScraping finished at {datetime.now().isoformat()}")
    print(f"Output: {args.output_dir}")


if __name__ == "__main__":
    main()
