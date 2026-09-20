"""Item pipelines for Urdu news scraper."""
import os
import json
import csv
import threading
from itemadapter import ItemAdapter


class DuplicatesPipeline:
    """Drop already-seen URLs (in-memory per source)."""
    seen_urls = set()
    lock = threading.Lock()

    def process_item(self, item, spider):
        url = item.get("url", "")
        with self.lock:
            if url in self.seen_urls:
                spider.logger.debug(f"Duplicate dropped: {url[:80]}")
                raise DropItem(f"Duplicate URL: {url}")
            self.seen_urls.add(url)
        return item


from scrapy.exceptions import DropItem


class JsonWriterPipeline:
    """Append each article to a JSONL file per source."""
    files = {}
    lock = threading.Lock()

    def open_spider(self, spider):
        source = getattr(spider, "source_key", spider.name)
        self.source = source
        out_dir = os.environ.get("OUTPUT_DIR", "/data/urdu_scrape")
        os.makedirs(out_dir, exist_ok=True)
        self.path = os.path.join(out_dir, f"{source}_articles.jsonl")
        # Open in append mode (resume support)
        self.fh = open(self.path, "a", encoding="utf-8")
        spider.logger.info(f"Appending to {self.path}")

    def process_item(self, item, spider):
        line = json.dumps(dict(item), ensure_ascii=False)
        with self.lock:
            self.fh.write(line + "\n")
            self.fh.flush()
        return item

    def close_spider(self, spider):
        with self.lock:
            self.fh.close()


class CsvWriterPipeline:
    """Append to a combined CSV with category labels (for ML training)."""
    lock = threading.Lock()
    header_written = False

    def open_spider(self, spider):
        out_dir = os.environ.get("OUTPUT_DIR", "/data/urdu_scrape")
        os.makedirs(out_dir, exist_ok=True)
        self.path = os.path.join(out_dir, "all_articles_labeled.csv")
        # Check if file exists (for resume)
        self.file_exists = os.path.exists(self.path) and os.path.getsize(self.path) > 0
        self.fh = open(self.path, "a", encoding="utf-8", newline="")
        self.writer = csv.writer(self.fh)
        if not self.file_exists:
            self.writer.writerow(["url", "title", "category", "source", "publish_date", "body", "word_count"])
            self.header_written = True

    def process_item(self, item, spider):
        with self.lock:
            self.writer.writerow([
                item.get("url", ""),
                item.get("title", ""),
                item.get("category", ""),
                item.get("source", ""),
                item.get("publish_date", ""),
                item.get("body", "")[:5000],  # cap body for CSV
                item.get("word_count", 0),
            ])
        return item

    def close_spider(self, spider):
        with self.lock:
            self.fh.close()


class StatsPipeline:
    """Log progress every 100 articles."""
    counters = {}
    lock = threading.Lock()

    def open_spider(self, spider):
        source = getattr(spider, "source_key", spider.name)
        self.source = source
        with self.lock:
            self.counters[source] = 0

    def process_item(self, item, spider):
        with self.lock:
            self.counters[self.source] = self.counters.get(self.source, 0) + 1
            count = self.counters[self.source]
        if count % 100 == 0:
            spider.logger.info(f"[{self.source}] Scraped {count:,} articles")
        return item
