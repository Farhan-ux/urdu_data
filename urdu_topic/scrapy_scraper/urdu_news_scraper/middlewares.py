"""Scrapy middlewares for Urdu news scraper."""
import random
from scrapy import signals
from scrapy.http import Request


# User agents to rotate (avoids blocking)
USER_AGENTS = [
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36",
]


class RotateUserAgentMiddleware:
    """Rotate User-Agent per request to avoid blocking."""
    def process_request(self, request, spider):
        request.headers["User-Agent"] = random.choice(USER_AGENTS)


class RetryMiddleware:
    """Custom retry middleware with longer backoff for 403s."""
    def process_response(self, request, response, spider):
        if response.status in (429, 503):
            spider.logger.warning(f"Rate limited on {request.url} — backing off")
            # Scrapy's built-in retry will handle this
        if response.status == 403:
            spider.logger.warning(f"403 Forbidden on {request.url} — trying Googlebot UA")
            request.headers["User-Agent"] = USER_AGENTS[0]  # Googlebot
            return Request(url=request.url, headers=request.headers, dont_filter=True, meta=request.meta)
        return response
