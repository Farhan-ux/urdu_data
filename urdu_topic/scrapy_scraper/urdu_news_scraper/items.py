"""Scrapy items for Urdu news articles."""
import scrapy


class ArticleItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    body = scrapy.Field()
    category = scrapy.Field()       # Ground-truth label (from URL/category page)
    source = scrapy.Field()         # Source key (e.g., 'express')
    source_name = scrapy.Field()    # Human-readable source name
    publish_date = scrapy.Field()
    author = scrapy.Field()
    word_count = scrapy.Field()
    scraped_at = scrapy.Field()
