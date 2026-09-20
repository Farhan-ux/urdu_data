"""Parse all search result JSONs and consolidate unique entries."""
import json, os, re, glob
from collections import defaultdict

research_dir = "/home/z/my-project/research"
all_results = []

for fp in sorted(glob.glob(os.path.join(research_dir, "*.json"))):
    topic = os.path.basename(fp).replace(".json", "")
    try:
        with open(fp) as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERR {fp}: {e}")
        continue

    # data may be a list of result items
    items = data if isinstance(data, list) else data.get("results", data.get("data", []))
    if not isinstance(items, list):
        # try common nested
        items = []
    for it in items:
        if not isinstance(it, dict):
            continue
        url = it.get("url", "")
        name = it.get("name", "") or it.get("title", "")
        snippet = it.get("snippet", "") or it.get("description", "")
        host = it.get("host_name", "") or it.get("hostname", "")
        date = it.get("date", "") or ""
        if not (url or name):
            continue
        all_results.append({
            "topic": topic,
            "url": url,
            "title": name,
            "snippet": snippet,
            "host": host,
            "date": date,
        })

print(f"Total raw entries: {len(all_results)}")

# Deduplicate by URL (then by title)
seen_urls = set()
seen_titles = set()
unique = []
for r in all_results:
    url = r["url"].lower().rstrip("/")
    title_key = re.sub(r"\W+", " ", r["title"].lower()).strip()
    if url and url in seen_urls:
        continue
    if title_key and title_key in seen_titles:
        continue
    seen_urls.add(url)
    seen_titles.add(title_key)
    unique.append(r)

print(f"Unique entries: {len(unique)}")

# Save consolidated
out_path = os.path.join(research_dir, "_consolidated.json")
with open(out_path, "w") as f:
    json.dump(unique, f, indent=2, ensure_ascii=False)
print(f"Saved to {out_path}")

# Quick breakdown by host
host_counts = defaultdict(int)
for r in unique:
    h = r["host"] or "unknown"
    host_counts[h] += 1
print("\nTop hosts:")
for h, c in sorted(host_counts.items(), key=lambda x: -x[1])[:25]:
    print(f"  {c:4d}  {h}")
