"""
Verify all dataset URLs in parallel using HEAD requests.
Skip empty URLs and 'Request'/'No' ones without URLs.
Output: url_status.json mapping url -> status (OK/Broken/Timeout/Redirect)
"""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request
import urllib.error
import ssl
import socket

sys.path.insert(0, "/home/z/my-project/scripts")
from papers_data import PAPERS

# Collect unique URLs
urls = set()
for p in PAPERS:
    u = (p.get("dataset_url") or "").strip()
    if u and u.startswith("http"):
        urls.add(u)
    u2 = (p.get("paper_url") or "").strip()
    if u2 and u2.startswith("http"):
        urls.add(u2)

print(f"Unique URLs to verify: {len(urls)}")

# Skip these (search result aggregators that don't need verification)
SKIP_HOSTS = {"medium.com", "www.linkedin.com", "www.youtube.com", "play.google.com", "reddit.com", "www.reddit.com", "www.scribd.com", "www.academia.edu", "maestra.ai", "www.narakeet.com", "discuss.huggingface.co", "www.emergentmind.com"}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def check_url(url, timeout=10):
    host = urllib.parse.urlparse(url).hostname or ""
    if host in SKIP_HOSTS:
        return url, "Skipped"
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            code = resp.getcode()
            if 200 <= code < 400:
                return url, f"OK ({code})"
            else:
                return url, f"Broken ({code})"
    except urllib.error.HTTPError as e:
        if e.code in (405, 403):  # HEAD not allowed, try GET
            try:
                req2 = urllib.request.Request(url, method="GET", headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req2, timeout=timeout, context=ctx) as resp:
                    code = resp.getcode()
                    if 200 <= code < 400:
                        return url, f"OK ({code})"
                    else:
                        return url, f"Broken ({code})"
            except Exception as e2:
                return url, f"Broken ({e2.__class__.__name__})"
        return url, f"Broken ({e.code})"
    except socket.timeout:
        return url, "Timeout"
    except Exception as e:
        return url, f"Broken ({e.__class__.__name__})"

results = {}
with ThreadPoolExecutor(max_workers=20) as ex:
    futures = {ex.submit(check_url, u): u for u in sorted(urls)}
    for i, fut in enumerate(as_completed(futures)):
        url, status = fut.result()
        results[url] = status
        if (i+1) % 20 == 0:
            print(f"  {i+1}/{len(urls)} done")

# Save
out = "/home/z/my-project/research/url_status.json"
with open(out, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved to {out}")

# Summary
from collections import Counter
status_cats = Counter()
for s in results.values():
    if s.startswith("OK"):
        status_cats["OK"] += 1
    elif s.startswith("Broken"):
        status_cats["Broken"] += 1
    elif s == "Timeout":
        status_cats["Timeout"] += 1
    elif s == "Skipped":
        status_cats["Skipped"] += 1
    else:
        status_cats["Other"] += 1
print("\nStatus breakdown:")
for k, v in status_cats.most_common():
    print(f"  {v:4d}  {k}")
